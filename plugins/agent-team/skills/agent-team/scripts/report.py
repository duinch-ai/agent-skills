"""Morning report and status table."""
import re
import time

import store
import tasks


def parse_since(text):
    m = re.fullmatch(r"(\d+)([hdm])", text or "")
    if not m:
        raise SystemExit("--since expects e.g. 24h, 7d, 90m")
    return int(m.group(1)) * {"h": 3600, "d": 86400, "m": 60}[m.group(2)]


def _activity(d):
    ts = []
    for kind in ("verify", "review", "repro"):
        r = store.latest(d, kind)
        if r:
            ts.append(r["ts"])
    return max(ts) if ts else None


def collect(ctx, since_seconds=None):
    rows = []
    now = time.time()
    for t in tasks.list_tasks(ctx):
        d = ctx.runs(t.id)
        act = _activity(d)
        if since_seconds is not None and (act is None or now - act > since_seconds):
            continue
        state, why = store.task_state(ctx, t)
        rev = store.latest(d, "review")
        rows.append({"id": t.id, "title": t.title, "state": state, "why": why,
                     "verify": store.count(d, "verify"), "review": store.count(d, "review"),
                     "reviewer": rev["vendor"] if rev else "-",
                     "tauto": len(rev["tautological_tests"]) if rev else 0})
    return rows


def render(rows, title="Agent team report"):
    out = [f"# {title}", ""]
    if not rows:
        return "\n".join(out + ["No task activity in this window."]) + "\n"
    groups = {}
    for r in rows:
        groups.setdefault(r["state"], []).append(r)
    out.append("| state | count |\n|---|---|")
    out += [f"| {s} | {len(v)} |" for s, v in sorted(groups.items())]
    out += ["", "| task | state | verify rounds | review rounds | reviewer | note |", "|---|---|---|---|---|---|"]
    for r in rows:
        note = r["why"] + (f"; {r['tauto']} tautological test(s)" if r["tauto"] else "")
        out.append(f"| {r['id']} {r['title']} | {r['state']} | {r['verify']} | {r['review']} | {r['reviewer']} | {note} |")
    blocked = [r for r in rows if r["state"] == "blocked"]
    if blocked:
        out += ["", "## Needs a human decision"] + [f"- {r['id']}: {r['why']}" for r in blocked]
    return "\n".join(out) + "\n"
