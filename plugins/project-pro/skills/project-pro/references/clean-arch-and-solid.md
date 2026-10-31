# Clean Architecture, SOLID, Pragmatic DRY & Coding Conventions

## 1. The Dependency Rule & Pragmatic Sizing

Source code dependencies **must point inward** toward higher-level policy:

```text
[ Presentation / UI / API Controllers ]
                  │
                  ▼
     [ Domain (Pure Business Policy) ]
                  ▲
                  │
[ Data / Infrastructure (DB, HTTP, SDKs) ]
```

### Proportional Architecture (KISS + YAGNI Meets Clean Arch)

Do **not** apply heavy enterprise ceremony blindly to tiny scripts. Match structure to system lifespan:

| Project Tier | Recommended Structure | UseCase Rule |
|--------------|-----------------------|--------------|
| **Tier 1: CLI / Utility (< 1k LOC)** | Clean modular files (`cli`, `core`, `adapters`) | Functions/services in `core`; no empty interfaces |
| **Tier 2: Standard App / Service** | **Feature-First** slices (`features/<name>/{domain,data,presentation}`) + `core/` | Create UseCases when combining multiple repos, enforcing business invariants, or reusing across ViewModels/handlers; avoid meaningless 3-line pass-through wrappers unless team convention mandates uniform entrypoints |
| **Tier 3: Multi-Team / Large Scale** | **Multi-Module / Workspace Packages** (`:feature:*`, `:core:domain`, `:core:data`, `:core:network`, `:core:database`, `:core:ui`) | Enforced by build-system visibility (`internal` modifiers, separate Gradle/SPM/pnpm/Go modules) |

---

## 2. Layer Contracts & Model Isolation ("False DRY" Prevention)

One of the deadliest mistakes in codebases is **False DRY**: reusing a single model class across API serialization, Database persistence, Domain logic, and UI rendering because "the fields look 85% identical right now."

**Why False DRY fails:**
- Adding `@JsonNames` / `@SerialName` / `@ColumnInfo` pollutes Domain with framework libraries.
- An API field rename silently breaks local DB migrations or UI screens.
- UI-only transient flags (`isExpanded`, `formattedPrice`) leak into DB schemas.

**Canonical Model Separation:**
1. **`*Dto` / `*Response` / `*Request` (Data - Remote)**: Mirrors wire JSON/Protobuf contract (`nullable` defensive fields, snake_case annotations).
2. **`*Entity` / `*Record` (Data - Local)**: Mirrors SQL/NoSQL table schema, foreign keys, indexes.
3. **Domain Model (`User`, `Order`, `Money`) (Domain)**: Pure, non-null valid invariants, value objects (`Email`, `OrderId`), rich domain methods (`order.canCancel()`).
4. **`*UiState` / `*UiModel` (Presentation)**: Pre-formatted, immutable, ready-to-render values for views.

**Bridge layers with pure, stateless Mapper functions/extensions:**
- `UserDto.toDomain(): User` (inside `data/mapper/`)
- `UserDto.toEntity(): UserEntity` (inside `data/mapper/`)
- `UserEntity.toDomain(): User` (inside `data/mapper/`)
- `User.toUiModel(): UserUiModel` (inside `presentation/mapper/`)

---

## 3. Actionable SOLID Checklist

### S — Single Responsibility Principle (SRP) & Anti-God-File Lock
*A module should be responsible to one, and only one, actor / reason to change.*
- **Check**: Can you describe the class's responsibility in one short sentence without using the word **"and"**?
- **One File = One Primary Responsibility**:
  - Never dump `Dto` + `Mapper` + `RepositoryImpl` into one file.
  - Never dump `UiState`/`Intent` + `ViewModel`/`Reducer` + `Screen` + `Sub-components` into one file; split reusable sub-views into `components/` once a screen passes ~200 lines.
- **Hard Thresholds** *(enforced by `project_pro.py audit` & Git `pre-commit`, excluding generated files `*.g.dart`, `*.freezed.dart`, `*.gen.ts`, `*_pb2.py`, `*.pb.go`)*:
  - File > **300 LOC** → `[WARN]` Stop adding code; split collaborator or UI component.
  - File > **450 LOC** → **`[FAIL]` Hard Block**; must decompose before commit/completion.
  - Function > **30–35 LOC** or > **3 levels of indentation** → Extract helper functions with intention-revealing names.
  - Constructor > **5–6 injected dependencies** → Orchestrating too much; extract a facade or sub-collaborator.

