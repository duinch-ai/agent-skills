"""Secret redaction and environment scrubbing: nothing sensitive reaches logs or prompts."""
import os
import re

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
