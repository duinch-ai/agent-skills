# Principles (and why)

Source: public write-ups of Lauren Tan's agent workflow (secondary sources, so treat the
specifics as inspiration, not quotation).

- **Hierarchy, not a swarm.** A lead owns planning and acceptance; engineer agents own
  execution. Flat swarms duplicate work and nobody owns the outcome.
- **Outer loop pulls context** (issues, chat) into task specs; **inner loop** is execute,
  verify, fix, re-verify. Keep them separate so untrusted input is filtered at the seam.
- **Verification is the core.** Agents run the real product (browser via Playwright/CDP,
  CLI, API) against measurable criteria. Without it, "done" is a guess.
- **Hill climbing.** Change, run, compare to the last result, keep or refine. Needs a
  number or pass/fail, so define one first.
- **Reproduce before fixing.** A bug that does not fail on latest main may already be
  fixed or misunderstood; the fix then proves nothing.
- **Tautological tests.** Agents write tests that pass by construction (mock the unit,
  assert the constant). Humans and the reviewer judge what a test could catch.
- **Different model family judges.** Self-review repeats the same blind spots.
- **Agent-friendly code.** One feature per directory, small files, lint and static rules
  turn conventions into failures an agent can see.
- **Skills encode process**: when to verify, what the next step's criteria are.
- **Sweepers.** Background read-only agents log findings for later triage.
- **Overnight work, morning review** of the commit log and report.
- **Fix the system.** Repeated shortcut across agents means missing tooling, not a bad run.

## Anti-patterns

- Criteria like "works well" with no command. Rewrite until a command can fail.
- Same vendor writes and reviews.
- Coder edits the check to make it pass (review diffs of test and check files first).
- Letting an issue's text run with edit rights unreviewed.
- Auto-merge or auto-deploy: one-way doors stay human.
