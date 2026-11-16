# Cross-vendor review

Applies only when `review_mode` is `cross-vendor` in `.agent-team/config.json`. The default
`same-vendor` mode uses the `reviewer` subagent instead (`review --prompt`, then `review --record FILE`).

## Selection rule

`review.available_reviewers`: walk `reviewer_preference`, skip every vendor in the coder's
family (`vendor_family`, default agy = gemini), keep vendors that are usable now. The coder
comes from the task's `Coder:` field or `--coder`; there is no default, a missing coder stops
the command. No candidate means the command fails; never review with the coder's own family.

## Commands (verified on this machine with `--help`)

codex (codex-cli 0.153.4), built in:

```
codex exec -s read-only --ephemeral --color never -C <worktree> \
  --output-schema <schema.json> -o <last-message-file> [-m <model>] -     < prompt on stdin
```

`-s/--sandbox read-only`, `-C/--cd`, `--output-schema`, `-o/--output-last-message`,
`--ephemeral`, `--color` and the `-` stdin convention all appear in `codex exec --help`.
Re-check after upgrading codex.

agy (Antigravity CLI 1.5.7): not supported. `agy --help` shows `-p/--print` taking the
prompt as the flag's value (argv, not stdin) and no read-only flag, which breaks the
stdin and read-only rules. A bare `-p` with stdin prompt errors "flag needs an argument".

gemini, claude: not installed here. Detect with `command -v gemini claude`, read
`<cli> --help` for a non-interactive print mode, a read-only/plan permission mode and
stdin prompt support, then add the argv under `reviewer_commands` in
`.agent-team/config.json`, for example `{"gemini": ["gemini", "<flags from --help>"]}`.
The tool pipes the prompt on stdin and expects the JSON verdict on stdout. If the CLI
cannot read the prompt from stdin or cannot run read-only, do not use it.

## Review lens

`review.build_prompt` asks the reviewer to check, besides the criteria and tautological
tests, the same list as `working-method.md` section 4: concurrency (double submit, refresh
stampede, stale async overwrite), unbounded data (N+1, no pagination), idempotency and
partial failure (retry after commit, missing transaction), trust boundaries (IDOR, missing
ownership check, unvalidated input, secrets or PII in logs). A finding from this lens uses
the normal verdict schema below.

## Verdict schema

```
{"verdict": "approve"|"changes_requested",
 "findings": [{"severity": "high|medium|low", "file": str, "line": int|null,
               "issue": str, "criterion": str}],
 "tautological_tests": [str], "summary": str}
```

Validation rejects non-JSON, missing fields, and `approve` combined with a high finding.
An invalid reply is saved as `review-invalid-<k>.json` and does not count as a verdict.

## Handling findings

High severity: coder fixes, re-verify, re-review (round 2). Still red after round 2:
`blocked`, human decides. Medium/low: coder judges; record rejected ones in the PR text.
