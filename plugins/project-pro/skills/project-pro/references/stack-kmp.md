# KMP / CMP (Kotlin Multiplatform & Compose Multiplatform) Reference Architecture

Always ground module layouts, build setup, DI wiring, and UDF state holders in these battle-tested open-source repositories instead of inventing custom structures.

---

## Famous Reference Repositories
1. **`chrisbanes/tivi`** *(Gold standard KMP + Compose Multiplatform across Android, iOS, Desktop)*
2. **`JetBrains/kotlinconf-app`** *(Official JetBrains KMP + CMP production app, Ktor + Koin)*
3. **`touchlab/KaMPKit`** *(Touchlab's KMP architectural starter, SKIE/Coroutines/SQLDelight best practices)*
4. **`philipplackner/CMP-Bookpedia`** *(Clean 3-layer Feature-First CMP reference: Koin + Ktor + Room KMP + Navigation Compose)*
5. **`arkivanov/Decompose`** *(Lifecycle-aware KMP components + MVIKotlin strict MVI)*

## Canonical KMP Directory Structure (`composeApp` / Multi-module `shared`)
```text
project-root/
├── composeApp/ (or shared/)
│   └── src/
│       ├── commonMain/kotlin/com/example/app/
│       │   ├── app/               # Root App composable, typed Route graph, Koin init
│       │   ├── core/
│       │   │   ├── domain/        # AppResult<D, E>, DataError, DomainError
│       │   │   ├── data/          # HttpClientFactory (Ktor), safeCall {}, DB factory
│       │   │   └── presentation/  # UiText, Theme tokens, base MVI/UDF helpers
│       │   └── features/
│       │       └── <feature>/
│       │           ├── domain/    # Pure Kotlin models, Repository interface, UseCases
│       │           ├── data/      # Ktor RemoteDataSource, Room/SQLDelight DAO, Mappers
│       │           └── presentation/ # State, Intent/Action, ViewModel/Component, Screen
│       ├── androidMain/           # Platform engine (OkHttp), Room builder, Android entry
│       ├── iosMain/               # Platform engine (Darwin), MainViewController, Room builder
│       ├── desktopMain/           # JVM engine (CIO/OkHttp), main() window
│       └── commonTest/            # 100% shared multiplatform unit tests (Turbine + Fakes)
└── iosApp/                        # Thin Swift host wrapper launching MainViewController
```

## KMP Non-Negotiables
- Prefer `expect`/`actual` **only** for platform-specific drivers/capabilities (HTTP engine, DB file path, biometrics); prefer **interface injection via Koin/DI** over `expect class` for testable components.
- If exposing Kotlin APIs directly to native SwiftUI (instead of shared CMP UI), enable **SKIE** (`co.touchlab.skie`) so Kotlin `Flow` and `sealed` hierarchies map naturally to Swift `AsyncSequence` and exhaustive `switch` enums!
- In `safeCall {}` around Ktor, **always** catch `UnresolvedAddressException` / `SerializationException` and `coroutineContext.ensureActive()` so `CancellationException` is never swallowed!
