# Multi-Agent Project Harness & Tickable Base Modules Specification

A modern codebase is maintained by both human engineers and AI coding agents (**Antigravity, Claude Code, OpenAI Codex, Gemini CLI, Cursor, Windsurf, Cline, Roo Code, DeepSeek, Aider**). Without an explicit architectural harness inside the repository, every AI session guesses conventions, leaks dependencies across layers, and drifts from the original architecture.

---

## 1. Canonical Multi-Agent File Layout

When `project-pro` initializes a repository, it creates a **Single-Source-of-Truth Agent Harness** with zero duplicated prose:

```text
<project-root>/
├── AGENTS.md                              # Canonical root map (< 180 lines) — read natively by Codex, Antigravity, Cursor, Cline, Aider
├── CLAUDE.md                              # Thin bridge importing @AGENTS.md for Claude Code
├── GEMINI.md                              # Thin bridge importing @[AGENTS.md](./AGENTS.md) for Antigravity / Gemini CLI
├── .editorconfig                          # Deterministic whitespace, UTF-8, newline & indent rules
├── .gitignore                             # Blocks .env*, *.pem, *.key, *.keystore, *.jks, *.p12 secrets
├── .githooks/                             # Auto-activated via `git config core.hooksPath .githooks`
│   ├── pre-commit                         # Fast staged check: Secrets, .env, Domain leaks, >450 LOC God-files
│   ├── commit-msg                         # Enforces Conventional Commits + blocks secrets in commit msg
│   └── pre-push                           # Full audit + CVE dependency check + lint/typecheck + unit tests
├── .agents/
│   ├── project-profile.json               # Machine-readable record of ticked options (stack, arch, pattern, refRepo, features)
│   ├── hooks.json                         # Antigravity runtime PreToolUse hook blocking `--no-verify` & force-push main
│   └── rules/                             # Scoped progressive-disclosure guardrails
│       ├── execution-harness.md           # Mandatory 6-Gate loop for ANY coding request (Feature/Bugfix/Refactor)
│       ├── security-gate.md               # Shift-left OWASP, secret hygiene & safe transport rules
│       ├── domain-layer.md                # Pure domain invariants & zero-framework rule
│       ├── data-layer.md                  # DTO/Entity isolation, mappers & error translation
│       └── presentation-layer.md          # UDF/MVI/MVVM state rules, dumb views, lifecycle safety
├── .claude/
│   └── settings.json                      # Claude Code PreToolUse Bash guard blocking `--no-verify` & force-push main
├── .cursor/
│   └── rules/
│       └── 00-project-architecture.mdc    # Optional: Cursor MDC rule referencing AGENTS.md
├── .clinerules                            # Optional: Cline / Roo Code / DeepSeek rule pointer
└── docs/
    └── architecture/
        └── ADR-0001-architecture.md       # Deep Architecture Decision Record, module graph & migration guide
```

### Why `< 180 Lines` for Root `AGENTS.md`?
LLM instruction-following degrades sharply when root context files exceed ~200–300 lines of prose. Keep `AGENTS.md` ultra-dense and verifiable:
1. **Project Profile Summary** (Stack, Architecture Style, Presentation Pattern, Anchored Reference Repo).
2. **Module / Layer Dependency Matrix** (Exact allowed vs forbidden imports).
3. **Canonical Commands** (Build, Typecheck, Lint/Format, Single-Test command — agents iterate 5x faster when given a single-test command!).
4. **Non-Negotiable Coding Contracts** (Model separation, Error `Result` type, UDF state rules, SOLID/DRY thresholds).
5. **Pointers** to `.agents/rules/*.md` and `docs/architecture/ADR-0001-architecture.md` for deeper layer rules.

---

## 2. Specification for Each Tickable Base Module (Q3 Options)

When the user ticks base options during `project-pro` setup, implement the selected capabilities cleanly according to the stack's gold-standard reference repository:

### `[x] solid-dry` — Core SOLID + Pragmatic DRY + Layer Model Isolation
- Enforce distinct `*Dto` (wire), `*Entity` (DB), Domain model, and `*UiState` types with pure mapper extensions.
- Add shared marker interfaces or value-object primitives only if idiomatic to the stack.

