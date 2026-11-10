# Product Category Taxonomy & Architecture Blueprints

When scaffolding a project with `project-pro`, the **Product Category (Mục đích dự án & Thể loại sản phẩm)** determines the optimal tech stack, layer boundaries, lifecycle contracts, and operational capabilities.

---

## 1. Taxonomy of 9 Product Categories

| Category ID | Display Name | Recommended Stacks | Canonical Architecture | Key Operational Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| `mobile-app` | Mobile Native / Cross-Platform App | `android`, `ios`, `flutter`, `kmp` | `modular-clean`, `clean` | Offline-first, UI state survival, runtime permissions, reactive flows |
| `desktop-app` | Desktop Native / GUI App | `rust`, `flutter`, `kmp`, `ios` | `modular-clean`, `clean` | Window bounds, file dialogs, system tray, drag & drop, background threads |
| `multiplatform-app`| Universal Client App | `kmp`, `flutter`, `rust` | `clean`, `modular-clean` | Expect/actual isolation, adaptive layout (touch/mouse), multi-target CI |
| `web-app` | Web Application / SaaS Portal | `web` (Next.js, React, Vue) | `vertical-slice`, `fsd` | SSR/SSG/ISR, server vs client state split, CWV metrics, CSP security |
| `backend-api` | Backend Service / Microservice | `python`, `go`, `nestjs` | `hexagonal`, `vertical-slice` | OpenAPI contracts, /healthz & /readyz, connection pooling, RFC 9457 errors |
| `service-worker` | Queue Consumer / Scheduled Daemon | `python`, `go`, `rust`, `nestjs` | `hexagonal` | Graceful shutdown, idempotency, retry + DLQ, backpressure control |
| `cli-tool` | CLI / Developer Tooling / TUI | `rust`, `go`, `python` | `lightweight`, `clean` | < 50ms startup, subcommands, POSIX exit codes, TTY auto-detection |
| `library-sdk` | Shared Library / Reusable SDK | `rust`, `web`, `python`, `kmp`, `go` | `clean`, `lightweight` | Stable public API, zero unsolicited logs/prints, minimal dependencies |
| `embedded-homebrew`| Embedded / Game / Console Homebrew | `cpp-switch`, `rust` | `modular-clean`, `clean-layered`| Constrained memory, gamepad/touch input, ROM/asset packaging, zero leak |

---

## 2. Detailed Category Specifications & Best Practices

### 2.1. `mobile-app` (Mobile Native / Cross-Platform Application)
- **Primary Mission**: High-performance, touch-first mobile application running on iOS and/or Android devices.
- **Recommended Stacks**:
  - Android Native: `android` (Kotlin + Jetpack Compose) — reference: `android/nowinandroid`, `chrisbanes/tivi`
  - iOS Native: `ios` (Swift + SwiftUI + Swift 6) — reference: `pointfreeco/swift-composable-architecture`
  - Cross-Platform: `flutter` (Dart) or `kmp` (Compose Multiplatform)
- **Core Architecture Rules**:
  1. **Offline-First Single Source of Truth**: Room/SwiftData/Drift repositories emit reactive streams/flows from local database. Network responses write to DB; UI observes DB.
  2. **Decoupled ViewModels**: ViewModels never import `android.content.Context`, `UIKit`, or `BuildContext`. Use sealed `UiText` or typed resource IDs for string localization.
  3. **State Survival & Recomposition**: Screen states must survive configuration changes (rotation, font scale) and handle process death via SavedStateHandle.
  4. **Strict Permission & Lifecycle Flow**: Never assume camera, location, or notifications are granted. Always guard with stateful permission handlers.

### 2.2. `desktop-app` (Desktop Native / GUI Application)
- **Primary Mission**: Standalone desktop software running on macOS, Windows, and Linux workstations.
- **Recommended Stacks**:
  - `rust` with `egui` (immediate-mode), `iced` (Elm-style UDF), or `tauri` (Rust core + Web frontend)
  - `flutter` (Desktop target)
  - `kmp` (Compose Multiplatform Desktop via Skiko/JVM)
  - `ios` (Mac Catalyst / Native macOS SwiftUI)
