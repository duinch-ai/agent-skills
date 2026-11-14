"""Guided mode glue: plain-language summary, `recommend` command, answers -> init parameters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from catalog import STACK_CATALOG
from detector import detect_project
from presets import resolve_selection
from safety import safety_lines
from presets import preset_agents, preset_features
from recommend import RecommendError, load_answers, recommend


def detected_stack_for(target: Path, answers: dict[str, Any]) -> str | None:
    """`existing_code: auto` (the default): an existing, supported project in `target` wins."""
    if answers.get("existing_code", "auto") != "auto" or not target.exists():
        return None
    return detect_project(target)["detected_stack"]


def run_recommend(answers: dict[str, Any], target: Path) -> dict[str, Any]:
    return recommend(answers, detected_stack_for(target, answers))


def format_summary(result: dict[str, Any]) -> str:
    info = STACK_CATALOG[result["stack"]]
    lines = [f"Recommendation: {info['label']}", "", "Why:"]
    lines += [f"  - {r['text']}" for r in result["reasons"]]
    alt = result["alternative"]
    if alt:
        lines += ["", f"Alternative: {STACK_CATALOG[alt['stack']]['label']}"]
        lines += [f"  - {r['text']}" for r in alt["reasons"]]
    if result["notes"]:
        lines += ["", "Please note:"] + [f"  - {n['text']}" for n in result["notes"]]
    feats = preset_features(result["preset"], result["stack"]) + result["features_add"]
    lines += ["", "Safety net that will be switched on:"]
    lines += [f"  - {s}" for s in safety_lines(feats, preset_agents(result["preset"], result["stack"]))]
    lines += ["", f"Set-up that will be created: preset '{result['preset']}'"
              + (f" plus {', '.join(result['features_add'])}" if result["features_add"] else "")
              + ". Say 'expert' any time to choose every option yourself."]
    return "\n".join(lines)


def cmd_recommend(answers_src: str, target: Path, as_json: bool) -> int:
    try:
        result = run_recommend(load_answers(answers_src), target)
    except RecommendError as exc:
        if as_json:
            print(json.dumps({"error": {"code": exc.code, "message": exc.message}}, indent=2, ensure_ascii=False))
        else:
            print(f"error [{exc.code}]: {exc.message}")
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False) if as_json else format_summary(result))
    return 0


def selection_from_result(result: dict[str, Any], overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """init parameters from a recommendation; explicit CLI flags (non-None) in `overrides` win."""
    ov = {k: v for k, v in (overrides or {}).items() if v is not None}
    stack = ov.get("stack", result["stack"])
    stack_changed = stack != result["stack"]
    category = ov.get("category") or (None if stack_changed else result["category"])
    preset = ov.get("preset", result["preset"])
    feats = resolve_selection(ov.get("features"), preset, stack, category, "features")
    if "features" not in ov:
        feats += [f for f in result["features_add"] if f not in feats]
    return {
        "stack": stack, "category": category, "preset": preset, "features": feats,
        "agents": resolve_selection(ov.get("agents"), preset, stack, category, "agents"),
        "arch": ov.get("arch") or (None if stack_changed else result["arch"]),
        "pattern": ov.get("pattern") or (None if stack_changed else result["pattern"]),
        "locales": list(result["locales"]) or None,
        "overridden": sorted(k for k in ov if k in {"stack", "arch", "pattern", "category", "features", "agents"}),
    }
