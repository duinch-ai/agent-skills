"""Done-gate: deterministic conditions that must all hold before merge."""
import os
import subprocess
import sys
from pathlib import Path

import config
import store


def find_project_pro():
    env = os.environ.get("PROJECT_PRO_SCRIPT")
    cands = [Path(env)] if env else []
    here = Path(__file__).resolve()
    cands.append(here.parents[4] / "project-pro/skills/project-pro/scripts/project_pro.py")
    cands.append(Path.home() / ".claude/skills/project-pro/scripts/project_pro.py")
    return next((c for c in cands if c.is_file()), None)


def find_task_board():
    env = os.environ.get("TASK_BOARD_SCRIPT")
    cands = [Path(env)] if env else []
    here = Path(__file__).resolve()
    cands.append(here.parents[4] / "task-board/skills/task-board/scripts/project_board.py")
    for sub in (".gemini/config/skills", ".claude/skills", ".agents/skills"):
        cands.append(Path.home() / sub / "task-board/scripts/project_board.py")
    return next((c for c in cands if c.is_file()), None)


def move_task_board_done(root, task_id):
    """If task-board is configured and installed, move task_id to Done. Returns (status_msg, warn_msg)."""
    root = Path(root)
    if not any((root / rel).is_file() for rel in (".agents/task-board.json", ".github/project.json")):
        return None, None
    script = find_task_board()
    if script is None:
        return None, "task-board configured but skill not found (set TASK_BOARD_SCRIPT)"
    try:
        p = subprocess.run([sys.executable, str(script), "move", task_id, "Done"],
                           cwd=str(root), capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"task-board move failed: {exc}"
    if p.returncode != 0:
        detail = (p.stderr or p.stdout).strip().splitlines()[-1] if (p.stderr or p.stdout).strip() else f"exit {p.returncode}"
        return None, f"task-board move failed: {detail}"
    return f"task-board: moved {task_id} -> Done", None


def _has_artifacts(ctx, task, cwd):
    """Return True if at least one non-empty artifact file matches task.artifacts."""
    spec = task.artifacts
    if not spec or spec.lower() in ("none", "n/a", "no"):
        return True
    if spec.lower() in ("required", "yes", "true", "artifacts"):
        adir = ctx.runs(task.id) / "artifacts"
        return adir.is_dir() and any(p.is_file() and p.stat().st_size > 0 for p in adir.rglob("*"))
    for base in (Path(cwd), ctx.root):
        matches = [p for p in base.glob(spec) if p.is_file() and p.stat().st_size > 0]
        if matches:
            return True
        target = base / spec
        if target.is_dir() and any(p.is_file() and p.stat().st_size > 0 for p in target.rglob("*")):
            return True
    return False


def evaluate(ctx, task, cwd, run_audit=True):
    """Return (ok, reasons, warnings)."""
    d = ctx.runs(task.id)
    reasons, warns = [], []
    require_git = ctx.cfg.get("require_git", True)
    head = store.head_info(cwd) if require_git else {"head": None, "dirty": False}
    ver, rev = store.latest(d, "verify"), store.latest(d, "review")
    if require_git and head["dirty"]:
        reasons.append("working tree has uncommitted changes (reviewed code must be committed)")
    if ver is None:
        reasons.append("no verify run")
    else:
        if not ver["ok"]:
            reasons.append(f"latest verify (round {ver['n']}) is red")
        if require_git and ver.get("head") != head["head"]:
            reasons.append("latest verify ran on a different commit than HEAD; re-run verify")
        eh = ver.get("escape_hatches") or []
        eh_policy = ctx.cfg.get("escape_hatch_policy", "warn")
        if eh and eh_policy == "fail":
            reasons.append(f"{len(eh)} escape hatch(es) / workaround comment(s) in diff")
        elif eh and eh_policy == "warn":
            warns.append(f"{len(eh)} escape hatch(es) / workaround comment(s) in diff")
    if not _has_artifacts(ctx, task, cwd):
        reasons.append(f"required verification artifact missing or empty ({task.artifacts})")
    if task.is_bug:
        rp = store.latest(d, "repro")
        if rp is None or not rp.get("reproduced"):
            reasons.append("bug was never shown to fail before the fix (run verify --repro-before on main)")
    if rev is None:
        reasons.append("no review")
    else:
        if rev["verdict"] != "approve":
            reasons.append("latest review is not approve")
        if require_git and rev.get("head") != head["head"]:
            reasons.append("latest review covered a different commit than HEAD; re-run review")
        elif not require_git and ver is not None and rev.get("ts", 0) < ver.get("ts", 0):
            reasons.append("latest review predates latest verify; re-run review")
        if ctx.cfg["review_mode"] == "cross-vendor":
            if rev.get("mode") == "same-vendor":
                reasons.append("review was same-vendor but review_mode is cross-vendor")
            elif not rev.get("coder"):
                reasons.append("review has no recorded coder")
            elif config.family(ctx.cfg, rev.get("vendor")) == config.family(ctx.cfg, rev["coder"]):
                reasons.append("reviewer and coder are from the same vendor family")
        highs = [f for f in rev.get("findings", []) if f.get("severity") == "high"]
        if highs:
            reasons.append(f"{len(highs)} unresolved high-severity finding(s)")
        if rev.get("tautological_tests"):
            warns.append(f"{len(rev['tautological_tests'])} tautological test(s) flagged by reviewer")
    if run_audit and ctx.cfg.get("run_audit", True):
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
