"""Run artifacts under .agent-team/runs/<TASK>/ and the derived task state."""
import json
import re
import subprocess
import time
from pathlib import Path


def git(cwd, *args):
    out = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=60)
    return out.returncode, out.stdout.strip()


def head_info(cwd):
    rc, sha = git(cwd, "rev-parse", "HEAD")
    _, status = git(cwd, "status", "--porcelain", "--", ".", ":(exclude).agent-team")
    return {"head": sha if rc == 0 else None, "dirty": bool(status)}


def _files(d, kind):
    pat = re.compile(rf"^{kind}-(\d+)\.json$")
    found = []
    if Path(d).is_dir():
        for p in Path(d).iterdir():
            m = pat.match(p.name)
            if m:
                found.append((int(m.group(1)), p))
    return sorted(found)


def count(d, kind):
    return len(_files(d, kind))


def write(d, kind, data):
    Path(d).mkdir(parents=True, exist_ok=True)
    n = count(d, kind) + 1
    data = {"n": n, "ts": time.time(), **data}
    path = Path(d) / f"{kind}-{n}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def latest(d, kind):
    files = _files(d, kind)
    if not files:
        return None
    return json.loads(files[-1][1].read_text(encoding="utf-8"))


def task_state(ctx, task):
    """new | needs_fix | verified | changes_requested | approved | blocked (+ reason)."""
    d = ctx.runs(task.id)
    ver, rev = latest(d, "verify"), latest(d, "review")
    cfg = ctx.cfg
    if ver is None:
        return "new", ""
    if not ver["ok"]:
        if count(d, "verify") >= cfg["max_verify_rounds"]:
            return "blocked", f"verify failed after {cfg['max_verify_rounds']} rounds"
        return "needs_fix", f"verify round {ver['n']} failed"
    if rev is None or rev["ts"] < ver["ts"]:
        return "verified", "awaiting review"
    if rev["verdict"] == "approve":
        return "approved", f"approved by {rev['vendor']}"
    if count(d, "review") >= cfg["max_review_rounds"]:
        return "blocked", f"changes still requested after {cfg['max_review_rounds']} reviews"
    return "changes_requested", f"{len(rev['findings'])} finding(s) from {rev['vendor']}"
