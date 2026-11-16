"""Morning report and status table."""
import re
import subprocess
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


def _git_revert_stats(root):
    """Return (reverts, total) across recent commits on root, or (0, 0) if unavailable."""
    try:
        tot = subprocess.run(["git", "-C", str(root), "rev-list", "--count", "-n", "100", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        if tot.returncode != 0 or not tot.stdout.strip().isdigit():
            return 0, 0
        total = int(tot.stdout.strip())
        rev = subprocess.run(["git", "-C", str(root), "log", "-n", "100", "--grep=^Revert", "--oneline"],
                             capture_output=True, text=True, timeout=10)
        reverts = len([ln for ln in (rev.stdout or "").splitlines() if ln.strip()]) if rev.returncode == 0 else 0
        return reverts, total
    except (OSError, subprocess.SubprocessError):
        return 0, 0


def render(rows, title="Agent team report", root=None):
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
    ver_counts = [r["verify"] for r in rows if r["verify"] > 0]
    rev_counts = [r["review"] for r in rows if r["review"] > 0]
    avg_ver = round(sum(ver_counts) / len(ver_counts), 2) if ver_counts else 0
    avg_rev = round(sum(rev_counts) / len(rev_counts), 2) if rev_counts else 0
    first_pass = sum(1 for r in rows if r["state"] == "ready-to-merge" and r["verify"] == 1 and r["review"] == 1)
    ready_n = sum(1 for r in rows if r["state"] == "ready-to-merge")
    health = [
        f"- avg verify rounds: {avg_ver}, avg review rounds: {avg_rev}",
        f"- first-pass ready: {first_pass}/{ready_n}" if ready_n else "- first-pass ready: 0/0",
    ]
    if root is not None:
        reverts, total = _git_revert_stats(root)
        if total:
            pct = round(100 * reverts / total, 1)
            health.append(f"- recent reverts: {reverts}/{total} ({pct}%)")
    out += ["", "## Inner-loop health"] + health
    blocked = [r for r in rows if r["state"] == "blocked"]
    if blocked:
        out += ["", "## Needs a human decision"] + [f"- {r['id']}: {r['why']}" for r in blocked]
    return "\n".join(out) + "\n"
