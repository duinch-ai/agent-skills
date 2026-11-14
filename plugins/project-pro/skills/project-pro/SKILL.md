---
name: project-pro
description: >-
  Project setup and standardization wizard: scaffold or standardize a repository, choose
  stacks and reference repos (Android, KMP/CMP, Flutter, iOS/Swift, Rust, Web, Python/FastAPI,
  Go, Node.js/NestJS, C++ Switch), architecture and layer rules (Clean Architecture & UDF),
  the Coding Standards Checklist (file-size caps, SOLID/DRY, tests), Git/Agent security hooks
  and the deterministic `audit`, plus generated AGENTS.md/CLAUDE.md/GEMINI.md/ADR/CODEBASE_MAP.
  Activate when creating or scaffolding a project, standardizing an existing repo with tickable
  options, choosing stacks or architecture, auditing coding standards, or installing
  pre-commit/pre-push security hooks. How agents work on a task (grounding, debugging,
  review, delivery) belongs to the agent-team skill.
---

# Project Pro — Interactive Architect, Coding Standards & DevSecOps Guard

Build, standardize, and ship production software using **interactive checkbox blueprints**, **famous open-source reference repositories**, **Clean Architecture + UDF**, **SOLID + pragmatic DRY**, **hard file-size caps**, and a **4-Shield Security & Hook Defense** (`pre-commit`, `commit-msg`, `pre-push`, plus runtime AI Agent anti-bypass hooks).

Boundary: project-pro is the repository's constitution, the WHAT every change must satisfy
(structure, layer rules, coding standards, security rails enforced by code). HOW an agent works
(grounding, debugging, review, delivery, lessons) is the `agent-team` skill.

## Two Operating Modes

Check `<PROJECT_DIR>/.agents/project-profile.json` and `<PROJECT_DIR>/AGENTS.md` (via `project_pro.py detect`) first:

1. **Mode A — Interactive Project Setup / Standardization Wizard** *(New project, unconfigured repo, or user asks to configure/scaffold base options)*:
   - Run `detect` → present **tickable multi-select checkboxes** for Architecture, Flow Pattern + Famous Reference Repo, Base Modules, and AI Agent + Git/Security Hooks → scaffold and persist `.agents/project-profile.json`.
2. **Mode B — Standards check** *(a configured project; user changes code, audits, or asks what the repo requires)*:
   - Read the saved profile **without re-asking setup questions**; apply the Coding Standards Checklist below (and `references/execution-harness.md`) and run `audit --fail-on-error` before finishing. Working method (grounding, bugfix rule, review, delivery report): `agent-team` skill, `references/working-method.md`.

---

## CLI Toolkit (100% Python 3 Standard Library — Zero Dependencies)

Resolve `<SKILL_DIR>` to the directory containing this `SKILL.md`:

