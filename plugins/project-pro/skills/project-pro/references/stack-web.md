# Web Frontend (React, Next.js, TypeScript, Vue) Reference Architecture

Ground every project layout, state boundary, API error contract, and dependency rule in these industry-standard open-source repositories.

---

## Famous Reference Repositories
1. **`alan2207/bulletproof-react`** *(30k+ stars — Gold-standard scalable React/Next.js Feature-Based Architecture)*
   - **Learn from it**: Strict unidirectional codebase imports (`shared/components -> features -> app`), separating `api/` (TanStack Query hooks) from `components/` and local stores inside each feature, `eslint-plugin-boundaries` enforcement.
2. **`feature-sliced/documentation`** *(Feature-Sliced Design — FSD)*
   - **Learn from it**: Strict 7-layer hierarchy (`app` → `pages` → `widgets` → `features` → `entities` → `shared`), public API `index.ts` barrel per slice, zero cross-imports at the same layer.
3. **`antfu/vitesse`** *(Anthony Fu's canonical Vue 3 + Vite + Pinia + TypeScript starter)*

## Canonical Web Structure (`Bulletproof Feature-First` — React / Next.js)
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

## Web Frontend Non-Negotiables
- **Never copy Server State into Client Global Stores**: API data belongs in `TanStack Query` / `SWR` / React Server Components; `Zustand` / `Pinia` is strictly for client-side ephemeral UI state (sidebar open, multi-step wizard draft, canvas selection).
- **Enforce unidirectional imports via ESLint**: `shared` cannot import `features`; `features/A` cannot reach into `features/B/internal` (compose features up at the `app/pages` layer instead!).
- Validate untrusted external API payloads & environment variables at the boundary using **Zod** / **Valibot**.
