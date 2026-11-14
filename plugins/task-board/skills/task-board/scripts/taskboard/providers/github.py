"""GitHub Projects v2 provider (behaviour of the former monolithic project_board.py)."""
import json
import re
import sys
from datetime import datetime

from ..specs import normalize_board_status
from ..store import DEFAULT_CACHE_TTL, enqueue_outbox, get_cache_paths, load_json, save_json
from . import github_api as api
from .base import Provider
from .github_flush import flush_outbox_entries, opportunistic_auto_sync
from .github_sync import sync_project_state
from .runner import run_gh


def _reset_str(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else "N/A"


class GithubProvider(Provider):
    name = "github"
    label = "GitHub Project"

    def sync_state(self, config, cache, cache_path, outbox_path, force=False, ttl=DEFAULT_CACHE_TTL):
        return sync_project_state(config, cache, cache_path, outbox_path, force=force, ttl=ttl)

    def auto_sync(self, config):
        opportunistic_auto_sync(config)

    def flush_outbox(self, config):
        return flush_outbox_entries(config)

    def move(self, config, task_id, status, cache, cache_path, outbox_path):
        try:
            api.set_status(config, cache, cache_path, task_id, status)
            print(f"Moved {task_id} -> [{status}] on GitHub Project #{config.get('project_number')} (1 GraphQL point)")
        except Exception as exc:
            print(f"[RATE-LIMIT / SCOPE GUARD] Deferred GitHub Project update ({str(exc).splitlines()[-1]}).")
            enqueue_outbox({"action": "move", "task_id": task_id, "status": status},
                           config, outbox_path, api.get_rate_limit_info)

    def push(self, config, spec, status, cache_path, outbox_path):
        task_id, phase_code = spec["task_id"], spec["phase_code"]
        rc, issue_url, err = api.create_issue(config, spec["header"], spec["content"], phase_code)
        if rc != 0:
            print(f"[RATE-LIMIT GUARD] Could not create remote issue right now ({err.splitlines()[-1] if err else 'error'}).")
            enqueue_outbox({"action": "push", "task_id": task_id, "spec_file": spec["spec_path"], "status": status},
                           config, outbox_path, api.get_rate_limit_info)
            return

        print(f"Created GitHub Issue for {task_id} -> {issue_url}")
        m = re.search(r"/issues/(\d+)$", issue_url.strip())
        issue_num = int(m.group(1)) if m else None
        cache = load_json(cache_path, {})
        try:
            api.attach_issue(config, cache, cache_path, task_id, issue_url, phase_code, status, issue_num=issue_num)
            print(f"Synced {task_id} ({status}) to GitHub Project #{config.get('project_number')}")
        except Exception as exc:
            print(f"[RATE-LIMIT / SCOPE GUARD] Issue created ({issue_url}), Project board card queued ({str(exc).splitlines()[-1]}).")
            enqueue_outbox({"action": "attach_issue", "task_id": task_id, "issue_url": issue_url,
                            "phase": phase_code, "status": status},
                           config, outbox_path, api.get_rate_limit_info)

    def sync(self, config, args):
        cache_path, outbox_path = get_cache_paths(config)
        print("🔄 [SYNC] Bắt đầu đồng bộ 2 chiều (Local <-> GitHub Project)...")
        flushed = self.flush_outbox(config)
        outbox = load_json(outbox_path, [])
        cache = load_json(cache_path, {})
        force = getattr(args, "refresh", True)
        ttl = getattr(args, "ttl", DEFAULT_CACHE_TTL)
        items, _, _, msg = sync_project_state(config, cache, cache_path, outbox_path, force=force, ttl=ttl)
        print(f"  • Local -> Remote: Đã đẩy {flushed} tác vụ ({len(outbox)} tác vụ còn tồn trong outbox).")
        print(f"  • Remote -> Local: {msg} (Tổng {len(items)} tác vụ).")

    def rate_limit(self, config):
        cache_path, outbox_path = get_cache_paths(config)
        rc, out, err = run_gh(["gh", "api", "rate_limit"], check=False)
        outbox = load_json(outbox_path, [])
        cache = load_json(cache_path, {})
        if rc != 0:
            print(f"GitHub API unreachable: {err}")
            return
        res = json.loads(out).get("resources", {})
        core, gql = res.get("core", {}), res.get("graphql", {})
        print(f"REST (core)   : {core.get('remaining', '?')}/{core.get('limit', '?')} remaining")
        print(f"GraphQL       : {gql.get('remaining', '?')}/{gql.get('limit', '?')} remaining (resets at {_reset_str(gql.get('reset', 0))})")
        print(f"Cached items  : {len(cache.get('items', {}))} task(s)")
        print(f"Pending outbox: {len(outbox)} mutation(s)")

    def report_lines(self, config, cache, outbox, sync_banner):
        rc, out, _ = run_gh(["gh", "api", "rate_limit"], check=False)
        core_rem = core_lim = gql_rem = gql_lim = "?"
        reset_str = "N/A"
        if rc == 0:
            res = json.loads(out).get("resources", {})
            core, gql = res.get("core", {}), res.get("graphql", {})
            core_rem, core_lim = core.get("remaining", "?"), core.get("limit", "?")
            gql_rem, gql_lim = gql.get("remaining", "?"), gql.get("limit", "?")
            reset_str = _reset_str(gql.get("reset", 0))
        return [
            "# 📊 GitHub Project Workflow Report",
            "",
            f"- **Repository**: `{config.get('owner') or 'N/A'}/{config.get('repo') or 'N/A'}`",
            f"- **Project Board**: `#{config.get('project_number') or 'N/A'}` (Node ID: `{config.get('project_id') or 'Not set'}`)",
            f"- **Spec Directory**: `{config['tasks_dir']}`",
            f"- **Sync State**: {sync_banner}",
            "",
            "## 🚦 API Rate-Limit Status",
            f"- **REST Core**: `{core_rem}/{core_lim}` remaining",
            f"- **GraphQL**: `{gql_rem}/{gql_lim}` remaining (resets at `{reset_str}`)",
            f"- **Pending Outbox**: `{len(outbox)}` mutations deferred",
            f"- **Cached Items**: `{len(cache.get('items', {}))}` tasks in local schema cache",
            "",
            "## 📋 Task Breakdown by Status",
            "| Status | Count | Tasks |",
            "|---|:---:|---|",
        ]

    def init_config(self, config, args):
        owner = getattr(args, "owner", None) or config["owner"]
        repo = getattr(args, "repo", None) or config["repo"]
        number = getattr(args, "project_number", None) or config["project_number"]
        if not owner or not repo:
            print("Error: Could not auto-detect owner/repo. Please specify --owner and --repo.", file=sys.stderr)
            sys.exit(1)
        project_id = config.get("project_id")
        if number and not project_id:
            print(f"Querying GitHub GraphQL for Project #{number} Node ID (owner: {owner})...")
            q = f"""
            query {{
              user(login: "{owner}") {{ projectV2(number: {number}) {{ id title }} }}
              organization(login: "{owner}") {{ projectV2(number: {number}) {{ id title }} }}
            }}
            """
            rc, out, _ = run_gh(["gh", "api", "graphql", "-f", f"query={q}"], check=False)
            if rc == 0:
                data = json.loads(out).get("data", {})
                proj = ((data.get("user") or {}).get("projectV2")) or ((data.get("organization") or {}).get("projectV2"))
                if proj:
                    project_id = proj["id"]
                    print(f"Found Project: '{proj.get('title')}' (Node ID: {project_id})")
        return {
            "owner": owner,
            "repo": repo,
            "project_number": str(number) if number else None,
            "project_id": project_id,
        }
