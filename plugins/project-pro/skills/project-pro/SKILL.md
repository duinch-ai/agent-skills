---
name: project-pro
description: >-
  Interactive project base architect, 6-Gate task execution harness, Clean Architecture
  & UDF standardizer, Shift-Left DevSecOps security & Git/Agent hook guard, and
  reference-repo-first engineering guide across Android, KMP/CMP, Flutter, iOS/Swift,
  Rust, Web (React/Next.js/Vue/TS), and Backend (Python/FastAPI, Go, Node.js/NestJS).
  Activate whenever creating/scaffolding a project, standardizing an existing repo
  with tickable checkbox options, writing/fixing/refactoring ANY feature or bug,
  enforcing SOLID/DRY and file-length caps, or setting up pre-commit/pre-push security
  and multi-agent hooks.
---

# Project Pro — Interactive Architect, 6-Gate Execution Harness & DevSecOps Guard

Build, standardize, and ship production software using **interactive checkbox blueprints**, **famous open-source reference repositories**, **Clean Architecture + UDF**, **SOLID + pragmatic DRY**, **hard file-size caps**, and a **4-Shield Security & Hook Defense** (`pre-commit`, `commit-msg`, `pre-push`, plus runtime AI Agent anti-bypass hooks).

## Two Operating Modes

Check `<PROJECT_DIR>/.agents/project-profile.json` and `<PROJECT_DIR>/AGENTS.md` (via `project_pro.py detect`) first:

1. **Mode A — Interactive Project Setup / Standardization Wizard** *(New project, unconfigured repo, or user asks to configure/scaffold base options)*:
   - Run `detect` → present **tickable multi-select checkboxes** for Architecture, Flow Pattern + Famous Reference Repo, Base Modules, and AI Agent + Git/Security Hooks → scaffold and persist `.agents/project-profile.json`.
2. **Mode B — 6-Gate Execution Harness** *(Every arbitrary coding request — Feature, Bugfix, or Refactor — on a configured project)*:
   - Read the saved profile **without re-asking setup questions** → execute strictly through **Gates 1–6** below → run `audit --fail-on-error` + tests before finishing.

---

## CLI Toolkit (100% Python 3 Standard Library — Zero Dependencies)

Resolve `<SKILL_DIR>` to the directory containing this `SKILL.md`:

```bash
# 1. Detect project mode (greenfield / brownfield / configured), stack & hook status
python3 "<SKILL_DIR>/scripts/project_pro.py" detect --target "<PROJECT_DIR>"

# 2. Lookup famous reference repos, patterns & GitHub search queries for a stack
python3 "<SKILL_DIR>/scripts/project_pro.py" lookup --stack <android|kmp|flutter|ios|web|python|go|nestjs|rust|cpp-switch>

# 3. Initialize multi-agent harness, 6-Gate rules, Git security hooks & runtime agent guards
python3 "<SKILL_DIR>/scripts/project_pro.py" init \
  --target "<PROJECT_DIR>" \
  --stack <stack> \
  --arch <clean|modular-clean|vertical-slice|hexagonal|lightweight> \
  --pattern <mvi|mvvm-udf|tca|bloc|riverpod|fsd|query-zustand|service-repo|cqrs> \
  --features "solid-dry,typed-errors,i18n,di-core,network-storage,ui-nav,arch-lint,testing-ci" \
  --agents "agents-root,claude-gemini,git-security-hooks,agent-runtime-hooks,adr-docs,cursor-ide" \
  [--category <mobile-app|desktop-app|multiplatform-app|web-app|backend-api|service-worker|cli-tool|library-sdk|embedded-homebrew>] \
  [--i18n] [--locales "vi,en,ja"] \
  [--ref-repo "<owner/repo>"] [--scaffold-dirs] [--force]

# 4. Interactive terminal checkbox TUI (when run directly in a shell)
python3 "<SKILL_DIR>/scripts/project_pro.py" wizard --target "<PROJECT_DIR>"

# 5. Generate/refresh compact Codebase Architecture Map (.agents/CODEBASE_MAP.md) to save tokens
python3 "<SKILL_DIR>/scripts/project_pro.py" map --target "<PROJECT_DIR>" --write

# 6. Full or Staged Audit (Secrets, OWASP, Domain Leaks, 300/450 LOC cap, Harness)
python3 "<SKILL_DIR>/scripts/project_pro.py" audit --target "<PROJECT_DIR>" [--staged] --fail-on-error

# 7. Real-time Markdown Dashboard (`report` standard command)
python3 "<SKILL_DIR>/scripts/project_pro.py" report --target "<PROJECT_DIR>"
```

