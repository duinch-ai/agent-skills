# Presentation Patterns: MVI, MVVM, TCA, BLoC, Riverpod & FSD

## 1. Pattern Selection Matrix

Never choose MVI or MVVM dogmatically—select the lightest pattern that guarantees **Unidirectional Data Flow (UDF)** and **impossible-state prevention** for the screen's complexity:

| Pattern | Best For | Trade-off | Reference Implementation |
|---------|----------|-----------|--------------------------|
| **MVVM + UDF** | Data-display screens, forms, CRUD flows, standard master-detail screens | Low boilerplate; ViewModel exposes single `StateFlow<UiState>` and public action methods (`onSearchQueryChanged()`) | `android/nowinandroid` |
| **MVI (Strict Intent + Reducer)** | Complex interactive flows, multi-event concurrency, optimistic UI, undo/redo, deterministic state machines | Explicit `Intent` → pure `Reducer(State, Result) -> State` + `Effect`; slightly higher ceremony, 100% deterministic tests | `slackhq/circuit`, `arkivanov/Decompose` (MVIKotlin), `orbit-mvi` |
| **TCA (Composable Architecture)** | SwiftUI apps needing composable child-parent state, deep navigation trees, exhaustive `TestStore` assertions | Steep initial learning curve, unmatched testability and modularity in Swift | `pointfreeco/swift-composable-architecture` (`SyncUps`) |
| **BLoC / Cubit** | Flutter enterprise apps requiring strict event traceability (`BlocObserver`) and stream transformers (debounce/restartable) | `Cubit` = MVVM+UDF (minimal ceremony); full `Bloc` = MVI (explicit Event classes) | `felangel/bloc` |
| **Riverpod (`AsyncNotifier`)** | Reactive Flutter apps heavily driven by async data caching, derived providers, and declarative invalidation | Less boilerplate than BLoC; requires strict discipline not to put UI navigation inside providers | `bizz84/starter_architecture_flutter_firebase` |
| **Server State + Client Store (FSD / Bulletproof)** | Modern Web (`React` / `Next.js` / `Vue`) | Split **Server Cache** (`TanStack Query` / `SWR`) from **Client UI State** (`Zustand` / `Pinia`); never copy API responses into global Redux/Zustand stores manually | `alan2207/bulletproof-react`, `feature-sliced/documentation` |

---

## 2. The Canonical Unidirectional Data Flow (UDF) Contract

Every presentation module across all stacks MUST obey the UDF loop:

```text
   ┌───────────────────────────────────────────────┐
   │                                               ▼
[ UI / View ] ──── emits Intent / Event ────► [ State Holder ]
   ▲          (Stateless, Declarative)      (ViewModel/Store/BLoC)
   │                                               │
   └────────── observes immutable UiState ─────────┘
                         ▲
                         │ Domain Models / Result<T, DomainError>
                  [ Domain / Data ]
```

### Rule 1: Eliminate "Boolean Soup" (Make Illegal States Unrepresentable)

**Anti-Pattern (Boolean Soup — allows `2^4 = 16` states, 12 of which are bugs!):**
```kotlin
// BAD: Can isLoading=true AND error != null AND items.isNotEmpty() happen? Yes, by accident!
data class FeedUiState(
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val items: List<Article> = emptyList()
)
```

**Gold-Standard Pattern (Algebraic Data Types / Sealed State):**
```kotlin
// GOOD: Mutually exclusive screen states + explicit refresh flag inside Content
sealed interface FeedUiState {
    data object Loading : FeedUiState
    data class Error(val reason: UiError, val canRetry: Boolean) : FeedUiState
    data class Content(
        val items: ImmutableList<ArticleUiModel>,
        val isRefreshing: Boolean = false,
        val activeFilter: FeedFilter = FeedFilter.ALL,
    ) : FeedUiState
}
```
*(In TypeScript: discriminated union `{ status: 'loading' } | { status: 'error'; error: UiError } | { status: 'content'; items: readonly Article[] }`. In Dart: `sealed class FeedState` or `@freezed`. In Swift: `enum FeedState: Equatable`.)*

### Rule 2: Separate Persistent `UiState` from One-Off `Effect` (or Consume-Once State)

- **Persistent State (`UiState`)**: Survives screen rotation, tab switches, and re-renders (e.g., list items, form inputs, dialog visibility, inline field validation errors).
- **Transient Side Effects (`UiEffect` / `Channel`)**: Trigger-once actions like navigating to an external URL, triggering haptic feedback, or showing an ephemeral toast/snackbar.
  - Note: Per `android/nowinandroid` & Google's official guidance, **navigation driven by data state** or **snackbar messages modeled in `UiState` with an explicit `onMessageShown(id)` acknowledgement callback** guarantees zero lost events even if the UI lifecycle pauses mid-flight! If using an `Effect` channel, always use a **buffered `Channel` collected with lifecycle awareness** (never `SharedFlow(replay = 0)` which drops events during configuration changes!).

### Rule 3: Dumb Views, Framework-Free State Holders

- **UI Components (`@Composable`, `SwiftUI View`, `Flutter Widget`, `React Component`)**:
  - Render `UiState` and forward lambdas (`onIntent: (CheckoutIntent) -> Unit`).
  - Pass **primitive values or `UiState` slices**, NOT the entire `ViewModel`, into reusable child components and Previews/Storybooks! This makes every screen 100% previewable in `@Preview` / `#Preview` / Storybook without DI setup.
- **State Holders (`ViewModel`, `BLoC`, `Reducer`, `Store`)**:
  - NEVER reference `android.content.Context`, `android.view.View`, `BuildContext`, `UIViewController`, or `window/document` DOM APIs.
  - Convert string resources via a lightweight `UiText` wrapper (`StringResource(resId, args)` | `DynamicString(value)`) resolved at the UI edge.

### Rule 4: Lifecycle-Safe Collection & Structured Concurrency

- **Android / KMP**: Collect flows with `collectAsStateWithLifecycle()`. Expose cold repository flows converted via `.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), InitialState)`. Never launch untracked `GlobalScope` coroutines.
- **iOS / Swift**: Bind lifecycles with `.task { ... }` in SwiftUI (auto-cancels when view disappears). Mark UI state holders `@MainActor` (`@Observable` macro in modern Swift).
- **Flutter**: Dispose `StreamSubscription`s or rely on `BlocBuilder` / `ref.watch()` auto-disposal. Check `context.mounted` after every `await` inside widget callbacks.
- **Web (React)**: Pass `signal` (`AbortSignal`) inside `TanStack Query` `queryFn`. Never synchronize state via `useEffect(() => setDerivedState(...), [prop])` — compute derived values inline or with `useMemo`!
