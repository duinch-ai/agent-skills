"""`init` subcommand: expert flow (explicit flags) and guided flow (answers -> recommendation)."""

from __future__ import annotations

import argparse
from pathlib import Path

from catalog import STACK_CATALOG
from guided import format_summary, run_recommend, selection_from_result
from presets import resolve_selection
from recommend import RecommendError, load_answers
from safety import safety_warnings
from scaffolder import init_project

OVERRIDE_FLAGS = ("stack", "arch", "pattern", "category", "features", "agents")


def _split_locales(raw: str | None) -> list[str]:
    return [x.strip() for x in (raw or "vi,en").split(",") if x.strip()]


def run_init(args: argparse.Namespace) -> int:
    target = Path(args.target)
    locales = _split_locales(args.locales)
    if args.mode == "guided":
        if not args.answers:
            print("error: --mode guided needs --answers <file|->")
            return 2
        try:
            result = run_recommend(load_answers(args.answers), target)
        except RecommendError as exc:
            print(f"error [{exc.code}]: {exc.message}")
            return 2
        print(format_summary(result))
        sel = selection_from_result(result, {k: getattr(args, k) for k in (*OVERRIDE_FLAGS, "preset")})
        if sel["overridden"]:
            print(f"NOTICE: explicit flags override the recommendation ({', '.join('--' + k for k in sel['overridden'])}); "
                  "expert semantics apply for those choices.")
        stack, category, preset = sel["stack"], sel["category"], sel["preset"]
        feat_list, agent_list = sel["features"], sel["agents"]
        arch, pattern = sel["arch"], sel["pattern"]
        if sel["locales"] and args.locales == "vi,en":
            locales = sel["locales"]
    else:
        stack, category, preset = args.stack, args.category, args.preset or "recommended"
        feat_list = resolve_selection(args.features, preset, stack, category, "features")
        agent_list = resolve_selection(args.agents, preset, stack, category, "agents")
        arch, pattern = args.arch, args.pattern
    info = STACK_CATALOG[stack]
    if args.i18n and "i18n" not in feat_list:
        feat_list.append("i18n")
    if preset == "guided":
        for warning in safety_warnings(feat_list, agent_list):
            print(warning)
    print(f"Resolved preset={preset}\n  features: {', '.join(feat_list)}\n  agents:   {', '.join(agent_list)}")
    results = init_project(
        target=target, stack=stack, arch=arch or info["recommended_arch"],
        pattern=pattern or info["recommended_pattern"], features=feat_list, agents=agent_list,
        ref_repo=args.ref_repo, project_name=args.name, scaffold_dirs=args.scaffold_dirs, force=args.force,
        locales=locales, category=category, task_provider=args.task_provider, go_module=args.go_module, preset=preset,
    )
    print("\n".join(results))
    return 0
