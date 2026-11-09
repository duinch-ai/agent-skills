"""PreToolUse runtime guard for Claude Code & Antigravity: blocks Git hook bypasses per shell command segment."""

from __future__ import annotations

import json
import re
import shlex
import sys

# Split on shell control operators so one rule never matches across `&&`, `||`, `;`, `|`, or newlines.
_SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")


def _tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def _git_subcommand(tokens: list[str]) -> tuple[str, list[str]] | None:
    """Return (subcommand, args) for a `git ...` segment, skipping global options such as `-C <dir>`."""
    if not tokens or tokens[0] != "git":
        return None
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        i += 2 if tokens[i] in {"-C", "-c", "--git-dir", "--work-tree"} else 1
    if i >= len(tokens):
        return None
    return tokens[i], tokens[i + 1:]


def _bypasses_verify(sub: str, args: list[str]) -> bool:
    if sub not in {"commit", "push", "merge"}:
        return False
    if "--no-verify" in args:
        return True
    # Only `git commit` treats `-n` as `--no-verify` (`push -n` = dry-run, `merge -n` = no-stat).
    if sub != "commit":
        return False
    short_flags = (a for a in args if re.fullmatch(r"-[a-zA-Z]+", a))
    return any("n" in flag for flag in short_flags)


def _force_pushes_protected(sub: str, args: list[str]) -> bool:
    if sub != "push":
        return False
    protected = {"main", "master", "refs/heads/main", "refs/heads/master"}
    flag_forced = any(a.startswith("--force") or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a) for a in args)
    refspecs = [a for a in args if not a.startswith("-")]
    for spec in refspecs:
        dest = spec.lstrip("+").split(":")[-1]
        # A leading `+` in a refspec forces that ref even without `--force`.
        if dest in protected and (flag_forced or spec.startswith("+")):
            return True
    return False


def _disables_hooks_path(sub: str, args: list[str]) -> bool:
    if sub != "config":
        return False
    lowered = [a.lower() for a in args]
    if "core.hookspath" not in lowered:
        return False
    if any(a in {"--unset", "--unset-all", "--remove-section"} for a in args):
        return True
    idx = lowered.index("core.hookspath")
    value = args[idx + 1] if idx + 1 < len(args) else None
    # Reading the value (`--get` or no value) is fine; setting it anywhere but `.githooks` is not.
    return value is not None and value.rstrip("/") not in {".githooks", "./.githooks"}


def _deletes_githooks(tokens: list[str]) -> bool:
    if not tokens or tokens[0] not in {"rm", "rmdir", "trash"}:
        return False
    targets = (t for t in tokens[1:] if not t.startswith("-"))
    return any(t.rstrip("/").split("/")[-1] == ".githooks" or "/.githooks/" in f"/{t}" for t in targets)


def check_command(cmd: str) -> str | None:
    """Return a block reason when any segment of `cmd` bypasses Git hooks, else None."""
    for segment in _SEGMENT_SPLIT.split(cmd):
        tokens = _tokens(segment.strip())
        if _deletes_githooks(tokens):
            return "Blocked by project-pro: Deleting `.githooks` is prohibited."
        git = _git_subcommand(tokens)
        if git is None:
            continue
        sub, args = git
        if _bypasses_verify(sub, args):
            return "Blocked by project-pro: Bypassing Git security/architecture hooks (`--no-verify`) is prohibited."
        if _force_pushes_protected(sub, args):
            return "Blocked by project-pro: Force-pushing to `main`/`master` is prohibited."
        if _disables_hooks_path(sub, args):
            return "Blocked by project-pro: Disabling `.githooks` via `core.hooksPath` is prohibited."
    return None


def run_agent_guard() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except Exception:
        return 0

    is_agy = "toolCall" in payload
    args = payload.get("toolCall", {}).get("args", {}) if is_agy else payload.get("tool_input", {})
    cmd = str((args or {}).get("CommandLine") or (args or {}).get("command") or "")
    reason = check_command(cmd)

    if is_agy:
        print(json.dumps({"decision": "deny", "reason": reason} if reason else {"decision": "allow"}))
        return 0
    if reason:
        sys.stderr.write(reason + "\n")
        return 2
    return 0
