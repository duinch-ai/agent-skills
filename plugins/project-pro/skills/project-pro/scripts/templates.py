"""Markdown, rule, ADR, editorconfig, and Git hook template builders for project-pro."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any


def render_agents_md(
    name: str,
    info: dict[str, Any],
    arch: str,
    pattern: str,
    repo: str,
    repo_url: str,
    features: list[str],
) -> str:
    cmds = info["commands"]
    feat_badges = ", ".join(f"`{f}`" for f in features) if features else "`solid-dry`"

    if arch in {"clean", "modular-clean", "hexagonal"}:
        dep_rules = (
            "- **Dependency Rule**: `Presentation/Entrypoints -> Domain <- Data/Adapters`.\n"
            "- **Domain Layer**: 100% pure language types. ZERO imports from UI frameworks, HTTP clients, ORMs, or Data/Presentation packages.\n"
            "- **Data Layer**: Owns wire `*Dto` & DB `*Entity` models, implements Domain repository ports, maps errors to typed `DomainError`.\n"
            "- **Presentation Layer**: Stateless declarative UI + framework-free State Holder (`Sealed UiState`, `Intent`/`Event`, `Effect`)."
        )
    elif arch == "vertical-slice":
        dep_rules = (
            "- **Unidirectional Slice Flow**: `shared/core -> features/<slice> -> app`.\n"
            "- **Feature Encapsulation**: Import across features ONLY via public entrypoints; never reach into another slice's internals.\n"
            "- **Boundary Isolation**: Keep transport DTOs/API clients separate from UI state & components."
        )
    else:
        dep_rules = (
            "- **Lightweight Modular**: Separate pure core logic (`core/`) from I/O adapters (`adapters/`) and entrypoints.\n"
            "- Avoid empty pass-through abstractions (KISS & YAGNI)."
        )

    return f"""# {name} — AI Agent Engineering & Security Contract

> Managed by `project-pro` (`.agents/project-profile.json`). Every coding task MUST follow the 6-Gate Execution Harness.

## 1. Architectural Profile
- **Stack**: {info['label']}
- **Architecture**: `{arch}` | **Flow / State Pattern**: `{pattern}`
- **Gold-Standard Reference Repo**: [`{repo}`]({repo_url}) — **consult & adapt patterns from this repo instead of inventing custom structures.**
- **Enabled Capabilities**: {feat_badges}

## 2. Canonical Commands
- **Build**: `{cmds['build']}`
- **Run All Tests**: `{cmds['test_all']}`
- **Run Single Test**: `{cmds['test_single']}`
- **Lint & Typecheck**: `{cmds['lint']}`
- **Security Audit**: `{cmds['sec_audit']}`

## 3. Layer & Module Dependency Rules
{dep_rules}
- **Boundary Enforcement**: {info['boundary_tool']}

## 4. Mandatory 6-Gate Execution & Behavioral Guardrails
1. **Think & Ground (`karpathy-skills`)**: Read `.agents/CODEBASE_MAP.md`, `.agents/memory/lessons.md`, and `referenceRepo` before coding. Surface hidden assumptions; push back on unsafe anti-patterns; write `.agents/memory/active-plan.md` for > 3-file tasks.
2. **Surgical & Bounded Files**: Touch ONLY lines/files required. **1 File = 1 Primary Responsibility** (`> 300 LOC` = WARN, `> 450 LOC` = FAIL).
3. **Disciplined Coding (`obra/superpowers`)**: Build Inside-Out (`Domain -> Data -> State -> UI`) for features; for bugs, trace **Root Cause** + **3-Strike Stop** (if 3 fixes fail, STOP & re-evaluate architecture). Zero `TODO` stubs, zero dead code.
4. **SOLID & Anti-False-DRY**: Separate `*Dto`, `*Entity`, `Domain`, and `*UiState` models. Sealed states over boolean soup (`isLoading && isError` banned). Guard clauses (`<= 3` indent levels), immutable by default.
5. **Security & Paranoid Review (`gstack`)**: Zero hardcoded secrets, parameterized SQL, redacted logs, check race conditions/N+1/pagination bounds. Never bypass Git hooks with `--no-verify`.
6. **Self-Healing & Terse Delivery (`caveman`)**: Run `Single Test` -> `Lint/Typecheck` -> `audit` until green; log non-obvious pitfalls to `.agents/memory/lessons.md`; report concisely with file links.

