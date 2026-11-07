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
    if info["label"].startswith("Rust "):
        dep_rules = (
            "- **Dependency Rule**: Keep domain crates/modules independent from UI, transport, database, and runtime frameworks.\n"
            "- **Rust Modeling**: Prefer ownership-based APIs, enums/newtypes, traits at real boundaries, and `Result<T, E>`; do not impose DTO/Entity or sealed UI-state patterns by default.\n"
            "- **Platform Contract**: Build/test Linux, macOS, and Windows in CI; add Android, iOS, WebAssembly, or embedded targets only when declared and provisioned with their SDK/linker."
        )
        solid_rules = "Use ownership, borrowing, enums, and traits to model invariants; introduce wire/database models only at real boundaries. Keep state types as simple as the UI requires."
        implementation_style = "Build from domain types and behavior outward; use Rust-native adapters and UI state only where the project needs them."
    else:
        solid_rules = "Separate `*Dto`, `*Entity`, `Domain`, and `*UiState` models. Sealed states over boolean soup (`isLoading && isError` banned)."
        implementation_style = "Build Inside-Out (`Domain -> Data -> State -> UI`) using the layer-specific models and state holder."

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
3. **Disciplined Coding (`obra/superpowers`)**: {implementation_style} For bugs, trace **Root Cause** + **3-Strike Stop** (if 3 fixes fail, STOP & re-evaluate architecture). Zero unfinished stubs, zero dead code.
4. **SOLID & Anti-False-DRY**: {solid_rules} Guard clauses (`<= 3` indent levels), immutable by default.
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
    if info["label"].startswith("Rust "):
        feature_flow = (
            "Model domain behavior with owned/borrowed values, enums/newtypes, and narrow traits where a real boundary needs one; implement adapters at I/O edges and use `Result<T, E>` for recoverable errors. Add UI state/message types only when the chosen UI architecture needs them."
        )
        bugfix_notes = "Do not replace errors with `unwrap()`/`expect()` on runtime paths; preserve ownership and cancellation semantics."
        no_leftovers = "Ban `todo!()`, `unimplemented!()`, avoidable panics, and unused imports."
        cancellation_note = "Do not swallow cancellation or turn it into a success-shaped fallback."
        tests = "Cover behavior with unit/integration tests; run native tests on Linux/macOS/Windows and compile each declared cross target with its required SDK/linker."
        security = "Review unsafe blocks and invariants, dependency changes, platform-specific input boundaries, and secrets/signing material."
    else:
        feature_flow = "`Domain` (entities, narrow ports, `DomainError`) -> `Data` (DTO/Entity, Mappers, RepoImpl) -> `State Holder` (Sealed `UiState`, `Intent`) -> `Stateless UI` -> `DI/Nav`."
        bugfix_notes = "Ban blind `try/catch`, arbitrary delays, and unsafe casts."
        no_leftovers = "Ban `// TODO`, fake production returns, unused imports, or swallowed `CancellationException`/`CancelledError`."
        cancellation_note = ""
        tests = "Cover happy path, empty state, offline/error mapping, and invalid inputs using fast in-memory Fakes."
        security = "Audit diff for race conditions, N+1 queries, and unbounded lists."
    return f"""# Task Execution Harness (Mandatory for Every Coding Request)

1. **Gate 1 — Grounding & Assumptions**: Read `.agents/CODEBASE_MAP.md`, `.agents/memory/lessons.md`, and `referenceRepo` conventions. Surface assumptions upfront; track > 3-file work in `.agents/memory/active-plan.md`.
2. **Gate 2 — Surgical File Split**: Touch only required files/lines (`karpathy-skills`). Keep 1 primary responsibility per file (`> 300 LOC` = WARN, `> 450 LOC` = FAIL).
3. **Gate 3 — Implementation & 3-Strike Debugging**:
   - **Feature**: {feature_flow}
   - **Bugfix**: Trace root cause; test 1 hypothesis at a time; **STOP after 3 failed attempts** (`obra/superpowers`) to reassess architecture. {bugfix_notes}
   - **No Leftovers**: {no_leftovers} {cancellation_note}
4. **Gate 4 — Edge-Case Unit Tests**: {tests}
5. **Gate 5 — Paranoid Check & Self-Healing**: {security} Run `{cmds['test_single']}` and `{cmds['lint']}` until green; run the stack security audit before delivery.
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
    if info["label"].startswith("Rust "):
        return f"""# Domain Layer Guardrails (`{arch}`)

