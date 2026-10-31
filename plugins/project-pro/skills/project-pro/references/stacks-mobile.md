# Mobile & Multiplatform Reference Architectures (Android, KMP, Flutter, iOS)

Always ground module layouts, Gradle/SPM/Pubspec setup, DI wiring, and UDF state holders in these battle-tested open-source repositories instead of inventing custom structures.

---

## 1. Android (Kotlin + Jetpack Compose)

### Famous Reference Repositories
1. **`android/nowinandroid`** *(Official Google Reference — 47k+ stars)*
   - **Learn from it**: Convention plugins (`build-logic/`), multi-module split (`:app`, `:feature:*`, `:core:data`, `:core:domain`, `:core:model`, `:core:database`, `:core:network`, `:core:designsystem`, `:core:ui`, `:core:testing`), offline-first reactive `Flow` repositories, `StateFlow<UiState>` with `SharingStarted.WhileSubscribed(5_000)`, Fakes-over-Mocks testing.
2. **`chrisbanes/tivi`** *(Modular Compose + Circuit UDF)*
   - **Learn from it**: Strict UDF (`UiState` + `UiEvent` sink inside state), clean separation of pagination/sync workers, SQLDelight/Room reactive queries.
3. **`slackhq/circuit`** *(Compose-first MVI/UDF Architecture)*
   - **Learn from it**: Lightweight `Presenter<State>` + `@Composable Ui<State>` split, zero-ViewModel Compose testing, type-safe navigation.
4. **`android/architecture-samples`** *(Single-module pragmatic starter)*
   - **Learn from it**: Clean single-app package layout when multi-module Gradle is overkill.

### Canonical Directory Structures

**Option A: Modular Clean Architecture (`modular-clean` — NowInAndroid style)**
```text
project-root/
├── build-logic/convention/        # Shared Gradle convention plugins
├── app/                           # Composition root, Hilt App, top-level NavHost
├── core/
│   ├── model/                     # Pure Kotlin domain models (zero Android deps!)
│   ├── common/                    # AppResult<D, E>, Dispatcher qualifiers, extensions
│   ├── domain/                    # Complex/reusable UseCases & repository interfaces
│   ├── data/                      # Offline-first Repository impls + DTO/Entity mappers
│   ├── network/                   # Retrofit/Ktor, OkHttp auth/retry interceptors, *Dto
│   ├── database/                  # Room DAOs, *Entity, migrations
│   ├── designsystem/              # Material3 Theme, tokens, stateless atomic components
│   └── testing/                   # TestDispatchers, Fake repositories
└── feature/
    └── <feature-name>/
        ├── api/                   # Public navigation route keys (decouples features!)
        └── impl/                  # Screen, ViewModel/Presenter, UiState, UiIntent, tests
```

**Option B: Single-Module Feature-First Clean Architecture (`clean`)**
```text
app/src/main/kotlin/com/example/app/
├── core/                          # common/, network/, database/, designsystem/, di/
└── features/
    └── auth/
        ├── domain/                # model/, repository/AuthRepository.kt, usecase/
        ├── data/                  # remote/*Dto, local/*Entity, mapper/, AuthRepositoryImpl.kt
        └── presentation/          # AuthUiState.kt, AuthIntent.kt, AuthViewModel.kt, AuthScreen.kt
```

### Android Non-Negotiables
- Collect state with `collectAsStateWithLifecycle()`.
- Mark UI list models `@Immutable` or use `kotlinx.collections.immutable.ImmutableList` so Compose skips unnecessary recompositions.
- `:core:model` and `:core:domain` must remain **pure JVM/Kotlin modules** (`id("java-library")` / `kotlin("jvm")`) — never `com.android.library` unless Android platform types are unavoidable.

---

## 2. KMP / CMP (Kotlin Multiplatform & Compose Multiplatform)

