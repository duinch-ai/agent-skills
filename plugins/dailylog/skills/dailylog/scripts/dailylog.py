#!/usr/bin/env python3
"""dailylog - layered long-term memory shared by every coding agent in a workspace.

Layers inside <root>/memory/:
  INDEX.md             always-read map (generated block + human notes)
  HISTORY.md           one line per consolidated week
  projects/<slug>.md   current state and open tasks (overwritten as things change)
  knowledge/<slug>.md  durable facts, with a verified date
  decisions/<date>-<slug>.md  why something was chosen; superseded, never deleted
  YYYY-Www/            weekly folder: YYYY-MM-DD.md logs (append-only) + summary.md

Python 3.8+ standard library only. Text is never passed through str.format, so
Plex-style tags such as {tvdb-227501} survive untouched.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: appends still work, without inter-process locking
    fcntl = None

INDEX_BUDGET_LINES = 100
STALE_DAYS = 90
CLAIM_STALE_DAYS = 7
SUMMARY_CHARS = 120
INDEX_MAX_PROJECTS = 20
INDEX_MAX_KNOWLEDGE = 30
LAYERS = {"knowledge": 40, "decisions": 40, "projects": 30, "summary": 20, "history": 20, "log": 10}
WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
INDEX_START = "<!-- dailylog:index:start (generated, edit outside this block) -->"
INDEX_END = "<!-- dailylog:index:end -->"
WIRE_START = "<!-- dailylog:start -->"
WIRE_END = "<!-- dailylog:end -->"
CONSOLIDATED_RE = re.compile(r"<!-- consolidated: (\S+) by (.+?) -->")
LEGACY_TODO_RE = re.compile(r"^\s*-\s*\[ \]|\[TODO\]")
SECRET_PATTERNS = {
    "GitHub token": r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}",
    "API key": r"\bsk-[A-Za-z0-9_-]{20,}|\bAIza[0-9A-Za-z_-]{30,}",
    "AWS key": r"\bAKIA[0-9A-Z]{16}\b",
    "Slack token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "credential assignment":
        r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token)\b\s*[:=]\s*['\"]?[^\s'\"`<>{}]{6,}",
}
WIRE_BLOCK = f"""{WIRE_START}
### Shared memory (dailylog)

`memory/` is shared by every agent and session here. Sessions are recorded automatically by hooks where installed, so do not spend turns logging routine steps.

