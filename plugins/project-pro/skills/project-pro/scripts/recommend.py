"""Guided-mode recommendation engine: answers -> deterministic stack/architecture recommendation."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from catalog import PRODUCT_CATEGORIES, STACK_CATALOG
from recommend_rules import (
    ERRORS, GOAL_CATEGORY, GOALS, LANGUAGES, MAINTAINERS, NEEDS, NO_MATCH_ERRORS, NOTES, PLATFORMS, REASONS,
    RULES, UNSUPPORTED_LANGUAGES,
)

FIELDS = ("goal", "platforms", "needs", "known_languages", "maintainers", "existing_code")
DEFAULT_LOCALES = ["vi", "en"]


class RecommendError(Exception):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        self.message = message or ERRORS[code]
        super().__init__(f"{code}: {self.message}")


def load_answers(src: str) -> dict[str, Any]:
    """Read an answers JSON object from a file path or `-` (stdin)."""
    try:
        raw = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise RecommendError("invalid-answers", f"cannot read answers from {src!r}: {exc}") from exc
    if not isinstance(data, dict):
        raise RecommendError("invalid-answers", "answers must be a JSON object")
    return data


def _check_list(answers: dict[str, Any], field: str, allowed: tuple[str, ...]) -> list[str]:
    value = answers.get(field, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise RecommendError("invalid-answers", f"'{field}' must be a list of strings from: {', '.join(allowed)}")
    bad = [v for v in value if v not in allowed]
    if bad:
        raise RecommendError("invalid-answers", f"unknown {field} value(s) {', '.join(map(repr, bad))}; allowed: {', '.join(allowed)}")
    return sorted(set(value))


def validate_answers(answers: dict[str, Any]) -> dict[str, Any]:
    unknown = sorted(set(answers) - set(FIELDS))
    if unknown:
        raise RecommendError("invalid-answers", f"unknown field(s) {', '.join(unknown)}; allowed: {', '.join(FIELDS)}")
    goal = answers.get("goal")
    if goal is None:
        raise RecommendError("need-goal")
    if goal not in GOALS:
        raise RecommendError("invalid-answers", f"unknown goal {goal!r}; allowed: {', '.join(GOALS)}")
    maintainers = answers.get("maintainers")
    if maintainers is not None and maintainers not in MAINTAINERS:
        raise RecommendError("invalid-answers", f"unknown maintainers {maintainers!r}; allowed: {', '.join(MAINTAINERS)}")
    existing = answers.get("existing_code", "auto")
    if existing != "auto":
        raise RecommendError("invalid-answers", f"unknown existing_code {existing!r}; allowed: auto")
    langs = [x for x in _check_list(answers, "known_languages", LANGUAGES) if x != "none"]
    return {
        "goal": goal, "platforms": _check_list(answers, "platforms", PLATFORMS),
        "needs": _check_list(answers, "needs", NEEDS), "known_languages": langs,
        "maintainers": maintainers, "existing_code": existing,
    }


def _matches(when: dict[str, Any], a: dict[str, Any]) -> bool:
    plat, knows, needs = set(a["platforms"]), set(a["known_languages"]), set(a["needs"])
    return (
        when["goal"] == a["goal"]
        and set(when.get("platforms_all", ())) <= plat
        and (not when.get("platforms_any") or plat & set(when["platforms_any"]))
        and not plat & set(when.get("platforms_none_of", ()))
        and (not when.get("knows_any") or knows & set(when["knows_any"]))
        and not knows & set(when.get("knows_none_of", ()))
        and (not when.get("needs_any") or needs & set(when["needs_any"]))
        and ("maintainers" not in when or when["maintainers"] == a["maintainers"])
    )


def _reasons(codes: list[str]) -> list[dict[str, str]]:
    return [{"code": c, "text": REASONS[c]} for c in codes]


def _notes(codes: list[str], a: dict[str, Any], stack: str | None = None) -> list[dict[str, str]]:
    return [{"code": c, "text": NOTES[c].format(langs=", ".join(a["known_languages"]), stack=stack)} for c in codes]


def recommend(answers: dict[str, Any], detected_stack: str | None = None) -> dict[str, Any]:
    """Pure function: same answers (+ same detected stack) always give the same result."""
    a = validate_answers(answers)
    if a["goal"] == "unsure" and not detected_stack:
        raise RecommendError("need-goal")
    goal = a["goal"]
    category = GOAL_CATEGORY.get(goal)
    rule = next((r for r in RULES if _matches(r["when"], a)), None) if goal != "unsure" else None
    note_codes: list[str] = list(rule["notes"]) if rule else []
    if detected_stack in STACK_CATALOG:
        stack, reason_codes, alternative = detected_stack, ["existing-code"], None
        if category and stack not in PRODUCT_CATEGORIES[category]["recommended_stacks"]:
            note_codes = ["existing-stack-unusual"]
        else:
            note_codes = []
    elif rule is None:
        raise RecommendError(NO_MATCH_ERRORS.get(goal, "need-goal"))
    else:
        stack, reason_codes = rule["stack"], list(rule["reasons"])
        alternative = rule["alternative"]
    info = STACK_CATALOG[stack]
    features_add: list[str] = []
    if "multi-language-ui" in a["needs"]:
        features_add.append("i18n")
        reason_codes.append("multi-language-ui")
    supported = set(LANGUAGES) - set(UNSUPPORTED_LANGUAGES) - {"none"}
    unsupported = [x for x in a["known_languages"] if x in UNSUPPORTED_LANGUAGES]
    if unsupported and not set(a["known_languages"]) & supported:
        note_codes.append("unsupported-language")
        a_notes = {**a, "known_languages": unsupported}
    else:
        a_notes = a
    return {
        "stack": stack, "category": category or _default_category(stack),
        "arch": info["recommended_arch"], "pattern": info["recommended_pattern"],
        "preset": "guided", "features_add": features_add,
        "locales": list(DEFAULT_LOCALES) if features_add else [],
        "reasons": _reasons(reason_codes),
        "alternative": {"stack": alternative["stack"], "reasons": _reasons(alternative["reasons"])} if alternative else None,
        "notes": _notes(note_codes, a_notes, stack),
    }


def _default_category(stack: str) -> str:
    return {"android": "mobile-app", "ios": "mobile-app", "kmp": "multiplatform-app", "flutter": "multiplatform-app",
            "web": "web-app", "python": "backend-api", "go": "backend-api", "nestjs": "backend-api",
            "rust": "desktop-app", "cpp-switch": "embedded-homebrew"}[stack]