1. **Zero Framework Leakage**: Domain modules must not depend on UI/runtime crates such as {forbidden}.
2. **Rust Types**: Prefer value types, enums, and explicit `Result<T, E>`; keep repository/port traits narrow and consumer-owned. Introduce separate wire/database models only where serialization or persistence boundaries require them.
3. **Ownership & Safety**: Keep ownership simple and avoid unnecessary shared mutability. Do not use `unsafe` in domain code; if unavoidable, isolate it and document its safety invariants.
4. **Pure Tests**: Keep domain tests independent from UI, network, database, and platform SDKs.
"""
    return f"""# Domain Layer Guardrails (`{arch}`)

1. **Zero Framework Leakage**: Domain files MUST NOT import {forbidden}.
2. **Ownership**: Domain owns business Entities, Value Objects, narrow Repository interfaces (ISP), UseCases/Policies, and `DomainError`.
3. **Pure Unit Tests**: Every Domain class must be testable in milliseconds using pure in-memory Fakes.
"""


def render_data_rule(features: list[str], info: dict[str, Any]) -> str:
    if info["label"].startswith("Rust "):
        return """# Data & Infrastructure Layer Guardrails

1. Keep network, persistence, platform SDK, and serialization dependencies in adapters or infrastructure modules.
2. Use DTO/entity types only when they represent a real wire/database boundary; map at that boundary and keep domain types independent.
3. Translate I/O failures into meaningful errors at adapter boundaries. Preserve error sources and propagate cancellation rather than swallowing it.
"""
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


def render_presentation_rule(pattern: str, info: dict[str, Any]) -> str:
    if info["label"].startswith("Rust "):
        return f"""# Presentation Layer Guardrails (`{pattern}`)

1. Keep UI frameworks and platform APIs outside domain modules.
2. Choose state/message/update patterns that fit the UI framework; use enums and exhaustive matching where they clarify valid states. Do not force a sealed UI-state abstraction onto simple applications.
3. Keep platform-specific code behind target configuration or adapter boundaries, and verify each declared target in CI.
"""
    return f"""# Presentation Layer Guardrails (`{pattern}`)

1. **Unidirectional Data Flow (UDF)**: Views observe immutable `Sealed UiState` and emit user `Intent` / action callbacks upward.
2. **Dumb Previewable Views**: Pass state slices and event lambdas into UI components (not whole ViewModels/Stores). Split sub-components into `components/` when a screen passes ~200 LOC.
3. **No Framework Leaks in State Holders**: State holders (`ViewModel`, `BLoC`, `Reducer`, `Store`) never hold UI widget, `Context`, `BuildContext`, or DOM references.
"""


def render_rust_ci_workflow() -> str:
    return """name: Rust CI

on:
  push:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: rust-ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  verify:
    name: Verify (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: actions-rust-lang/setup-rust-toolchain@v1
        with:
          toolchain: stable
          components: rustfmt, clippy
      - name: Check formatting
        run: cargo fmt --all -- --check
      - name: Build workspace
        run: cargo build --workspace
      - name: Run Clippy
        run: cargo clippy --workspace --all-targets -- -D warnings
      - name: Run tests
        run: cargo test --workspace

  dependency-audit:
    name: Audit dependencies
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions-rust-lang/setup-rust-toolchain@v1
        with:
          toolchain: stable
      - name: Install cargo-audit
        run: cargo install cargo-audit --locked
      - name: Audit dependencies
        run: cargo audit
"""


def render_cpp_switch_ci_workflow(project_name: str = "SwitchFS") -> str:
    return f"""name: Nintendo Switch Build CI

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]
  workflow_dispatch:

jobs:
  build-nx:
    name: Build Switch NRO
    runs-on: ubuntu-latest
    container:
      image: devkitpro/devkita64:latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      - name: Install Switch Dependencies
        run: |
          dkp-pacman --noconfirm -Syu
          dkp-pacman --noconfirm -S switch-curl switch-mbedtls switch-libarchive switch-pkg-config
          git config --system --add safe.directory $GITHUB_WORKSPACE
      - name: Build NRO
        run: |
          cmake -B build \\
            -DCMAKE_BUILD_TYPE=Release \\
            -DPLATFORM_SWITCH=ON \\
            -DVERSION_BUILD=${{{{ github.run_number }}}}
          make -C build {project_name}.nro -j$(nproc)
      - name: Upload NRO Artifact
        uses: actions/upload-artifact@v4
        with:
          name: {project_name}-Switch-${{{{ github.run_number }}}}
          path: build/{project_name}.nro
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
