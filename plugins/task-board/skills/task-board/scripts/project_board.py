#!/usr/bin/env python3
"""task-board CLI: local-first task specs + backlog with pluggable remote providers.

Providers: github (Projects v2 via `gh`, rate-limit resilient), local (no remote), gitlab (stub).
Config: .agents/task-board.json (`provider` + fields); legacy .github/project.json = provider github.
Precedence: CLI flags > env vars > config file > git remote/filesystem detection.

Layout: taskboard/{config,specs,store,commands}.py (core) and taskboard/providers/* (adapters).
Cache/outbox: .local-artifacts/project_board_{cache,outbox}.json (formats unchanged).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from taskboard import commands as c  # noqa: E402
from taskboard.config import PROVIDER_NAMES  # noqa: E402
from taskboard.store import DEFAULT_CACHE_TTL  # noqa: E402


def build_parser():
    parser = argparse.ArgumentParser(description="Task board CLI (local specs + GitHub/GitLab/local providers)")
    parser.add_argument("--config", help="Path to custom config file (.agents/task-board.json or legacy project.json)")
    parser.add_argument("--provider", choices=PROVIDER_NAMES, help="Provider: github (default), gitlab (stub), local")
    parser.add_argument("--owner", help="GitHub repo or project owner")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--project", dest="project_number", help="GitHub Project number")
    parser.add_argument("--project-id", dest="project_id", help="GitHub Project Node ID (PVT_...)")
    parser.add_argument("--tasks-dir", help="Directory containing task spec markdown files")
    parser.add_argument("--backlog-doc", help="Path to backlog markdown document")
    parser.add_argument("--cache-dir", help="Directory for cache and outbox JSON files")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="List tasks (cached state with TTL by default; auto-syncs from the provider)")
    p.add_argument("--status", help="Filter by status (Backlog, Todo, In Progress, Done, Released)")
    p.add_argument("-r", "--refresh", "--remote", action="store_true", dest="refresh", help="Force refresh from the provider")
    p.add_argument("--ttl", type=int, help=f"Cache validity TTL in seconds (default: {DEFAULT_CACHE_TTL})")
    p.add_argument("--local-only", action="store_true", help="Pure offline mode (read only markdown files without cache sync)")
    p.set_defaults(func=c.cmd_list)

    p = sub.add_parser("move", help="Move a task to a status column (local-first, then provider / outbox)")
    p.add_argument("task_id", help="Task ID, e.g. TASK-01 or FEAT-12")
    p.add_argument("status", help="Target status: Backlog, Todo, In Progress, Done, Released")
    p.set_defaults(func=c.cmd_move)

    p = sub.add_parser("push", help="Create remote issue from spec file and attach to the board")
    p.add_argument("spec_file", help="Path to spec markdown file, e.g. docs/tasks/TASK-01.md")
    p.add_argument("--status", default="Backlog", help="Initial status (default: Backlog)")
    p.set_defaults(func=c.cmd_push)

    p = sub.add_parser("sync", help="Bidirectional sync: flush outbox (Local->Remote) and refresh board state (Remote->Local)")
    p.add_argument("-r", "--refresh", action="store_true", default=True, help="Force refresh state from the provider")
    p.add_argument("--ttl", type=int, default=DEFAULT_CACHE_TTL, help="Cache validity TTL in seconds")
    p.set_defaults(func=c.cmd_sync)

    p = sub.add_parser("rate-limit", help="Check provider API quota and local cache/outbox status")
    p.set_defaults(func=c.cmd_rate_limit)

    p = sub.add_parser("report", help="Render Markdown status report of board, tasks, rate limits, and outbox")
    p.set_defaults(func=c.cmd_report)

    p = sub.add_parser("daemon", help="Background daemon to auto-sync when rate limit resets")
    p.add_argument("--until", type=float, required=True, help="Epoch timestamp to sleep until")
    p.set_defaults(func=c.cmd_daemon)

    p = sub.add_parser("init", help="Write .agents/task-board.json for a provider")
    # SUPPRESS: keep the top-level value when the flag is given before the subcommand.
    p.add_argument("--provider", choices=PROVIDER_NAMES, default=argparse.SUPPRESS, help="Provider (default: github)")
    p.add_argument("--project", dest="project_number", default=argparse.SUPPRESS, help="GitHub Project number")
    p.set_defaults(func=c.cmd_init)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
