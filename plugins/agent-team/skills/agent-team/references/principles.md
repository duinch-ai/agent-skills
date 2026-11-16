# Principles (and why)

Source: Lauren Tan (`@poteto`, "Slop into gold" talk and `poteto/plugins` `pstack` + `poteto/verification-skill-example`).

- **Trust is the goal, not raw volume.** High PR throughput only works when the agent environment makes good code the default.
- **Inverted pyramid of agent environment.** Invest from bottom (strongest) to top (thinnest):
  1. Code, API design, and architecture (make invalid states unrepresentable; ban nuance-heavy APIs; enforce directory/module boundaries with dependency rules).
  2. Deterministic static checks (types, linters with root-cause error messages, tests, ratchets).
  3. Runtime & formal verification (custom driver CLIs, user-POV feature maps, property-based / formal checks; ~70% of tokens go to verification).
  4. Prose (`AGENTS.md`, rules, skills) is the **thinnest** layer. "The instruction IS the symptom."
- **Codebase is the largest input.** Agents copy existing patterns—good or bad. Keep the codebase clean: add a lint rule to block new bad patterns, then clean up old ones.
- **Encode every correction in structure.** On any correction, pick the strongest rung (type -> lint -> check -> helper -> prose). Never just add another rule line when a deterministic check can enforce it.
- **Review verification artifacts, not every line.** Shift human review from reading every diff line to inspecting proof artifacts (screenshots, videos, diagrams, test/lint outputs).
- **Inner loop before outer loop.** Automating a slop loop just produces more slop. Measure first-pass rate and revert rate before enabling unattended batches or tiered auto-merge.
- **Different model family judges.** Self-review repeats the same blind spots.
- **Sweepers.** Background read-only agents run legacy pattern censuses and log system-fix tasks.

## Anti-patterns

- Criteria like "works well" with no command. Rewrite until a command can fail.
- Adding a prose rule instead of a lint/type/test check when an agent slips up.
- Escape hatches & workaround comments (`eslint-disable`, `@ts-ignore`, `as any`, `setTimeout(..., 0)` + prose excuses) instead of fixing the root cause.
- Same vendor writes and reviews.
- Coder edits the check to make it pass (review diffs of test and check files first).
- Letting an issue's text run with edit rights unreviewed.
- Unbounded auto-merge without proven inner-loop metrics (only opt in for `Risk: low` when revert rate is low and deterministic + artifact gates pass).