### Famous Reference Repositories
1. **`chrisbanes/tivi`** *(Gold standard KMP + Compose Multiplatform across Android, iOS, Desktop)*
2. **`JetBrains/kotlinconf-app`** *(Official JetBrains KMP + CMP production app, Ktor + Koin)*
3. **`touchlab/KaMPKit`** *(Touchlab's KMP architectural starter, SKIE/Coroutines/SQLDelight best practices)*
4. **`philipplackner/CMP-Bookpedia`** *(Clean 3-layer Feature-First CMP reference: Koin + Ktor + Room KMP + Navigation Compose)*
5. **`arkivanov/Decompose`** *(Lifecycle-aware KMP components + MVIKotlin strict MVI)*

### Canonical KMP Directory Structure (`composeApp` / Multi-module `shared`)
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

### KMP Non-Negotiables
- Prefer `expect`/`actual` **only** for platform-specific drivers/capabilities (HTTP engine, DB file path, biometrics); prefer **interface injection via Koin/DI** over `expect class` for testable components.
- If exposing Kotlin APIs directly to native SwiftUI (instead of shared CMP UI), enable **SKIE** (`co.touchlab.skie`) so Kotlin `Flow` and `sealed` hierarchies map naturally to Swift `AsyncSequence` and exhaustive `switch` enums!
- In `safeCall {}` around Ktor, **always** catch `UnresolvedAddressException` / `SerializationException` and `coroutineContext.ensureActive()` so `CancellationException` is never swallowed!

---

## 3. Flutter / Dart

### Famous Reference Repositories
1. **`bizz84/starter_architecture_flutter_firebase`** *(Andrea Bizzotto's canonical Feature-First Riverpod Architecture: Presentation → Application → Domain → Data)*
2. **`felangel/bloc`** *(Official `flutter_todos` & `github_search` multi-package Clean/Layered BLoC architecture)*
3. **`VGVentures/very_good_cli`** *(Very Good Ventures enterprise Flutter conventions, `very_good_analysis` lint rules, 100% test coverage patterns)*

### Canonical Flutter Directory Structure (`Feature-First Clean / Riverpod or BLoC`)
```text
lib/
├── main_staging.dart / main_production.dart  # Environment flavor entrypoints
├── app/                                      # MaterialApp.router, GoRouter config, DI bootstrap
├── core/
│   ├── error/                                # Result<T>, Failure sealed hierarchy
│   ├── network/                              # Dio client, Auth/Retry interceptors
│   ├── storage/                              # Drift / SecureStorage wrappers
│   └── theme/                                # AppTheme, ThemeExtension tokens, reusable widgets
└── features/
    └── <feature_name>/
        ├── domain/                           # Entities (@freezed / Equatable), Repository abstract interface, UseCases
        ├── data/                             # *Dto (@JsonSerializable), Remote/Local DataSources, RepositoryImpl
        └── presentation/                     # BLoC/Cubit or AsyncNotifier + sealed State + Stateless Screens/Widgets
```

### Flutter Non-Negotiables
- Enable `very_good_analysis` (or strict `analysis_options.yaml` with `strict-casts: true`, `strict-inference: true`, `strict-raw-types: true`).
- Break widgets into small `const`-constructible `StatelessWidget` classes rather than 150-line `_buildSomething()` helper methods (widget classes let Flutter short-circuit element rebuilds!).
- Never pass `BuildContext` into a `Bloc`, `Cubit`, or Riverpod `Notifier`.

---

## 4. iOS / Swift (SwiftUI + Swift 6 Concurrency)

### Famous Reference Repositories
1. **`pointfreeco/swift-composable-architecture`** *(TCA — inspect `Examples/SyncUps` and `Examples/CaseStudies` for gold-standard `@Reducer`, `@ObservableState`, `@Dependency`, and `TestStore`)*
2. **`nalexn/clean-architecture-swiftui`** *(Clean Architecture + SwiftUI + Environment DI without external frameworks)*
3. **`kudoleh/iOS-Clean-Architecture-MVVM`** *(Modular Clean Architecture + MVVM + Coordinator/Flow separation)*

### Canonical iOS Modular Structure (Local Swift Package Manager `Packages/` — Zero Xcode `.xcodeproj` Merge Conflicts!)
```text
project-root/
├── App/                           # Thin Xcode target (Assets, Info.plist, AppEntrypoint)
└── Packages/                      # Local SPM Workspace enforcing strict compile-time boundaries
    ├── CoreDomain/                # Pure Swift entities, Value Objects, Repository protocols, DomainError
    ├── CoreData/                  # URLSession/HTTPClient, SwiftData/GRDB persistence, DTOs, Repository impls
    ├── CoreDesignSystem/          # SwiftUI Design tokens, reusable Views, #Preview catalog
    └── Features/
        ├── AuthFeature/           # TCA @Reducer (or @Observable @MainActor ViewModel) + SwiftUI Views + Tests
        └── HomeFeature/           # Depends ONLY on CoreDomain + CoreDesignSystem (never CoreData impl!)
```

### iOS Non-Negotiables
- Favor **Local Swift Packages (`Package.swift`)** over monolithic Xcode targets: SPM enforces module encapsulation at compile time and lets you run `swift test` in < 2 seconds without booting the iOS Simulator!
- Embrace Swift 6 strict concurrency (`Sendable` value types/`struct` in Domain, `@MainActor` isolated UI state holders, structured `async let` / `TaskGroup`).
