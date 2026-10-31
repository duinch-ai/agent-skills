"""Architecture boundary, file-size, secret-leak, OWASP, commit-msg, and AI runtime guard auditor."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from catalog import IGNORE_DIRS, SOURCE_EXTENSIONS, STACK_CATALOG
from detector import detect_project

TEXT_SCAN_EXTENSIONS = SOURCE_EXTENSIONS | {".json", ".yaml", ".yml", ".toml", ".properties", ".xml", ".env", ".sh"}
GENERATED_FILE_PATTERNS = (
    ".g.dart", ".freezed.dart", ".gr.dart", ".config.dart", ".gen.ts",
    ".d.ts", "_pb2.py", "_pb2_grpc.py", ".pb.go", ".generated.",
)
GENERATED_DIR_NAMES = {"migrations", "versions", "generated", "__generated__"}
ALLOWED_ENV_TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.defaults", ".env.test.example"}
SENSITIVE_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".mobileprovision"}
SENSITIVE_EXACT_NAMES = {"id_rsa", "id_ed25519", "id_ecdsa", "credentials.json"}

SECRET_REGEXES: list[tuple[str, re.Pattern[str]]] = [
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY-----")),
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google / Firebase API Key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("GitHub Personal/App Token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{22,})\b")),
    ("Anthropic API Key", re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,}\b")),
    ("OpenAI API Key", re.compile(r"\bsk-(?:proj|svcacct)-[A-Za-z0-9\-_]{20,}\b")),
    ("Stripe Live Secret Key", re.compile(r"\b(?:sk|rk)_live_[0-9a-zA-Z]{20,}\b")),
    ("Slack Token", re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{10,}\b")),
    ("Hardcoded JWT Bearer Token", re.compile(r"\bBearer\s+eyJ[A-Za-z0-9_\-]{15,}\.eyJ[A-Za-z0-9_\-]{15,}\.")),
    (
        "Database URI with Embedded Password",
        re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^/\s:@\"']+:[^/\s@\"']{4,}@(?!(?:localhost|127\.0\.0\.1))"),
    ),
    (
        "Hardcoded Secret/API-Key/Password Literal",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|password|passwd)\b"
            r"\s*[:=]\s*[\"'](?![\"']|\$\{|process\.env|os\.environ|YOUR_|REPLACE_|CHANGE_ME|example|dummy|test|mock|<)[A-Za-z0-9/+_\-=!@#$%^&*]{12,}[\"']"
        ),
    ),
]

OWASP_REGEXES: list[tuple[str, str, re.Pattern[str]]] = [
    ("ERROR", "Potential SQL Injection (string interpolation/concatenation in SQL)", re.compile(r"(?i)(?:f[\"']\s*(?:SELECT|INSERT|UPDATE|DELETE)\b.*\{|[\"']\s*(?:SELECT|INSERT|UPDATE|DELETE)\b[^\"']*[\"']\s*\+|`\s*(?:SELECT|INSERT|UPDATE|DELETE)\b[^`]*\$\{)")),
    ("WARN", "Disabled TLS Certificate Verification", re.compile(r"(?:InsecureSkipVerify\s*:\s*true|verify\s*=\s*False|usesCleartextTraffic\s*=\s*\"true\")")),
    ("WARN", "Dangerous Dynamic Code Execution / Shell Interpolation", re.compile(r"(?:\bsubprocess\.(?:run|Popen|call)\([^)]*shell\s*=\s*True|\bdangerouslySetInnerHTML\b)")),
]

COMMIT_MSG_RE = re.compile(
    r"^(?:Merge\b|Revert\b|(?:feat|fix|refactor|perf|security|test|docs|build|ci|chore|style)(?:\([a-zA-Z0-9_./\-]+\))?!?: .{3,})"
)


def _is_generated_file(rel_file: Path) -> bool:
    lower = rel_file.name.lower()
    return any(lower.endswith(pat) or pat in lower for pat in GENERATED_FILE_PATTERNS) or any(
        p.lower() in GENERATED_DIR_NAMES for p in rel_file.parts
    )


def _is_sensitive_filename(rel_file: Path) -> bool:
    lower = rel_file.name.lower()
    if lower in ALLOWED_ENV_TEMPLATES:
        return False
    if lower == ".env" or (lower.startswith(".env.") and not lower.endswith((".example", ".sample", ".template"))):
        return True
    return (
        Path(lower).suffix in SENSITIVE_EXTENSIONS
        or lower in SENSITIVE_EXACT_NAMES
        or (lower.startswith("service-account") and lower.endswith(".json"))
    )


def _candidate_files(target: Path, staged_only: bool) -> list[Path]:
    if staged_only:
        try:
            res = subprocess.run(
                ["git", "-C", str(target), "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                check=True, capture_output=True, text=True,
            )
            return [target / ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
        except Exception:
            return []
    if (target / ".git").exists():
        try:
            res = subprocess.run(
                ["git", "-C", str(target), "ls-files", "--cached", "--others", "--exclude-standard"],
                check=True, capture_output=True, text=True,
            )
            return [
                target / ln.strip()
                for ln in res.stdout.splitlines()
                if ln.strip() and (target / ln.strip()).is_file()
                and not any(part in IGNORE_DIRS for part in Path(ln.strip()).parts)
            ]
        except Exception:
            pass
    collected: list[Path] = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        collected.extend(Path(root) / f for f in files)
    return collected


def _redact(text: str) -> str:
    s = text.strip()
    return (s[:20] + "...[REDACTED]..." + s[-8:]) if len(s) > 48 else (s[:8] + "...[REDACTED]")


def audit_project(target: Path, warn_lines: int = 300, max_lines: int = 450, staged_only: bool = False) -> dict[str, Any]:
    target = target.resolve()
    det = detect_project(target)
    stack = det["detected_stack"]
    stack_info = STACK_CATALOG.get(stack or "")
    errors: list[str] = []
    warnings: list[str] = []
    passes: list[str] = []

    if not staged_only:
        agents_md = target / "AGENTS.md"
        if agents_md.is_file():
            lc = len(agents_md.read_text(encoding="utf-8", errors="ignore").splitlines())
            if lc <= 200:
                passes.append(f"`AGENTS.md` present and concise ({lc} lines <= 200 budget).")
            else:
                warnings.append(f"`AGENTS.md` is {lc} lines (> 200 recommended). Move details into `.agents/rules/`.")
        else:
            warnings.append("Missing `AGENTS.md` at project root (run `project_pro.py init`).")

        if (target / ".agents" / "project-profile.json").is_file():
            passes.append("`.agents/project-profile.json` present.")
        else:
            warnings.append("Missing `.agents/project-profile.json` profile metadata.")

        if (target / ".githooks" / "pre-commit").is_file() and (target / ".githooks" / "pre-push").is_file():
            passes.append("Git security & quality hooks (`pre-commit`, `commit-msg`, `pre-push`) present.")
        else:
            warnings.append("Missing `.githooks/` (`pre-commit` / `pre-push`) security & quality gates.")

    forbidden_patterns: list[str] = list(stack_info["domain_forbidden_imports"]) if stack_info else []
    scanned_code = 0
    scanned_sec = 0

    for fpath in _candidate_files(target, staged_only):
        if not fpath.is_file():
            continue
        try:
            rel_file = fpath.relative_to(target)
        except ValueError:
            continue

        if _is_sensitive_filename(rel_file):
            errors.append(f"Security Leak Blocked: Sensitive file `{rel_file}` must NOT be committed.")
            continue

        suffix = fpath.suffix.lower()
        is_code = suffix in SOURCE_EXTENSIONS
        if not (suffix in TEXT_SCAN_EXTENSIONS or rel_file.name.startswith(".env")):
            continue

        lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
        scanned_sec += 1
        is_test_or_scanner = any(
            t in str(rel_file).lower() for t in ("test", "spec", "mock", "fake", "fixture", "auditor.py")
        )

        for idx, line in enumerate(lines, start=1):
            if line.startswith(("<<<<<<< ", ">>>>>>> ")):
                errors.append(f"Unresolved Git Merge Conflict Marker in `{rel_file}:{idx}`.")
                break
            if "project-pro-ignore" in line or "gitleaks:allow" in line or is_test_or_scanner:
                continue
            for sec_label, sec_re in SECRET_REGEXES:
                if sec_re.search(line):
                    errors.append(f"Hardcoded Secret Detected ({sec_label}) in `{rel_file}:{idx}` -> `{_redact(line)}`")
            if is_code:
                for sev, owasp_label, owasp_re in OWASP_REGEXES:
                    if owasp_re.search(line):
                        (errors if sev == "ERROR" else warnings).append(
                            f"Security Heuristic ({owasp_label}) in `{rel_file}:{idx}`"
                        )

        if is_code:
            scanned_code += 1
            if not _is_generated_file(rel_file):
                loc = len(lines)
                if loc > max_lines:
                    errors.append(
                        f"God-File Hard Limit Exceeded: `{rel_file}` has {loc} lines (> {max_lines} max). Split into smaller single-responsibility files!"
                    )
                elif loc > warn_lines:
                    warnings.append(f"Large File Warning: `{rel_file}` has {loc} lines (> {warn_lines} recommended).")

            parts_lower = [p.lower() for p in rel_file.parent.parts]
            if "domain" in parts_lower or any("coredomain" in p for p in parts_lower):
                for idx, line in enumerate(lines[:100], start=1):
                    s = line.strip()
                    for bad in forbidden_patterns:
                        if bad in s:
                            errors.append(f"Domain Boundary Leak in `{rel_file}:{idx}` -> forbidden dependency `{bad}`")
                    if re.search(r"\b(import|from)\b.*(\.presentation\.|\.data\.|/presentation/|/data/)", s):
                        if ".core.domain" not in s:
                            errors.append(f"Clean Arch Violation in `{rel_file}:{idx}` -> Domain imports outer layer (`{s}`)")

    if scanned_sec > 0 and not any("Secret" in e or "Sensitive file" in e for e in errors):
        passes.append(f"Zero hardcoded secrets or sensitive files across {scanned_sec} scanned files.")
    if scanned_code > 0 and not any("Domain" in e or "Clean Arch" in e for e in errors):
        passes.append(f"Zero Domain layer boundary leaks across {scanned_code} code files.")
    if scanned_code > 0 and not any("God-File" in e for e in errors):
        passes.append(f"All code files within hard size cap (<= {max_lines} LOC).")

    return {
        "target": str(target), "mode": "staged" if staged_only else "full", "stack": stack,
        "scanned_files": scanned_code, "scanned_security_files": scanned_sec,
        "passes": passes, "warnings": warnings, "errors": errors,
        "status": "FAIL" if errors else ("WARN" if warnings else "PASS"),
    }


def format_audit_markdown(report: dict[str, Any]) -> str:
    scope = "Staged Git Index" if report["mode"] == "staged" else "Full Repository"
    lines = [
        f"## Project Pro Architecture & Security Audit ({scope}) — `{report['status']}`",
        f"- **Target**: `{report['target']}`",
        f"- **Stack**: `{report['stack'] or 'unknown'}` | **Code Files**: `{report['scanned_files']}` | **Security-Scanned**: `{report['scanned_security_files']}`\n",
    ]
    if report["errors"]:
        lines.extend(["### Blocking Errors (`[FAIL]`)", *[f"- [FAIL] {e}" for e in report["errors"]], ""])
    if report["warnings"]:
        lines.extend(["### Warnings (`[WARN]`)", *[f"- [WARN] {w}" for w in report["warnings"]], ""])
    if report["passes"]:
        lines.extend(["### Passed Gates (`[OK]`)", *[f"- [OK] {p}" for p in report["passes"]]])
    return "\n".join(lines)


def check_commit_message(msg_file: Path) -> int:
    non_comment = [ln for ln in msg_file.read_text(encoding="utf-8", errors="ignore").splitlines() if not ln.startswith("#")]
    header = non_comment[0].strip() if non_comment else ""
    body = "\n".join(non_comment)
    if not COMMIT_MSG_RE.match(header):
        sys.stderr.write(
            "[commit-msg BLOCKED] Follow Conventional Commits: <type>(<scope>): <description>\n"
            f"  Got: {header!r}\n"
        )
        return 1
    for sec_label, sec_re in SECRET_REGEXES:
        if sec_re.search(body):
            sys.stderr.write(f"[commit-msg BLOCKED] Potential secret ({sec_label}) inside commit message!\n")
            return 1
    return 0


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

    reason: str | None = None
    if re.search(r"\bgit\s+(?:commit|push|merge)\b.*(?:\s--no-verify\b|\s-[a-zA-Z]*n\b)", cmd):
        reason = "Blocked by project-pro: Bypassing Git security/architecture hooks (`--no-verify`) is prohibited."
    elif re.search(r"\bgit\s+push\b.*(?:\s--force\b|\s-f\b).*\b(?:main|master)\b", cmd):
        reason = "Blocked by project-pro: Force-pushing to `main`/`master` is prohibited."
    elif re.search(r"\bgit\s+config\b.*\bcore\.hooksPath\b", cmd) and ".githooks" not in cmd:
        reason = "Blocked by project-pro: Disabling `.githooks` via `core.hooksPath` is prohibited."
    elif re.search(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+.*\.githooks\b", cmd):
        reason = "Blocked by project-pro: Deleting `.githooks` is prohibited."

    if is_agy:
        print(json.dumps({"decision": "deny", "reason": reason} if reason else {"decision": "allow"}))
        return 0
    if reason:
        sys.stderr.write(reason + "\n")
        return 2
    return 0