Load reference manuals progressively **only as needed**:
- **Product Category Taxonomy & Operational Blueprints** → [`references/product-categories.md`](./references/product-categories.md)
- **6-Gate Task Execution Runbook** (Feature / Bugfix / Refactor) → [`references/execution-harness.md`](./references/execution-harness.md)
- **Agentic Patterns (`karpathy-skills`, `superpowers`, `gstack`, `ECC`, `planning-with-files`, `caveman`)** → [`references/agentic-patterns.md`](./references/agentic-patterns.md)
- **Security Gateways, Git Hooks & Runtime Agent Hooks** → [`references/security-and-hooks.md`](./references/security-and-hooks.md)
- **Clean Arch, SOLID, Pragmatic DRY (AHA) & Anti-God-File Rules** → [`references/clean-arch-and-solid.md`](./references/clean-arch-and-solid.md)
- **MVI / MVVM / TCA / BLoC / Riverpod / FSD & UDF Contracts** → [`references/presentation-patterns.md`](./references/presentation-patterns.md)
- **Multi-Agent Harness & Tickable Base Module Specs** → [`references/agent-harness-spec.md`](./references/agent-harness-spec.md)
- **Mobile Famous Reference Repos (Android, KMP, Flutter, iOS)** → [`references/stacks-mobile.md`](./references/stacks-mobile.md)
- **Web & Backend Famous Reference Repos (Web, Python, Go, NestJS)** → [`references/stacks-web-backend.md`](./references/stacks-web-backend.md)
- **Rust Idioms, Platform Targets & CI/CD** → [`references/stacks-rust.md`](./references/stacks-rust.md)
- **C++ Modern Idioms & Nintendo Switch Homebrew** → [`references/stacks-cpp-switch.md`](./references/stacks-cpp-switch.md)

---

## Mode A: Interactive Checkbox Wizard (New or Existing Project)

Never guess architecture, product type, or base modules. Run `detect`, then present **tickable questions** via your platform's structured question tool (`ask_question` in Antigravity, `AskUserQuestion` in Claude Code, `request_user_input` in Codex, or numbered checkboxes in plain-text chat):

0. **Q0 — Product Category & Project Purpose / Thể loại sản phẩm & Mục đích dự án** *(single-select)*:
   - `(Recommended) [1] Mobile App (Android / iOS / Cross-Platform — Offline-first DB, lifecycle safety, touch UX)`
   - `[2] Desktop App (macOS / Windows / Linux — Window bounds, file dialogs, system tray, non-blocking threadpool)`
   - `[3] Multi-Platform Universal Client (Mobile + Desktop + Web — Expect/actual isolation, adaptive layout)`
   - `[4] Web Application (SPA / SSR / SaaS Portal / Dashboard — Server vs client state, Core Web Vitals, CSP)`
   - `[5] Backend Service / API (REST / gRPC / GraphQL / Microservice — OpenAPI, /healthz, RFC 9457, connection pool)`
   - `[6] Background Worker / Daemon (Queue Consumer / Cron / Async Processor — Graceful shutdown, idempotency, retry/DLQ)`
   - `[7] CLI Tool / Developer Utility (Command Line / TUI — < 50ms cold startup, POSIX exit codes, TTY aware)`
   - `[8] Reusable Library / Client SDK (Shared Package — Stable SemVer API, zero unsolicited prints, minimal deps)`
   - `[9] Embedded / Console Homebrew (Nintendo Switch / Low-Level / Game — Constrained RAM, gamepad input, RomFS)`
   *(Chi tiết kỹ thuật & checklist cho từng thể loại: xem [`references/product-categories.md`](./references/product-categories.md))*

