"""Stack data for `web`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
    "label": "Web Frontend (React / Next.js / Vue / TypeScript)",
    "recommended_arch": "vertical-slice",
    "recommended_pattern": "query-zustand",
    "patterns": [
        ("query-zustand", "Server/Client Split (TanStack Query + Zustand Feature Slices) — ref: alan2207/bulletproof-react"),
        ("fsd", "Feature-Sliced Design (Strict 7-Layer FSD + Public index.ts) — ref: feature-sliced/documentation"),
        ("pinia-udf", "Vue 3 Composition API + Pinia Feature Stores — ref: antfu/vitesse"),
    ],
    "repos": [
        {"repo": "alan2207/bulletproof-react", "url": "https://github.com/alan2207/bulletproof-react", "why": "Canonical scalable React/Next.js architecture with unidirectional feature slices & eslint-plugin-boundaries."},
        {"repo": "feature-sliced/documentation", "url": "https://github.com/feature-sliced/documentation", "why": "Feature-Sliced Design (FSD) strict layer hierarchy (app -> pages -> widgets -> features -> entities -> shared)."},
        {"repo": "antfu/vitesse", "url": "https://github.com/antfu/vitesse", "why": "Clean, idiomatic Vue 3 + TypeScript + Pinia + Vitest reference setup."},
    ],
    "commands": {
        "build": "npm run build",
        "test_all": "npm run test",
        "test_single": "npx vitest run src/features/<feature>/<file>.test.ts",
        "lint": "npm run lint && npx tsc --noEmit",
        "sec_audit": "npm audit --audit-level=high",
    },
    "boundary_tool": "TypeScript strict + eslint-plugin-boundaries / dependency-cruiser",
    "domain_forbidden_imports": ["from 'react'", 'from "react"', "from 'next/", 'from "next/', "from 'axios'", 'from "axios"'],
    "scaffold_dirs": {
        "vertical-slice": [
            "src/app", "src/components/ui", "src/lib", "src/hooks", "src/types",
            "src/features/auth/api", "src/features/auth/components", "src/features/auth/hooks", "src/features/auth/types",
        ],
    },
}

I18N: dict[str, Any] = {
    "standard": "next-intl (Next.js App Router) or react-i18next (Vite/SPA) or vue-i18n",
    "tooling": "useTranslations(\"namespace\") / t(\"key\") + messages/*.json catalogs",
    "guidance": "Store translations in messages/en.json and messages/vi.json. In Next.js App Router, implement next-intl middleware for /[locale]/ routing and server component translations. Enforce type-safety via TypeScript declaration files.",
    "dirs": ["messages"],
    "sample_files": {
        "messages/en.json": '{\n  "common": {\n    "confirm": "Confirm",\n    "cancel": "Cancel"\n  }\n}\n',
        "messages/vi.json": '{\n  "common": {\n    "confirm": "Xác nhận",\n    "cancel": "Hủy"\n  }\n}\n',
    },
}