- No context was injected at session start: run `dailylog context`.
- Need older context: `dailylog search "<terms>"`, then read only the files it names. Do not bulk-read old weeks.
- Record only what the session record cannot infer: durable facts (`dailylog new knowledge`), decisions and rejected alternatives (`dailylog new decision`), open tasks (`dailylog todo add|start|done <project> "<text>"`). Send these alongside another tool call, not as a turn of their own.
- A `[/]` task is claimed by another instance: leave its files alone unless the user asks.
- Never store secrets; dailylog refuses them.
{WIRE_END}
"""


def fail(message, code=2):
    print(f"dailylog: {message}", file=sys.stderr)
    raise SystemExit(code)


def now():
    override = os.environ.get("DAILYLOG_NOW")
    return dt.datetime.fromisoformat(override) if override else dt.datetime.now()


def week_id(day):
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def week_bounds(week):
    year, number = int(week[:4]), int(week[6:])
    monday = dt.date.fromisocalendar(year, number, 1)
    return monday, monday + dt.timedelta(days=6)


def instance_name(args):
    explicit = getattr(args, "instance", None) or os.environ.get("DAILYLOG_INSTANCE")
    if explicit:
        return explicit
    env = os.environ
    if env.get("CLAUDECODE") or env.get("CLAUDE_CODE_ENTRYPOINT"):
        return "Claude"
    if any(key.startswith("CODEX_") for key in env):
        return "Codex"
    if any(key.startswith(("ANTIGRAVITY", "AGY_")) for key in env):
        return "Antigravity"
    if env.get("GEMINI_CLI"):
        return "Gemini"
    return "Agent"


def fold(text):
    """Lowercase and strip diacritics so `quyet dinh` finds `quyết định`."""
    decomposed = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", fold(text)).strip("-")
    if not slug:
        fail(f"cannot build a file name from {text!r}")
    return slug


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def atomic_write(path, text):
    real = Path(os.path.realpath(path))
    real.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(real.parent), prefix=".dailylog-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        if real.exists():
            os.chmod(tmp, real.stat().st_mode & 0o777)
        else:
            os.chmod(tmp, 0o644)
        os.replace(tmp, real)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


@contextlib.contextmanager
def locked(mem):
    mem.mkdir(parents=True, exist_ok=True)
    with open(mem / ".lock", "a", encoding="utf-8") as handle:
        if fcntl:
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(handle, fcntl.LOCK_UN)


def find_secret(text):
    for label, pattern in SECRET_PATTERNS.items():
        if re.search(pattern, text):
            return label
    return None


def refuse_secrets(*parts):
    for part in parts:
        label = find_secret(part or "")
        if label:
            fail(f"refused: text looks like it contains a {label}. Remove it and describe where it is stored instead.")


def input_text(value):
    """`-` reads stdin, the safe route for text with $, backticks or quotes."""
    return sys.stdin.read().strip() if value == "-" else value


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    rest = text[end + 4:]
    return meta, rest[1:] if rest.startswith("\n") else rest


def join_frontmatter(meta, body):
    lines = ["---"] + [f"{key}: {value}" for key, value in meta.items() if value not in (None, "")] + ["---", ""]
    return "\n".join(lines) + body


def one_line(text):
    return " ".join((text or "").split())


def global_store():
    return Path.home() / ".dailylog"


def store_of(root):
    """A project keeps its store in <root>/memory; the global store is flat."""
    root = Path(root)
    if root == global_store() or (root / "INDEX.md").exists():
        return root
    return root / "memory"


def resolve_root(args):
    explicit = getattr(args, "root", None) or os.environ.get("DAILYLOG_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()
    here = Path.cwd().resolve()
    for candidate in [here, *here.parents]:
        mem = candidate / "memory"
        if mem.is_dir() and ((mem / "INDEX.md").exists() or week_dirs(mem)):
            return candidate
    return None


def memory_dir(args):
    root = resolve_root(args)
    if root is None or not store_of(root).is_dir():
        fail("no memory/ found here or in a parent folder. Run `dailylog init` in the workspace root, or pass --root ~/.dailylog for the global store.")
    return store_of(root)


def week_dirs(mem):
    return sorted(p for p in mem.iterdir() if p.is_dir() and WEEK_RE.match(p.name))


def day_files(mem):
    files = [f for week in week_dirs(mem) for f in week.iterdir() if DAY_RE.match(f.name)]
    return sorted(files, key=lambda f: f.name)


def day_path(mem, day):
    return mem / week_id(day) / f"{day.isoformat()}.md"


def append_log(mem, line):
    day = now().date()
    path = day_path(mem, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = ""
    if not path.exists():
        prefix = f"# Work log - {day.isoformat()} ({week_id(day)})\n\n"
    elif not read_text(path).endswith("\n"):
        prefix = "\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(prefix + line + "\n")
    return path


def log_line(args, text, status="note", project=None):
    stamp = now().strftime("%H:%M")
    tag = f" [{project}]" if project else ""
    body = "\n  ".join(text.splitlines()) or text
    who = instance_name(args)
    marks = {
        "done": f"- [x] [DONE] ({who}) {stamp}{tag} ",
        "todo": f"- [ ] [TODO] ({who}) {stamp}{tag} ",
        "start": f"- [/] [IN_PROGRESS] ({who}) {stamp}{tag} ",
        "note": f"- ({who}) {stamp}{tag} ",
    }
    return marks[status] + body


# --- projects and tasks -----------------------------------------------------

TASK_RE = re.compile(r"^- \[( |/)\] ")
TASK_HEADING = "## Open tasks"


def project_template(name, summary, day):
    meta = {"title": name, "type": "project", "status": "active", "summary": one_line(summary), "updated": day}
    body = f"# {name}\n\n## Current state\n\n{TASK_HEADING}\n\n## Key links\n"
    return join_frontmatter(meta, body)


def project_path(mem, name):
    return mem / "projects" / f"{slugify(name)}.md"


def ensure_project(mem, name, summary=""):
    path = project_path(mem, name)
    if not path.exists():
        atomic_write(path, project_template(name, summary, now().date().isoformat()))
    return path


def set_field(text, key, value):
    meta, body = split_frontmatter(text)
    meta[key] = value
    return join_frontmatter(meta, body)


def open_tasks(text):
    return [line for line in text.splitlines() if TASK_RE.match(line)]


def insert_task(text, task):
    lines = text.splitlines()
    if TASK_HEADING not in lines:
        lines += ["", TASK_HEADING, ""]
    at = lines.index(TASK_HEADING) + 1
    last = at
    for i in range(at, len(lines)):
        if lines[i].startswith("## "):
            break
        if TASK_RE.match(lines[i]):
            last = i + 1
    if last == at:
        lines[at:at] = ["", task]
    else:
        lines.insert(last, task)
    return "\n".join(lines) + "\n"


def match_task(text, needle):
    wanted = fold(needle)
    hits = [line for line in open_tasks(text) if wanted in fold(line)]
    if not hits:
        fail(f"no open task matches {needle!r}")
    if len(hits) > 1:
        fail("more than one open task matches; be more specific:\n" + "\n".join(hits))
    return hits[0]


def task_text(line):
    text = re.sub(r"^- \[[ /]\] (\[[A-Z_]+\] )?(\([^)]*\) )?", "", line)
    return text


def cmd_todo(args):
    mem = memory_dir(args)
    if args.action == "list":
        return print_tasks(mem, args.project)
    if not args.project or not args.text:
        fail("usage: dailylog todo add|start|done <project> <text>")
    text_arg = input_text(args.text)
    refuse_secrets(text_arg)
    day = now().date().isoformat()
    with locked(mem):
        path = ensure_project(mem, args.project) if args.action == "add" else project_path(mem, args.project)
        if not path.exists():
            fail(f"no project {args.project!r}")
        text = read_text(path)
        who = instance_name(args)
        if args.action == "add":
            text = insert_task(text, f"- [ ] [TODO] {one_line(text_arg)}")
            entry, status = text_arg, "todo"
        else:
            line = match_task(text, text_arg)
            entry = task_text(line)
            lines = text.splitlines()
            at = lines.index(line)
            if args.action == "start":
                lines[at] = f"- [/] [IN_PROGRESS] ({who}) {entry}"
                status = "start"
            else:
                del lines[at]
                status = "done"
            text = "\n".join(lines) + "\n"
        atomic_write(path, set_field(text, "updated", day))
        append_log(mem, log_line(args, entry, status, slugify(args.project)))
        refresh_index(mem)
    print(f"{args.action}: {entry}")
    return 0


def print_tasks(mem, project=None):
    paths = [project_path(mem, project)] if project else sorted((mem / "projects").glob("*.md"))
    found = False
    for path in paths:
        if not path.exists():
            fail(f"no project {project!r}")
        tasks = open_tasks(read_text(path))
        if tasks:
            found = True
            print(f"{path.stem}:")
            print("\n".join(f"  {task}" for task in tasks))
    if not found:
        print("no open tasks")
    return 0


# --- index ------------------------------------------------------------------


def docs(mem, folder):
    for path in sorted((mem / folder).glob("*.md")):
        meta, _ = split_frontmatter(read_text(path))
        yield path, meta


def clip(text, limit=SUMMARY_CHARS):
    text = one_line(text).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def recent_first(items):
    return sorted(items, key=lambda item: item[1].get("updated", ""), reverse=True)


def index_block(mem):
    out = [INDEX_START]
    every = list(docs(mem, "projects"))
    projects = recent_first([(p, m) for p, m in every if m.get("status") != "archived"])
    if projects:
        out += ["", "## Projects", "", "| Project | Status | Open | Updated | Summary |", "|---|---|---|---|---|"]
        for path, meta in projects[:INDEX_MAX_PROJECTS]:
            count = len(open_tasks(read_text(path)))
            link = f"[{meta.get('title', path.stem)}](projects/{path.name})"
            row = [link, meta.get("status", "-"), str(count), meta.get("updated", "-"), clip(meta.get("summary", ""))]
            out.append("| " + " | ".join(row) + " |")
    hidden = len(every) - len(projects[:INDEX_MAX_PROJECTS])
    if hidden:
        out += ["", f"...and {hidden} older or archived projects; use `dailylog search`."]
    knowledge = recent_first(list(docs(mem, "knowledge")))
    if knowledge:
        out += ["", "## Knowledge", ""]
    for path, meta in knowledge[:INDEX_MAX_KNOWLEDGE]:
        verified = meta.get("verified", "unverified")
        out.append(f"- [{meta.get('title', path.stem)}](knowledge/{path.name}) - {clip(meta.get('summary', ''))} (verified {verified})")
    if len(knowledge) > INDEX_MAX_KNOWLEDGE:
        out.append(f"- ...and {len(knowledge) - INDEX_MAX_KNOWLEDGE} older notes; use `dailylog search`.")
    decisions = [(p, m) for p, m in docs(mem, "decisions") if m.get("status") != "superseded"]
    if decisions:
        out += ["", "## Recent decisions", ""]
    for path, meta in decisions[-10:][::-1]:
        out.append(f"- [{meta.get('date', '')} {meta.get('title', path.stem)}](decisions/{path.name})")
    if len(decisions) > 10:
        out.append(f"- ...and {len(decisions) - 10} older; use `dailylog search`.")
    history = [l for l in read_text(mem / "HISTORY.md").splitlines() if l.startswith("- ")] if (mem / "HISTORY.md").exists() else []
    if history:
        out += ["", "## Recent weeks", ""] + history[-4:]
    return "\n".join(out + ["", INDEX_END])


def refresh_index(mem):
    path = mem / "INDEX.md"
    block = index_block(mem)
    if not path.exists():
        text = f"# Memory index\n\n{block}\n\n## Notes\n"
    else:
        text = read_text(path)
        start, end = text.find(INDEX_START), text.find(INDEX_END)
        if start >= 0 and end > start:
            text = text[:start] + block + text[end + len(INDEX_END):]
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
    atomic_write(path, text)
    return path


def cmd_index(args):
    mem = memory_dir(args)
    with locked(mem):
        print(refresh_index(mem))
    return 0


# --- init and wire ----------------------------------------------------------


def wire_targets(root):
    names = ["AGENTS.md"] + [n for n in ("CLAUDE.md", "GEMINI.md") if (root / n).exists()]
    seen, targets = set(), []
    for name in names:
        real = os.path.realpath(root / name)
        if real not in seen:
            seen.add(real)
            targets.append(root / name)
    return targets


def apply_wire(root, remove=False, dry_run=False):
    for path in wire_targets(root):
        text = read_text(path) if path.exists() else ""
        start, end = text.find(WIRE_START), text.find(WIRE_END)
        if start >= 0 and end > start:
            tail = text[end + len(WIRE_END):]
            new = text[:start] + tail.lstrip("\n") if remove else text[:start] + WIRE_BLOCK.rstrip("\n") + tail
        elif remove:
            new = text
        else:
            new = (text.rstrip() + "\n\n" if text.strip() else "") + WIRE_BLOCK
        verb = "unchanged" if new == text else ("would update" if dry_run else "updated")
        if new != text and not dry_run:
            atomic_write(path, new)
        print(f"{verb}: {path}")
    if not (root / "CLAUDE.md").exists() and not remove:
        print("note: no CLAUDE.md here. If Claude Code does not load AGENTS.md for you, create CLAUDE.md containing @AGENTS.md")


def cmd_wire(args):
    root = resolve_root(args) or Path.cwd().resolve()
    apply_wire(root, args.remove, args.dry_run)
    return 0


def init_layers(mem):
    for folder in ("projects", "knowledge", "decisions"):
        (mem / folder).mkdir(parents=True, exist_ok=True)
    with locked(mem):
        if not (mem / "HISTORY.md").exists():
            atomic_write(mem / "HISTORY.md", "# Work history\n\nOne line per consolidated week, oldest first.\n\n")
        ignore = mem / ".gitignore"
        if not ignore.exists():
            atomic_write(ignore, ".lock\n.sessions/\n.index.db*\n.dailylog-*\n.DS_Store\n")
        refresh_index(mem)


def cmd_init(args):
    root = (Path(args.root).expanduser().resolve() if args.root else resolve_root(args)) or Path.cwd().resolve()
    mem = store_of(root)
    init_layers(mem)
    print(f"memory ready: {mem} ({len(week_dirs(mem))} existing week folders kept untouched)")
    if args.git and not (mem / ".git").exists():
        subprocess.run(["git", "init", "-q", str(mem)], check=True)
        print("git repository created in memory/ (nothing committed)")
    if args.wire:
        apply_wire(root)
    return 0


# --- writing ----------------------------------------------------------------


def cmd_log(args):
    mem = memory_dir(args)
    text = input_text(args.text)
    refuse_secrets(text)
    project = slugify(args.project) if args.project else None
    with locked(mem):
        path = append_log(mem, log_line(args, text, args.status, project))
    print(path)
    return 0


def cmd_new(args):
    mem = memory_dir(args)
    day = now().date().isoformat()
    body = input_text(args.body) if getattr(args, "body", None) else ""
    fields = [args.summary, body, args.title] + [getattr(args, k, "") for k in ("context", "choice", "alternatives", "consequences")]
    refuse_secrets(*fields)
    slug = slugify(args.slug)
    title = args.title or args.slug
    with locked(mem):
        if args.kind == "project":
            path = project_path(mem, args.slug)
            text = project_template(title, args.summary, day)
        elif args.kind == "knowledge":
            path = mem / "knowledge" / f"{slug}.md"
            meta = {"title": title, "type": "knowledge", "project": args.project, "summary": one_line(args.summary),
                    "tags": args.tags, "aliases": args.aliases, "verified": day, "updated": day}
            text = join_frontmatter(meta, f"# {title}\n\n{body}\n")
        else:
            path = mem / "decisions" / f"{day}-{slug}.md"
            meta = {"title": title, "type": "decision", "date": day, "status": "accepted", "project": args.project,
                    "summary": one_line(args.summary), "tags": args.tags, "aliases": args.aliases, "supersedes": args.supersedes}
            sections = [("Context", args.context), ("Decision", args.choice),
                        ("Alternatives considered", args.alternatives), ("Consequences", args.consequences)]
            parts = [f"# {title}\n"] + [f"## {name}\n\n{value or '-'}\n" for name, value in sections]
            text = join_frontmatter(meta, "\n".join(parts))
        if path.exists():
            fail(f"{path} already exists; edit it instead of creating a new one")
        if args.kind == "decision" and args.supersedes:
            mark_superseded(mem, args.supersedes, path.stem)
        atomic_write(path, text)
        refresh_index(mem)
    print(path)
    return 0


def mark_superseded(mem, needle, by):
    wanted = slugify(needle)
    hits = [p for p in (mem / "decisions").glob("*.md") if wanted in p.stem]
    if len(hits) != 1:
        fail(f"--supersedes must match exactly one decision; {needle!r} matched {len(hits)}")
    atomic_write(hits[0], set_field(set_field(read_text(hits[0]), "status", "superseded"), "superseded_by", by))


def cmd_verify(args):
    mem = memory_dir(args)
    path = (mem / args.path) if not Path(args.path).is_absolute() else Path(args.path)
    if not path.exists():
        fail(f"no such file: {path}")
    day = now().date().isoformat()
    with locked(mem):
        atomic_write(path, set_field(set_field(read_text(path), "verified", day), "updated", day))
        refresh_index(mem)
    print(f"verified {day}: {path}")
    return 0


# --- reading ----------------------------------------------------------------


def tail(text, limit):
    if len(text) <= limit:
        return text
    cut = text[-limit:]
    return "[...older lines omitted...]\n" + cut[cut.find("\n") + 1:]


def pending_weeks(mem):
    current = week_id(now().date())
    pending = []
    for week in week_dirs(mem):
        if week.name >= current:
            continue
        summary = week / "summary.md"
        if not (summary.exists() and CONSOLIDATED_RE.search(read_text(summary))):
            pending.append(week.name)
    return pending


def lint_findings(mem, stale_days=STALE_DAYS):
    errors, warnings = [], []
    today = now().date()
    files = [p for p in mem.rglob("*.md") if ".git" not in p.parts]
    stems = {p.stem for p in files}
    for path in files:
        rel = path.relative_to(mem)
        text = read_text(path)
        for number, line in enumerate(text.splitlines(), 1):
            label = find_secret(line)
            if label:
                errors.append(f"{rel}:{number} looks like a {label}")
        for link in re.findall(r"\[\[([^\]|#]+)", text):
            if link.strip() not in stems:
                warnings.append(f"{rel}: broken link [[{link.strip()}]]")
    for path, meta in docs(mem, "knowledge"):
        verified = meta.get("verified", "")
        try:
            age = (today - dt.date.fromisoformat(verified)).days
        except ValueError:
            warnings.append(f"knowledge/{path.name}: no valid verified date")
            continue
        if age > stale_days:
            warnings.append(f"knowledge/{path.name}: last verified {age} days ago; re-check it, then `dailylog verify`")
    for path, meta in docs(mem, "projects"):
        if "[/]" not in read_text(path):
            continue
        with contextlib.suppress(ValueError):
            age = (today - dt.date.fromisoformat(meta.get("updated", ""))).days
            if age > CLAIM_STALE_DAYS:
                warnings.append(f"projects/{path.name}: in-progress task untouched for {age} days; the claim may be dead")
    index = mem / "INDEX.md"
    if index.exists():
        count = len(read_text(index).splitlines())
        if count > INDEX_BUDGET_LINES:
            warnings.append(f"INDEX.md has {count} lines (budget {INDEX_BUDGET_LINES}); merge knowledge notes or archive projects")
    for path in day_files(mem):
        with contextlib.suppress(ValueError):
            expected = week_id(dt.date.fromisoformat(path.stem))
            if path.parent.name != expected:
                warnings.append(f"{path.relative_to(mem)}: this date belongs in {expected}")
    for week in pending_weeks(mem):
        warnings.append(f"{week}: not consolidated yet; run `dailylog consolidate --week {week}`")
    return errors, warnings


def cmd_lint(args):
    mem = memory_dir(args)
    errors, warnings = lint_findings(mem, args.stale_days)
    for line in errors:
        print(f"ERROR {line}")
    for line in warnings:
        print(f"WARN  {line}")
    if not errors and not warnings:
        print("memory is healthy")
    return 1 if errors else 0


def cmd_context(args):
    print(build_context(memory_dir(args), args.max_chars))
    return 0


def build_context(mem, max_chars):
    today = now().date()
    current = week_id(today)
    budget = max_chars
    out = [f"# Memory context: {today.isoformat()} ({current}), {mem}"]

    def add(title, text, limit=None):
        nonlocal budget
        room = min(budget, limit) if limit else budget
        if room < 200 or not text.strip():
            return
        clipped = tail(text.strip(), room)
        budget -= len(clipped)
        out.append(f"\n## {title}\n\n{clipped}")

    if (mem / "INDEX.md").exists():
        index = re.sub(r"<!-- dailylog:index:.*?-->\n?", "", read_text(mem / "INDEX.md"))
        index = re.sub(r"^# Memory index\s*|\n## Notes\s*$", "", index).strip()
        add("INDEX.md", index, int(max_chars * 0.5))
    else:
        out.append("\nNo INDEX.md yet. Run `dailylog init` to add the long-term layers (existing logs are kept).")
    claims = []
    if (mem / "projects").is_dir():
        for path in sorted((mem / "projects").glob("*.md")):
            claims += [f"{path.stem}: {t}" for t in open_tasks(read_text(path)) if t.startswith("- [/]")]
    add("In progress (leave these files alone unless the user asks)", "\n".join(claims))
    days = day_files(mem)
    if days:
        latest = days[-1]
        label = "Today's log" if latest.stem == today.isoformat() else f"Latest log, {latest.stem} (nothing logged today)"
        add(label, read_text(latest), int(max_chars * 0.3))
    summary = mem / current / "summary.md"
    if not summary.exists():
        earlier = [w for w in week_dirs(mem) if w.name < current and (w / "summary.md").exists()]
        if earlier:
            add(f"Previous week's summary, {earlier[-1].name}", read_text(earlier[-1] / "summary.md"))
    notes = []
    pending = pending_weeks(mem)
    if len(pending) > 3:
        notes.append(f"{len(pending)} weeks are not consolidated ({pending[0]} to {pending[-1]}); `dailylog consolidate` lists them.")
    else:
        for week in pending:
            notes.append(f"{week} is not consolidated; offer to run `dailylog consolidate --week {week}`.")
    add("Reminders", "\n".join(notes))
    out.append('\nOlder context: `dailylog search "<terms>"`.')
    return "\n".join(out)


def layer_of(path, mem):
    rel = path.relative_to(mem)
    if rel.parts[0] in ("knowledge", "decisions", "projects"):
        return rel.parts[0]
    if path.name == "HISTORY.md":
        return "history"
    if path.name == "summary.md":
        return "summary"
    return "log" if DAY_RE.match(path.name) else None


def search_store(mem, terms, layer_filter, lines, require_all):
    results = []
    for path in mem.rglob("*.md"):
        if ".git" in path.parts or ".sessions" in path.parts:
            continue
        layer = layer_of(path, mem)
        if not layer or (layer_filter and layer != layer_filter):
            continue
        text = read_text(path)
        folded = fold(text) + " " + fold(path.name)
        present = sum(term in folded for term in terms)
        if present == 0 or (require_all and present < len(terms)):
            continue
        hits = []
        for number, line in enumerate(text.splitlines(), 1):
            value = fold(line)
            count = sum(term in value for term in terms)
            if count and not line.startswith("---"):
                hits.append((count, number, line.strip()))
        hits.sort(key=lambda h: (-h[0], h[1]))
        best = hits[0][0] if hits else 0
        meta, _ = split_frontmatter(text)
        superseded = meta.get("status") == "superseded"
        score = LAYERS[layer] + best * 10 + present * 20 - (35 if superseded else 0)
        recency = path.stem if layer == "log" else meta.get("updated", "")
        results.append((score, recency, mem, path, hits[:lines], superseded))
    return results


def linear_search(args, mem, stores):
    """Fallback for Python builds without SQLite FTS5."""
    terms = [fold(t) for t in " ".join(args.query).split()]
    results = [r for store in stores for r in search_store(store, terms, args.layer, args.lines, True)]
    if not results and len(terms) > 1:
        results = [r for store in stores for r in search_store(store, terms, args.layer, args.lines, False)]
        if results:
            print("no file has every term; closest partial matches:")
    results.sort(key=lambda r: (r[0], r[1]), reverse=True)
    if not results:
        print("no matches")
        return 0
    for _, _, store, path, hits, superseded in results[: args.limit]:
        flag = "  [SUPERSEDED]" if superseded else ""
        prefix = "~/.dailylog: " if store != mem else ""
        print(f"{prefix}{path.relative_to(store)}{flag}")
        for _, number, line in hits:
            print(f"  {number}: {clip(line, 200)}")
    if len(results) > args.limit:
        print(f"...{len(results) - args.limit} more files; narrow the terms or raise --limit")
    return 0


# --- ranked search index (SQLite FTS5; rebuilt from Markdown, never the source) --

INDEX_VERSION = 2
COMMON_WORDS = frozenset("""
bang bien buoc cac cach cam can cho chua chung chuyen cua cung dang day den deu dieu doc dong duoc gan giua hay hien hoac
hoat hon khac khi khong lai lam lan len lieu luon mat minh mot muc nay neu nhan nhieu nhu nhung noi phai phan qua quan rat
rieng roi sang sau sua tai tang the them theo thi thuc tiep toan tren trong truoc tuan tung tuy vao viec voi xong
and are but can for from has have into not that the their then this was were will with you your
""".split())
CHUNK_CHARS = 700
LAYER_BOOST = {"knowledge": 1.6, "decisions": 1.6, "projects": 1.3, "summary": 1.2, "history": 1.1, "log": 1.0}
SCHEMA = """
create table files(path text primary key, mtime real, size integer, layer text, title text, project text,
                   tags text, links text, status text, updated text);