1. **Q1 — Architecture Blueprint** *(single-select)*:
   - `Clean Architecture (3-Layer: Presentation → Domain ← Data)` | `Modular Clean (:feature:* + :core:*)` | `Vertical Slice / Feature-First` | `Hexagonal / Ports & Adapters + DDD` | `Lightweight Modular (KISS/YAGNI)`
2. **Q2 — Flow / State Pattern + Famous Reference Repo** *(single-select, stack-aware via `lookup`)*:
   - Android/KMP: `MVI Strict UDF (chrisbanes/tivi, slackhq/circuit)` | `MVVM + UDF (android/nowinandroid)` | `Decompose (arkivanov/Decompose)`
   - Flutter: `BLoC / Cubit (felangel/bloc)` | `Riverpod AsyncNotifier (bizz84/starter_architecture_flutter_firebase)`
   - iOS: `TCA (pointfreeco/swift-composable-architecture)` | `MVVM + @Observable (nalexn/clean-architecture-swiftui)`
   - Web: `TanStack Query + Zustand (alan2207/bulletproof-react)` | `Feature-Sliced Design (feature-sliced/documentation)` | `Vue Pinia (antfu/vitesse)`
   - Backend: `Domain Router → Service → Repo (fastapi-best-practices / go-clean-template)` | `DDD + Hexagonal + CQRS/UoW (cosmicpython / domain-driven-hexagon)`
   - Rust: `MVI / Immediate Mode (emilk/egui, iced-rs/iced)` | `Hexagonal Ports & Adapters (LukeMathWalker/zero-to-production)`
3. **Q3 — Project Base Modules** *(`is_multi_select: true` checkboxes)*:
   - `(Recommended) Core SOLID + Anti-False-DRY + Anti-God-File Cap (300 Warn / 450 Fail LOC)`
   - `(Recommended) Typed Error Handling & Result Wrapper (Result<T, DomainError> / RFC 9457)`
   - `(Recommended) Dependency Injection + Validated Env Config + Secret-Redacted Logging`
   - `(Recommended) Network Client (Auth/Retry) + Local DB/Storage Repository Base`
   - `(Recommended) Design System Tokens + Type-Safe Navigation (Client) / OpenAPI + Healthchecks (Backend)`
   - `(Recommended) Strict Compiler Flags + Linter/Formatter + Architecture Boundary Tests`
   - `Testing Harness (Fakes over Mocks + State/Service tests) + GitHub Actions CI (Rust: Linux/macOS/Windows matrix)`
