# Overnight and batch runs

1. Prepare tasks during the day; `lint` each. Only tasks with full checks go in the batch.
2. One worktree per task, from the repo root: `git worktree add .worktrees/TASK-n -b agent/TASK-n main`
   (`.worktrees/` is git-ignored by `init`; remove with `git worktree remove .worktrees/TASK-n`).
   Tools that do not read .gitignore (IDE indexers, tsc/jest without exclude) may need
   `.worktrees` excluded. Cap at
   `max_parallel` (3); tasks must touch disjoint files or merge conflicts eat the gain.
3. Per task run: coder, then `verify`, loop up to 3 rounds, then `review`, then `gate`.
   A shell loop or your agent's own scheduler can drive this; the script only provides
   the steps and exit codes.
4. Scheduling: Claude Code `/schedule` (routines) or `/loop`, or launchd/cron calling a
   small runner script. Use absolute paths and a log file without secrets.
5. Budget: before starting, write down max tasks, max rounds and a token ceiling; stop
   the batch when it is reached rather than letting retries accumulate.
6. Morning: `agent_team.py report --since 24h`, then read the commit log of each
   branch. Merging is yours.
7. Safe defaults for unattended runs: no network writes, no pushes to protected branches,
   no deploys, no messages sent. Sweepers stay read-only.
