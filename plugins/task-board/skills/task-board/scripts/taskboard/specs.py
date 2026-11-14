"""Local task specs (docs/tasks/*.md) and backlog parsing. Pure filesystem, zero API calls."""
import glob
import os
import re

CANONICAL_STATUS = {
    "backlog": "Backlog",
    "todo": "Todo",
    "in progress": "In Progress",
    "in_progress": "In Progress",
    "done": "Done",
    "released": "Released",
}

LOCAL_SPEC_STATUS = {
    "Backlog": "Backlog",
    "Todo": "TODO",
    "In Progress": "IN_PROGRESS",
    "Done": "DONE",
    "Released": "RELEASED",
}


def normalize_board_status(raw_status):
    cleaned = (raw_status or "").strip().lower()
    return CANONICAL_STATUS.get(cleaned, raw_status.strip() or "Backlog")


def parse_backlog_issue_map(backlog_doc):
    """Parse backlog markdown doc to map TASK-ID -> issue number without any API call."""
    mapping = {}
    if not backlog_doc or not os.path.exists(backlog_doc):
        return mapping
    with open(backlog_doc, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\|\s*([A-Za-z0-9_-]+)\s*\|\s*\[#(\d+)\]", line.strip())
            if m:
                mapping[m.group(1).upper()] = int(m.group(2))
    return mapping


def parse_local_specs(tasks_dir, backlog_doc):
    """Read all markdown spec files in tasks_dir and return structured task records."""
    issue_map = parse_backlog_issue_map(backlog_doc)
    tasks = []
    pattern = os.path.join(tasks_dir, "*.md")
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        lines = content.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else os.path.basename(path)
        id_match = re.match(r"^([A-Za-z0-9]+-\d+)", title)
        if id_match:
            task_id = id_match.group(1).upper()
        else:
            base_match = re.match(r"^([A-Za-z0-9]+-\d+)", os.path.basename(path))
            task_id = base_match.group(1).upper() if base_match else os.path.splitext(os.path.basename(path))[0].upper()

        phase_m = re.search(r"^(?:Phase|Priority):\s*(.+)$", content, re.M | re.I)
        status_m = re.search(r"^Status:\s*(.+)$", content, re.M | re.I)
        phase = phase_m.group(1).strip() if phase_m else "P0"
        raw_status = status_m.group(1).strip() if status_m else "Backlog"
        tasks.append(
            {
                "task_id": task_id,
                "issue_number": issue_map.get(task_id, "?"),
                "status": normalize_board_status(raw_status),
                "raw_status": raw_status,
                "phase": phase,
                "title": title,
                "spec_path": path,
            }
        )

    def sort_key(t):
        digits = re.sub(r"\D", "", t["task_id"])
        return int(digits) if digits else 999999

    tasks.sort(key=sort_key)
    return tasks


def parse_spec_for_push(spec_path):
    """Return (task_id, header, content, phase_code) for a spec file."""
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    header = content.splitlines()[0].lstrip("# ").strip()
    id_m = re.match(r"^([A-Za-z0-9]+-\d+)", header)
    task_id = id_m.group(1).upper() if id_m else os.path.splitext(os.path.basename(spec_path))[0].upper()
    phase_match = re.search(r"^(?:Phase|Priority):\s*([^\n\r]+)", content, re.M | re.I)
    phase_code = phase_match.group(1).split("—")[0].strip() if phase_match else "P0"
    return task_id, header, content, phase_code


class SpecStatusError(Exception):
    """A local spec exists but has no parseable `Status:` line, so its status cannot be updated."""


def update_local_spec_status_if_changed(task_id, board_status, tasks_dir):
    """Update local spec status only if different from current content.

    Returns True when a file changed, False when nothing needed changing (or no spec exists).
    Raises SpecStatusError when a matching spec has no `Status:` line.
    """
    matches = glob.glob(os.path.join(tasks_dir, f"{task_id}*.md"))
    if not matches:
        spec_path = os.path.join(tasks_dir, f"{task_id}.md")
        if not os.path.exists(spec_path):
            return False
        matches = [spec_path]

    mapped = LOCAL_SPEC_STATUS.get(board_status, board_status.upper())
    updated_any = False
    for spec_path in matches:
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            continue
        current_match = re.search(r"^Status:\s*(.+)$", text, re.M | re.I)
        if not current_match:
            raise SpecStatusError(
                f"{spec_path}: no parseable 'Status:' line; add e.g. 'Status: Backlog' to the spec header, then retry."
            )
        if current_match.group(1).strip().upper() == mapped.upper():
            continue
        updated = re.sub(r"^Status:\s*.*$", f"Status: {mapped}", text, flags=re.M | re.I)
        try:
            with open(spec_path, "w", encoding="utf-8") as f:
                f.write(updated)
            updated_any = True
        except Exception:
            pass
    return updated_any
