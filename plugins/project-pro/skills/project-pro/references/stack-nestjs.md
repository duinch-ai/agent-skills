# Backend — Node.js / TypeScript / NestJS Reference Architecture

Ground every project layout, state boundary, API error contract, and dependency rule in these industry-standard open-source repositories.

---

## Famous Reference Repositories
1. **`Sairyss/domain-driven-hexagon`** *(13k+ stars — Comprehensive DDD + Hexagonal + Clean Architecture + CQRS in TypeScript/NestJS)*
2. **`goldbergyoni/nodebestpractices`** *(100k+ stars — Canonical Node.js production architecture, error handling, testing & security checklist)*

## Canonical NestJS / TypeScript Hexagonal Structure
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