4. **Q4 — Multi-Language Support / Internationalization (i18n/l10n) & Locales** *(single-select & locale multi-select)*:
   - **Kích hoạt đa ngôn ngữ**:
     - `(Recommended) Có — Thiết lập sẵn kiến trúc đa ngôn ngữ (i18n/l10n) chuẩn theo nền tảng`
     - `Không — Chỉ dùng ngôn ngữ đơn bản mặc định`
   - **Danh sách ngôn ngữ hỗ trợ (Locales)** *(`is_multi_select: true` checkboxes)*:
     - `(Recommended) [x] Tiếng Việt (vi / vi-VN)`
     - `(Recommended) [x] English (en / en-US)`
     - `[ ] 日本語 / Japanese (ja / ja-JP)`
     - `[ ] 中文 / Chinese Simplified (zh / zh-CN)`
     - `[ ] 한국어 / Korean (ko / ko-KR)`
     - `[ ] Français / French (fr / fr-FR)`
     - `[ ] Español / Spanish (es / es-ES)`
     - `[ ] Deutsch / German (de / de-DE)`
     *(Hoặc nhập danh sách mã ngôn ngữ BCP 47 tùy chọn: e.g. `vi,en,ja`)*
   - **Preset kiến trúc đa ngôn ngữ chuẩn theo từng nền tảng khi chọn "Có"**:
     - **Android (Kotlin + Jetpack Compose)**: `res/values/strings.xml` (base/en) + `res/values-<lang>/strings.xml`, `stringResource(...)`, chuỗi tập trung trong `:core:designsystem` hoặc `:core:resources`. Chuyển đổi ngôn ngữ runtime qua `AppCompatDelegate.setApplicationLocales()` hoặc Android 13+ `LocaleManager`.
     - **KMP / CMP (Compose Multiplatform)**: Compose Multiplatform Resources `Res.string.*` (`composeResources/values/strings.xml`, `values-<lang>/strings.xml`) hoặc MOKO Resources, dùng sealed class `UiText` (`UiText.DynamicString` / `UiText.StringResourceId`) trong ViewModel để không rò rỉ Android `Context`.
     - **Flutter**: Official `flutter_localizations`, `intl`, `l10n.yaml`, `.arb` catalogs (`lib/l10n/app_<lang>.arb`), `AppLocalizations.of(context)!.key` với code generation tự động.
     - **iOS / Swift (SwiftUI + Swift 6)**: Modern **String Catalog** (`.xcstrings` / `Localizable.xcstrings`), `LocalizedStringKey`, `String(localized: "key", bundle: .module)` cho SPM packages. Nghiêm cấm hardcode raw text trong Views.
     - **Web Frontend (React / Next.js / Vue / TS)**: `next-intl` (Next.js App Router, routing `/[locale]/...`, middleware, catalogs `messages/<lang>.json`), `react-i18next` (Vite/SPA), hoặc `vue-i18n` với strict TypeScript schemas.
     - **Backend Python (FastAPI / Async)**: GNU gettext / `Babel` (`pybabel`), `Accept-Language` header middleware, catalogs `locales/<lang>/LC_MESSAGES/messages.po`.
     - **Backend Go**: `nicksnyder/go-i18n/v2` + `golang.org/x/text/language`, JSON/TOML locale bundles (`locales/active.<lang>.json`), inject `i18n.Localizer` vào request context.
     - **Backend Node.js / NestJS**: `nestjs-i18n` (JSON catalogs `src/i18n/<lang>/common.json`) hoặc `i18next`, `AcceptLanguageResolver`, type-safe translation keys.
     - **Rust (Desktop GUI / Cargo Workspace)**: Centralized type-safe `strings` / `i18n` catalog (`AppLanguage { Vietnamese, English, ... }` enum + `strings::*` module) hoặc `fluent-rs` / `unic-langid`. Nghiêm cấm hardcode raw string literals trong UI views.
     - **C++ / Nintendo Switch Homebrew**: Borealis built-in i18n (`brls::loadTranslations("romfs:/i18n")`), catalogs `resources/romfs/i18n/<lang-TAG>/strings.json`, truy xuất bằng `brls::getStr("key")`.
5. **Q5 — AI Agent Harness, Persistent Memory, Git Hooks & Security Shields** *(`is_multi_select: true` checkboxes)*:
   - `(Recommended) Universal Agent & 6-Gate Execution Harness (AGENTS.md + execution-harness.md + security-gate.md + layer rules)`
   - `(Recommended) Cross-Session Memory & Codebase Map (.agents/CODEBASE_MAP.md + memory/active-plan.md + lessons.md)`
   - `(Recommended) Claude Code & Antigravity/Gemini Bridges (CLAUDE.md + GEMINI.md)`
   - `(Recommended) Git Security & Quality Hooks (pre-commit secret/boundary scan, commit-msg, pre-push CVE + tests + .gitignore)`
   - `(Recommended) AI Agent Anti-Bypass Runtime Hooks (.agents/hooks.json + .claude/settings.json blocking --no-verify)`
   - `(Recommended) Architecture Decision Record (docs/architecture/ADR-0001-architecture.md)`
   - `Cursor / Windsurf / Cline / Roo / DeepSeek Rules (.cursor/rules/*.mdc + .clinerules)`