create table chunks(id integer primary key, path text, heading text, line integer, text text);
create index chunks_path on chunks(path);
create virtual table fts using fts5(title, aliases, heading, body, tokenize="unicode61");
create virtual table vocab using fts5vocab(fts, 'row');
"""


def fts_available():
    if os.environ.get("DAILYLOG_NO_FTS"):
        return False
    try:
        probe = sqlite3.connect(":memory:")
        probe.execute("create virtual table t using fts5(x)")
        probe.close()
        return True
    except sqlite3.Error:
        return False


def index_words(text):
    """Folded text plus split identifiers, so `lru cache` also finds LRUCache."""
    parts = []
    for word in re.findall(r"[A-Za-z0-9]*[a-z0-9][A-Z][A-Za-z0-9]*|[A-Z]{2,}[a-z][A-Za-z0-9]*", text):
        parts.append(" ".join(re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+", word)))
    return fold(text + (" " + " ".join(parts) if parts else ""))


def chunk_markdown(body, first_line):
    """Sections split at headings; each session line and long list stays findable alone."""
    chunks, heading, buffer, start = [], "", [], first_line

    def flush():
        nonlocal buffer
        text = "\n".join(buffer).strip()
        if text:
            chunks.append((start, heading, text))
        buffer = []

    for number, line in enumerate(body.splitlines(), first_line):
        found = re.match(r"^(#{1,6})\s+(.*)", line)
        if found:
            flush()
            heading = found.group(2).strip() if len(found.group(1)) > 1 else ""  # h1 is just the file's title
            start = number + 1
            continue
        session = line.startswith("- [session]")
        if session or (sum(map(len, buffer)) > CHUNK_CHARS and re.match(r"^\s*$|^- ", line)):
            flush()
            start = number
        if not buffer:
            start = number
        buffer.append(re.sub(r"\s*<!-- .*? -->", "", line))
        if session:
            flush()
    flush()
    return chunks


def open_index(mem):
    path = mem / ".index.db"
    for attempt in (1, 2):
        try:
            con = sqlite3.connect(str(path), timeout=10)
            version = con.execute("pragma user_version").fetchone()[0]
            if version != INDEX_VERSION:
                for table in ("vocab", "fts", "chunks", "files"):
                    con.execute(f"drop table if exists {table}")
                con.executescript(SCHEMA)
                con.execute(f"pragma user_version={INDEX_VERSION}")
                con.commit()
            con.execute("select count(*) from files").fetchone()
            con.execute("select rowid from fts limit 1").fetchone()
            return con
        except sqlite3.DatabaseError:  # safe to discard: the Markdown is the source
            if attempt == 2:
                raise
            with contextlib.suppress(OSError):
                con.close()
            for suffix in ("", "-journal", "-wal", "-shm"):
                with contextlib.suppress(OSError):
                    os.unlink(str(path) + suffix)


def index_file(con, mem, path, rel, stat):
    layer = layer_of(path, mem)
    text = read_text(path)
    meta, body = split_frontmatter(text)
    offset = text[: len(text) - len(body)].count("\n") + 1
    title = meta.get("title", "")
    summary = meta.get("summary", "")
    aliases = meta.get("aliases", "")
    tags = meta.get("tags", "")
    links = ",".join(sorted({l.strip() for l in re.findall(r"\[\[([^\]|#]+)", text)}))
    con.execute("insert or replace into files values (?,?,?,?,?,?,?,?,?,?)",
                (rel, stat.st_mtime, stat.st_size, layer, title or path.stem, meta.get("project", ""), tags, links,
                 meta.get("status", ""), meta.get("updated", "") or (path.stem if layer == "log" else "")))
    head = index_words(" ".join((title, summary, path.stem.replace("-", " "))))
    extra = index_words(" ".join((aliases, tags)))
    chunks = chunk_markdown(body, offset) or [(offset, "", summary or title or path.stem)]
    for line, heading, chunk in chunks:
        cursor = con.execute("insert into chunks(path,heading,line,text) values (?,?,?,?)", (rel, heading, line, chunk))
        con.execute("insert into fts(rowid,title,aliases,heading,body) values (?,?,?,?,?)",
                    (cursor.lastrowid, head, extra, index_words(heading), index_words(chunk)))


def drop_file(con, rel):
    ids = [row[0] for row in con.execute("select id from chunks where path=?", (rel,))]
    con.executemany("delete from fts where rowid=?", [(i,) for i in ids])
    con.execute("delete from chunks where path=?", (rel,))
    con.execute("delete from files where path=?", (rel,))


def refresh_search_index(mem, con):
    wanted = {}
    for path in mem.rglob("*.md"):
        if ".git" in path.parts or ".sessions" in path.parts or not layer_of(path, mem):
            continue
        with contextlib.suppress(OSError):
            wanted[path.relative_to(mem).as_posix()] = (path, path.stat())
    known = {row[0]: (row[1], row[2]) for row in con.execute("select path,mtime,size from files")}
    stale = [rel for rel, (_, st) in wanted.items() if known.get(rel) != (st.st_mtime, st.st_size)]
    gone = [rel for rel in known if rel not in wanted]
    if not stale and not gone:
        return
    with locked(mem):
        ignore = mem / ".gitignore"
        if ignore.exists() and ".index.db" not in read_text(ignore):
            atomic_write(ignore, read_text(ignore).rstrip() + "\n.index.db*\n")
        with con:
            for rel in gone + stale:
                drop_file(con, rel)
            for rel in stale:
                index_file(con, mem, wanted[rel][0], rel, wanted[rel][1])


def query_tokens(text):
    return re.findall(r"\w+", fold(text))


def fts_term(word):
    return f'"{word}"' + ("*" if len(word) >= 5 else "")


def alias_groups(mem):
    path = mem / "aliases.md"
    if not path.exists():
        return []
    groups = []
    for line in read_text(path).splitlines():
        if "|" in line and not line.startswith("#"):
            groups.append([" ".join(query_tokens(part)) for part in line.split("|") if query_tokens(part)])
    return groups


def query_variants(mem, tokens):
    joined = f" {' '.join(tokens)} "
    variants = [tokens]
    for group in alias_groups(mem):
        for phrase in group:
            if f" {phrase} " in joined:
                for other in group:
                    if other != phrase:
                        variants.append(joined.replace(f" {phrase} ", f" {other} ").split())
    return variants


def ranked_hits(con, tokens, mode, layer):
    if not tokens:
        return []
    match = f" {mode} ".join(fts_term(t) for t in tokens)
    sql = ("select c.path,c.heading,c.line,c.text,f.title,f.layer,f.status,f.updated,bm25(fts,6.0,6.0,3.0,1.0),fts.title||' '||fts.aliases from fts "
           "join chunks c on c.id=fts.rowid join files f on f.path=c.path where fts match ?")
    params = [match]
    if layer:
        sql += " and f.layer=?"
        params.append(layer)
    return con.execute(sql + " order by bm25(fts,6.0,6.0,3.0,1.0) limit 300", params).fetchall()


def term_in(term, words):
    return term in words or (len(term) >= 5 and any(w.startswith(term) for w in words))


def score_hit(hit, tokens):
    _, heading, _, text, title, layer, status, _, rank, head = hit
    folded = index_words(" ".join((title, head, heading, text)))
    words = set(re.findall(r"\w+", folded))
    matched = sum(term_in(t, words) for t in tokens)
    score = -rank * LAYER_BOOST.get(layer, 1.0) * (matched / len(tokens)) ** 2
    if len(tokens) > 1:  # Vietnamese words span syllables, so neighbours matter
        spaced = " ".join(re.findall(r"\w+", folded))
        pairs = sum(f"{a} {b}" in spaced for a, b in zip(tokens, tokens[1:]))
        score *= 1 + pairs / (len(tokens) - 1)
    return score * (0.4 if status == "superseded" else 1.0)


def display_line(line):
    """Session lines lead with the time and agent; their long folder path can wait."""
    return re.sub(r"^(- \[session\] \([^)]*\) \S+, [^,]+), [^:\"]*(?:/[^:\"]*)?:", r"\1:", line)


def best_lines(text, tokens, first_line, count):
    picked = []
    for number, line in enumerate(text.splitlines(), first_line):
        words = set(query_tokens(index_words(line)))
        hits = sum(term_in(t, words) for t in tokens)
        if hits and line.strip():
            picked.append((-hits, number, line.strip()))
    return sorted(picked)[:count] or [(0, first_line, text.splitlines()[0].strip())]


def search_index(mem, tokens, layer):
    con = open_index(mem)
    try:
        refresh_search_index(mem, con)
        found = {}
        partial = False
        variants = query_variants(mem, tokens)
        for at, variant in enumerate(variants):
            for hit in ranked_hits(con, variant, "AND", layer):
                key = (hit[0], hit[2])
                score = score_hit(hit, variant) * (1.0 if at == 0 else 0.9)
                if key not in found or score > found[key][0]:
                    found[key] = (score, hit, variant)
        if not found and len(tokens) > 1:
            partial = True
            for variant in variants:
                for hit in ranked_hits(con, variant, "OR", layer):
                    words = set(query_tokens(index_words(" ".join((hit[4], hit[9], hit[1], hit[3])))))
                    if sum(term_in(t, words) for t in variant) * 2 < len(variant):  # one common syllable is noise
                        continue
                    key = (hit[0], hit[2])
                    score = score_hit(hit, variant)
                    if key not in found or score > found[key][0]:
                        found[key] = (score, hit, variant)
        return list(found.values()), partial
    finally:
        con.close()


def cmd_search(args):
    mem = memory_dir(args)
    tokens = query_tokens(" ".join(args.query))
    if not tokens:
        fail("nothing to search for")
    stores = [mem]
    other = global_store()
    if not args.here and other.resolve() != mem.resolve() and (other / "INDEX.md").exists():
        stores.append(other)
    if not fts_available():
        return linear_search(args, mem, stores)
    by_file, any_partial, any_full = {}, False, False
    for store in stores:
        try:
            scored, partial = search_index(store, tokens, args.layer)
        except sqlite3.Error as exc:
            print(f"dailylog: search index unavailable ({exc}); using a plain scan", file=sys.stderr)
            return linear_search(args, mem, stores)
        any_partial |= partial and bool(scored)
        any_full |= bool(scored) and not partial
        for score, hit, variant in scored:
            by_file.setdefault((store, hit[0]), []).append((score, hit, variant))
    if not by_file:
        print("no matches; try other wording, or `dailylog alias` once you learn what it is called here")
        return 0
    if any_partial and not any_full:
        print("no entry has every term; closest partial matches:")
    ordered = sorted(by_file.items(), key=lambda item: (max(h[0] for h in item[1]), max(h[1][7] for h in item[1])), reverse=True)
    for (store, rel), hits in ordered[: args.limit]:
        hits.sort(key=lambda h: h[0], reverse=True)
        flag = "  [SUPERSEDED]" if hits[0][1][6] == "superseded" else ""
        prefix = "~/.dailylog: " if store != mem else ""
        print(f"{prefix}{rel}{flag}")
        shown = 0
        for _, hit, variant in hits:
            heading = f"[{hit[1]}] " if hit[1] and hit[1] != hit[4] else ""
            for _, number, line in best_lines(hit[3], variant, hit[2], 1):
                print(f"  {number}: {heading}{clip(display_line(line), 200)}")
                shown += 1
            if shown >= args.lines:
                break
    if len(ordered) > args.limit:
        print(f"...{len(ordered) - args.limit} more files; narrow the terms or raise --limit")
    return 0


def cmd_related(args):
    mem = memory_dir(args)
    if not fts_available():
        fail("related needs a Python build with SQLite FTS5")
    con = open_index(mem)
    try:
        refresh_search_index(mem, con)
        rows = {row[0]: row for row in con.execute("select path,layer,title,project,tags,links,status,updated from files")}
        needle = args.target.removeprefix("memory/") if hasattr(str, "removeprefix") else args.target
        wanted = ([p for p in rows if p == needle] or [p for p in rows if Path(p).stem == needle]
                  or [p for p in rows if needle in Path(p).stem])
        if len(wanted) != 1:
            fail(f"{args.target!r} matches {len(wanted)} files; give the path relative to memory/" + ("".join("\n  " + p for p in wanted[:8])))
        target = wanted[0]
        _, _, title, project, tags, links, _, _ = rows[target]
        stem = Path(target).stem
        reasons = {}

        def add(path, points, why):
            if path != target:
                entry = reasons.setdefault(path, [0, []])
                entry[0] += points
                if why not in entry[1]:
                    entry[1].append(why)

        by_stem = {Path(p).stem: p for p in rows}
        for link in filter(None, links.split(",")):
            if link in by_stem:
                add(by_stem[link], 100, "linked from it")
        target_tags = {t.strip() for t in tags.split(",") if t.strip()}
        for path, row in rows.items():
            if stem in filter(None, row[5].split(",")):
                add(path, 100, "links to it")
            if project and row[3] == project:
                add(path, 25 * LAYER_BOOST.get(row[1], 1.0), f"project {project}")
            shared = target_tags & {t.strip() for t in row[4].split(",") if t.strip()}
            if shared:
                add(path, 20 * len(shared), "tag " + ", ".join(sorted(shared)))
        words = [w for w in query_tokens(index_words(" ".join(
            text for (text,) in con.execute("select text from chunks where path=?", (target,))) + " " + title)) if len(w) >= 3]
        total = con.execute("select count(*) from chunks").fetchone()[0] or 1
        rare = {}
        for word in set(words):
            row = con.execute("select doc from vocab where term=?", (word,)).fetchone()
            if row and 1 < row[0] < max(3, total * 0.05) and word not in COMMON_WORDS:
                rare[word] = row[0]
        picked = sorted(rare, key=lambda w: (rare[w], w))[:15]
        if picked:
            overlap = {}
            for path, text, heading, ftitle in con.execute(
                    "select c.path,c.text,c.heading,f.title from fts join chunks c on c.id=fts.rowid join files f on f.path=c.path "
                    "where fts match ? limit 1000", (" OR ".join(f'"{w}"' for w in picked),)):
                found = set(query_tokens(index_words(" ".join((text, heading, ftitle))))) & set(picked)
                overlap.setdefault(path, set()).update(found)
            for path, found in overlap.items():
                if len(found) >= 2 and any(len(word) >= 5 for word in found):
                    add(path, 6 * len(found) * LAYER_BOOST.get(rows[path][1], 1.0), "shared: " + ", ".join(sorted(found)[:4]))
        if not reasons:
            print("nothing related found")
            return 0
        ordered = sorted(reasons.items(), key=lambda item: item[1][0], reverse=True)
        for path, (_, why) in ordered[: args.limit]:
            flag = " [SUPERSEDED]" if rows[path][6] == "superseded" else ""
            print(f"{path}{flag} ({'; '.join(why)})")
        return 0
    finally:
        con.close()


def cmd_alias(args):
    mem = memory_dir(args)
    if len(args.names) < 2:
        fail('give at least two names for one thing: dailylog alias "phinh cache" "tran bo nho"')
    refuse_secrets(*args.names)
    line = " | ".join(one_line(name) for name in args.names)
    path = mem / "aliases.md"
    with locked(mem):
        current = read_text(path) if path.exists() else "# Search aliases\n\nNames on one line mean the same thing to `dailylog search`.\n\n"
        if line not in current:
            atomic_write(path, current.rstrip() + "\n" + line + "\n")
    print(line)
    return 0


# --- report -----------------------------------------------------------------

ENTRY_RE = re.compile(r"^- (?:\[session\] |\[.\] \[[A-Z_]+\] )?\(([^)]+)\) (\d\d:\d\d)(?:-(\d\d:\d\d))?[,\s]*(.*)$")
TURNS_RE = re.compile(r"^(\d+) turns?,")


def minutes_between(start, end):
    to_minutes = lambda value: int(value[:2]) * 60 + int(value[3:])
    return max(0, to_minutes(end) - to_minutes(start))


def cmd_report(args):
    mem = memory_dir(args)
    day = dt.date.fromisoformat(args.day) if args.day else now().date()
    path = day_path(mem, day)
    if not path.exists():
        print(f"no log for {day.isoformat()}")
        return 0
    entries, unstamped, totals = [], 0, {}
    for raw in read_text(path).splitlines():
        line = re.sub(r"\s*<!-- session:[^>]* -->$", "", raw)
        found = ENTRY_RE.match(line)
        if not found:
            if raw.startswith(("- ", "  - ", "    - ")):
                unstamped += 1
            continue
        who, start, end, rest = found.groups()
        if args.agent and fold(args.agent) not in fold(who):
            continue
        agent = who.split(",")[0]
        total = totals.setdefault(agent, {"sessions": 0, "turns": 0, "minutes": 0, "entries": 0})
        total["entries"] += 1
        if end:
            total["sessions"] += 1
            total["minutes"] += minutes_between(start, end)
            turns = TURNS_RE.match(rest)
            total["turns"] += int(turns.group(1)) if turns else 0
        entries.append((start, end, who, rest))
    print(f"# Report {day.isoformat()} ({week_id(day)})")
    if totals:
        print("\n| Agent | Sessions | Turns | Minutes | Entries |\n|---|---|---|---|---|")
        for agent, total in sorted(totals.items()):
            print(f"| {agent} | {total['sessions']} | {total['turns']} | {total['minutes']} | {total['entries']} |")
    current = None
    for start, end, who, rest in sorted(entries, key=lambda e: e[0]):
        if start[:2] != current:
            current = start[:2]
            print(f"\n## {current}:00\n")
        span = f"{start}-{end}" if end else start
        print(f"- {span} ({who}) {clip(rest, args.width)}")
    if unstamped:
        print(f"\n{unstamped} older lines in this file have no time or agent.")
    return 0


# --- consolidation ----------------------------------------------------------


def cmd_consolidate(args):
    mem = memory_dir(args)
    if not args.week:
        pending = pending_weeks(mem)
        print("\n".join(pending) if pending else "nothing to consolidate")
        return 0
    if not WEEK_RE.match(args.week):
        fail("--week must look like 2026-W45")
    week = mem / args.week
    if not week.is_dir():
        fail(f"no folder for {args.week}")
    summary = week / "summary.md"
    if args.done:
        return finish_consolidation(args, mem, summary)
    days = sorted(f for f in week.iterdir() if DAY_RE.match(f.name))
    start, end = week_bounds(args.week)
    print(f"# Consolidate {args.week} ({start} to {end})\n\nRead these files (only these):")
    for path in days:
        print(f"  {path}  ({path.stat().st_size} bytes)")
    print(f"  {summary}  ({'exists' if summary.exists() else 'missing, write it'})")
    todos = [f"  {p.name}: {line.strip()}" for p in days for line in read_text(p).splitlines() if LEGACY_TODO_RE.search(line)]
    print("\nOpen items mentioned in these logs (some may already be finished):")
    print("\n".join(todos) if todos else "  none")
    print(f"""
