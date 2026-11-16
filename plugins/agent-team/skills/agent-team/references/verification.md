# Building a verify harness

Goal: every criterion has a command that fails when the behavior is wrong. Build the
harness before the feature; if you cannot, the task is not ready.

| Product | Check command idea |
|---|---|
| Web app | Playwright test against a locally started app (`npx playwright test`); assert on visible text/URL, save a screenshot as artifact |
| CLI | golden input/output: run with fixture, `diff` against expected file |
| Library | contract tests on the public API only, plus a type check |
| Backend | start server, `curl -fsS` status and body assertions, schema check |
| Bots / webhooks | replay a recorded payload against a local handler, assert outgoing calls with a fake |
| Mobile / desktop | UI test or simulator script that exits non-zero on mismatch |

## Hill climbing

When the criterion is a number (latency, score, bundle size): store the baseline in the
task file, make the check compare against it (`test $(measure) -le 120`), iterate until
green. Record each attempt's number in the verify output so progress is visible.

## Tautological-test check

Before trusting green tests, ask: would this test fail if the feature were deleted?
Quick probe: revert the source change (keep tests) in a scratch worktree and run the
check; it must go red. The reviewer prompt also asks for tests that mock the unit under
test, have no assertion, or assert constants.

## Artifacts

Save screenshots/logs under `.agent-team/runs/TASK-n/artifacts/` (git-ignored); never
write secrets or real user data into them.

## Project verification skill + feature map (`init --verify-skill`)

For non-trivial apps, scaffold `.agents/skills/verify-app/` with `agent_team.py init --verify-skill`:
- **Doctor preflight:** check runtime, build freshness, and fixtures before driving flows.
- **Custom driver CLI:** wrap repetitive UI/API steps into a deterministic, token-cheap CLI.
- **Proof bar:** exercise the real user path (no stale builds), inspect state only to confirm side effects, and save evidence (`screenshot`/`video`/`log`) to `.agent-team/runs/TASK-n/artifacts/` when `Artifacts:` is set.
- **Feature map (`references/features/*.md`):** 4 sections per feature: `Sub-features`, `How to get to it (user POV)`, `Driving it with <cli>`, `Gotchas`.

## Ratchet checks & formal/PBT

- **Ratchet check:** add a `check:` that fails if occurrences of a legacy/banned pattern exceed the baseline (e.g., `test "$(rg -c 'legacyApi' src | awk -F: '{s+=$2}END{print s+0}')" -le 12`), blocking new slop while cleaning old code.
- **Repo standards (`project-pro`):** keep banned-API rules, directory import boundaries, and root-cause lint messages in `project-pro` so `gate` enforces them across all tasks.
- **Formal / PBT:** for concurrency or state-machine invariants, reference TLA+, Lean, or property-based UI testing (e.g., Bombadil) in a `check:` command when applicable.
