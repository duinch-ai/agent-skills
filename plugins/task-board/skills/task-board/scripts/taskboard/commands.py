"""CLI command handlers. Provider-neutral: remote behaviour is delegated to the provider adapter."""
import os
import sys
import time
from datetime import datetime

from .config import NEW_CONFIG_PATH, resolve_config
from .providers import get_provider
from .specs import (SpecStatusError, normalize_board_status, parse_local_specs, parse_spec_for_push,
                    update_local_spec_status_if_changed)
from .store import (DEFAULT_CACHE_TTL, get_cache_paths, load_json, save_json, update_cache_task_status)


def _setup(args, need_remote=True):
    config = resolve_config(args)
    provider = get_provider(config)
    if need_remote:
        provider.ensure_ready(config)
        provider.auto_sync(config)
    return config, provider


def _update_spec_or_exit(task_id, status, tasks_dir):
    """Update the local spec; a spec without a `Status:` line is a hard error (non-zero exit), not a silent success."""
    try:
        return update_local_spec_status_if_changed(task_id, status, tasks_dir)
    except SpecStatusError as e:
        raise SystemExit(f"error: cannot move {task_id}: {e}")


def cmd_list(args):
    local_only = getattr(args, "local_only", False)
    config, provider = _setup(args, need_remote=not local_only)
    cache_path, outbox_path = get_cache_paths(config)
    cache = load_json(cache_path, {}) if provider.uses_cache else {}
    force = getattr(args, "refresh", False) or getattr(args, "remote", False)
    ttl = getattr(args, "ttl", None)
    if ttl is None:
        ttl = int(os.environ.get("GH_PROJECT_CACHE_TTL", DEFAULT_CACHE_TTL))

    if local_only:
        tasks = parse_local_specs(config["tasks_dir"], config["backlog_doc"])
        banner = "📁 [LOCAL ONLY] Đọc từ local markdown specs (0 API calls)."
    else:
        tasks, _, _, banner = provider.sync_state(config, cache, cache_path, outbox_path, force=force, ttl=ttl)

    if args.status:
        target = normalize_board_status(args.status).lower()
        tasks = [
            t for t in tasks
            if t["status"].lower() == target
            or (target == "todo" and t.get("raw_status", "").strip().upper() == "TODO")
        ]

    print(f"{banner}\n")
    for t in tasks:
        phase_short = t.get("phase", "P0").split("—")[0].strip()
        print(f"#{str(t.get('issue_number', '?')):<3} | {t['status']:<12} | {phase_short:<6} | {t['title']}")

    outbox = load_json(outbox_path, []) if provider.uses_cache else []
    suffix = f" (Pending outbox sync: {len(outbox)})" if outbox else ""
    print(f"\nTotal: {len(tasks)} task(s){suffix}")


def cmd_move(args):
    config, provider = _setup(args)
    cache_path, outbox_path = get_cache_paths(config)
    task_id = args.task_id.upper()
    target_status = normalize_board_status(args.status)

    # Local-first: update the spec file immediately
    _update_spec_or_exit(task_id, target_status, config["tasks_dir"])
    cache = {}
    if provider.uses_cache:
        cache = load_json(cache_path, {})
        update_cache_task_status(task_id, target_status, cache, cache_path)
    provider.move(config, task_id, target_status, cache, cache_path, outbox_path)


def cmd_push(args):
    config, provider = _setup(args)
    cache_path, outbox_path = get_cache_paths(config)
    spec_path = args.spec_file
    if not os.path.exists(spec_path):
        raise SystemExit(f"Spec file not found: {spec_path}")

    task_id, header, content, phase_code = parse_spec_for_push(spec_path)
    board_status = normalize_board_status(args.status)
    _update_spec_or_exit(task_id, board_status, config["tasks_dir"])
    if provider.uses_cache:
        update_cache_task_status(task_id, board_status, load_json(cache_path, {}), cache_path)
    spec = {"task_id": task_id, "header": header, "content": content,
            "phase_code": phase_code, "spec_path": spec_path}
    provider.push(config, spec, board_status, cache_path, outbox_path)


def cmd_sync(args):
    config, provider = _setup(args, need_remote=False)
    provider.ensure_ready(config)
    provider.sync(config, args)


def cmd_rate_limit(args):
    config, provider = _setup(args, need_remote=False)
    provider.ensure_ready(config)
    provider.rate_limit(config)


def cmd_daemon(args):
    """Background daemon: sleep until the rate-limit reset timestamp, then flush the outbox."""
    config, provider = _setup(args, need_remote=False)
    _, outbox_path = get_cache_paths(config)
    target_ts = getattr(args, "until", 0)
    pid_file = os.path.join(config.get("cache_dir", ".local-artifacts"), "auto_sync.pid")
    stamp = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # noqa: E731
    try:
        while time.time() < target_ts:
            if not load_json(outbox_path, []):
                print(f"[{stamp()}] Outbox is empty. Daemon exiting cleanly.")
                return
            time.sleep(min(15, max(1, target_ts - time.time())))
        time.sleep(3)  # buffer for the API to update counters
        print(f"[{stamp()}] Rate-limit reset time reached. Flushing outbox...")
        print(f"[{stamp()}] Finished auto-sync: {provider.flush_outbox(config)} tasks synced.")
    except Exception as e:
        print(f"[{stamp()}] Daemon error: {e}")
    finally:
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
            except Exception:
                pass


def cmd_report(args):
    """Render a Markdown status report of the board, tasks, rate limits, and outbox."""
    config, provider = _setup(args)
    cache_path, outbox_path = get_cache_paths(config)
    cache = load_json(cache_path, {}) if provider.uses_cache else {}
    tasks, _, _, banner = provider.sync_state(config, cache, cache_path, outbox_path, force=False, ttl=DEFAULT_CACHE_TTL)
    outbox = load_json(outbox_path, []) if provider.uses_cache else []

    groups = {s: [] for s in ["Backlog", "Todo", "In Progress", "Done", "Released"]}
    for t in tasks:
        groups.setdefault(t.get("status", "Backlog"), []).append(t)

    lines = provider.report_lines(config, cache, outbox, banner)
    for status_name, task_list in groups.items():
        if not task_list:
            continue
        preview = ", ".join(f"`{t['task_id']}`" for t in task_list[:6])
        if len(task_list) > 6:
            preview += f" ... (+{len(task_list) - 6} more)"
        lines.append(f"| **{status_name}** | {len(task_list)} | {preview} |")
    lines += ["", f"**Total Tracked Tasks**: {len(tasks)}"]
    print("\n".join(lines))


def cmd_init(args):
    """Write .agents/task-board.json for the chosen provider (default github)."""
    config = resolve_config(args)
    provider = get_provider(config)
    provider.ensure_ready(config)
    out_cfg = {"provider": provider.name}
    out_cfg.update(provider.init_config(config, args))
    out_cfg.update({
        "tasks_dir": config.get("tasks_dir") or "docs/tasks",
        "backlog_doc": config.get("backlog_doc") or "docs/BACKLOG.md",
        "cache_dir": config.get("cache_dir") or ".local-artifacts",
    })
    save_json(NEW_CONFIG_PATH, out_cfg)
    import json
    print(f"\nSaved configuration to {NEW_CONFIG_PATH}:")
    print(json.dumps(out_cfg, indent=2))
