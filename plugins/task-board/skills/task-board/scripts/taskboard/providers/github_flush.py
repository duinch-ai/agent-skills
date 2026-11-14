"""Flush the offline outbox to GitHub Projects."""
import os

from ..specs import parse_spec_for_push
from ..store import get_cache_paths, load_json, save_json
from . import github_api as api


def flush_outbox_entries(config):
    """Flush pending outbox entries to GitHub Project and remote repository."""
    cache_path, outbox_path = get_cache_paths(config)
    outbox = load_json(outbox_path, [])
    if not outbox:
        return 0

    cache = load_json(cache_path, {})
    remaining = []
    flushed = 0
    pnum = config.get("project_number")

    for entry in outbox:
        try:
            action = entry.get("action")
            task_id = entry.get("task_id")
            if action == "move":
                api.set_status(config, cache, cache_path, task_id, entry["status"], exit_on_invalid=False)
                print(f"Flushed move: {task_id} -> {entry['status']}")
            elif action == "attach_issue":
                api.attach_issue(config, cache, cache_path, task_id, entry["issue_url"],
                                 entry.get("phase", "P0"), entry["status"])
                print(f"Flushed attach_issue: {task_id} -> Project #{pnum}")
            elif action == "push":
                _, header, content, phase_code = parse_spec_for_push(entry["spec_file"])
                rc, issue_url, err = api.create_issue(config, header, content, phase_code)
                if rc != 0:
                    raise RuntimeError(f"Could not create issue: {err}")
                api.attach_issue(config, cache, cache_path, task_id, issue_url, phase_code, entry["status"])
                print(f"Flushed push: {task_id} -> Issue created & attached to Project #{pnum}")
            else:
                remaining.append(entry)
                continue
            flushed += 1
        except Exception as exc:
            print(f"Still deferred ({entry.get('task_id')}): {str(exc).splitlines()[-1]}")
            remaining.append(entry)

    save_json(outbox_path, remaining)
    return flushed


def opportunistic_auto_sync(config):
    """Automatically flush the outbox if rate limits have recovered."""
    _, outbox_path = get_cache_paths(config)
    if not os.path.exists(outbox_path) or not load_json(outbox_path, []):
        return
    rl = api.get_rate_limit_info()
    if rl and rl.get("gql_remaining", 0) > 5 and rl.get("core_remaining", 0) > 5:
        flushed = flush_outbox_entries(config)
        if flushed > 0:
            print(f"⚡ [AUTO-SYNC] Đã tự động đồng bộ {flushed} tác vụ từ outbox lên GitHub Project.")