Then:
1. Durable facts (hosts, paths, device specs, pitfalls, how-tos): `dailylog new knowledge`, or edit the existing note and `dailylog verify`.
2. Choices someone may later question: `dailylog new decision`, with the alternatives rejected.
3. Current state of each project: rewrite "Current state" in projects/<slug>.md.
4. Still-open items: `dailylog todo add <project> "..."`. Drop finished ones.
5. Project-specific knowledge belongs in that project's own repo docs; link to it instead of copying.
6. Write or refresh summary.md (1-2 lines per project; no debugging detail).
7. Finish: dailylog consolidate --week {args.week} --done --headline "<one line for this week>"
Daily logs stay as they are: they are the record, not a draft.""")
    return 0


def finish_consolidation(args, mem, summary):
    if not args.headline:
        fail("--done needs --headline, the week's line in HISTORY.md")
    if not summary.exists():
        fail(f"write {summary} first")
    text = read_text(summary)
    if CONSOLIDATED_RE.search(text):
        fail(f"{args.week} is already consolidated")
    refuse_secrets(args.headline)
    start, end = week_bounds(args.week)
    with locked(mem):
        who = instance_name(args)
        atomic_write(summary, text.rstrip() + f"\n\n<!-- consolidated: {now().date().isoformat()} by {who} -->\n")
        history = mem / "HISTORY.md"
        current = read_text(history) if history.exists() else "# Work history\n\n"
        line = f"- **{args.week}** ({start} to {end}): {one_line(args.headline)}"
        atomic_write(history, current.rstrip() + "\n" + line + "\n")
        refresh_index(mem)
    print(f"consolidated {args.week}")
    return 0


# --- automatic session capture (runs in hooks, uses no model tokens) ----------

HOOK_EVENTS = {
    "claude": ["SessionStart", "UserPromptSubmit", "Stop", "SessionEnd"],
    "codex": ["SessionStart", "UserPromptSubmit", "Stop"],
    "agy": ["SessionStart", "Stop"],
}
AGENT_LABELS = {"claude": "Claude", "codex": "Codex", "agy": "Antigravity"}
SESSION_KEEP_DAYS = 14
SESSION_TEXT_CHARS = 140


def scrub(text):
    text = one_line(re.sub(r"[*`#]+", "", text))
    for pattern in SECRET_PATTERNS.values():
        text = re.sub(pattern, "[redacted]", text)
    return text


def first_value(payload, *keys):
    for key in keys:
        value = payload.get(key)
        if value:
            return value
    return ""


def hook_memory(cwd):
    explicit = os.environ.get("DAILYLOG_ROOT")
    if explicit:
        return store_of(Path(explicit).expanduser().resolve())
    here = Path(cwd).expanduser()
    if here.is_dir():
        for candidate in [here.resolve(), *here.resolve().parents]:
            mem = candidate / "memory"
            if mem.is_dir() and ((mem / "INDEX.md").exists() or week_dirs(mem)):
                return mem
    return global_store()


def commits_since(cwd, started):
    try:
        done = subprocess.run(["git", "-C", cwd, "log", f"--since={started}", "--format=%h", "-n", "10"],
                              capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return []
    return done.stdout.split() if done.returncode == 0 else []


def session_line(state):
    started = state["started"][11:16]
    ended = state.get("ended", state["started"])[11:16]
    place = state["cwd"].replace(str(Path.home()), "~")
    who = state["label"] + (f", {state['model']}" if state.get("model") else "")
    turns = f"{state['turns']} turn" + ("" if state["turns"] == 1 else "s")
    if state.get("steps"):
        turns = f"{state['steps']} steps"
    line = f"- [session] ({who}) {started}-{ended}, {turns}, {place}"
    if state.get("title"):
        line += f': "{state["title"]}"'
    if state.get("outcome"):
        line += f" -> {state['outcome']}"
    if state.get("commits"):
        line += f" (commits: {' '.join(state['commits'])})"
    return line + f" <!-- session:{state['id']} -->"


def upsert_session_line(mem, state):
    path = mem / state["week"] / f"{state['day']}.md"
    marker = f"<!-- session:{state['id']} -->"
    line = session_line(state)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, f"# Work log - {state['day']} ({state['week']})\n\n{line}\n")
        return
    lines = read_text(path).splitlines()
    for i, existing in enumerate(lines):
        if existing.endswith(marker):
            lines[i] = line
            break
    else:
        lines.append(line)
    atomic_write(path, "\n".join(lines) + "\n")


def clean_sessions(folder):
    limit = now().timestamp() - SESSION_KEEP_DAYS * 86400
    for path in folder.glob("*.json"):
        with contextlib.suppress(OSError):
            if path.stat().st_mtime < limit:
                path.unlink()


def run_hook(args, payload):
    cwd = str(first_value(payload, "cwd") or (payload.get("workspacePaths") or [""])[0] or os.getcwd())
    mem = hook_memory(cwd)
    if not (mem / "INDEX.md").exists():
        init_layers(mem)
    moment = now()
    today = moment.date()
    session = re.sub(r"[^A-Za-z0-9_-]", "", str(first_value(payload, "session_id", "conversationId", "thread_id")))[:12]
    session = session or f"pid{os.getppid()}"
    folder = mem / ".sessions"
    folder.mkdir(exist_ok=True)
    path = folder / f"{session}.json"
    label = AGENT_LABELS.get(args.agent, args.agent)
    if os.environ.get("DAILYLOG_INSTANCE"):
        label += ":" + one_line(os.environ["DAILYLOG_INSTANCE"]).replace(")", "")
    fresh = {"id": session, "label": label, "cwd": cwd, "turns": 0,
             "started": moment.isoformat(timespec="seconds"), "day": today.isoformat(), "week": week_id(today)}
    with locked(mem):
        state = json.loads(read_text(path)) if path.exists() else fresh
        if state.get("day") != today.isoformat():  # a resumed session gets a new line in today's log
            state = fresh
        model = first_value(payload, "model", "modelName")
        model = model.get("id", "") if isinstance(model, dict) else model
        if model and model != "auto":
            state["model"] = re.sub(r"[^\w.\[\]:-]", "", str(model))[:40]
        prompt = first_value(payload, "prompt", "lastUserInput")
        if args.event == "UserPromptSubmit" or (args.event == "Stop" and args.agent == "agy"):
            state["turns"] += 1
        if args.capture == "full":
            if prompt and not state.get("title"):
                state["title"] = clip(scrub(prompt), SESSION_TEXT_CHARS)
            reply = first_value(payload, "last_assistant_message", "lastAssistantMessage")
            if reply:
                state["outcome"] = clip(scrub(reply), SESSION_TEXT_CHARS)
        if args.event in ("Stop", "SessionEnd"):
            state["ended"] = moment.isoformat(timespec="seconds")
            state["commits"] = commits_since(cwd, state["started"])
        if args.event == "SessionStart":
            clean_sessions(folder)
        atomic_write(path, json.dumps(state, ensure_ascii=False))
        if state["turns"] or state.get("title"):  # sessions that never did anything stay out of the log
            upsert_session_line(mem, state)
    if args.event == "SessionStart" and args.context_chars > 0 and payload.get("source") != "resume":
        return build_context(mem, args.context_chars)
    return ""


def cmd_hook(args):
    """Must never break the agent's session: every failure is swallowed."""
    output = ""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        output = run_hook(args, payload if isinstance(payload, dict) else {})
    except (Exception, SystemExit) as exc:
        print(f"dailylog hook: {exc}", file=sys.stderr)
    if args.agent == "agy":
        steps = {"injectSteps": [{"systemMessage": {"systemMessage": output}}]} if output else {}
        print(json.dumps(steps, ensure_ascii=False))
    elif output:
        print(output)
    return 0


