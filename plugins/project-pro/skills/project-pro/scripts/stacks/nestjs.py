"""Stack data for `nestjs`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
    "label": "Backend Node.js / TypeScript / NestJS",
    "recommended_arch": "hexagonal",
    "recommended_pattern": "cqrs",
    "patterns": [
        ("cqrs", "DDD + Hexagonal Ports & Adapters + CQRS — ref: Sairyss/domain-driven-hexagon"),
        ("service-repo", "Modular Clean Controller -> UseCase -> Repository — ref: goldbergyoni/nodebestpractices"),
    ],
    "repos": [
        {"repo": "Sairyss/domain-driven-hexagon", "url": "https://github.com/Sairyss/domain-driven-hexagon", "why": "Gold-standard TypeScript/NestJS DDD, Hexagonal Ports/Adapters, Value Objects, Result monad & Mapper separation."},
        {"repo": "goldbergyoni/nodebestpractices", "url": "https://github.com/goldbergyoni/nodebestpractices", "why": "Authoritative Node.js production architecture, RFC 9457 error handling, testing & observability practices."},
    ],
    "commands": {
        "build": "npm run build",
        "test_all": "npm run test",
        "test_single": "npx jest src/modules/<module>/<file>.spec.ts",
        "lint": "npm run lint && npx tsc --noEmit",
        "sec_audit": "npm audit --audit-level=high",
    },
    "boundary_tool": "TypeScript strict + eslint-plugin-boundaries / dependency-cruiser",
    "domain_forbidden_imports": ["@nestjs/common", "@prisma/client", "typeorm", "drizzle-orm", "axios", "express"],
    "scaffold_dirs": {
        "hexagonal": ["src/shared/domain", "src/shared/core", "src/modules/users/domain", "src/modules/users/application", "src/modules/users/infrastructure", "src/modules/users/presentation", "test"],
    },
}

I18N: dict[str, Any] = {
    "standard": "nestjs-i18n + JSON/YAML catalogs + Accept-Language Resolver",
    "tooling": "I18nService.translate(\"common.KEY\", { lang }) + @I18nLang() lang: string",
    "guidance": "Store translations in src/i18n/{en,vi}/*.json. Configure I18nModule with AcceptLanguageResolver and HeaderResolver. Inject I18nService into controllers and exception filters. Ban hardcoded response strings.",
    "dirs": ["src/i18n/en", "src/i18n/vi"],
    "sample_files": {
        "src/i18n/en/common.json": '{\n  "confirm": "Confirm",\n  "cancel": "Cancel"\n}\n',
        "src/i18n/vi/common.json": '{\n  "confirm": "Xác nhận",\n  "cancel": "Hủy"\n}\n',
    },
}