- **Core Architecture Rules**:
  1. **Window State Persistence**: Persist window width, height, position, and maximized state across app restarts.
  2. **Non-Blocking Main Thread**: Heavy file operations, hashing, decompression, and network downloads MUST run on worker threads/threadpools.
  3. **Desktop Native Interop**: Support native file picker dialogs, system menus, keyboard shortcuts (Cmd/Ctrl bindings), and drag-and-drop.
  4. **Packaging & Updates**: Include packaging pipelines (`.dmg` with codesigning/notarization for macOS, `.msi`/`.exe` for Windows, `.AppImage`/`.deb` for Linux).

### 2.3. `multiplatform-app` (Universal Client Application)
- **Primary Mission**: A single unified codebase targeting Mobile (iOS/Android), Desktop (macOS/Windows/Linux), and optionally Web.
- **Recommended Stacks**:
  - `kmp` (Kotlin Multiplatform + Compose Multiplatform)
  - `flutter` (Dart)
  - `rust` (Shared Core Crate + Platform-specific GUI shells or pure `egui`)
- **Core Architecture Rules**:
  1. **Strict Core Isolation**: Pure Domain and Business logic live in common modules without any platform SDK imports.
  2. **Adaptive Layouts**: UI must dynamically adapt between touch mobile screens (single-column, bottom sheets, gestures) and desktop/web screens (split views, multi-column data tables, hover states).
  3. **Expect / Actual Discipline**: Keep platform-specific bridges minimal, stateless, and narrow. Test the shared logic on JVM/desktop tests for sub-second feedback.

### 2.4. `web-app` (Web Application / Portal / SaaS Dashboard)
- **Primary Mission**: Modern browser-based web application, SaaS platform, interactive dashboard, or public web portal.
- **Recommended Stacks**:
  - `web` (React / Next.js / Vue / TypeScript) — reference: `alan2207/bulletproof-react`, `feature-sliced/documentation`
- **Core Architecture Rules**:
  1. **Server vs Client Separation**: Compute expensive data transformations on the server or in edge handlers. Keep client bundles lightweight.
  2. **Server Cache vs Client UI State**: Use TanStack Query / SWR for server cache, pagination, and invalidation. Reserve Zustand / Pinia strictly for local UI states (modal open, sidebar collapse).
  3. **Core Web Vitals & Accessibility**: Optimize LCP, INP, and CLS. Ensure semantic HTML, ARIA landmarks, keyboard focus rings, and dark/light color contrast compliance.
  4. **Defensive Web Security**: Sanitize all untrusted HTML (DOMPurify), prevent XSS, use CSRF tokens for mutating routes, and enforce strict Content Security Policy.

### 2.5. `backend-api` (Backend Service / Microservice)
- **Primary Mission**: Scalable server application providing REST, gRPC, or GraphQL APIs to client applications and third-party consumers.
- **Recommended Stacks**:
  - `python` (FastAPI + Pydantic v2 + async SQLAlchemy) — reference: `zhanymkanov/fastapi-best-practices`
  - `go` (Chi / standard net/http + pgx + sqlc) — reference: `evrone/go-clean-template`
  - `nestjs` (TypeScript + DDD Hexagonal) — reference: `Sairyss/domain-driven-hexagon`
- **Core Architecture Rules**:
  1. **Type-Safe API Contracts**: Auto-generate OpenAPI specs. Validate 100% of incoming payloads at the boundary using schema models before passing into domain services.
  2. **Standardized RFC 9457 Errors**: All API error responses return structured Problem Details JSON (`type`, `title`, `status`, `detail`, `instance`).
  3. **Cloud-Native Observability**: Expose `/healthz` (liveness) and `/readyz` (readiness with DB check). Inject unique Request-ID tracing headers and structured JSON logs.
  4. **Explicit DB Transactions & Pooling**: Manage connection pools defensively, enforce query timeouts, and wrap multi-entity writes in explicit Unit of Work transactions.