After user selection: run `project_pro.py init`, consult the chosen famous reference repo, and implement the ticked base modules with clean, production-grade code.

---

## Mode B: Mandatory 6-Gate Execution Harness (Every Coding Request)

Execute **every** feature, bugfix, or refactor through all 6 Gates (full details in [`references/execution-harness.md`](./references/execution-harness.md)):

1. **Gate 1 — Grounding**: Read `AGENTS.md`, `.agents/project-profile.json`, and neighboring files. Consult the anchored `referenceRepo` (via `references/stacks-*.md` or GitHub/docs search) instead of inventing custom patterns. Ask early if business rules are ambiguous.
2. **Gate 2 — File-Split Blueprint (Anti-God-File Lock)**:
   - **1 File = 1 Primary Responsibility** (never bundle `Dto` + `Mapper` + `RepoImpl`, or `UiState` + `ViewModel` + `Screen` + `Sub-components`).
   - Hard LOC caps on code files: **`> 300 LOC` = `[WARN]`**, **`> 450 LOC` = `[FAIL]`** (blocks `pre-commit` & `audit`; generated files are auto-exempt).
3. **Gate 3 — Disciplined Coding &SOLID/DRY**:
   - **Features**: Inside-Out (`Domain` pure entities/ports/`DomainError` → `Data` DTO/Entity/Mappers/RepoImpl → `State Holder` Sealed `UiState` → `Stateless Previewable UI` → `DI/Nav`).
   - **Bugfixes**: Fix **Root Cause** + add reproduction test (ban blind `try/catch`, arbitrary `delay()`, or unsafe casts).
   - **Clean Code**: Separate layer models (no False DRY), ban boolean state soup, guard clauses (`<= 3` indent levels), immutable by default, rethrow `CancellationException`/`CancelledError`, zero `// TODO` stubs or dead code.
4. **Gate 4 — Shift-Left Security**:
   - Zero hardcoded API keys, tokens, passwords, or `.env`/keystore commits; parameterized SQL/ORM queries only; validate untrusted inputs; redact tokens/PII in logs. **Never run `--no-verify` to bypass Git hooks.**
5. **Gate 5 — Fast Unit Tests & Self-Healing Verification**:
   - Cover happy, empty, error/offline, and boundary cases with fast **Fakes**.
   - Run `Single Test` → `Lint/Typecheck` → `project_pro.py audit --target "<PROJECT_DIR>" --fail-on-error`. Fix every failure before concluding.
6. **Gate 6 — Clean Delivery**: Summarize changes by layer alongside actual test, lint, and audit results.

---

## Mode C: GitHub Projects & Parallel Sub-Agent Execution Protocol

Scale multi-step development across autonomous sub-agents with GitHub Projects v2 Kanban:
1. **Board Setup**: `python3 scripts/workflow.py setup [--public|--private]`
2. **Create Task**: `python3 scripts/workflow.py new "<Title>" --body "<Specs>"` (places in `Todo`)
3. **Start Task**: `python3 scripts/workflow.py start <issue_id>` (moves to `In Progress`, creates branch `feat/issue-<id>-...`)
4. **Dispatch Sub-Agent**: `python3 scripts/workflow.py dispatch <issue_id>` (generates token-efficient English prompt for `invoke_subagent`)
5. **Complete Task**: `python3 scripts/workflow.py done <issue_id>` (verifies 6-Gate audit green, merges, closes issue, moves to `Done`)
