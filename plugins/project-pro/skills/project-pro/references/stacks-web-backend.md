# Web Frontend & Backend Reference Architectures (React/Next/Vue, Python, Go, NestJS)

Ground every project layout, state boundary, API error contract, and dependency rule in these industry-standard open-source repositories.

---

## 1. Web Frontend (React, Next.js, TypeScript, Vue)

### Famous Reference Repositories
1. **`alan2207/bulletproof-react`** *(30k+ stars — Gold-standard scalable React/Next.js Feature-Based Architecture)*
   - **Learn from it**: Strict unidirectional codebase imports (`shared/components -> features -> app`), separating `api/` (TanStack Query hooks) from `components/` and local stores inside each feature, `eslint-plugin-boundaries` enforcement.
2. **`feature-sliced/documentation`** *(Feature-Sliced Design — FSD)*
   - **Learn from it**: Strict 7-layer hierarchy (`app` → `pages` → `widgets` → `features` → `entities` → `shared`), public API `index.ts` barrel per slice, zero cross-imports at the same layer.
3. **`antfu/vitesse`** *(Anthony Fu's canonical Vue 3 + Vite + Pinia + TypeScript starter)*

### Canonical Web Structure (`Bulletproof Feature-First` — React / Next.js)
```text
src/
├── app/                           # Routes/Pages, Root Providers, Composition Root ONLY (thin routing!)
├── features/                      # Self-contained domain/product slices
│   └── orders/
│       ├── api/                   # TanStack Query queries/mutations + Zod DTO schemas
│       ├── components/            # Feature-scoped UI components
│       ├── hooks/                 # Feature-scoped view logic hooks
│       ├── stores/                # Scoped client UI state (Zustand) — ONLY if needed
│       ├── types/                 # Domain/Feature TypeScript interfaces
│       └── index.ts               # Explicit Public API (other layers import ONLY from index.ts!)
├── components/ (or shared/ui/)    # Stateless Design System primitives (Button, Dialog, Table)
├── lib/                           # Configured HTTP client (ky/axios/fetch), queryClient, auth, logger
├── hooks/                         # Generic framework-agnostic hooks
└── types/                         # Shared base types & Result<T, AppError>
```

### Web Frontend Non-Negotiables
- **Never copy Server State into Client Global Stores**: API data belongs in `TanStack Query` / `SWR` / React Server Components; `Zustand` / `Pinia` is strictly for client-side ephemeral UI state (sidebar open, multi-step wizard draft, canvas selection).
- **Enforce unidirectional imports via ESLint**: `shared` cannot import `features`; `features/A` cannot reach into `features/B/internal` (compose features up at the `app/pages` layer instead!).
- Validate untrusted external API payloads & environment variables at the boundary using **Zod** / **Valibot**.

---

## 2. Backend — Python (FastAPI / Async Services)

### Famous Reference Repositories
1. **`zhanymkanov/fastapi-best-practices`** *(12k+ stars — Inspired by Netflix's `Dispatch` architecture)*
   - **Learn from it**: Domain/module-first package structure (`src/auth/`, `src/orders/`), Pydantic boundary discipline, async SQLAlchemy dependency patterns, avoiding blocking calls in async routes.
2. **`cosmicpython/code`** *(Architecture Patterns with Python — O'Reilly DDD, Repository, Unit of Work, Message Bus)*
   - **Learn from it**: Pure Python Domain model completely decoupled from SQLAlchemy ORM, explicit `UnitOfWork` context manager for atomic transactions, fake repositories for lightning-fast tests.
3. **`fastapi/full-stack-fastapi-template`** *(Official Tiangolo FastAPI + Pydantic v2 + Alembic + Pytest + Ruff template)*

### Canonical Python Structure
- **Option A (`vertical-slice` — `fastapi-best-practices` / Netflix Dispatch style)**:
```text
src/
├── main.py                        # FastAPI app factory, lifespan, RFC 9457 exception handlers
├── config.py                      # BaseSettings (pydantic-settings) validated at startup
├── database.py                    # AsyncEngine, async_sessionmaker
├── shared/                        # Pagination, AppError base classes, logging (structlog)
└── modules/
    └── billing/
        ├── router.py              # Thin HTTP endpoints, status codes, Depends()
        ├── schemas.py             # Request/Response Pydantic v2 DTOs
        ├── service.py             # Business use-cases / orchestration
        ├── models.py              # Domain / ORM models (split into domain/ + repository.py if Clean Arch)
        ├── dependencies.py        # Route guards & injected collaborators
        └── exceptions.py          # Module-specific domain errors
```
- **Option B (`clean` / `hexagonal` — `cosmicpython` style)**: Inside each module (or root), separate `domain/` (pure dataclasses/entities + abstract `Repository` Protocol + `UnitOfWork` Protocol), `application/` (use-case services), `adapters/` (SQLAlchemy repos, Redis, external HTTP clients), and `entrypoints/` (FastAPI routers, CLI, Celery/TaskIQ workers).

### Python Non-Negotiables
- Enforce `ruff` + `mypy --strict` (or `pyright`) + `import-linter` contracts in `pyproject.toml`.
- Never run synchronous I/O (`requests`, `time.sleep`, CPU-heavy loops) inside `async def` endpoints without offloading or using async clients (`httpx.AsyncClient`).

---

## 3. Backend — Go (Golang)

### Famous Reference Repositories
1. **`evrone/go-clean-template`** *(Clean Architecture template for Go services: HTTP + gRPC + RabbitMQ + pgx)*
2. **`ThreeDotsLabs/wild-workouts-go-ddd-example`** *(Gold-standard Go DDD + Clean/Hexagonal Architecture + CQRS in production)*
3. **`uber-go/guide`** *(Uber's authoritative Go Style Guide — concurrency, error wrapping, interface rules)*

### Canonical Go Structure (`Clean / Hexagonal`)
```text
project-root/
├── cmd/
│   └── api/main.go                # Tiny entrypoint: load config, wire dependencies, graceful shutdown
├── internal/                      # Compiler-enforced private boundary!
│   ├── domain/                    # Pure Go entities, value objects, sentinel/typed domain errors
│   │   └── order/
│   ├── usecase/ (or app/)         # Business orchestration; defines narrow consumer-side interfaces!
│   ├── adapter/
│   │   ├── postgres/              # pgx / sqlc repository implementations (no ORM magic!)
│   │   └── external/              # Outbound HTTP/gRPC/Queue clients
│   └── controller/
│       └── http/                  # chi/echo/gin/stdlib mux handlers, DTOs, RFC 9457 middleware
├── migrations/                    # SQL schema migrations
└── pkg/                           # Strictly generic utilities safe for external import (keep minimal!)
```

### Go Non-Negotiables
- **Define interfaces on the consumer side** (`usecase` defines the exact 2-method `OrderRepo` interface it needs; `adapter/postgres` returns concrete `*PostgresOrderRepo` — *"Accept interfaces, return structs"*).
- Propagate `context.Context` as the first parameter across all I/O and usecase boundaries; wrap errors with `fmt.Errorf("save order %s: %w", id, err)` and inspect via `errors.Is` / `errors.As`.

---

## 4. Backend — Node.js / TypeScript / NestJS

### Famous Reference Repositories
1. **`Sairyss/domain-driven-hexagon`** *(13k+ stars — Comprehensive DDD + Hexagonal + Clean Architecture + CQRS in TypeScript/NestJS)*
2. **`goldbergyoni/nodebestpractices`** *(100k+ stars — Canonical Node.js production architecture, error handling, testing & security checklist)*

### Canonical NestJS / TypeScript Hexagonal Structure
```text
src/
├── main.ts                        # Bootstrap, global pipes, ProblemDetails exception filter
├── shared/                        # Result<T, E>, Entity/AggregateRoot/ValueObject base, Env schema (Zod)
└── modules/
    └── wallet/
        ├── domain/                # Wallet aggregate, Money value object, WalletErrors, WalletRepository.port.ts
        ├── application/           # Commands/Queries or UseCases (pure orchestration, injected via Symbol token)
        ├── infrastructure/        # Prisma/Drizzle WalletRepository adapter, *OrmEntity, WalletMapper
        └── presentation/          # WalletHttpController, Request/Response DTOs (zod/class-validator)
```
