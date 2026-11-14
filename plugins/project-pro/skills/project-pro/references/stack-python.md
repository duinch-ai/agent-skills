# Backend — Python (FastAPI / Async Services) Reference Architecture

Ground every project layout, state boundary, API error contract, and dependency rule in these industry-standard open-source repositories.

---

## Famous Reference Repositories
1. **`zhanymkanov/fastapi-best-practices`** *(12k+ stars — Inspired by Netflix's `Dispatch` architecture)*
   - **Learn from it**: Domain/module-first package structure (`src/auth/`, `src/orders/`), Pydantic boundary discipline, async SQLAlchemy dependency patterns, avoiding blocking calls in async routes.
2. **`cosmicpython/code`** *(Architecture Patterns with Python — O'Reilly DDD, Repository, Unit of Work, Message Bus)*
   - **Learn from it**: Pure Python Domain model completely decoupled from SQLAlchemy ORM, explicit `UnitOfWork` context manager for atomic transactions, fake repositories for lightning-fast tests.
3. **`fastapi/full-stack-fastapi-template`** *(Official Tiangolo FastAPI + Pydantic v2 + Alembic + Pytest + Ruff template)*

## Canonical Python Structure
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

## Python Non-Negotiables
- Enforce `ruff` + `mypy --strict` (or `pyright`) + `import-linter` contracts in `pyproject.toml`.
- Never run synchronous I/O (`requests`, `time.sleep`, CPU-heavy loops) inside `async def` endpoints without offloading or using async clients (`httpx.AsyncClient`).