### 2.6. `service-worker` (Background Worker / Queue Consumer / Scheduled Daemon)
- **Primary Mission**: Headless asynchronous task executor, message queue consumer (Kafka, RabbitMQ, SQS, Redis BullMQ), or periodic cron daemon.
- **Recommended Stacks**: `python`, `go`, `rust`, `nestjs`
- **Core Architecture Rules**:
  1. **Graceful Shutdown**: Listen for `SIGINT` and `SIGTERM`. Finish processing the active in-flight message or batch, commit the queue offset, and release resources before exiting.
  2. **Idempotency by Design**: Every message handler must be idempotent. Use idempotency keys, unique database constraints, or optimistic locking to guarantee safe re-delivery.
  3. **Exponential Backoff & Dead Letter Queue (DLQ)**: Retries on transient errors must have exponential backoff with random jitter. Exhausted retries must route to a DLQ with root-cause diagnostic payloads.
  4. **Backpressure & Concurrency Caps**: Never spawn unbounded threads or goroutines on incoming queue bursts. Constrain concurrency with worker pools or semaphore tokens.

### 2.7. `cli-tool` (Command Line Interface / Developer Tooling / TUI)
- **Primary Mission**: Fast, scriptable command-line utility, terminal interactive tool (TUI), compiler wrapper, or automation script.
- **Recommended Stacks**:
  - `rust` (using `clap` for args, `crossterm`/`ratatui` for TUI)
  - `go` (using `cobra` for commands, `bubbletea` for TUI)
  - `python` (using `argparse`/`typer`, `rich` for formatting)
- **Core Architecture Rules**:
  1. **Sub-50ms Cold Startup**: Zero unnecessary dynamic imports or heavy daemon initialization. Parse arguments and exit fast.
  2. **Standard POSIX Conventions**: Support standard flags (`-h, --help`, `-v, --version`, `-q, --quiet`, `--json`). Return exit code `0` on success, `1` on error, `2` on bad arguments, `130` on Ctrl+C.
  3. **Terminal Awareness**: Check `isatty(stdout)`. Disable ANSI colors and progress animations when piped to another program (`cat`, `grep`, `file`). Output raw data or clean JSON when requested.
  4. **Separation of CLI Shell & Logic**: The CLI parsing module should only parse flags and call pure, easily unit-testable command functions.

### 2.8. `library-sdk` (Shared Library / Client SDK / Reusable Package)
- **Primary Mission**: Reusable codebase packaged and published to a package registry (crates.io, npm, PyPI, Maven, pub.dev) or consumed as an internal shared module.
- **Recommended Stacks**: `rust`, `web` (TypeScript), `python`, `kmp`, `go`
- **Core Architecture Rules**:
  1. **Minimal Public API Surface**: Hide all internals (`internal`, `pub(crate)`). Never leak transport DTOs or third-party dependencies in public signatures.
  2. **Semantic Versioning & Backward Compatibility**: Breaking changes require a major version bump. Deprecate with compiler warnings one cycle before deletion.
  3. **Zero Unsolicited Side-Effects**: A library MUST NOT print to stdout/stderr, install signal handlers, call `exit()`, or mutate global state without explicit client configuration.
  4. **Zero-Dependency Goal**: Keep external dependencies minimal to avoid dependency conflicts (diamond dependencies) in consumer projects.

### 2.9. `embedded-homebrew` (Embedded / Console Homebrew / Low-Level / Game Engine)
- **Primary Mission**: Software running on resource-constrained hardware, custom embedded chips, or homebrew video game consoles (e.g. Nintendo Switch).
- **Recommended Stacks**:
  - `cpp-switch` (CMake + devkitPro + libnx + Borealis GUI)
  - `rust` (`no_std` or embedded HAL)
- **Core Architecture Rules**:
  1. **Zero Memory Leaks & Deterministic Footprint**: Strict RAII, zero heap churn in render loops, and bounded cache structures.
  2. **Hardware Controller & Video Modes**: Support gamepad button mapping, analog stick deadzones, touch events, and dynamic resolution switches (Docked 1080p vs Handheld 720p).
  3. **Asset Packaging & RomFS**: Package assets, textures, and localization strings into read-only embedded filesystems (`romfs:/`).
  4. **Cross-Compilation Toolchain Integrity**: Guard CMake and linker targets for specific target toolchains (e.g. `aarch64-none-elf`).
