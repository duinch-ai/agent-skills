"""Resolve `init` feature/agent selections: presets (minimal|recommended|all) and the `all` token."""

from __future__ import annotations

from catalog import (
    AGENT_CHOICES,
    FEATURE_CHOICES,
    PRESET_GUIDED_AGENTS,
    PRESET_GUIDED_FEATURES,
    PRESET_MINIMAL_AGENTS,
    PRESET_MINIMAL_FEATURES,
    PRESET_RECOMMENDED_AGENTS,
    PRESET_RECOMMENDED_FEATURES,
)

ALL_TOKENS = {"a", "all", "*"}


def applicable_features(stack: str, category: str | None = None) -> list[str]:
    """Every feature id applicable to the stack/category.

    The catalog defines no per-stack exclusions (init accepts every feature on every stack; `testing-ci`
    only emits a workflow for rust and cpp-switch, and is a harmless flag elsewhere), so this is the full list.
    """
    return [key for key, _, _ in FEATURE_CHOICES]


def applicable_agents(stack: str, category: str | None = None) -> list[str]:
    return [key for key, _, _ in AGENT_CHOICES]


def preset_features(preset: str, stack: str, category: str | None = None) -> list[str]:
    if preset == "minimal":
        return list(PRESET_MINIMAL_FEATURES)
    if preset == "all":
        return applicable_features(stack, category)
    if preset == "guided":
        return list(PRESET_GUIDED_FEATURES)
    feats = list(PRESET_RECOMMENDED_FEATURES)
    return feats + ["testing-ci"] if stack == "rust" else feats


def preset_agents(preset: str, stack: str, category: str | None = None) -> list[str]:
    if preset == "minimal":
        return list(PRESET_MINIMAL_AGENTS)
    if preset == "all":
        return applicable_agents(stack, category)
    return list(PRESET_GUIDED_AGENTS if preset == "guided" else PRESET_RECOMMENDED_AGENTS)


def _split(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def resolve_selection(
    raw: str | None, preset: str, stack: str, category: str | None, kind: str
) -> list[str]:
    """Explicit `raw` (comma list or `all`) overrides the preset; `None` falls back to the preset."""
    if raw is None:
        return (preset_features if kind == "features" else preset_agents)(preset, stack, category)
    items = _split(raw)
    if any(x.lower() in ALL_TOKENS for x in items):
        everything = (applicable_features if kind == "features" else applicable_agents)(stack, category)
        return list(dict.fromkeys(everything + [x for x in items if x.lower() not in ALL_TOKENS]))
    return items