```bash
# 1. Detect project mode (greenfield / brownfield / configured), stack & hook status
python3 "<SKILL_DIR>/scripts/project_pro.py" detect --target "<PROJECT_DIR>"

# 2. Lookup famous reference repos, patterns & GitHub search queries for a stack
python3 "<SKILL_DIR>/scripts/project_pro.py" lookup --stack <android|kmp|flutter|ios|web|python|go|nestjs|rust|cpp-switch>

# 3. Initialize agent harness, coding standards, Git security hooks & runtime agent guards
python3 "<SKILL_DIR>/scripts/project_pro.py" init \
  --target "<PROJECT_DIR>" \
  --stack <stack> \
  --arch <clean|modular-clean|vertical-slice|hexagonal|lightweight> \
  --pattern <mvi|mvvm-udf|tca|bloc|riverpod|fsd|query-zustand|service-repo|cqrs> \
  [--preset minimal|recommended|all|guided] \
  [--features "solid-dry,typed-errors,i18n,di-core,network-storage,ui-nav,arch-lint,testing-ci" | --features all] \
  [--agents "agents-root,persistent-memory,claude-gemini,git-security-hooks,agent-runtime-hooks,adr-docs,cursor-ide" | --agents all] \
  [--category <mobile-app|desktop-app|multiplatform-app|web-app|backend-api|service-worker|cli-tool|library-sdk|embedded-homebrew>] \
  [--i18n] [--locales "vi,en,ja"] \
  [--ref-repo "<owner/repo>"] [--scaffold-dirs] [--force]

# `--preset recommended` (default) = the usual set; `minimal` = solid-dry + agents-root (enough for `audit`);
# `all` (or `--features all` / `--agents all`) = every choice applicable to the stack. The resolved lists are printed.
# Explicit --features / --agents override the preset.

# Boundary config (feature `arch-lint`): go writes .golangci.yml (depguard; needs go.mod or --go-module <path>),
# python writes .importlinter (import-linter contracts). Existing config is never overwritten: a snippet is printed
# instead. Other stacks print "not yet automated".

# 3b. Guided mode: plain-language answers -> recommendation -> init (see "Choosing a mode")
python3 "<SKILL_DIR>/scripts/project_pro.py" recommend --answers <answers.json|-> [--target "<PROJECT_DIR>"] [--json]
python3 "<SKILL_DIR>/scripts/project_pro.py" init --mode guided --answers <answers.json|-> --target "<PROJECT_DIR>"

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
- **Coding Standards Checklist** (file split, disciplined coding, security, tests) → [`references/execution-harness.md`](./references/execution-harness.md)
- **Agent working method** (grounding, debugging + 3-strike stop, review lens, delivery, lessons) → `agent-team` skill, `references/working-method.md`
- **Security Gateways, Git Hooks & Runtime Agent Hooks** → [`references/security-and-hooks.md`](./references/security-and-hooks.md)
- **Clean Arch, SOLID, Pragmatic DRY (AHA) & Anti-God-File Rules** → [`references/clean-arch-and-solid.md`](./references/clean-arch-and-solid.md)
- **MVI / MVVM / TCA / BLoC / Riverpod / FSD & UDF Contracts** → [`references/presentation-patterns.md`](./references/presentation-patterns.md)
- **Agent Harness & Tickable Base Module Specs** → [`references/agent-harness-spec.md`](./references/agent-harness-spec.md)
- **Stack references** (famous repos, canonical structure, non-negotiables), load only the chosen stack:
  [`android`](./references/stack-android.md) | [`kmp`](./references/stack-kmp.md) | [`flutter`](./references/stack-flutter.md) | [`ios`](./references/stack-ios.md) | [`web`](./references/stack-web.md) | [`python`](./references/stack-python.md) | [`go`](./references/stack-go.md) | [`nestjs`](./references/stack-nestjs.md)
- **Rust Idioms, Platform Targets & CI/CD** → [`references/stack-rust.md`](./references/stack-rust.md)
- **C++ Modern Idioms & Nintendo Switch Homebrew** → [`references/stack-cpp-switch.md`](./references/stack-cpp-switch.md)

---

## Choosing a mode

- **Guided**: the user asks which language/framework to use, describes a product without technical terms, or says they are not a developer (or are from another field).
- **Expert**: the user names stacks or architectures, or passes explicit options. Use the flow below (Mode A) unchanged.

Guided interview (agents run this in chat): ask at most 6 questions, in the user's language, in plain words, one or two at a time, with examples:
1. What do you want to build? (`goal`) 2. Where should it run? (`platforms`) 3. Does it need offline use, live updates, many users, several UI languages or heavy processing? (`needs`) 4. Which programming languages do you already know, if any? (`known_languages`) 5. Who will work on it? (`maintainers`). `existing_code` is automatic: an existing supported project in the folder wins.

Write the answers to `answers.json` (only `goal` is required; unknown values are rejected with the allowed list), then:

```bash
python3 "<SKILL_DIR>/scripts/project_pro.py" recommend --answers answers.json --target "<PROJECT_DIR>" --json
python3 "<SKILL_DIR>/scripts/project_pro.py" init --mode guided --answers answers.json --target "<PROJECT_DIR>"
```

Explain the result in plain language: what is recommended, why (`reasons`), what the `alternative` would mean, and every `notes` entry. On confirmation run `init --mode guided` (it uses `--preset guided` = recommended + `testing-ci` + `data-integrity`, and also writes `START_HERE.md` and `scripts/check.sh`; explicit flags such as `--stack` override it and print a notice; if `--agents`/`--features` drop a safety item you get a `WARNING: guided mode normally keeps <x>` line - tell the user in plain words, do not re-add it silently). Then run `sh scripts/check.sh` once in the project, tell the user the result in plain words (passed / what failed and what to ask the agent), and point them to `START_HERE.md`. Finish by saying what was created and how to run it, and that the agent-team skill can continue the work with verification. Expert mode is unchanged: `START_HERE.md` and `check.sh` exist only with `--preset guided` / guided mode.

Honesty: only recommend supported stacks; if the user knows a language project-pro has no stack for (Java, C#, PHP, Ruby) show the `unsupported-language` note instead of hiding it. The rules are project-pro policy defaults (`scripts/recommend_rules.py`), not claims about frameworks; never invent facts about them. If `recommend` returns `need-goal` or `need-language`, ask the user, never guess.

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
   - **`[ ] task-tracking`** — task board (default OFF). When ticked, setup asks for a provider (`github` or `local`; `gitlab` is coming), creates `docs/tasks/` and `docs/BACKLOG.md` in the format the `task-board` skill parses, adds one pointer line to AGENTS.md, checks that skill is installed (prints install help if not, never installs it) and prints the `project_board.py init --provider <github|local> [--project <N>]` next step. It does not call any provider API: board sync belongs to `task-board`.
   - **`[ ] data-integrity`** — optional AGENTS.md rule (default OFF; in `--features all`): never invent numbers, limits, versions, flags or model ids; fixtures recorded from real runs with CLI+version+date; reports state what was actually run and label unverified items.
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
   - `(Recommended) Universal Agent & Coding Standards (AGENTS.md + execution-harness.md checklist + security-gate.md + layer rules)`
   - `(Recommended) Cross-Session Memory & Codebase Map (.agents/CODEBASE_MAP.md + memory/lessons.md)`
   - `(Recommended) Claude Code & Antigravity/Gemini Bridges (CLAUDE.md + GEMINI.md)`
   - `(Recommended) Git Security & Quality Hooks (pre-commit secret/boundary scan, commit-msg, pre-push CVE + tests + .gitignore)`
   - `(Recommended) AI Agent Anti-Bypass Runtime Hooks (.agents/hooks.json + .claude/settings.json blocking --no-verify)`
   - `(Recommended) Architecture Decision Record (docs/architecture/ADR-0001-architecture.md)`
   - `Cursor / Windsurf / Cline / Roo / DeepSeek Rules (.cursor/rules/*.mdc + .clinerules)`

After user selection: run `project_pro.py init`, consult the chosen famous reference repo, and implement the ticked base modules with clean, production-grade code.

---

## Mode B: Coding Standards Checklist (every code change)

Full details in [`references/execution-harness.md`](./references/execution-harness.md):

1. **File Split (Anti-God-File Lock)**:
   - **1 File = 1 Primary Responsibility** (never bundle `Dto` + `Mapper` + `RepoImpl`, or `UiState` + `ViewModel` + `Screen` + sub-components).
   - Hard LOC caps on code files: **`> 300 LOC` = `[WARN]`**, **`> 450 LOC` = `[FAIL]`** (blocks `pre-commit` & `audit`; generated files are auto-exempt). Touch only the files the task needs.
2. **Disciplined Coding & SOLID/DRY**:
   - **Features**: Inside-Out (`Domain` pure entities/ports/`DomainError` -> `Data` DTO/Entity/Mappers/RepoImpl -> `State Holder` sealed `UiState` -> stateless previewable UI -> `DI/Nav`).
   - **Bugfixes**: fix the root cause and add a regression test (ban blind `try/catch`, arbitrary `delay()`, unsafe casts). The debugging method and 3-strike stop live in agent-team.
   - **Clean Code**: separate layer models (no False DRY), ban boolean state soup, guard clauses (`<= 3` indent levels), immutable by default, rethrow `CancellationException`/`CancelledError`, zero `// TODO` stubs or dead code.
3. **Security**: zero hardcoded API keys, tokens, passwords, or `.env`/keystore commits; parameterized SQL/ORM queries only; validate untrusted inputs; redact tokens/PII in logs. **Never run `--no-verify` to bypass Git hooks.**
4. **Tests**: cover happy, empty, error/offline, and boundary cases with fast **Fakes**; run `Single Test` -> `Lint/Typecheck` -> `project_pro.py audit --target "<PROJECT_DIR>" --fail-on-error` and fix every failure before concluding.

Task board work -> `task-board`; working method and multi-agent / issue-driven team work (lead, coders, cross-vendor review, done gate) -> `agent-team` skill.