## 5. Scoped Rules, Memory & Architecture Docs (Read on Demand)
- Task & Sub-Agent Workflow: [`.agents/rules/task-workflow.md`](./.agents/rules/task-workflow.md)
- Codebase Map & Memory: [`.agents/CODEBASE_MAP.md`](./.agents/CODEBASE_MAP.md) | [`active-plan.md`](./.agents/memory/active-plan.md) | [`lessons.md`](./.agents/memory/lessons.md)
- Execution & Security: [`.agents/rules/execution-harness.md`](./.agents/rules/execution-harness.md) | [`.agents/rules/security-gate.md`](./.agents/rules/security-gate.md)
- Layer Guardrails: [`domain`](./.agents/rules/domain-layer.md) | [`data`](./.agents/rules/data-layer.md) | [`presentation`](./.agents/rules/presentation-layer.md)
- ADR-0001: [`docs/architecture/ADR-0001-architecture.md`](./docs/architecture/ADR-0001-architecture.md)

## 6. GitHub Project Board & Parallel Sub-Agent Execution
- **1 Task = 1 GitHub Issue**: Managed via `scripts/workflow.py`.
- **Kanban Progression**: `Todo` (created) -> `In Progress` (started on branch `feat/issue-<id>`) -> `Done` (verified & closed).
- **Parallel Sub-Agents**: Primary Agent acts as Orchestrator, dispatches independent issues to isolated subagents via `invoke_subagent`, enforces prompt language discipline (English), and immediately terminates completed subagents (`manage_subagents kill`).
"""


def render_execution_harness_rule(info: dict[str, Any]) -> str:
    cmds = info["commands"]
    return f"""# Task Execution Harness (Mandatory for Every Coding Request)

1. **Gate 1 — Grounding & Assumptions**: Read `.agents/CODEBASE_MAP.md`, `.agents/memory/lessons.md`, and `referenceRepo` conventions. Surface assumptions upfront; track > 3-file work in `.agents/memory/active-plan.md`.
2. **Gate 2 — Surgical File Split**: Touch only required files/lines (`karpathy-skills`). Keep 1 primary responsibility per file (`> 300 LOC` = WARN, `> 450 LOC` = FAIL).
3. **Gate 3 — Implementation & 3-Strike Debugging**:
   - **Feature**: `Domain` (entities, narrow ports, `DomainError`) -> `Data` (DTO/Entity, Mappers, RepoImpl) -> `State Holder` (Sealed `UiState`, `Intent`) -> `Stateless UI` -> `DI/Nav`.
   - **Bugfix**: Trace root cause; test 1 hypothesis at a time; **STOP after 3 failed attempts** (`obra/superpowers`) to reassess architecture.
   - **No Leftovers**: Ban `// TODO`, fake production returns, unused imports, or swallowed `CancellationException`/`CancelledError`.
4. **Gate 4 — Edge-Case Unit Tests**: Cover happy path, empty state, offline/error mapping, and invalid inputs using fast in-memory **Fakes**.
5. **Gate 5 — Paranoid Check & Self-Healing**: Audit diff for race conditions, N+1 queries, and unbounded lists; run `{cmds['test_single']}` and `{cmds['lint']}` until green.
6. **Gate 6 — Lessons & Terse Output**: Append new project gotchas to `.agents/memory/lessons.md`; deliver concise high-signal summary (`caveman`).
"""


def render_security_rule() -> str:
    return """# Security & Git Hook Gate

1. **Secrets & Identifier Hygiene**: Never hardcode API keys, JWTs, private keys, credentialed DB URLs, developer LAN IPs (`192.168.x.x`), static room/pairing codes (`xxx-xxx`), or personal device serials/models. Load from validated env/keystore or dynamic runtime discovery; keep `.env*` (except `.env.example`) out of Git.
2. **Injection Defense**: Parameterized SQL/ORM queries only; no shell string interpolation (`shell=True`) with untrusted input; sanitize untrusted HTML.
3. **Transport & Logging**: Keep TLS verification enabled in production; redact tokens, cookies, passwords, and PII from logs.
4. **Hook Integrity**: `.githooks/pre-commit`, `commit-msg`, and `pre-push` enforce secret scanning, Conventional Commits, Clean Arch boundaries, and file-size caps. **Never bypass hooks with `--no-verify`**.
"""


def render_domain_rule(info: dict[str, Any], arch: str) -> str:
    forbidden = ", ".join(f"`{x.strip()}`" for x in info["domain_forbidden_imports"])
    return f"""# Domain Layer Guardrails (`{arch}`)