def hook_settings_path(agent, scope, root):
    base = Path.home() if scope == "global" else root
    return base / {
        ("claude", "global"): ".claude/settings.json", ("claude", "project"): ".claude/settings.json",
        ("codex", "global"): ".codex/hooks.json", ("codex", "project"): ".codex/hooks.json",
        ("agy", "global"): ".gemini/config/hooks.json", ("agy", "project"): ".agents/hooks.json",
    }[(agent, scope)]


def is_ours(handler):
    return "dailylog.py" in str(handler.get("command", "")) and " hook " in str(handler.get("command", ""))


def merge_grouped(hooks, agent, commands):
    for event in list(hooks):
        kept = []
        for group in hooks[event]:
            inner = [h for h in group.get("hooks", []) if not is_ours(h)]
            if inner or not group.get("hooks"):
                kept.append({**group, "hooks": inner})
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    for event, command in commands.items():
        hooks.setdefault(event, []).append(
            {"matcher": "", "hooks": [{"type": "command", "command": command, "timeout": 10}]})


def merged_settings(agent, current, commands):
    data = dict(current)
    if agent == "agy":
        data.pop("dailylog", None)
        if commands:
            data["dailylog"] = {event: [{"type": "command", "command": command, "timeout": 10}]
                                for event, command in commands.items()}
        return data
    hooks = dict(data.get("hooks") or {})
    merge_grouped(hooks, agent, commands)
    if hooks:
        data["hooks"] = hooks
    else:
        data.pop("hooks", None)
    return data


