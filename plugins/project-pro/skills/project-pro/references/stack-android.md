# Android (Kotlin + Jetpack Compose) Reference Architecture

Always ground module layouts, build setup, DI wiring, and UDF state holders in these battle-tested open-source repositories instead of inventing custom structures.

---

## Famous Reference Repositories
1. **`android/nowinandroid`** *(Official Google Reference — 47k+ stars)*
   - **Learn from it**: Convention plugins (`build-logic/`), multi-module split (`:app`, `:feature:*`, `:core:data`, `:core:domain`, `:core:model`, `:core:database`, `:core:network`, `:core:designsystem`, `:core:ui`, `:core:testing`), offline-first reactive `Flow` repositories, `StateFlow<UiState>` with `SharingStarted.WhileSubscribed(5_000)`, Fakes-over-Mocks testing.
2. **`chrisbanes/tivi`** *(Modular Compose + Circuit UDF)*
   - **Learn from it**: Strict UDF (`UiState` + `UiEvent` sink inside state), clean separation of pagination/sync workers, SQLDelight/Room reactive queries.
3. **`slackhq/circuit`** *(Compose-first MVI/UDF Architecture)*
   - **Learn from it**: Lightweight `Presenter<State>` + `@Composable Ui<State>` split, zero-ViewModel Compose testing, type-safe navigation.
4. **`android/architecture-samples`** *(Single-module pragmatic starter)*
   - **Learn from it**: Clean single-app package layout when multi-module Gradle is overkill.

## Canonical Directory Structures

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

## Android Non-Negotiables
- Collect state with `collectAsStateWithLifecycle()`.
- Mark UI list models `@Immutable` or use `kotlinx.collections.immutable.ImmutableList` so Compose skips unnecessary recompositions.
- `:core:model` and `:core:domain` must remain **pure JVM/Kotlin modules** (`id("java-library")` / `kotlin("jvm")`) — never `com.android.library` unless Android platform types are unavoidable.
