"""Architecture, feature and agent choices plus `init --preset` definitions."""

from __future__ import annotations

ARCH_CHOICES: list[tuple[str, str]] = [
    ("clean", "Clean Architecture (3-Layer: Presentation -> Domain <- Data)"),
    ("modular-clean", "Modular Clean Architecture (Multi-module :feature:* + :core:*)"),
    ("vertical-slice", "Vertical Slice / Feature-First (Pragmatic feature slices, minimal ceremony)"),
    ("hexagonal", "Hexagonal / Ports & Adapters + DDD"),
    ("lightweight", "Lightweight Modular (KISS/YAGNI for CLI, scripts & small utilities)"),
]

FEATURE_CHOICES: list[tuple[str, str, bool]] = [
    ("solid-dry", "Core SOLID + Pragmatic DRY (AHA) + Layer Model Isolation + Anti-God-File (300/450 LOC)", True),
    ("typed-errors", "Typed Error Handling & Result Wrapper (Result<T, DomainError> / RFC 9457)", True),
    ("i18n", "Internationalization (i18n/l10n) Architecture Preset & Centralized Resource Catalog", False),
    ("di-core", "Dependency Injection + Validated Env Config + Secret-Redacted Logging Base", True),
    ("network-storage", "Network Client (Auth/Retry Interceptors) + Local DB/Storage Repository Base", True),
    ("ui-nav", "Design System Tokens + Type-Safe Navigation (Client) / OpenAPI + Healthchecks (Backend)", True),
    ("arch-lint", "Strict Compiler Flags + Linter/Formatter + Architecture Boundary Tests", True),
    ("task-tracking", "Task Tracking: task board (provider: github or local; gitlab coming; docs/tasks + docs/BACKLOG.md, synced by the task-board skill)", False),
    ("data-integrity", "Data Integrity rule in AGENTS.md: never invent numbers/limits/versions/model ids; fixtures recorded from real runs; reports state what was actually run", False),
    ("testing-ci", "Testing Harness (Fakes over Mocks + State/Service tests) + GitHub Actions CI (Rust: Linux/macOS/Windows matrix)", False),
]

AGENT_CHOICES: list[tuple[str, str, bool]] = [
    ("agents-root", "Universal Root & Coding Standards (AGENTS.md + execution-harness.md checklist + security-gate.md + layer rules)", True),
    ("persistent-memory", "Cross-Session Memory & Codebase Map (.agents/CODEBASE_MAP.md + memory/lessons.md)", True),
    ("claude-gemini", "Claude Code & Antigravity/Gemini Bridges (CLAUDE.md + GEMINI.md)", True),
    ("git-security-hooks", "Git Security & Quality Hooks (pre-commit, commit-msg, pre-push + .gitignore secret guard)", True),
    ("agent-runtime-hooks", "AI Agent Anti-Bypass Runtime Hooks (.agents/hooks.json + .claude/settings.json)", True),
    ("adr-docs", "Architecture Decision Record (docs/architecture/ADR-0001-architecture.md)", True),
    ("cursor-ide", "Cursor / Windsurf / Cline / Roo / DeepSeek Rules (.cursor/rules/*.mdc + .clinerules)", False),
]

# `init --preset`. "recommended" mirrors the CLI defaults (rust additionally gets testing-ci, see presets.py).
# "minimal" is the smallest set that lets `project_pro.py audit` run clean of errors: audit needs only
# AGENTS.md + .agents/project-profile.json (both written by agents-root); hooks are warnings, not errors.
PRESET_RECOMMENDED_FEATURES: list[str] = ["solid-dry", "typed-errors", "di-core", "network-storage", "ui-nav", "arch-lint"]
PRESET_RECOMMENDED_AGENTS: list[str] = [
    "agents-root", "persistent-memory", "claude-gemini", "git-security-hooks", "agent-runtime-hooks", "adr-docs",
]
PRESET_MINIMAL_FEATURES: list[str] = ["solid-dry"]
PRESET_MINIMAL_AGENTS: list[str] = ["agents-root"]
# "guided" = recommended + `testing-ci` (the safety net a non-technical owner relies on: scripts/check.sh) +
# `data-integrity` (agents must not invent numbers/versions). Agents are exactly the recommended set
# (git hooks, runtime hooks, ADR, memory, bridges). Same codebase structure as expert; only the net is thicker.
PRESET_GUIDED_FEATURES: list[str] = PRESET_RECOMMENDED_FEATURES + ["testing-ci", "data-integrity"]
PRESET_GUIDED_AGENTS: list[str] = list(PRESET_RECOMMENDED_AGENTS)
PRESET_CHOICES: tuple[str, ...] = ("minimal", "recommended", "all", "guided")