def cmd_install_hooks(args):
    root = (Path(args.root).expanduser().resolve() if args.root else Path.cwd().resolve())
    agents = args.agents.split(",") if args.agents else [
        a for a, folder in (("claude", ".claude"), ("codex", ".codex"), ("agy", ".gemini/config"))
        if (Path.home() / folder).is_dir()]
    script = os.path.realpath(__file__)
    chars = 0 if args.context == "off" else args.context_chars
    for agent in agents:
        if agent not in HOOK_EVENTS:
            fail(f"no hook support for {agent!r}; use the skill plus `dailylog wire` for that agent")
        path = hook_settings_path(agent, args.scope, root)
        current = {}
        if path.exists():
            try:
                current = json.loads(read_text(path) or "{}")
            except ValueError:
                fail(f"{path} is not valid JSON; fix it first, nothing was changed")
        commands = {} if args.remove else {
            event: (f"python3 {shlex.quote(script)} hook --agent {agent} --event {event} "
                    f"--context-chars {chars} --capture {args.capture}")
            for event in HOOK_EVENTS[agent]}
        merged = merged_settings(agent, current, commands)
        if merged == current:
            print(f"unchanged: {path}")
            continue
        if args.dry_run:
            print(f"would update: {path}")
            continue
        backup = path.with_name(path.name + ".dailylog-backup")
        if path.exists() and not backup.exists():
            backup.write_text(read_text(path), encoding="utf-8")
        atomic_write(path, json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
        print(f"{'removed from' if args.remove else 'installed in'}: {path}")
    if args.scope == "project" and not args.remove and not args.dry_run:
        init_layers(root / "memory")
        tracked = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "memory"], capture_output=True)
        if tracked.returncode == 1:
            print("warning: memory/ is not git-ignored here. Session lines quote prompts; do not push it to a public repo, or use --capture meta.")
    return 0


