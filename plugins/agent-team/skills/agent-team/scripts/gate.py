"""Done-gate: deterministic conditions that must all hold before merge."""
import os
import subprocess
import sys
from pathlib import Path

import store


def find_project_pro():
    env = os.environ.get("PROJECT_PRO_SCRIPT")
    cands = [Path(env)] if env else []
    here = Path(__file__).resolve()
    cands.append(here.parents[4] / "project-pro/skills/project-pro/scripts/project_pro.py")
    cands.append(Path.home() / ".claude/skills/project-pro/scripts/project_pro.py")
    return next((c for c in cands if c.is_file()), None)


def evaluate(ctx, task, cwd, run_audit=True):
    """Return (ok, reasons, warnings)."""
    d = ctx.runs(task.id)
    reasons, warns = [], []
    head = store.head_info(cwd)
    ver, rev = store.latest(d, "verify"), store.latest(d, "review")
    if head["dirty"]:
        reasons.append("working tree has uncommitted changes (reviewed code must be committed)")
    if ver is None:
        reasons.append("no verify run")
    else:
        if not ver["ok"]:
            reasons.append(f"latest verify (round {ver['n']}) is red")
        if ver.get("head") != head["head"]:
            reasons.append("latest verify ran on a different commit than HEAD; re-run verify")
    if task.is_bug:
        rp = store.latest(d, "repro")
        if rp is None or not rp.get("reproduced"):
            reasons.append("bug was never shown to fail before the fix (run verify --repro-before on main)")
    if rev is None:
        reasons.append("no review")
    else:
        if rev["verdict"] != "approve":
            reasons.append("latest review is not approve")
        if rev.get("head") != head["head"]:
            reasons.append("latest review covered a different commit than HEAD; re-run review")
        if rev.get("vendor") == rev.get("coder"):
            reasons.append("reviewer vendor equals coder vendor")
        highs = [f for f in rev.get("findings", []) if f.get("severity") == "high"]
        if highs:
            reasons.append(f"{len(highs)} unresolved high-severity finding(s)")
        if rev.get("tautological_tests"):
            warns.append(f"{len(rev['tautological_tests'])} tautological test(s) flagged by reviewer")
    if run_audit:
        if not (Path(cwd) / ".agents/project-profile.json").is_file():
            warns.append("project-pro not configured here; audit skipped")
        else:
            script = find_project_pro()
            if script is None:
                warns.append("project-pro script not found; audit skipped (set PROJECT_PRO_SCRIPT)")
            else:
                p = subprocess.run([sys.executable, str(script), "audit", "--target", str(cwd),
                                    "--fail-on-error"], capture_output=True, text=True, timeout=600)
                if p.returncode != 0:
                    reasons.append("project-pro audit failed")
    return not reasons, reasons, warns
