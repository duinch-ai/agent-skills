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
