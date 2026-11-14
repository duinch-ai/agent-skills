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
    for name, hlp in (("verify", "run every check: of a task"), ("review", "cross-vendor review"),
                      ("gate", "done-gate for a task"), ("lint", "check a task spec is verifiable")):
        s = sub.add_parser(name, help=hlp)
        s.add_argument("task")
        s.add_argument("--cwd", help="worktree to operate in (default: root)")
        if name == "verify":
            s.add_argument("--repro-before", action="store_true",
                           help="run the repro only; passes when it FAILS (bug exists)")
        if name == "review":
            s.add_argument("--coder", help="vendor that wrote the code (default: config coder_vendor)")
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
        print("\n".join(init_cmd.init(ctx, a.force)))
        return 0
    if a.cmd == "report":
        since = report.parse_since(a.since) if a.since else None
        print(report.render(report.collect(ctx, since)), end="")
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
        print(f"{res['label']}: {'OK' if res['ok'] else 'NOT OK'} -> {res['path']}")
        return 0 if res["ok"] else 1
    if a.cmd == "review":
        path, rec = review.review_task(ctx, task, cwd, a.coder)
        print(f"{rec['vendor']}: {rec['verdict']} ({len(rec['findings'])} findings) -> {path}")
        return 0 if rec["verdict"] == "approve" else 1
    ok, reasons, warns = gate.evaluate(ctx, task, cwd, run_audit=not a.no_audit)
    for w in warns:
        print(f"warn: {w}")
    print("GATE PASSED" if ok else "GATE FAILED")
    for r in reasons:
        print(f"- {r}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
