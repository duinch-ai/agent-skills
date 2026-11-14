"""Provider registry. Add a provider by writing a Provider subclass and listing it here."""
import importlib

_REGISTRY = {
    "github": ("taskboard.providers.github", "GithubProvider"),
    "gitlab": ("taskboard.providers.gitlab", "GitlabProvider"),
    "local": ("taskboard.providers.local", "LocalProvider"),
}


def get_provider(config_or_name):
    name = config_or_name if isinstance(config_or_name, str) else config_or_name.get("provider")
    name = (name or "github").lower()
    if name not in _REGISTRY:
        raise SystemExit(f"Unknown provider '{name}'. Valid providers: {', '.join(sorted(_REGISTRY))}")
    module, cls = _REGISTRY[name]
    return getattr(importlib.import_module(module), cls)()
