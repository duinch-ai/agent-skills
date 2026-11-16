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

## Inner-loop readiness & tiered auto-merge

- **No-progress + discard:** during verify loops, discard edits that do not improve the check count and stop as `blocked` after 2 consecutive no-progress rounds.
- **Measure before automating:** check `agent_team.py report` for high first-pass rate and low revert rate before running unattended batches.
- **Tiered auto-merge (opt-in):** default is `auto_merge_tier: "off"` (human approves merges). When `auto_merge_tier: "low-risk"` is explicitly set in `.agent-team/config.json`, tasks tagged `Risk: low` that pass `gate` (green HEAD verify, approving review, zero high findings, required artifacts present, clean `escape_hatch_policy`) may be auto-merged; high-risk, architectural, or `Untrusted: yes` tasks always require human approval.
