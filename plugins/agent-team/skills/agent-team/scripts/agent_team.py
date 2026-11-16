#!/usr/bin/env python3
"""agent-team CLI: init | verify | review | gate | report | status (Python 3 stdlib only)."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
import gate  # noqa: E402
import init_cmd  # noqa: E402
import report  # noqa: E402
import review_same  # noqa: E402
import review  # noqa: E402
import store  # noqa: E402
import tasks  # noqa: E402
import verify  # noqa: E402


def build_parser():
    p = argparse.ArgumentParser(prog="agent_team.py", description=__doc__)
    p.add_argument("--root", default=".", help="repository root (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init", help="write config, .gitignore entry, subagent templates")
    s.add_argument("--force", action="store_true")
    s.add_argument("--profile", choices=config.PROFILES, default="dev",
                   help="workspace profile preset (default: dev)")
    s.add_argument("--verify-skill", action="store_true",
                   help="scaffold .agents/skills/verify-app/ with feature map template")
    for name, hlp in (("verify", "run every check: of a task"), ("review", "cross-vendor review"),
                      ("gate", "done-gate for a task"), ("lint", "check a task spec is verifiable")):
        s = sub.add_parser(name, help=hlp)
        s.add_argument("task")
        s.add_argument("--cwd", help="worktree to operate in (default: root)")
        if name == "verify":
            s.add_argument("--repro-before", action="store_true",
                           help="run the repro only; passes when it FAILS (bug exists)")
        if name == "review":
            s.add_argument("--coder", help="vendor that wrote the code (default: Coder: field in the task)")
            s.add_argument("--prompt", action="store_true",
                           help="same-vendor: print the review prompt and schema for the reviewer subagent")
            s.add_argument("--record", metavar="FILE",
                           help="same-vendor: record the reviewer subagent's JSON verdict from FILE")
            s.add_argument("--reviewer", help="same-vendor: reviewer subagent name (default: subagent)")
        if name == "gate":
            s.add_argument("--no-audit", action="store_true")
    s = sub.add_parser("report", help="markdown morning report")
    s.add_argument("--since", help="e.g. 24h, 7d")
    sub.add_parser("status", help="one line per task")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    ctx = config.Ctx(a.root)
    if a.cmd == "init":
        print("\n".join(init_cmd.init(ctx, a.force, profile=a.profile, verify_skill=a.verify_skill)))
        return 0
    if a.cmd == "report":
        since = report.parse_since(a.since) if a.since else None
        print(report.render(report.collect(ctx, since), root=ctx.root), end="")
        return 0
    if a.cmd == "status":
        for r in report.collect(ctx):
            print(f"{r['id']:<12} {r['state']:<18} {r['why']}")
        return 0
    task = tasks.load_task(ctx, a.task)
    cwd = Path(a.cwd).resolve() if a.cwd else ctx.root
    if a.cmd == "lint":
        probs = tasks.lint_task(task)
        print("\n".join(probs) if probs else "ok")
        sugg = tasks.suggest_checks(ctx) if tasks.needs_suggestions(task) else []
        if sugg:
            print("suggested checks (from .agents/project-profile.json; review and paste manually):")
            print("\n".join(f"  {x}" for x in sugg))
        return 1 if probs else 0
    if a.cmd == "verify":
        res = verify.verify_task(ctx, task, cwd, a.repro_before)
        for r in res["results"]:
            print(f"[{'PASS' if r['ok'] else 'FAIL'}] {r.get('criterion', 'repro')}: {r['cmd']}")
            if not r["ok"]:
                print(r["output_tail"])
        for h in res.get("escape_hatches") or []:
            print(f"warn: escape-hatch {h['file']} [{h['rule']}]: {h['line']}")
        print(f"{res['label']}: {'OK' if res['ok'] else 'NOT OK'} -> {res['path']}")
        return 0 if res["ok"] else 1
    if a.cmd == "review":
        mode = ctx.cfg["review_mode"]
        if mode == "cross-vendor" and (a.prompt or a.record or a.reviewer):
            print("error: --prompt/--record/--reviewer apply to review_mode 'same-vendor'; "
                  "set review_mode in .agent-team/config.json", file=sys.stderr)
            return 2
        if mode == "same-vendor":
            return review_same.run(ctx, task, cwd, a)
        path, rec = review.review_task(ctx, task, cwd, a.coder)
        print(f"{rec['vendor']}: {rec['verdict']} ({len(rec['findings'])} findings) -> {path}")
        return 0 if rec["verdict"] == "approve" else 1
    ok, reasons, warns = gate.evaluate(ctx, task, cwd, run_audit=not a.no_audit)
    board_msg = None
    if ok:
        board_msg, board_warn = gate.move_task_board_done(ctx.root, task.id)
        if board_warn:
            warns.append(board_warn)
    for w in warns:
        print(f"warn: {w}")
    print("GATE PASSED" if ok else "GATE FAILED")
    if board_msg:
        print(board_msg)
    for r in reasons:
        print(f"- {r}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