# --- importing past sessions (a local scan, uses no model tokens) --------------

NOT_TYPED_RE = re.compile(r"^\s*(<[a-zA-Z_-]+|\[Request interrupted|# AGENTS|I hit my usage limit)")


def parse_time(value):
    """ISO timestamps from any agent, as local time; None when unusable."""
    if not value or str(value).startswith("0001"):
        return None
    text = re.sub(r"(\.\d{6})\d+", r"\1", str(value).replace("Z", "+00:00"))
    try:
        moment = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    return moment.astimezone().replace(tzinfo=None) if moment.tzinfo else moment


def block_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict)]
        return "\n".join(p for p in parts if p)
    return ""


def session_id(raw):
    return re.sub(r"[^A-Za-z0-9_-]", "", str(raw))[:12]


class DayTally:
    """Collects one session's activity, one line per local day."""

    def __init__(self, agent, raw_id):
        self.agent, self.id, self.days, self.cwd, self.model = agent, session_id(raw_id), {}, "", ""
        self.seen = set()

    def day(self, moment):
        return self.days.setdefault(moment.date(), {"start": moment, "end": moment, "turns": 0, "title": "", "outcome": ""})

    def touch(self, moment):
        if moment:
            entry = self.day(moment)
            entry["start"], entry["end"] = min(entry["start"], moment), max(entry["end"], moment)

    def prompt(self, moment, text):
        if moment and text and not NOT_TYPED_RE.match(text) and (moment, text) not in self.seen:
            self.seen.add((moment, text))
            entry = self.day(moment)
            entry["turns"] += 1
            entry["title"] = entry["title"] or text

    def reply(self, moment, text):
        if moment and text:
            entry = self.day(moment)
            if moment >= entry.get("replied", moment):
                entry["replied"], entry["outcome"] = moment, text

    def states(self, capture):
        for day, entry in self.days.items():
            if not entry["turns"]:
                continue
            yield {"id": self.id, "label": self.agent, "model": self.model, "cwd": self.cwd or str(Path.home()),
                   "turns": entry["turns"], "started": entry["start"].isoformat(timespec="seconds"),
                   "ended": entry["end"].isoformat(timespec="seconds"), "day": day.isoformat(), "week": week_id(day),
                   "title": clip(scrub(entry["title"]), SESSION_TEXT_CHARS) if capture == "full" else "",
                   "outcome": clip(scrub(entry["outcome"]), SESSION_TEXT_CHARS) if capture == "full" else ""}


def read_jsonl(path):
    name = str(path)
    if name.endswith(".zst"):
        try:
            from compression import zstd
            stream = zstd.open(name, "rt", encoding="utf-8", errors="replace")
        except ImportError:
            done = subprocess.run(["zstd", "-dc", name], capture_output=True)
            if done.returncode:
                raise OSError("cannot read .zst: needs Python 3.14 or the zstd command")
            stream = done.stdout.decode("utf-8", "replace").splitlines()
    else:
        stream = open(name, encoding="utf-8", errors="replace")
    for line in stream:
        with contextlib.suppress(ValueError):
            record = json.loads(line)
            if isinstance(record, dict):
                yield record
    if hasattr(stream, "close"):
        stream.close()


def scan_claude(stats):
    for path in sorted(Path.home().glob(".claude/projects/*/*.jsonl")):
        try:
            tally = DayTally("Claude", path.stem)
            for record in read_jsonl(path):
                if record.get("isSidechain"):
                    continue
                moment = parse_time(record.get("timestamp"))
                kind, message = record.get("type"), record.get("message") or {}
                if kind == "user" and not record.get("isMeta"):
                    tally.cwd = tally.cwd or record.get("cwd", "")
                    tally.touch(moment)
                    if not record.get("toolUseResult"):
                        tally.prompt(moment, block_text(message.get("content")))
                elif kind == "assistant":
                    tally.touch(moment)
                    tally.model = message.get("model") if str(message.get("model", "")).startswith("claude") else tally.model
                    tally.reply(moment, block_text([b for b in message.get("content") or [] if isinstance(b, dict) and b.get("type") == "text"]))
            yield tally
        except OSError:
            stats["errors"] += 1


def scan_codex(stats):
    home = Path.home() / ".codex"
    paths = [p for folder in ("sessions", "archived_sessions") for p in (home / folder).rglob("*")
             if p.is_file() and p.name.endswith((".jsonl", ".jsonl.zst"))]
    tallies = {}  # a long session continues across several rollout files under one id
    for path in sorted(paths):
        try:
            tally, subagent = None, False
            typed_items = False
            for record in read_jsonl(path):
                kind, payload = record.get("type"), record.get("payload") or {}
                moment = parse_time(record.get("timestamp"))
                if kind == "session_meta":
                    source = payload.get("source")
                    subagent = isinstance(source, dict) and "subagent" in source
                    if subagent:
                        break
                    raw_id = payload.get("id") or path.stem
                    tally = tallies.setdefault(raw_id, DayTally("Codex", raw_id))
                    tally.cwd = tally.cwd or payload.get("cwd", "")
                elif tally is None:
                    continue
                elif kind == "turn_context":
                    tally.model = payload.get("model") or tally.model
                    tally.cwd = tally.cwd or payload.get("cwd", "")
                elif kind == "event_msg":
                    item = payload.get("item") or {}
                    tally.touch(moment)
                    if payload.get("type") == "item_completed" and item.get("type") == "UserMessage":
                        typed_items = True
                        tally.prompt(moment, block_text(item.get("content")))
                    elif payload.get("type") == "user_message":
                        typed_items = True
                        tally.prompt(moment, payload.get("message", ""))
                    elif payload.get("type") == "task_complete":
                        tally.reply(moment, payload.get("last_agent_message") or "")
                elif kind == "response_item" and payload.get("type") == "message":
                    text = block_text(payload.get("content"))
                    tally.touch(moment)
                    if payload.get("role") == "assistant":
                        tally.reply(moment, text)
                    elif payload.get("role") == "user" and not typed_items:
                        tally.prompt(moment, text)
            if subagent:
                stats["subagents"] += 1
        except OSError:
            stats["errors"] += 1
    yield from tallies.values()


def first_proto_string(blob):
    """Field 1 of a protobuf message: Antigravity's stored opening prompt."""
    if not isinstance(blob, (bytes, bytearray)) or len(blob) < 2 or blob[0] != 0x0A:
        return ""
    size, shift, at = 0, 0, 1
    while at < len(blob):
        byte = blob[at]
        size |= (byte & 0x7F) << shift
        at += 1
        if not byte & 0x80:
            break
        shift += 7
    return bytes(blob[at:at + size]).decode("utf-8", "replace")


def scan_antigravity(stats):
    found = {}
    for name in ("antigravity", "antigravity-cli"):
        path = Path.home() / ".gemini" / name / "conversation_summaries.db"
        if not path.exists():
            continue
        try:
            db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            rows = db.execute("select conversation_id,title,preview,step_count,last_modified_time,last_user_input_time,"
                              "workspace_uris,nesting_depth,parent_conversation_id,raw_summary from conversation_summaries").fetchall()
            tails = {}
            with contextlib.suppress(sqlite3.Error):
                for cid, body in db.execute("select c0,c14 from conversations_fts_content order by c0,c1"):
                    if body:
                        tails[cid] = body
        except sqlite3.Error:
            stats["errors"] += 1
            continue
        for cid, title, preview, steps, modified, asked, uris, depth, parent, raw in rows:
            if depth or parent:
                stats["subagents"] += 1
                continue
            ended = parse_time(modified) or parse_time(asked)
            if not ended:  # some rows carry an empty date; the conversation file still has one
                with contextlib.suppress(OSError):
                    ended = dt.datetime.fromtimestamp((path.parent / "conversations" / f"{cid}.db").stat().st_mtime)
            started = parse_time(asked) or ended
            if not ended or not steps:
                stats["undated"] += 1
                continue
            if started.date() != ended.date() or started > ended:
                started = ended
            cwd = ""
            with contextlib.suppress(ValueError, TypeError, IndexError):
                from urllib.parse import unquote
                cwd = unquote(json.loads(uris)[0]).replace("file://", "")
            known = found.get(cid)
            if not known or steps > known["steps"]:
                lines = [l for l in (tails.get(cid) or "").splitlines() if len(re.findall(r"\w", l)) >= 8]
                found[cid] = {"steps": steps, "start": started, "end": ended, "cwd": cwd, "outcome": lines[-1] if lines else "",
                              "title": title or first_proto_string(raw) or preview or ""}
    for cid, row in found.items():
        tally = DayTally("Antigravity", cid)
        tally.cwd = row["cwd"]
        tally.steps = row["steps"]
        tally.days[row["start"].date()] = {"start": row["start"], "end": row["end"], "turns": 1,
                                           "title": row["title"], "outcome": row["outcome"]}
        yield tally


