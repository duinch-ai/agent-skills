"""Scoped `.agents/rules/*.md` renderers: coding standards, security, layers, i18n and product category."""

from __future__ import annotations

from typing import Any


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
    return f"""# Coding Standards Checklist (apply to every code change)

How to work (grounding, debugging, review, delivery) is in `.agents/rules/agent-workflow.md` when present (agent-team skill).

1. **File Split**: Touch only required files/lines. Keep 1 primary responsibility per file (`> 300 LOC` = WARN, `> 450 LOC` = FAIL).
2. **Disciplined Coding**:
   - **Feature**: {feature_flow}
   - **Bugfix**: Fix the root cause and add a regression test. {bugfix_notes}
   - **No Leftovers**: {no_leftovers} {cancellation_note}
3. **Security**: Zero hardcoded secrets, parameterized queries, validated input at trust boundaries, redacted logs. {security}
4. **Tests**: {tests} Run `{cmds['test_single']}` and `{cmds['lint']}` until green; run the stack security audit and `project_pro.py audit` before delivery.
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


def render_i18n_rule(info: dict[str, Any], stack: str, locales: list[str]) -> str:
    i18n = info.get("i18n", {})
    standard = i18n.get("standard", "Standard Localization")
    tooling = i18n.get("tooling", "")
    guidance = i18n.get("guidance", "")
    loc_str = ", ".join(f"`{loc}`" for loc in locales)
    default_loc = locales[0] if locales else "vi"

    return f"""# Internationalization (i18n) & Localization Guardrails

- **Architecture Standard**: `{standard}`
- **Active Supported Locales**: {loc_str} (Default/Fallback: `{default_loc}`)
- **Tooling & Access Pattern**: `{tooling}`

## 1. Zero Hardcoded Strings Rule
Every user-facing label, button title, placeholder, dialog prompt, validation error, and notification string MUST be resolved through the centralized string catalog. Raw string literals (e.g. `"Đọc truyện"`, `"Submit"`, `"Cancel"`) in presentation views, screens, or view models are strictly prohibited.

## 2. Decoupled State & Context-Free ViewModels
- Never pass UI framework context (`android.content.Context`, `BuildContext`, or DOM window) into ViewModels, Presenters, or UseCases.
- For dynamic parameters (e.g. `"Trang %1$d / %2$d"`), return typed message identifiers, enums, or sealed wrapper models (`UiText.DynamicString` / `UiText.StringResourceId`) that the presentation layer resolves with its active locale.

## 3. Platform-Tailored Implementation
{guidance}

## 4. Adding New Strings & Locales
1. When creating a new UI string, add the key to the base catalog (`{default_loc}`) and all configured locales ({loc_str}).
2. Ensure fallback resolution is deterministic when a translation is pending.
3. Keep naming semantic: `<module>_<screen>_<element>` (e.g. `auth_login_title`, `downloads_hub_empty_label`).
"""


def render_category_rule(category: str, info: dict[str, Any]) -> str:
    from catalog import PRODUCT_CATEGORIES

    cat_info = PRODUCT_CATEGORIES.get(category, {})
    label = cat_info.get("label", category)
    desc = cat_info.get("description", "")
    guidance = cat_info.get("guidance", "")
    rec_stacks = ", ".join(f"`{s}`" for s in cat_info.get("recommended_stacks", []))
    rec_arch = cat_info.get("recommended_arch", "clean")

    return f"""# Product Category Architecture Guardrails: {label}

- **Category ID**: `{category}`
- **Scope & Purpose**: {desc}
- **Recommended Stacks**: {rec_stacks}
- **Baseline Architecture Style**: `{rec_arch}`

## 1. Core Engineering Contract
{guidance}

## 2. Operational & Lifecycle Checklist
- **Configuration & Secrets**: Load all runtime variables from validated environments; zero hardcoded credentials, static test tokens, or local LAN IPs.
- **Error Handling**: Follow strict domain error mapping (RFC 9457 for APIs, typed sealed errors for mobile/desktop, standard POSIX exit codes for CLI tools).
- **Resource Management**: Bounded cache sizes, graceful shutdown on termination signals, and automatic release of platform handles/descriptors.
- **Testing & Verification**: Pure unit tests using fast in-memory Fakes; integration tests against realistic platform runners.
"""