### O — Open/Closed Principle (OCP)
*Open for extension, closed for modification.*
- Replace recurring `when` / `switch` / `if-else` type-dispatch chains with:
  - **Sealed interfaces + exhaustive pattern matching** (when types are closed and operations vary), OR
  - **Strategy / Handler Registry** injected via DI (e.g., `Map<PaymentMethod, PaymentProcessor>` / multi-bindings when new types are added frequently).

### L — Liskov Substitution Principle (LSP)
*Subtypes must be substitutable for their base types without altering correctness.*
- **Never** implement an interface method by throwing `UnsupportedOperationException` / `NotImplementedError` or silently doing nothing when a postcondition is promised.
- If `ReadOnlyCache` cannot implement `put()`, split `Cache` into `CacheReader` and `CacheWriter` (ISP).

### I — Interface Segregation Principle (ISP)
*Clients should not be forced to depend on methods they do not use.*
- Ban `GodRepository` interfaces with 25+ unrelated methods.
- Define narrow **ports** tailored to the consumer (`AuthSessionProvider`, `ProfileUpdater`, `InvoiceExporter`). Small interfaces make unit testing with lightweight **Fakes** effortless (prefer Fakes over brittle Mock frameworks!).

### D — Dependency Inversion Principle (DIP)
*High-level modules own the abstractions; low-level modules implement them.*
- Interfaces belong in the **consumer/domain layer**, NOT alongside the low-level implementation (e.g., `UserRepository` lives in `domain/repository/`, while `OfflineFirstUserRepository` lives in `data/repository/`).
- Always use **Constructor Injection**. Ban hidden `Singleton.getInstance()` or global service locator calls inside Domain/Presentation logic (makes testing non-deterministic).

---

## 4. Pragmatic DRY: Rule of Three & AHA ("Avoid Hasty Abstractions")

> *"Duplication is far cheaper than the wrong abstraction."* — Sandi Metz

1. **1st & 2nd occurrence**: Write clean, explicit code. Do not prematurely merge two workflows that merely look superficially similar.
2. **3rd occurrence**: Extract shared abstraction **only if** all three share the same **semantic business rule** (they must change together for the same reason).
3. **Red Flag of a Bad Abstraction**: A shared helper function/component that grows boolean parameters (`if (isCheckoutFlow) ... else if (isAdminFlow) ...`). Split it back apart and compose smaller primitives instead!

---

## 5. Universal Coding Rules & Conventions

1. **Immutability by Default**:
   - Default to `val` (Kotlin), `let` + `struct` (Swift), `final` (Dart), `const` + `readonly` (TS), `@dataclass(frozen=True)` / `Pydantic ConfigDict(frozen=True)` (Python). Mutate state only inside tightly scoped reducers/builders.
2. **Guard Clauses Over Arrow Code**:
   - Validate preconditions at the top of functions and return early (`if (!user.isActive) return Err(InactiveUser)`). Never nest happy-path logic inside 4 levels of `if/else`.
3. **Typed Error Handling at Boundaries**:
   - **Data Layer** catches low-level exceptions (`IOException`, `HttpException`, `SQLiteException`, `TimeoutError`), logs technical context, and translates them into domain-meaningful failures (`NetworkUnavailable`, `Unauthorized`, `RateLimited`, `ValidationFailed`).
   - **Domain & Presentation** operate on explicit `Result<T, DomainError>` / `Either` / typed exceptions — never raw HTTP status codes or SQL errors.
   - **Zero Silent Swallowing**: Never write `catch (e) {}` without rethrowing, returning a typed failure, or explicitly handling cancellation (`CancellationException` in Kotlin Coroutines / `asyncio.CancelledError` in Python **MUST ALWAYS BE RETHROWN**!).
4. **Naming Precision**:
   - **Booleans**: Prefix with `is`, `has`, `can`, `should` (`isLoading`, `hasValidToken`, `canRetry`). Never negate boolean names (`isNotDisabled` → `isEnabled`).
   - **Functions**: Action verbs (`calculateTotal`, `syncBookmarks`, `observeUserProfile` for streams vs `getUserProfile` for one-shot).
   - **Constants**: Named semantic constants (`MAX_LOGIN_ATTEMPTS = 5`, `TOKEN_REFRESH_THRESHOLD_MS = 30_000`), zero magic literals scattered in logic.
5. **Testing Pyramid Alignment**:
   - **Domain Unit Tests (Fastest, 100% pure)**: Test UseCases, Entities, Value Objects, Reducers in milliseconds with Fakes.
   - **Data Integration Tests**: Test Repository offline-first sync, SQL queries (in-memory DB / Testcontainers), and DTO serialization contracts.
   - **Presentation State Tests**: Assert exact sequence of `UiState` emissions (`Turbine` in Kotlin, `bloc_test` in Dart, `TestStore` in Swift TCA, `Vitest` in TS) given `Intent` inputs.