SCANNERS = {"claude": scan_claude, "codex": scan_codex, "agy": scan_antigravity}
IMPORT_TURNS_RE = re.compile(r", (\d+) turns?,")


def merge_session_lines(path, day, week, states, dry_run):
    """Add or refresh this day's session lines; everything else stays byte for byte."""
    lines = read_text(path).splitlines() if path.exists() else [f"# Work log - {day} ({week})", ""]
    positions, unique = {}, []
    removed = 0
    for line in lines:
        found = re.search(r"<!-- session:([^ ]+) -->$", line)
        if found and found.group(1) in positions:  # keep the first copy of a repeated session
            removed += 1
            continue
        if found:
            positions[found.group(1)] = len(unique)
        unique.append(line)
    lines = unique
    added = updated = same = 0
    for state in sorted(states, key=lambda item: item["started"]):
        line = session_line(state)
        at = positions.get(state["id"])
        if at is None:
            positions[state["id"]] = len(lines)
            lines.append(line)
            added += 1
        elif lines[at] == line:
            same += 1
        else:
            kept = IMPORT_TURNS_RE.search(lines[at])
            if kept and not state.get("steps") and int(kept.group(1)) > state["turns"]:
                same += 1
            else:
                lines[at] = line
                updated += 1
    if (added or updated or removed) and not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, "\n".join(lines) + "\n")
    return added, updated, same


def cmd_import(args):
    agents = args.agents.split(",") if args.agents else list(SCANNERS)
    for agent in agents:
        if agent not in SCANNERS:
            fail(f"cannot import from {agent!r}; known sources: {', '.join(SCANNERS)}")
    since = args.since or ""
    grouped, tally_stats, redacted = {}, {}, 0
    for agent in agents:
        stats = {"sessions": 0, "lines": 0, "subagents": 0, "undated": 0, "errors": 0}
        tally_stats[agent] = stats
        for tally in SCANNERS[agent](stats):
            produced = list(tally.states(args.capture))
            if produced:
                stats["sessions"] += 1
            for state in produced:
                if state["day"] < since:
                    continue
                if getattr(tally, "steps", 0):
                    state["steps"] = tally.steps
                stats["lines"] += 1
                redacted += "[redacted]" in state["title"] + state["outcome"]
                grouped.setdefault(hook_memory(state["cwd"]), {}).setdefault((state["week"], state["day"]), []).append(state)
    for agent, stats in tally_stats.items():
        extras = "".join(f", {stats[k]} {k} skipped" for k in ("subagents", "undated", "errors") if stats[k])
        print(f"{agent}: {stats['sessions']} sessions, {stats['lines']} day lines{extras}")
    totals = [0, 0, 0]
    for mem, days in sorted(grouped.items()):
        if not (mem / "INDEX.md").exists() and not args.dry_run:
            init_layers(mem)
        counts = [0, 0, 0]
        with (locked(mem) if not args.dry_run else contextlib.nullcontext()):
            for (week, day), states in sorted(days.items()):
                for i, value in enumerate(merge_session_lines(mem / week / f"{day}.md", day, week, states, args.dry_run)):
                    counts[i] += value
        totals = [a + b for a, b in zip(totals, counts)]
        print(f"{mem}: {len(days)} days, {counts[0]} new, {counts[1]} updated, {counts[2]} unchanged")
    print(("dry run, nothing written. " if args.dry_run else "") + f"{totals[0]} new, {totals[1]} updated, {totals[2]} unchanged; {redacted} lines had secrets redacted.")
    return 0


# --- cli --------------------------------------------------------------------


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="folder containing memory/, or ~/.dailylog (default: $DAILYLOG_ROOT, then search upward)")
    common.add_argument("--instance", help="label for log lines (default: $DAILYLOG_INSTANCE, then auto-detect)")
    parser = argparse.ArgumentParser(prog="dailylog", description="Layered long-term memory shared by coding agents.")
    subs = parser.add_subparsers(dest="command", required=True)

    def sub(name, func, help_text):
        item = subs.add_parser(name, parents=[common], help=help_text, description=help_text)
        item.set_defaults(func=func)
        return item

    item = sub("init", cmd_init, "create the memory layers; never touches existing files")
    item.add_argument("--git", action="store_true", help="also git init inside memory/")
    item.add_argument("--wire", action="store_true", help="also add the protocol block to AGENTS.md")
    item = sub("wire", cmd_wire, "add or refresh the protocol block in AGENTS.md, CLAUDE.md, GEMINI.md")
    item.add_argument("--remove", action="store_true")
    item.add_argument("--dry-run", action="store_true")
    item = sub("context", cmd_context, "print what a new session should know")
    item.add_argument("--max-chars", type=int, default=4000)
    item = sub("search", cmd_search, "ranked search of all layers, ignoring case and Vietnamese diacritics")
    item.add_argument("query", nargs="+")
    item.add_argument("--layer", choices=sorted(LAYERS))
    item.add_argument("--here", action="store_true", help="skip the global store ~/.dailylog")
    item.add_argument("--limit", type=int, default=8)
    item.add_argument("--lines", type=int, default=3)
    item = sub("log", cmd_log, "append to today's log; use - to read the text from stdin")
    item.add_argument("text")
    item.add_argument("-p", "--project")
    item.add_argument("-s", "--status", choices=["note", "done"], default="note")
    item = sub("todo", cmd_todo, "track open tasks in a project file")
    item.add_argument("action", choices=["add", "start", "done", "list"])
    item.add_argument("project", nargs="?")
    item.add_argument("text", nargs="?")
    item = sub("new", cmd_new, "create a project, knowledge note or decision record")
    item.add_argument("kind", choices=["project", "knowledge", "decision"])
    item.add_argument("slug")
    item.add_argument("--title")
    item.add_argument("--summary", default="")
    item.add_argument("--project")
    item.add_argument("--tags")
    item.add_argument("--aliases", help="other names people use for this, comma separated")
    item.add_argument("--body", help="note body; - reads stdin")
    item.add_argument("--context")
    item.add_argument("--choice")
    item.add_argument("--alternatives")
    item.add_argument("--consequences")
    item.add_argument("--supersedes")
    item = sub("verify", cmd_verify, "mark a note as re-checked today")
    item.add_argument("path", help="path relative to memory/")
    item = sub("consolidate", cmd_consolidate, "list pending weeks, print a week's checklist, or close it")
    item.add_argument("--week")
    item.add_argument("--done", action="store_true")
    item.add_argument("--headline")
    item = sub("hook", cmd_hook, "internal: called by agent hooks; reads the event JSON from stdin")
    item.add_argument("--agent", required=True)
    item.add_argument("--event", required=True)
    item.add_argument("--context-chars", type=int, default=0)
    item.add_argument("--capture", choices=["full", "meta"], default="full")
    item = sub("install-hooks", cmd_install_hooks, "record every session automatically (Claude Code, Codex, Antigravity)")
    item.add_argument("--scope", choices=["global", "project"], default="global")
    item.add_argument("--agents", help="comma list: claude,codex,agy (default: those found on this machine)")
    item.add_argument("--context", choices=["lean", "off"], default="lean", help="inject a short context at session start")
    item.add_argument("--context-chars", type=int, default=2000)
    item.add_argument("--capture", choices=["full", "meta"], default="full", help="meta leaves out prompt and reply text")
    item.add_argument("--remove", action="store_true")
    item.add_argument("--dry-run", action="store_true")
    item = sub("related", cmd_related, "find notes connected to a file by links, project, tags and rare shared words")
    item.add_argument("target", help="path relative to memory/, or a file name")
    item.add_argument("--limit", type=int, default=8)
    item = sub("alias", cmd_alias, "teach search that several names mean the same thing")
    item.add_argument("names", nargs="+")
    item = sub("import", cmd_import, "add past sessions from agents' own history; local scan, no model tokens; safe to re-run")
    item.add_argument("--agents", help="comma list: claude,codex,agy (default: all)")
    item.add_argument("--since", help="YYYY-MM-DD")
    item.add_argument("--capture", choices=["full", "meta"], default="full")
    item.add_argument("--dry-run", action="store_true")
    item = sub("report", cmd_report, "show one day by hour and agent")
    item.add_argument("--day", help="YYYY-MM-DD (default: today)")
    item.add_argument("--agent")
    item.add_argument("--width", type=int, default=160)
    item = sub("index", cmd_index, "regenerate the generated block of INDEX.md")
    item = sub("lint", cmd_lint, "check for secrets, stale notes, broken links and pending weeks")
    item.add_argument("--stale-days", type=int, default=STALE_DAYS)
    return parser


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
