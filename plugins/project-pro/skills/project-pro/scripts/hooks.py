"""Git hook script renderers (pre-commit, commit-msg, pre-push)."""

from __future__ import annotations

from typing import Any


def render_pre_commit_hook(skill_script: str) -> str:
    return f"""#!/usr/bin/env bash
# project-pro pre-commit gate: Staged Secret Scan + Clean Arch Boundary + Anti-God-File (<= 450 LOC)
set -euo pipefail
ROOT_DIR="$(git rev-parse --show-toplevel)"
if command -v gitleaks >/dev/null 2>&1; then
  echo "[pre-commit] Running gitleaks staged secret scan..."
  gitleaks protect --staged --redact --no-banner
fi
if [ -f "{skill_script}" ]; then
  echo "[pre-commit] Running project-pro staged architecture & security audit..."
  python3 "{skill_script}" audit --target "$ROOT_DIR" --staged --fail-on-error
fi
"""


def render_commit_msg_hook(skill_script: str) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
if [ -f "{skill_script}" ]; then
  python3 "{skill_script}" check-commit-msg --file "$1"
fi
"""


def _tool_binary(command: str) -> str:
    """Executable that must exist for `command` (cargo plugin subcommands map to `cargo-<sub>`)."""
    parts = command.split()
    binary = parts[0]
    if binary == "cargo" and len(parts) > 1 and parts[1] not in {"fmt", "clippy", "test", "build", "check"}:
        binary = f"cargo-{parts[1]}"
    return binary


def _tool_probe(binary: str) -> str:
    if "/" in binary:
        return f'[ -x "{binary}" ]'
    return f'command -v "{binary}" >/dev/null 2>&1'


def _gated_step(label: str, command: str, on_fail: str = "") -> str:
    """Run `command` when its tool exists, otherwise print a skip notice (single quotes: never command-substitute)."""
    tool = _tool_binary(command)
    run = f"{command} || {{ {on_fail} exit 1; }}" if on_fail else command
    return (
        f'echo "[pre-push] {label}"\n'
        f"if {_tool_probe(tool)}; then\n"
        f"  {run}\n"
        "else\n"
        f"  echo '[pre-push] (Skipped: {command.replace(chr(39), '')} — {tool} not installed)'\n"
        "fi\n"
    )


def render_pre_push_hook(skill_script: str, info: dict[str, Any]) -> str:
    cmds = info["commands"]
    sec_fail = 'echo "[pre-push] Dependency vulnerability check failed." >&2;'
    steps = (
        _gated_step("2/4 Checking dependency vulnerabilities...", cmds["sec_audit"], sec_fail)
        + _gated_step("3/4 Running lint & static typecheck...", cmds["lint"])
        + _gated_step("4/4 Running unit test suite...", cmds["test_all"])
    )
    return f"""#!/usr/bin/env bash
# project-pro pre-push gate: Full Audit + CVE Check + Lint + Unit Tests
set -euo pipefail
ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"
if [ -f "{skill_script}" ]; then
  echo "[pre-push] 1/4 Running full repository architecture, file-size & security audit..."
  python3 "{skill_script}" audit --target "$ROOT_DIR" --fail-on-error
fi
if command -v gitleaks >/dev/null 2>&1; then
  echo "[pre-push] Running gitleaks repository scan..."
  gitleaks detect --source "$ROOT_DIR" --redact --no-banner
fi
{steps}echo "[pre-push] All security, architecture, lint, and test gates PASSED."
"""
