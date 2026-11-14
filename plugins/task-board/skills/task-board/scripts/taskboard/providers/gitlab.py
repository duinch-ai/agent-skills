"""GitLab provider stub. Intentionally has no API calls: details must come from official GitLab docs."""
from .base import Provider

MESSAGE = "GitLab provider not implemented yet. Use provider 'local' (or 'github') in .agents/task-board.json."


class GitlabProvider(Provider):
    name = "gitlab"
    label = "GitLab (not implemented)"
    uses_cache = False

    def ensure_ready(self, config):
        raise SystemExit(MESSAGE)

    def _unsupported(self, *a, **k):
        raise SystemExit(MESSAGE)

    sync_state = move = push = sync = rate_limit = report_lines = init_config = _unsupported
