"""Local provider: Markdown specs only. No remote, no cache, no outbox, never touches `gh`."""
from ..specs import parse_local_specs
from .base import Provider

NO_REMOTE = "Provider 'local': no remote board configured, nothing to sync."


class LocalProvider(Provider):
    name = "local"
    label = "Local only"
    uses_cache = False

    def sync_state(self, config, cache, cache_path, outbox_path, force=False, ttl=120):
        tasks = parse_local_specs(config["tasks_dir"], config["backlog_doc"])
        return tasks, False, "local", "📁 [LOCAL] Provider local: đọc từ local markdown specs (0 API calls)."

    def move(self, config, task_id, status, cache, cache_path, outbox_path):
        print(f"Moved {task_id} -> [{status}] in local spec only (provider local, no remote).")

    def push(self, config, spec, status, cache_path, outbox_path):
        print(f"Provider 'local': {spec['task_id']} kept as local spec with status [{status}]; nothing pushed (no remote).")

    def sync(self, config, args):
        print(NO_REMOTE)

    def rate_limit(self, config):
        print("Provider 'local': no remote API, rate limits do not apply (0 API calls ever made).")

    def report_lines(self, config, cache, outbox, sync_banner):
        return [
            "# 📊 Task Board Report",
            "",
            "- **Provider**: `local` (no remote)",
            f"- **Spec Directory**: `{config['tasks_dir']}`",
            f"- **Sync State**: {sync_banner}",
            "",
            "## 🚦 API Rate-Limit Status",
            "- Not applicable (local provider makes no API calls).",
            "",
            "## 📋 Task Breakdown by Status",
            "| Status | Count | Tasks |",
            "|---|:---:|---|",
        ]
