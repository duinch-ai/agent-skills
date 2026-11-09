#!/usr/bin/env python3
"""
project-pro CLI — Thin modular entrypoint (100% Python 3 Standard Library).
Subcommands: detect, lookup, init, wizard, map, audit, report, check-commit-msg, agent-guard.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from agent_guard import run_agent_guard
from auditor import audit_project, check_commit_message, format_audit_markdown
from catalog import ARCH_CHOICES, STACK_CATALOG
from detector import detect_project, format_lookup_markdown, generate_codebase_map
from scaffolder import init_project
from wizard import run_wizard


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="project-pro CLI: Detect, Lookup Reference Repos, Init Agent/Security Harness, Map, Guard & Audit."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_det = sub.add_parser("detect", help="Detect greenfield vs brownfield, stack & existing agent/hook harness.")
    p_det.add_argument("--target", default=".", help="Project directory path")

    p_lkp = sub.add_parser("lookup", help="Lookup curated gold-standard reference repos & patterns for a stack.")
    p_lkp.add_argument("--stack", choices=[*STACK_CATALOG.keys(), "all"], default="all")
    p_lkp.add_argument("--query", default=None, help="Optional topic to generate GitHub code search queries")
    p_lkp.add_argument("--json", action="store_true", help="Output raw JSON")

    p_init = sub.add_parser("init", help="Initialize multi-agent harness, security hooks, profile & optional directories.")
    p_init.add_argument("--target", default=".", help="Target project directory")
    p_init.add_argument("--stack", choices=list(STACK_CATALOG.keys()), required=True)
    p_init.add_argument("--arch", choices=[k for k, _ in ARCH_CHOICES], default=None)
    p_init.add_argument("--pattern", default=None, help="Presentation/flow pattern (e.g. mvi, mvvm-udf, tca, bloc, fsd)")
    p_init.add_argument(
        "--features",
        default=None,
        help="Comma-separated base feature IDs (Rust defaults to the multi-platform CI workflow)",
    )
    p_init.add_argument(
        "--agents",
        default="agents-root,persistent-memory,claude-gemini,git-security-hooks,agent-runtime-hooks,adr-docs",
        help="Comma-separated agent & hook targets ticked by user",
    )
    p_init.add_argument("--ref-repo", default=None, help="Override reference GitHub repo (owner/name)")
    p_init.add_argument("--name", default=None, help="Project display name")
    p_init.add_argument("--scaffold-dirs", action="store_true", help="Create canonical layer/module folders")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing harness files")

    p_wiz = sub.add_parser("wizard", help="Interactive terminal checkbox TUI to configure a project.")
    p_wiz.add_argument("--target", default=".", help="Target project directory")
    p_wiz.add_argument("--force", action="store_true", help="Overwrite existing harness files")

    p_map = sub.add_parser("map", help="Generate compact Codebase Architecture Map (.agents/CODEBASE_MAP.md).")
    p_map.add_argument("--target", default=".", help="Target project directory")
    p_map.add_argument("--write", action="store_true", help="Write directly to <target>/.agents/CODEBASE_MAP.md")

    p_aud = sub.add_parser("audit", help="Audit project for Secrets, OWASP, Domain leaks, God-files & Agent Harness.")
    p_aud.add_argument("--target", default=".", help="Target project directory")
    p_aud.add_argument("--warn-lines", type=int, default=300, help="Soft warning threshold for file LOC")
    p_aud.add_argument("--max-lines", type=int, default=450, help="Hard failure threshold for file LOC")
    p_aud.add_argument("--staged", action="store_true", help="Scan only Git staged files (fast pre-commit mode)")
    p_aud.add_argument("--json", action="store_true", help="Output raw JSON")
    p_aud.add_argument("--fail-on-error", action="store_true", help="Exit code 1 if blocking errors exist")

    p_rep = sub.add_parser("report", help="Render real-time Markdown dashboard of project architecture & security status.")
    p_rep.add_argument("--target", default=".", help="Target project directory")

    p_msg = sub.add_parser("check-commit-msg", help="Validate Conventional Commits & scan commit msg for secrets.")
    p_msg.add_argument("--file", required=True, help="Path to .git/COMMIT_EDITMSG")

    sub.add_parser("agent-guard", help="PreToolUse runtime hook guard for Antigravity & Claude Code.")
    return p


def main() -> int:
    args = build_parser().parse_args()

    if args.cmd == "detect":
        print(json.dumps(detect_project(Path(args.target)), indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "lookup":
        if args.json:
            payload = STACK_CATALOG if args.stack == "all" else {args.stack: STACK_CATALOG[args.stack]}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(format_lookup_markdown(args.stack, args.query))
        return 0

    if args.cmd == "init":
        info = STACK_CATALOG[args.stack]
        default_features = "solid-dry,typed-errors,di-core,network-storage,ui-nav,arch-lint"
        if args.stack == "rust":
            default_features += ",testing-ci"
        results = init_project(
            target=Path(args.target),
            stack=args.stack,
            arch=args.arch or info["recommended_arch"],
            pattern=args.pattern or info["recommended_pattern"],
            features=[
                x.strip()
                for x in (args.features if args.features is not None else default_features).split(",")
                if x.strip()
            ],
            agents=[x.strip() for x in args.agents.split(",") if x.strip()],
            ref_repo=args.ref_repo,
            project_name=args.name,
            scaffold_dirs=args.scaffold_dirs,
            force=args.force,
        )
        print("\n".join(results))
        return 0

    if args.cmd == "wizard":
        return run_wizard(Path(args.target), force=args.force)

    if args.cmd == "map":
        md = generate_codebase_map(Path(args.target), write_file_out=args.write)
        print(f"WRITE: {Path(args.target).resolve() / '.agents' / 'CODEBASE_MAP.md'}" if args.write else md)
        return 0

    if args.cmd == "audit":
        report = audit_project(Path(args.target), warn_lines=args.warn_lines, max_lines=args.max_lines, staged_only=args.staged)
        print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_audit_markdown(report))
        return 1 if (args.fail_on_error and report["errors"]) else 0

    if args.cmd == "report":
        target_p = Path(args.target).resolve()
        det = detect_project(target_p)
        aud = audit_project(target_p)
        prof = det.get("existing_profile") or {}
        ok = sum(1 for v in det["harness_present"].values() if v)
        total = len(det["harness_present"])
        print(f"# 📊 Project Pro Dashboard — `{target_p.name}`\n\n| Metric | Value |\n|---|---|")
        print(f"| **Mode** | `{det['mode']}` |")
        print(f"| **Detected Stack** | `{det['stack_label'] or det['detected_stack'] or 'Unconfigured'}` |")
        print(f"| **Architecture / Pattern** | `{prof.get('architecture', det['recommended_arch'])}` / `{prof.get('pattern', det['recommended_pattern'])}` |")
        print(f"| **Reference Repo Anchor** | `{prof.get('referenceRepo', det['recommended_ref_repo'] or 'N/A')}` |")
        print(f"| **Agent & Hook Readiness** | `{ok}/{total}` files active |")
        print(f"| **Audit & Security Gate** | **`{aud['status']}`** (`{len(aud['errors'])}` errors, `{len(aud['warnings'])}` warnings) |\n")
        print(format_audit_markdown(aud))
        return 0

    if args.cmd == "check-commit-msg":
        return check_commit_message(Path(args.file))

    if args.cmd == "agent-guard":
        return run_agent_guard()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
