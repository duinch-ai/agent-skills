"""Local cache + offline outbox (formats unchanged) and the background daemon launcher."""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

DEFAULT_CACHE_TTL = 120  # seconds
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "project_board.py")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_cache_paths(config):
    cache_dir = config.get("cache_dir", ".local-artifacts")
    return (
        os.path.join(cache_dir, "project_board_cache.json"),
        os.path.join(cache_dir, "project_board_outbox.json"),
    )


def update_cache_task_status(task_id, target_status, cache, cache_path):
    """Keep local cache snapshot in sync with immediate mutation."""
    items_cache = cache.setdefault("items", {})
    if task_id in items_cache:
        items_cache[task_id]["status"] = target_status
    else:
        items_cache[task_id] = {"status": target_status}

    snapshot = cache.get("board_snapshot", {})
    for item in snapshot.get("items", []):
        if item.get("task_id") == task_id:
            item["status"] = target_status
            item["raw_status"] = target_status
            break
    save_json(cache_path, cache)


def spawn_auto_sync_daemon(config, target_reset_ts):
    """Spawn a detached background process that pushes the outbox once the rate limit recovers."""
    cache_dir = config.get("cache_dir", ".local-artifacts")
    pid_file = os.path.join(cache_dir, "auto_sync.pid")
    log_file = os.path.join(cache_dir, "auto_sync.log")

    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            return old_pid
        except (ProcessLookupError, ValueError):
            pass
        except PermissionError:
            return None

    os.makedirs(cache_dir, exist_ok=True)
    # Global flags must come BEFORE the subcommand (argparse rejects them after it).
    cmd = [sys.executable, SCRIPT_PATH, "--cache-dir", cache_dir]
    for flag, key in (
        ("--provider", "provider"),
        ("--tasks-dir", "tasks_dir"),
        ("--backlog-doc", "backlog_doc"),
        ("--owner", "owner"),
        ("--repo", "repo"),
        ("--project-id", "project_id"),
    ):
        if config.get(key):
            cmd.extend([flag, str(config[key])])
    if config.get("project_number"):
        cmd.extend(["--project", str(config["project_number"])])
    cmd.extend(["daemon", "--until", str(int(target_reset_ts))])

    try:
        log_fp = open(log_file, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd, stdout=log_fp, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True
        )
        log_fp.close()
        with open(pid_file, "w") as f:
            f.write(str(proc.pid))
        return proc.pid
    except Exception as e:
        print(f"[WARN] Không thể khởi động background auto-sync daemon: {e}")
        return None


def enqueue_outbox(entry, config, outbox_path, rate_limit_info=None):
    """Save an unexecuted mutation to the outbox and schedule a background sync after quota reset.

    rate_limit_info: optional callable returning the provider's rate-limit dict (key `gql_reset`).
    """
    outbox = load_json(outbox_path, [])
    outbox = [
        item
        for item in outbox
        if not (item.get("task_id") == entry.get("task_id") and item.get("action") == entry.get("action"))
    ]
    entry["queued_at"] = datetime.now(timezone.utc).isoformat()
    outbox.append(entry)
    save_json(outbox_path, outbox)

    rl = rate_limit_info() if rate_limit_info else None
    reset_ts = rl.get("gql_reset", 0) if rl else 0
    if not reset_ts or reset_ts <= time.time():
        reset_ts = time.time() + 300
    target_ts = reset_ts + 5
    wait_secs = max(5, int(target_ts - time.time()))
    reset_str = datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S")

    print(f"📦 [LOCAL SAVED] Đã lưu task vào hàng đợi cục bộ ({outbox_path}): {entry['action']} {entry['task_id']} -> {entry.get('status')}")
    pid = spawn_auto_sync_daemon(config, target_ts)
    if pid:
        print(f"🚀 [AUTO-SYNC DAEMON] Tiến trình ngầm (PID {pid}) đang chờ rate-limit reset lúc {reset_str} (còn ~{wait_secs}s) để tự động đẩy lên GitHub.")
