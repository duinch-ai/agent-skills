"""Secret redaction, environment scrubbing, and deterministic diff hygiene checks."""
import os
import re
import subprocess

_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b(\s*[:=]\s*)(['\"]?)[^\s'\"]{6,}\3"),
]
_SENSITIVE_ENV = re.compile(r"(?i)(key|token|secret|passw|credential)")


def redact(text):
    for pat in _PATTERNS[:-1]:
        text = pat.sub("[REDACTED]", text)
    return _PATTERNS[-1].sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)


def scrubbed_env():
    """Environment for check commands: drop variables that look like credentials."""
    return {k: v for k, v in os.environ.items() if not _SENSITIVE_ENV.search(k)}


def tail(text, limit):
    if len(text) <= limit:
        return text
    return "...[truncated]...\n" + text[-limit:]


_SKIP_ESCAPE_EXTS = (".md", ".txt", ".rst", ".json", ".lock", ".yaml", ".yml")
_TS_EXTS = (".ts", ".tsx", ".mts", ".cts")
_ESCAPE_RULES = (
    ("eslint-disable", re.compile(r"\beslint-disable(?:-next-line|-line)?\b"), None),
    ("ts-suppression", re.compile(r"@ts-(?:ignore|expect-error|nocheck)\b"), None),
    ("ts-any", re.compile(r"(?:\bas\s+any\b|:\s*any\b)"), _TS_EXTS),
    ("python-suppression", re.compile(r"#\s*(?:noqa\b|type:\s*ignore\b|pragma:\s*no\s*cover\b)"), (".py",)),
    ("rust-allow", re.compile(r"#\[allow\("), (".rs",)),
    ("go-nolint", re.compile(r"//\s*nolint\b"), (".go",)),
    ("bare-except-pass", re.compile(r"\bexcept\s*:\s*pass\b"), (".py",)),
    ("timing-workaround", re.compile(r"\b(?:setTimeout\s*\([^,]+,\s*0\s*\)|requestAnimationFrame\s*\()"), None),
    ("workaround-comment", re.compile(r"(?i)(?://|#)\s*(?:hack|workaround|temporary\s+fix|(?:todo|fixme)\s*:?\s*hack)\b"), None),
)


def scan_escape_hatches(diff_text):
    """Scan added lines in a unified diff for lint/type suppressions and workaround comments."""
    hits = []
    cur_file = ""
    for raw in (diff_text or "").splitlines():
        if raw.startswith("+++ b/"):
            cur_file = raw[6:].strip()
            continue
        if raw.startswith("+++ "):
            cur_file = ""
            continue
        if not raw.startswith("+") or raw.startswith("+++"):
            continue
        if not cur_file or cur_file.startswith(".agent-team/") or cur_file.endswith(_SKIP_ESCAPE_EXTS):
            continue
        added = raw[1:]
        for name, pat, exts in _ESCAPE_RULES:
            if exts is not None and not cur_file.endswith(exts):
                continue
            if pat.search(added):
                hits.append({"file": cur_file, "rule": name, "line": added.strip()[:160]})
    return hits


def git_diff_for_scan(cwd, base_branch="main"):
    """Return unified diff of branch/worktree changes vs base_branch (falling back to HEAD~1 or HEAD)."""
    for args in (
        ["git", "-C", str(cwd), "diff", f"{base_branch}...HEAD"],
        ["git", "-C", str(cwd), "diff", "HEAD~1..HEAD"],
        ["git", "-C", str(cwd), "diff", "HEAD"],
    ):
        try:
            out = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=15)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout
        except (OSError, subprocess.SubprocessError):
            continue
    return ""
