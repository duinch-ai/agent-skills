"""Renderer for the root AGENTS.md (repo facts only: commands, layer rules, coding standards, security)."""

from __future__ import annotations

from typing import Any

import tasktracking


# Optional `data-integrity` capability; wording follows the hand-written rule in the agentry repo's AGENTS.md section 7.
DATA_INTEGRITY_SECTION = """
## 7. Data Integrity — Never Invent Values
- Every number, limit, price, quota, context length, version, flag or model id in code, fixtures, docs and reports must come from a verifiable source (CLI `--help`/output, official docs, API response). If it is unknown, leave the field empty/`nil`; never guess a default that looks real.
- Test fixtures for CLI/API parsers are **recorded from real runs** (note CLI name + version + date in the fixture header), not hand-written. Hand-made inputs are allowed only for malformed/edge cases and must be labelled as synthetic.
- Reports state what was actually run and its real output (test counts from the tool, not estimates). Anything not verified is labelled "not verified".
"""


def render_agents_md(
    name: str,
    info: dict[str, Any],
    arch: str,
    pattern: str,
    repo: str,
    repo_url: str,
    features: list[str],
    locales: list[str] | None = None,
    category: str | None = None,
    task_provider: str | None = None,
    workflow_rule_exists: bool = False,
    owner_guide: bool = False,
) -> str:
    cmds = info["commands"]
    feat_badges = ", ".join(f"`{f}`" for f in features) if features else "`solid-dry`"

    cat_line = ""
    cat_pointer = ""
    if category:
        from catalog import PRODUCT_CATEGORIES

        cat_title = PRODUCT_CATEGORIES.get(category, {}).get("label", category)
        cat_line = f"- **Product Category**: `{cat_title}` (`{category}`)\n"
        cat_pointer = " | [`category`](./.agents/rules/product-category.md)"

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

    i18n_rule_line = ""
    i18n_pointer = ""
    if "i18n" in features and locales:
        loc_str = ", ".join(locales)
        std_name = info.get("i18n", {}).get("standard", "Platform i18n")
        i18n_rule_line = f"\n- **Internationalization (i18n)**: Centralized catalog `{std_name}`. Zero raw hardcoded strings in UI. Supported locales: `{loc_str}`."
        i18n_pointer = " | [`i18n`](./.agents/rules/i18n-localization.md)"

    workflow_line = (
        "Agent working method: see [`.agents/rules/agent-workflow.md`](./.agents/rules/agent-workflow.md)"
        if workflow_rule_exists
        else "Agent working method: agent-team skill (optional)"
    )
    owner_line = "\n- Non-technical owner guide: START_HERE.md" if owner_guide else ""
    task_section = tasktracking.agents_md_section(task_provider) if "task-tracking" in features else ""

    data_section = DATA_INTEGRITY_SECTION if "data-integrity" in features else ""

    return f"""# {name} — AI Agent Engineering & Security Contract

> Managed by `project-pro` (`.agents/project-profile.json`). This file states what the repository must satisfy.

## 1. Architectural Profile
{cat_line}- **Stack**: {info['label']}
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
{dep_rules}{i18n_rule_line}
- **Boundary Enforcement**: {info['boundary_tool']}

## 4. Coding Standards Checklist
1. **File Split**: **1 File = 1 Primary Responsibility** (`> 300 LOC` = WARN, `> 450 LOC` = FAIL). Touch only the files the task needs.
2. **Disciplined Coding**: {implementation_style} Zero unfinished stubs, zero dead code.
3. **SOLID & Anti-False-DRY**: {solid_rules} Guard clauses (`<= 3` indent levels), immutable by default.
4. **Security**: Zero hardcoded secrets, parameterized SQL, validated untrusted input, redacted logs. Never bypass Git hooks with `--no-verify`.
5. **Tests**: Cover happy, empty, error/offline and boundary cases with fast fakes; run `Single Test` -> `Lint/Typecheck` -> `audit` until green.

## 5. Scoped Rules, Memory & Architecture Docs (Read on Demand)
- Codebase Map & Lessons: [`.agents/CODEBASE_MAP.md`](./.agents/CODEBASE_MAP.md) | [`lessons.md`](./.agents/memory/lessons.md)
- Coding Standards & Security: [`.agents/rules/execution-harness.md`](./.agents/rules/execution-harness.md) | [`.agents/rules/security-gate.md`](./.agents/rules/security-gate.md)
- Layer Guardrails: [`domain`](./.agents/rules/domain-layer.md) | [`data`](./.agents/rules/data-layer.md) | [`presentation`](./.agents/rules/presentation-layer.md){i18n_pointer}{cat_pointer}
- ADR-0001: [`docs/architecture/ADR-0001-architecture.md`](./docs/architecture/ADR-0001-architecture.md)
- {workflow_line}{owner_line}

{task_section}{data_section}"""