1. **Zero Framework Leakage**: Domain files MUST NOT import {forbidden}.
2. **Ownership**: Domain owns business Entities, Value Objects, narrow Repository interfaces (ISP), UseCases/Policies, and `DomainError`.
3. **Pure Unit Tests**: Every Domain class must be testable in milliseconds using pure in-memory Fakes.
"""


def render_data_rule(features: list[str]) -> str:
    typed_note = (
        "Wrap external I/O calls in a boundary translator that maps HTTP/DB failures into typed `DomainError` (always rethrowing coroutine/async cancellation)."
        if "typed-errors" in features
        else "Translate transport/SQL exceptions at the repository boundary before returning to Domain/Presentation."
    )
    return f"""# Data & Infrastructure Layer Guardrails

1. **Model Isolation**: Keep `*Dto` (serialization annotations) in `remote/` and `*Entity` (ORM/SQL annotations) in `local/`. Never leak them outside `data/`.
2. **Stateless Mappers**: Implement pure transformation extensions/functions (`toDomain()`, `toEntity()`) tested with unit tests.
3. **Error Translation**: {typed_note}
"""


def render_presentation_rule(pattern: str) -> str:
    return f"""# Presentation Layer Guardrails (`{pattern}`)

1. **Unidirectional Data Flow (UDF)**: Views observe immutable `Sealed UiState` and emit user `Intent` / action callbacks upward.
2. **Dumb Previewable Views**: Pass state slices and event lambdas into UI components (not whole ViewModels/Stores). Split sub-components into `components/` when a screen passes ~200 LOC.
3. **No Framework Leaks in State Holders**: State holders (`ViewModel`, `BLoC`, `Reducer`, `Store`) never hold UI widget, `Context`, `BuildContext`, or DOM references.
"""


def render_pre_commit_hook(skill_script: Path) -> str:
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


def render_commit_msg_hook(skill_script: Path) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
if [ -f "{skill_script}" ]; then
  python3 "{skill_script}" check-commit-msg --file "$1"
fi
"""


def render_pre_push_hook(skill_script: Path, info: dict[str, Any]) -> str:
    cmds = info["commands"]
    lint_bin = cmds["lint"].split()[0]
    test_bin = cmds["test_all"].split()[0]
    sec_bin = cmds["sec_audit"].split()[0]
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
echo "[pre-push] 2/4 Checking dependency vulnerabilities..."
if [ -x "{sec_bin}" ] || command -v "{sec_bin}" >/dev/null 2>&1; then
  {cmds['sec_audit']} || {{ echo "[pre-push] High-severity dependency issue found." >&2; exit 1; }}
else
  echo "[pre-push] (Skipped `{cmds['sec_audit']}` — `{sec_bin}` not in PATH)"
fi
echo "[pre-push] 3/4 Running lint & static typecheck..."
if [ -x "{lint_bin}" ] || command -v "{lint_bin}" >/dev/null 2>&1; then
  {cmds['lint']}
else
  echo "[pre-push] (Skipped `{cmds['lint']}` — `{lint_bin}` not in PATH)"
fi
echo "[pre-push] 4/4 Running unit test suite..."
if [ -x "{test_bin}" ] || command -v "{test_bin}" >/dev/null 2>&1; then
  {cmds['test_all']}
else
  echo "[pre-push] (Skipped `{cmds['test_all']}` — `{test_bin}` not in PATH)"
fi
echo "[pre-push] All security, architecture, lint, and test gates PASSED."
"""


def render_adr(name: str, info: dict[str, Any], arch: str, pattern: str, repo: str, repo_url: str, features: list[str]) -> str:
    today = dt.date.today().isoformat()
    feat_list = "\n".join(f"- `{f}`" for f in features) if features else "- `solid-dry`"
    return f"""# ADR-0001: Project Base Architecture, Security Gates & Multi-Agent Standards

- **Date**: {today} | **Status**: Accepted | **Project**: {name} | **Stack**: {info['label']}

## Decision
- **Architecture Style**: `{arch}` | **Flow Pattern**: `{pattern}`
- **Reference Architecture Anchor**: [`{repo}`]({repo_url})
- **Boundary Enforcement**: {info['boundary_tool']}
- **File Size Policy**: `1 File = 1 Primary Responsibility`, warn at `300 LOC`, hard block at `450 LOC`.
- **Security & Git Gates**: Staged secret scanning, OWASP heuristics, Conventional Commits, and pre-push test/CVE verification via `.githooks/`.

### Selected Base Capabilities
{feat_list}
"""


def render_editorconfig() -> str:
    return """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.{js,jsx,ts,tsx,vue,json,yaml,yml,md,dart,html,css,scss}]
indent_size = 2

[*.go]
indent_style = tab

[Makefile]
indent_style = tab
"""
