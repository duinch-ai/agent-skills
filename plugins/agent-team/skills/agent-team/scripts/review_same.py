"""Same-vendor review: a fresh-context read-only subagent of the lead's own vendor judges the diff.

The script launches no CLI. Step 1 `review --prompt` prints the prompt and schema; the lead
hands them to the `reviewer` subagent. Step 2 `review --record FILE` validates and stores
the subagent's JSON verdict.
"""
import json
import sys

import review
import safety
import store

HINT = ("review_mode is 'same-vendor': no CLI is launched. Step 1: `review TASK-n --cwd W --prompt` "
        "and give the output to the `reviewer` subagent in a fresh context. Step 2: save its reply "
        "to a file and run `review TASK-n --cwd W --record FILE [--reviewer NAME]`.")


def prompt_text(ctx, task, cwd):
    return (review.build_prompt(task, review.get_diff(ctx, task, cwd), profile=ctx.cfg.get("profile", "dev"))
            + "\nReply with ONLY a JSON object matching this schema (no prose, no code fences):\n"
            + json.dumps(review.SCHEMA, indent=2) + "\n")


def record(ctx, task, cwd, file, reviewer=None, coder_arg=None):
    cfg, d = ctx.cfg, ctx.runs(task.id)
    if store.count(d, "review") >= cfg["max_review_rounds"]:
        raise SystemExit(f"{task.id}: review rounds exhausted ({cfg['max_review_rounds']}); mark blocked")
    try:
        raw = open(file, encoding="utf-8", errors="replace").read()
    except OSError as exc:
        raise SystemExit(f"cannot read {file}: {exc}")
    name = reviewer or "subagent"
    obj = review.extract_json(raw)
    problems = review.validate_verdict(obj) if obj is not None else ["reply was not valid JSON"]
    if problems:
        path = store.write(d, "review-invalid", {"mode": "same-vendor", "reviewer": name,
                                                 "problems": problems,
                                                 "raw_tail": safety.tail(safety.redact(raw), 2000)})
        raise SystemExit(f"reviewer {name} returned an invalid verdict ({'; '.join(problems)}); see {path}")
    coder = (coder_arg.strip().lower() if coder_arg else None) or task.coder
    rec = {"mode": "same-vendor", "vendor": coder or "same-vendor", "reviewer": name,
           "coder": coder, **obj, **store.head_info(cwd)}
    return store.write(d, "review", rec), rec


def run(ctx, task, cwd, a):
    if a.prompt and a.record:
        print("error: use --prompt or --record, not both", file=sys.stderr)
        return 2
    if a.prompt:
        print(prompt_text(ctx, task, cwd), end="")
        return 0
    if a.record:
        path, rec = record(ctx, task, cwd, a.record, a.reviewer, a.coder)
        print(f"{rec['reviewer']}: {rec['verdict']} ({len(rec['findings'])} findings) -> {path}")
        return 0 if rec["verdict"] == "approve" else 1
    print(HINT, file=sys.stderr)
    return 2
