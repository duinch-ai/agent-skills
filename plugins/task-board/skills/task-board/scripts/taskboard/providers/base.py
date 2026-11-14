"""Provider interface. The core calls only these methods; providers own all remote behaviour."""


class Provider:
    name = "base"
    label = "Base"
    uses_cache = True  # False: provider has no remote state, so no cache/outbox files are written

    def ensure_ready(self, config):
        """Raise SystemExit with a clear message when the provider cannot run."""

    def sync_state(self, config, cache, cache_path, outbox_path, force=False, ttl=120):
        """Return (tasks, is_fresh, code, banner)."""
        raise NotImplementedError

    def auto_sync(self, config):
        """Opportunistically flush the outbox (cheap no-op when empty)."""

    def flush_outbox(self, config):
        """Flush pending outbox entries; return the count flushed."""
        return 0

    def move(self, config, task_id, status, cache, cache_path, outbox_path):
        raise NotImplementedError

    def push(self, config, spec, status, cache_path, outbox_path):
        """spec: dict(task_id, header, content, phase_code, spec_path)."""
        raise NotImplementedError

    def sync(self, config, args):
        raise NotImplementedError

    def rate_limit(self, config):
        raise NotImplementedError

    def report_lines(self, config, cache, outbox, sync_banner):
        """Markdown lines placed above the task breakdown table."""
        raise NotImplementedError

    def init_config(self, config, args):
        """Return provider-specific fields for .agents/task-board.json."""
        return {}
