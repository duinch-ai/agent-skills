"""Remote -> local state sync for GitHub Projects v2, guarded by TTL cache and rate-limit checks."""
import json
import re
import sys
import time
from datetime import datetime

from ..specs import SpecStatusError, normalize_board_status, parse_local_specs, update_local_spec_status_if_changed
from ..store import DEFAULT_CACHE_TTL, load_json, save_json
from .github_api import get_rate_limit_info
from .runner import run_gh


def _local(config):
    return parse_local_specs(config["tasks_dir"], config["backlog_doc"])


def sync_project_state(config, cache, cache_path, outbox_path, force=False, ttl=DEFAULT_CACHE_TTL):
    """Return (tasks, is_fresh, code, banner) from cache, GitHub Project v2, or local specs."""
    snapshot = cache.get("board_snapshot", {})
    synced_at = snapshot.get("synced_at", 0)
    cached_items = snapshot.get("items", [])
    age = int(time.time() - synced_at)

    if not force and cached_items and age < ttl:
        rem_ttl = max(0, ttl - age)
        return (
            cached_items, False, "cache_hit",
            f"📦 [CACHE] Trạng thái GitHub Project (đồng bộ {age}s trước, cache hiệu lực thêm {rem_ttl}s. Dùng --refresh để ép fetch)",
        )

    rl = get_rate_limit_info()
    if rl and (rl.get("gql_remaining", 0) <= 5 or rl.get("core_remaining", 0) <= 5):
        if cached_items:
            reset_ts = rl.get("gql_reset", 0) or rl.get("core_reset", 0)
            reset_str = datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S") if reset_ts else "sắp tới"
            return (
                cached_items, False, "rate_limited",
                f"⚠️ [RATE-LIMIT SHIELD] API quota gần cạn. Dùng dữ liệu cache từ {datetime.fromtimestamp(synced_at).strftime('%H:%M:%S')} (reset lúc {reset_str}).",
            )
        return _local(config), False, "rate_limited", "⚠️ [RATE-LIMIT SHIELD] API quota gần cạn. Dùng dữ liệu markdown cục bộ."

    project_number, owner = config.get("project_number"), config.get("owner")
    if not project_number or not owner:
        return _local(config), False, "no_config", "📁 [LOCAL] Chưa cấu hình project_number/owner. Dùng dữ liệu local specs."

    rc, out, err = run_gh(
        ["gh", "project", "item-list", str(project_number), "--owner", owner, "--limit", "150", "--format", "json"],
        check=False,
    )
    if rc == 0:
        parsed, reconciled = _parse_remote(json.loads(out).get("items", []), config, cache, outbox_path)
        cache["board_snapshot"] = {"synced_at": time.time(), "items": parsed}
        save_json(cache_path, cache)
        rec_msg = f" (đã tự động cập nhật {reconciled} local spec)" if reconciled > 0 else ""
        return (
            parsed, True, "success",
            f"⚡ [REMOTE SYNC] Đã đồng bộ mới nhất từ GitHub Project #{project_number}{rec_msg} (Cache TTL: {ttl}s)",
        )

    scope_missing = "missing required scopes" in err or "INSUFFICIENT_SCOPES" in err
    hint = " (Chạy 'gh auth refresh -s project,read:project' để cấp quyền Project Board)" if scope_missing else ""

    if cached_items:
        cache["board_snapshot"]["synced_at"] = time.time()
        save_json(cache_path, cache)
        return (
            cached_items, False, "error_fallback",
            f"⚠️ [FALLBACK] Không thể kết nối live Project{hint}. Dùng dữ liệu cache (TTL: {ttl}s).",
        )

    local_tasks = _local(config)
    cache["board_snapshot"] = {"synced_at": time.time(), "items": local_tasks}
    save_json(cache_path, cache)
    return (
        local_tasks, False, "local_fallback",
        f"📁 [LOCAL FALLBACK] Không thể kết nối live Project{hint}. Dùng dữ liệu local specs & lưu cache (TTL: {ttl}s).",
    )


def _parse_remote(remote_items, config, cache, outbox_path):
    """Convert `gh project item-list` items to task records; reconcile local spec status."""
    parsed = []
    items_cache = cache.setdefault("items", {})
    pending_ids = {e.get("task_id") for e in load_json(outbox_path, []) if e.get("task_id")}
    reconciled = 0
    for i in remote_items:
        title = i.get("title", "")
        m = re.match(r"^([A-Za-z0-9]+-\d+)", title)
        tid = m.group(1).upper() if m else None
        if not tid:
            continue
        issue_num = i.get("content", {}).get("number")
        status = normalize_board_status(i.get("status", "Backlog"))
        phase = i.get("phase", "P0")
        items_cache[tid] = {"item_id": i.get("id"), "issue_number": issue_num, "status": status, "phase": phase}
        parsed.append({
            "task_id": tid, "issue_number": issue_num or "?", "status": status,
            "raw_status": status, "phase": phase, "title": title,
        })
        if tid not in pending_ids:
            try:
                if update_local_spec_status_if_changed(tid, status, config["tasks_dir"]):
                    reconciled += 1
            except SpecStatusError as e:  # keep syncing the rest of the board; surface the broken spec
                print(f"warning: {e}", file=sys.stderr)

    def sort_key(t):
        num = re.search(r"\d+", t["task_id"])
        return int(num.group(0)) if num else 0

    parsed.sort(key=sort_key)
    return parsed, reconciled
