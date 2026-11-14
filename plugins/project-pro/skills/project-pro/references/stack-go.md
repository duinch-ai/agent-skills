# Backend — Go (Golang) Reference Architecture

Ground every project layout, state boundary, API error contract, and dependency rule in these industry-standard open-source repositories.

---

## Famous Reference Repositories
1. **`evrone/go-clean-template`** *(Clean Architecture template for Go services: HTTP + gRPC + RabbitMQ + pgx)*
2. **`ThreeDotsLabs/wild-workouts-go-ddd-example`** *(Gold-standard Go DDD + Clean/Hexagonal Architecture + CQRS in production)*
3. **`uber-go/guide`** *(Uber's authoritative Go Style Guide — concurrency, error wrapping, interface rules)*

## Canonical Go Structure (`Clean / Hexagonal`)
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

## Go Non-Negotiables
- **Define interfaces on the consumer side** (`usecase` defines the exact 2-method `OrderRepo` interface it needs; `adapter/postgres` returns concrete `*PostgresOrderRepo` — *"Accept interfaces, return structs"*).
- Propagate `context.Context` as the first parameter across all I/O and usecase boundaries; wrap errors with `fmt.Errorf("save order %s: %w", id, err)` and inspect via `errors.Is` / `errors.As`.
