"""Parse task specs (docs/tasks/TASK-*.md) in the task-board format.

Compatible header:   `# TASK-01 — Title`, `Status: ...`, `Priority: ...`
Additions (ignored by project_board.py):
  `Untrusted: yes`  `Type: bug`  `Coder: <vendor>` (who wrote the code; the review excludes it)
  `## Repro`  with a `check:` line, `## Acceptance criteria` with bullets,
  each followed by an indented `check: <shell command>` line (exit 0 = pass).
"""
import json
import re
from pathlib import Path

HEADER = re.compile(r"^#\s+([A-Z][A-Z0-9]*-\d+)\s*[—–:-]*\s*(.*)$")
META = re.compile(r"^(Status|Priority|Untrusted|Type|Base|Coder):\s*(.+?)\s*$")
CHECK = re.compile(r"^\s*(?:[-*]\s*)?check:\s*`?(.+?)`?\s*$")
BULLET = re.compile(r"^\s*[-*]\s*(?:\[[ xX]\]\s*)?(.+?)\s*$")


class Task:
    def __init__(self, path):
        self.path = Path(path)
        self.id = ""
        self.title = ""
        self.meta = {}
        self.criteria = []   # [{"id": "AC1", "text": str, "check": str|None}]
        self.repro = None    # shell command or None

    @property
    def status(self):
        return self.meta.get("Status", "Backlog")

    @property
    def is_bug(self):
        return self.repro is not None or self.meta.get("Type", "").lower() == "bug"

    @property
    def untrusted(self):
        return self.meta.get("Untrusted", "").lower() in ("yes", "true", "1")

    @property
    def base(self):
        return self.meta.get("Base")

    @property
    def coder(self):
        return (self.meta.get("Coder") or "").strip().lower() or None


def parse_task(path):
    task = Task(path)
    section = ""
    current = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = HEADER.match(line)
        if m and not task.id:
            task.id, task.title = m.group(1), m.group(2).strip()
            continue
        if line.startswith("## "):
            section = line[3:].strip().lower()
            current = None
            continue
        m = META.match(line)
        if m and not section:
            task.meta[m.group(1)] = m.group(2)
            continue
        c = CHECK.match(line)
        if c and section.startswith("repro"):
            task.repro = c.group(1)
        elif c and current is not None and section.startswith("acceptance"):
            current["check"] = c.group(1)
        elif section.startswith("acceptance"):
            b = BULLET.match(line)
            if b:
                current = {"id": f"AC{len(task.criteria) + 1}", "text": b.group(1), "check": None}
                task.criteria.append(current)
    if not task.id:
        raise ValueError(f"{path}: missing '# TASK-<n> — title' header")
    return task


def load_task(ctx, task_id):
    for path in sorted(ctx.tasks_dir.glob(f"{task_id}*.md")):
        t = parse_task(path)
        if t.id == task_id:
            return t
    raise SystemExit(f"task {task_id} not found under {ctx.tasks_dir}")


def list_tasks(ctx):
    out = []
    for path in sorted(ctx.tasks_dir.glob("*.md")):
        try:
            out.append(parse_task(path))
        except ValueError:
            continue
    return out


def lint_task(task):
    """Return problems that make a task unverifiable."""
    problems = []
    if not task.criteria:
        problems.append("no acceptance criteria")
    for c in task.criteria:
        if not c["check"]:
            problems.append(f"{c['id']} has no `check:` command")
    if task.meta.get("Type", "").lower() == "bug" and not task.repro:
        problems.append("bug task without a Repro `check:`")
    return problems


PROFILE_REL = ".agents/project-profile.json"
SUGGEST_KEYS = ("test_all", "lint", "build")  # keys of `commands` written by project-pro's scaffolder


def suggest_checks(ctx):
    """Default `check:` lines from the project-pro profile commands; never written to a task automatically."""
    path = ctx.root / PROFILE_REL
    try:
        cmds = json.loads(path.read_text(encoding="utf-8")).get("commands", {})
    except (OSError, ValueError, AttributeError):
        return []
    return [f"check: `{cmds[k]}`   (profile commands.{k})" for k in SUGGEST_KEYS
            if isinstance(cmds.get(k), str) and cmds[k].strip()]


def needs_suggestions(task):
    return not task.criteria or any(not c["check"] for c in task.criteria)