### `[x] typed-errors` — Typed Error Handling & Result Wrapper
- Create a small, idiomatic result & failure hierarchy in `core/common` or `core/domain`:
  - **Kotlin / KMP**: `sealed interface AppResult<out D, out E : DomainError>` (or `Either`) + `DataError.Network`, `DataError.Local`, `DomainError.Validation` — always rethrowing `CancellationException` in `safeCall {}` helpers!
  - **Dart / Flutter**: `sealed class Result<T>` (`Ok<T>` / `Err<T>`) + sealed `AppFailure`.
  - **Swift**: Typed throws (`throws(DomainError)`) in Swift 6 or `Result<Value, DomainError>`.
  - **TypeScript / Web / NestJS**: Discriminated union `Result<T, E = AppError>` (`{ ok: true; value: T } | { ok: false; error: E }`) + centralized API problem-details parser (`RFC 9457`).
  - **Python / Go**: Explicit domain exceptions caught by a single FastAPI exception handler (`RFC 9457 ProblemDetails`), or Go sentinel/typed domain errors wrapped with `fmt.Errorf("%w")` and translated at HTTP/gRPC transport edge.

### `[x] di-core` — Dependency Injection + Env Config + Structured Logging
- **Config**: Fail-fast startup validation of environment variables / build configs (`pydantic-settings` in Python, `zod` env schema in TS, `BuildConfig` / `XCConfig` in mobile, `envconfig` in Go) — zero raw `os.getenv()` / `process.env` scattered in business code!
- **DI**: Constructor injection wired at the Composition Root (`Hilt` / `Koin` / `metro` for Kotlin/KMP, `Riverpod` / `get_it+injectable` for Flutter, `swift-dependencies` / Factory container for iOS, FastAPI `Depends` / explicit container for Python, explicit `wire` or `cmd/app` struct wiring for Go, NestJS modules).
- **Logging**: Structured logger interface (`Timber` / `Kermit` / `structlog` / `slog` / `pino`) with automatic secret/token redaction.

### `[x] network-storage` — Network Client + Local Storage/DB Base
- Centralized HTTP client factory with timeout defaults, request-ID correlation header, auth token interceptor/authenticator, and retry with exponential backoff on transient `5xx`/network errors.
- Local persistence foundation (e.g., `Room` / `SQLDelight` / `DataStore`, `Drift` / `SharedPreferences`, `SwiftData` / `GRDB`, `SQLAlchemy 2.0 async` / `Alembic`, `pgx` + `sqlc`/migrations, `Prisma`/`Drizzle`) hidden strictly behind DataSource/Repository interfaces.

### `[x] ui-nav` (Client Apps) OR `api-ops` (Backend Services)
- **Client Apps (`ui-nav`)**:
  - `core/designsystem`: Semantic color tokens (Light/Dark), typography scale, spacing tokens, and stateless base components (never hardcode hex colors inside feature screens!).
  - Type-safe Navigation (`Navigation Compose` / `Navigation 3` typed routes, `Circuit`, `Decompose`, `go_router`, `TCA NavigationStack`, `TanStack Router` / Next App Router).
- **Backend Services (`api-ops`)**:
  - Versioned API router (`/api/v1`), `/healthz` (liveness) & `/readyz` (readiness) endpoints, `RFC 9457` error middleware, request validation schemas, and OpenAPI generation.

### `[x] arch-lint` — Linter, Formatter & Architectural Boundary Enforcement
Deterministic tools catch architectural violations automatically before code review:
- **Android / KMP**: `ktlint` or `spotless` + `detekt` + **Konsist** (or Gradle module boundaries where `:core:domain` has zero Android/Retrofit/Room dependencies!).
- **Flutter**: `very_good_analysis` (or strict `flutter_lints`) in `analysis_options.yaml` (`strict-casts: true`, `strict-raw-types: true`).
- **iOS / Swift**: `SwiftLint` + `swift-format` + Swift Package Manager (`Package.swift`) target isolation (`Feature` cannot import `DataImpl`, only `Domain`).
- **Web / Node / NestJS**: `tsconfig.json` (`strict: true`, `noUncheckedIndexedAccess: true`) + `ESLint` (`eslint-plugin-boundaries` or `dependency-cruiser`) + `Prettier` / `Biome`.
- **Python**: `ruff` (lint + format, including `TID` banned imports) + `mypy --strict` (or `pyright`) + `import-linter` enforcing layer contracts.
- **Go**: `golangci-lint` (`depguard` blocking outer imports in `internal/domain`) + Go `internal/` compiler enforcement.

### `[x] testing-ci` — Testing Harness (Fakes over Mocks) + CI Pipeline
- Scaffold `core/testing` with reusable **In-Memory Fakes** (`FakeUserRepository`, test clock/dispatchers) rather than fragile mockito setups.
- Add 1 canonical example unit test demonstrating Domain + State Holder/Service testing (`Turbine`, `bloc_test`, `TestStore`, `Vitest`, `pytest`, `go test -race`).
- Add `.github/workflows/ci.yml` running format check → lint → typecheck → unit & architecture boundary tests on every PR.
