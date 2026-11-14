# Task, verdict and report formats

## Task spec (compatible with task-board)

`docs/tasks/TASK-01.md`. The header lines are what `project_board.py` parses; the other
sections are extra and ignored by it.

```markdown
# TASK-01 — Fix login redirect
Status: Backlog
Priority: P1
Type: bug
Untrusted: no
Base: main
Coder: claude

## Goal
Users land on /home after login.

## Repro
check: `npx playwright test e2e/login.spec.ts -g redirect`

## Acceptance criteria
- [ ] redirect works
  check: `npx playwright test e2e/login.spec.ts`
- [ ] no regression in unit tests
  check: `npm test --silent`
```

`Type: bug` or a `## Repro` section makes the gate require proof the bug failed first
(`verify --repro-before`). `Base:` overrides the config base branch for the diff. The lead/coder writes `Coder: <vendor>` when
coding starts; `review` excludes that vendor's family (`--coder` overrides only when the task has none).
A `check:` is run by `sh -c` in the worktree with credential-looking environment variables
removed, and has `check_timeout` seconds (default 300).

## Run files `.agent-team/runs/TASK-n/`

- `repro-<k>.json`: `reproduced`, result, `head`, `dirty`.
- `verify-<k>.json`: `ok`, per-criterion `results` (cmd, exit, seconds, output tail), `head`.
- `review-<k>.json`: vendor, coder, coder_family, reviewer_family, verdict, findings, tautological_tests, summary, `head`.
- `review-invalid-<k>.json`: a reply that failed validation (kept for debugging).

## Morning report

`agent_team.py report --since 24h` prints a state count table, one row per task (rounds,
reviewer, note), and a "Needs a human decision" list for blocked tasks. States: new,
needs_fix, verified, changes_requested, approved, blocked.
