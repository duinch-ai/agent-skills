"""Guided wizard path: plain-language questions -> recommendation -> init (no technical jargon)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from catalog import STACK_CATALOG
from guided import format_summary, selection_from_result
from recommend import RecommendError, recommend
from scaffolder import init_project
from tasktracking import DEFAULT_PROVIDER

GOAL_CHOICES = [
    ("mobile-app", "A phone app (iPhone and/or Android)"),
    ("web-app", "A website or web app"),
    ("desktop-app", "A program for Windows, Mac or Linux"),
    ("multiplatform-app", "One app that runs on phones AND computers"),
    ("backend-api", "A service behind the scenes that apps or websites talk to"),
    ("cli-tool", "A tool you run by typing commands"),
    ("bot", "A bot or automation that runs in the background"),
    ("library", "Reusable code that other developers will install"),
    ("embedded-homebrew", "A game or app for a console (Nintendo Switch homebrew)"),
    ("unsure", "I am not sure yet"),
]
PLATFORM_CHOICES = [
    ("ios", "iPhone / iPad", False), ("android", "Android phones", False), ("web", "Web browser", False),
    ("windows", "Windows", False), ("macos", "Mac", False), ("linux", "Linux", False), ("switch", "Nintendo Switch", False),
]
NEED_CHOICES = [
    ("offline", "Works without internet", False), ("realtime", "Live updates (chat, live data)", False),
    ("many-users", "Many people using it at the same time", False),
    ("multi-language-ui", "Screens shown in several languages", False), ("heavy-compute", "Heavy number crunching or processing", False),
]
LANGUAGE_CHOICES = [
    ("kotlin", "Kotlin", False), ("swift", "Swift", False), ("dart", "Dart", False), ("typescript", "TypeScript", False),
    ("javascript", "JavaScript", False), ("python", "Python", False), ("go", "Go", False), ("rust", "Rust", False),
    ("cpp", "C++", False), ("java", "Java", False), ("csharp", "C#", False), ("php", "PHP", False), ("ruby", "Ruby", False),
]
MAINTAINER_CHOICES = [
    ("solo-with-ai", "Just me, working with an AI assistant"), ("small-team", "A small team (2-5 people)"),
    ("team", "A larger team"),
]
CONFIRM_CHOICES = [("yes", "Yes, use this recommendation"), ("alt", "Use the alternative instead"),
                   ("expert", "Switch to expert mode and choose everything myself")]


def collect_answers(select_single: Callable, select_multi: Callable) -> dict[str, Any]:
    goal = select_single("1. What do you want to build?", GOAL_CHOICES, "mobile-app")
    answers: dict[str, Any] = {"goal": goal}
    if goal == "unsure":
        return answers
    answers["platforms"] = select_multi("2. Where should it run? (tick all that apply)", PLATFORM_CHOICES)
    answers["needs"] = select_multi("3. Does it need any of these? (tick all that apply)", NEED_CHOICES)
    answers["known_languages"] = select_multi("4. Which programming languages do you already know? (tick none if you are new)", LANGUAGE_CHOICES)
    answers["maintainers"] = select_single("5. Who will work on it?", MAINTAINER_CHOICES, "solo-with-ai")
    return answers


def run_guided(target: Path, det: dict[str, Any], force: bool, select_single: Callable, select_multi: Callable) -> int | None:
    """Return an exit code, or None when the user asked to switch to expert mode."""
    answers = collect_answers(select_single, select_multi)
    try:
        result = recommend(answers, det["detected_stack"])
    except RecommendError as exc:
        print(f"\n{exc.message}")
        return 2
    print(f"\n{format_summary(result)}\n")
    choice = select_single("6. Use this?", CONFIRM_CHOICES if result["alternative"] else [CONFIRM_CHOICES[0], CONFIRM_CHOICES[2]], "yes")
    if choice == "expert":
        return None
    sel = selection_from_result(result, {"stack": result["alternative"]["stack"]} if choice == "alt" else None)
    info = STACK_CATALOG[sel["stack"]]
    created = init_project(
        target=target, stack=sel["stack"], arch=sel["arch"] or info["recommended_arch"],
        pattern=sel["pattern"] or info["recommended_pattern"], features=sel["features"], agents=sel["agents"],
        scaffold_dirs=det["mode"] == "greenfield", force=force, locales=sel["locales"],
        category=sel["category"], task_provider=DEFAULT_PROVIDER, preset=sel["preset"],
    )
    print("\n=== Done: your project is set up ===")
    for line in created:
        print(f"  {line}")
    return 0
