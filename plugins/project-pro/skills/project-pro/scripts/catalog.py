"""Curated reference repositories, architecture presets, and stack metadata for project-pro."""

from __future__ import annotations

from typing import Any

STACK_CATALOG: dict[str, dict[str, Any]] = {
    "android": {
        "label": "Android (Kotlin + Jetpack Compose)",
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvi",
        "patterns": [
            ("mvi", "MVI Strict UDF (Sealed UiState + Intent + Effect) — ref: chrisbanes/tivi, slackhq/circuit"),
            ("mvvm-udf", "MVVM + UDF (Single StateFlow<UiState> + Action methods) — ref: android/nowinandroid"),
        ],
        "repos": [
            {"repo": "android/nowinandroid", "url": "https://github.com/android/nowinandroid", "why": "Official Google multi-module Compose reference (:feature:*, :core:domain/data/model/network/database/designsystem), offline-first Flows, Fakes over Mocks."},
            {"repo": "chrisbanes/tivi", "url": "https://github.com/chrisbanes/tivi", "why": "Strict UDF Compose screens, clean paging/sync separation, modular architecture."},
            {"repo": "slackhq/circuit", "url": "https://github.com/slackhq/circuit", "why": "Compose-native Presenter + Ui MVI split with decoupled type-safe navigation."},
            {"repo": "android/architecture-samples", "url": "https://github.com/android/architecture-samples", "why": "Pragmatic single-module Clean/Layered Compose starter."},
        ],
        "commands": {
            "build": "./gradlew assembleDebug",
            "test_all": "./gradlew testDebugUnitTest",
            "test_single": "./gradlew :feature:<name>:testDebugUnitTest --tests '*<ClassName>*'",
            "lint": "./gradlew ktlintCheck detekt lintDebug",
            "sec_audit": "./gradlew dependencyCheckAnalyze",
        },
        "boundary_tool": "Gradle module visibility (:core:domain pure Kotlin/JVM) + Konsist / Detekt",
        "domain_forbidden_imports": ["android.content.", "android.view.", "androidx.compose.", "androidx.room.", "retrofit2.", "okhttp3.", "io.ktor."],
        "scaffold_dirs": {
            "clean": [
                "app/src/main/kotlin/core/common", "app/src/main/kotlin/core/network",
                "app/src/main/kotlin/core/database", "app/src/main/kotlin/core/designsystem",
                "app/src/main/kotlin/features/home/domain/model", "app/src/main/kotlin/features/home/domain/repository",
                "app/src/main/kotlin/features/home/domain/usecase", "app/src/main/kotlin/features/home/data/remote",
                "app/src/main/kotlin/features/home/data/local", "app/src/main/kotlin/features/home/data/mapper",
                "app/src/main/kotlin/features/home/data/repository", "app/src/main/kotlin/features/home/presentation",
            ],
            "modular-clean": [
                "build-logic/convention", "app/src/main/kotlin", "core/model/src/main/kotlin",
                "core/common/src/main/kotlin", "core/domain/src/main/kotlin", "core/data/src/main/kotlin",
                "core/network/src/main/kotlin", "core/database/src/main/kotlin", "core/designsystem/src/main/kotlin",
                "core/testing/src/main/kotlin", "feature/home/api/src/main/kotlin", "feature/home/impl/src/main/kotlin",
            ],
        },
    },
    "kmp": {
        "label": "Kotlin Multiplatform / Compose Multiplatform (KMP / CMP)",
        "recommended_arch": "clean",
        "recommended_pattern": "mvi",
        "patterns": [
            ("mvi", "MVI Strict UDF (Sealed State + Action/Intent + One-off Channel) — ref: chrisbanes/tivi, CMP-Bookpedia"),
            ("mvvm-udf", "MVVM + Shared ViewModel StateFlow<UiState> — ref: JetBrains/kotlinconf-app"),
            ("decompose", "Decompose Lifecycle Components + MVIKotlin — ref: arkivanov/Decompose"),
        ],
        "repos": [
            {"repo": "chrisbanes/tivi", "url": "https://github.com/chrisbanes/tivi", "why": "Production KMP + Compose Multiplatform (Android, iOS, Desktop) with strict UDF & modular DI."},
            {"repo": "JetBrains/kotlinconf-app", "url": "https://github.com/JetBrains/kotlinconf-app", "why": "Official JetBrains CMP app using Ktor, Koin, Compose Navigation & shared resources."},
            {"repo": "touchlab/KaMPKit", "url": "https://github.com/touchlab/KaMPKit", "why": "Touchlab KMP architecture foundation, SKIE Swift interop, SQLDelight & Coroutines testing."},
            {"repo": "philipplackner/CMP-Bookpedia", "url": "https://github.com/philipplackner/CMP-Bookpedia", "why": "Clean Feature-First 3-layer CMP reference (DataError/Result, Ktor safeCall, Room KMP, Koin)."},
        ],
        "commands": {
            "build": "./gradlew :composeApp:assembleDebug",
            "test_all": "./gradlew allTests",
            "test_single": "./gradlew :composeApp:desktopTest --tests '*<ClassName>*'",
            "lint": "./gradlew ktlintCheck detekt",
            "sec_audit": "./gradlew check",
        },
        "boundary_tool": "KMP sourceSet isolation + Konsist architecture tests in commonTest",
        "domain_forbidden_imports": ["androidx.compose.", "androidx.room.", "io.ktor.", "android.content.", "platform.UIKit."],
        "scaffold_dirs": {
            "clean": [
                "composeApp/src/commonMain/kotlin/app", "composeApp/src/commonMain/kotlin/core/domain",
                "composeApp/src/commonMain/kotlin/core/data", "composeApp/src/commonMain/kotlin/core/presentation",
                "composeApp/src/commonMain/kotlin/features/home/domain", "composeApp/src/commonMain/kotlin/features/home/data",
                "composeApp/src/commonMain/kotlin/features/home/presentation", "composeApp/src/androidMain/kotlin",
                "composeApp/src/iosMain/kotlin", "composeApp/src/commonTest/kotlin",
            ],
        },
    },
    "flutter": {
        "label": "Flutter / Dart",
        "recommended_arch": "clean",
        "recommended_pattern": "bloc",
        "patterns": [
            ("bloc", "BLoC / Cubit + Sealed/Freezed UDF State — ref: felangel/bloc, VGVentures/very_good_cli"),
            ("riverpod", "Riverpod AsyncNotifier Feature-First — ref: bizz84/starter_architecture_flutter_firebase"),
        ],
        "repos": [
            {"repo": "bizz84/starter_architecture_flutter_firebase", "url": "https://github.com/bizz84/starter_architecture_flutter_firebase", "why": "Andrea Bizzotto's canonical Feature-First Flutter Riverpod architecture."},
            {"repo": "felangel/bloc", "url": "https://github.com/felangel/bloc", "why": "Official BLoC & Cubit reference apps with clean package separation & bloc_test."},
            {"repo": "VGVentures/very_good_cli", "url": "https://github.com/VGVentures/very_good_cli", "why": "Enterprise Flutter conventions, flavors, l10n, very_good_analysis lint rules."},
        ],
        "commands": {
            "build": "flutter build apk --debug",
            "test_all": "flutter test",
            "test_single": "flutter test test/features/<feature>/<file>_test.dart",
            "lint": "dart format --output=none --set-exit-if-changed . && flutter analyze",
            "sec_audit": "dart pub outdated",
        },
        "boundary_tool": "very_good_analysis (analysis_options.yaml strict mode) + Dart sub-packages",
        "domain_forbidden_imports": ["package:flutter/material.dart", "package:flutter/cupertino.dart", "package:flutter/widgets.dart", "package:dio/", "package:http/", "package:drift/", "package:go_router/"],
        "scaffold_dirs": {
            "clean": [
                "lib/app", "lib/core/error", "lib/core/network", "lib/core/storage", "lib/core/theme",
                "lib/features/home/domain/entities", "lib/features/home/domain/repositories", "lib/features/home/domain/usecases",
                "lib/features/home/data/datasources", "lib/features/home/data/models", "lib/features/home/data/repositories",
                "lib/features/home/presentation/bloc", "lib/features/home/presentation/pages", "lib/features/home/presentation/widgets",
                "test/features/home",
            ],
        },
    },
    "ios": {
        "label": "iOS / Swift (SwiftUI + Swift 6 Concurrency)",
        "recommended_arch": "modular-clean",
        "recommended_pattern": "tca",
        "patterns": [
            ("tca", "TCA (The Composable Architecture @Reducer + @ObservableState) — ref: pointfreeco/swift-composable-architecture"),
            ("mvvm-udf", "MVVM + @Observable @MainActor UDF + Local SPM — ref: nalexn/clean-architecture-swiftui"),
        ],
        "repos": [
            {"repo": "pointfreeco/swift-composable-architecture", "url": "https://github.com/pointfreeco/swift-composable-architecture", "why": "Gold-standard SwiftUI UDF architecture (Examples/SyncUps & CaseStudies), @Dependency DI, exhaustive TestStore."},
            {"repo": "nalexn/clean-architecture-swiftui", "url": "https://github.com/nalexn/clean-architecture-swiftui", "why": "Clean Architecture in SwiftUI with pure Domain/Interactor/Repository boundaries."},
            {"repo": "kudoleh/iOS-Clean-Architecture-MVVM", "url": "https://github.com/kudoleh/iOS-Clean-Architecture-MVVM", "why": "Classic modular iOS Clean Architecture + MVVM + Flow Coordinator separation."},
        ],
        "commands": {
            "build": "swift build",
            "test_all": "swift test",
            "test_single": "swift test --filter <TargetTests>.<TestCase>",
            "lint": "swiftlint lint --strict && swift-format lint -r Packages",
            "sec_audit": "swift package show-dependencies",
        },
        "boundary_tool": "Local Swift Package Manager (Package.swift target dependencies) + SwiftLint",
        "domain_forbidden_imports": ["import SwiftUI", "import UIKit", "import SwiftData", "import CoreData", "import Alamofire"],
        "scaffold_dirs": {
            "modular-clean": [
                "App", "Packages/CoreDomain/Sources/CoreDomain", "Packages/CoreDomain/Tests/CoreDomainTests",
                "Packages/CoreData/Sources/CoreData", "Packages/CoreDesignSystem/Sources/CoreDesignSystem",
                "Packages/Features/HomeFeature/Sources/HomeFeature", "Packages/Features/HomeFeature/Tests/HomeFeatureTests",
            ],
        },
    },
    "web": {
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
    },
    "python": {
        "label": "Backend Python (FastAPI / Async / DDD)",
        "recommended_arch": "vertical-slice",
        "recommended_pattern": "service-repo",
        "patterns": [
            ("service-repo", "Domain-Module Router -> Service -> Repository — ref: zhanymkanov/fastapi-best-practices"),
            ("cqrs", "Hexagonal / DDD + Unit of Work + Pure Domain — ref: cosmicpython/code"),
        ],
        "repos": [
            {"repo": "zhanymkanov/fastapi-best-practices", "url": "https://github.com/zhanymkanov/fastapi-best-practices", "why": "Netflix Dispatch-inspired domain-module FastAPI structure, Pydantic v2 discipline, async DB best practices."},
            {"repo": "cosmicpython/code", "url": "https://github.com/cosmicpython/code", "why": "Architecture Patterns with Python (O'Reilly): pure Domain entities, Repository, UnitOfWork & Message Bus."},
            {"repo": "fastapi/full-stack-fastapi-template", "url": "https://github.com/fastapi/full-stack-fastapi-template", "why": "Official FastAPI + Pydantic v2 + Alembic + Pytest + Ruff production template."},
        ],
        "commands": {
            "build": "python3 -m compileall src",
            "test_all": "pytest",
            "test_single": "pytest tests/modules/<module>/test_<name>.py -k '<test_fn>'",
            "lint": "ruff check . && ruff format --check . && mypy --strict src",
            "sec_audit": "pip-audit",
        },
        "boundary_tool": "ruff + mypy --strict + import-linter (pyproject.toml layer contracts)",
        "domain_forbidden_imports": ["import fastapi", "from fastapi", "import sqlalchemy", "from sqlalchemy", "import httpx", "from httpx", "import requests"],
        "scaffold_dirs": {
            "vertical-slice": ["src/shared", "src/modules/health", "src/modules/users", "migrations", "tests/unit", "tests/integration"],
            "hexagonal": ["src/shared", "src/modules/users/domain", "src/modules/users/application", "src/modules/users/adapters", "src/modules/users/entrypoints", "migrations", "tests/unit", "tests/integration"],
        },
    },
    "go": {
        "label": "Backend Go (Golang Clean / Hexagonal)",
        "recommended_arch": "hexagonal",
        "recommended_pattern": "service-repo",
        "patterns": [
            ("service-repo", "Clean UseCase + Consumer-Owned Interfaces — ref: evrone/go-clean-template"),
            ("cqrs", "DDD + Clean/Hexagonal + CQRS — ref: ThreeDotsLabs/wild-workouts-go-ddd-example"),
        ],
        "repos": [
            {"repo": "evrone/go-clean-template", "url": "https://github.com/evrone/go-clean-template", "why": "Idiomatic Go Clean Architecture (cmd/, internal/entity, internal/usecase, internal/controller, internal/repo)."},
            {"repo": "ThreeDotsLabs/wild-workouts-go-ddd-example", "url": "https://github.com/ThreeDotsLabs/wild-workouts-go-ddd-example", "why": "Production Go DDD, Clean/Hexagonal boundaries, CQRS, zero ORM coupling."},
            {"repo": "uber-go/guide", "url": "https://github.com/uber-go/guide", "why": "Uber Go Style Guide: interface ownership, error wrapping, concurrency safety."},
        ],
        "commands": {
            "build": "go build ./...",
            "test_all": "go test -race ./...",
            "test_single": "go test -v -race ./internal/usecase/... -run Test<Name>",
            "lint": "golangci-lint run ./...",
            "sec_audit": "govulncheck ./...",
        },
        "boundary_tool": "Go compiler `internal/` boundary + golangci-lint (depguard)",
        "domain_forbidden_imports": ['"net/http"', '"database/sql"', '"github.com/jackc/pgx', '"github.com/gin-gonic/gin"', '"github.com/labstack/echo', '"gorm.io/gorm"'],
        "scaffold_dirs": {
            "hexagonal": ["cmd/api", "internal/domain", "internal/usecase", "internal/adapter/postgres", "internal/adapter/external", "internal/controller/http", "migrations"],
        },
    },
    "nestjs": {
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
    },
    "rust": {
        "label": "Rust (Cargo Workspace / Cross-Platform GUI & Core)",
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvi",
        "patterns": [
            ("mvi", "Strict UDF / Immediate Mode State Machine (App State + Message Enum + Update/View) — ref: emilk/egui, iced-rs/iced"),
            ("service-repo", "Clean Architecture / Hexagonal Ports & Adapters (Core Traits + Adapters) — ref: LukeMathWalker/zero-to-production"),
        ],
        "repos": [
            {"repo": "emilk/egui", "url": "https://github.com/emilk/egui", "why": "Immediate-mode GUI in pure Rust, cross-platform Desktop/Web/Wasm, zero-garbage state management."},
            {"repo": "iced-rs/iced", "url": "https://github.com/iced-rs/iced", "why": "Elm-inspired cross-platform GUI architecture with strict UDF, Command/Subscription, and clean View/Update split."},
            {"repo": "LukeMathWalker/zero-to-production", "url": "https://github.com/LukeMathWalker/zero-to-production", "why": "Production-grade Rust Clean Architecture, domain modelling, configuration, tracing, and integration tests."},
        ],
        "commands": {
            "build": "cargo build",
            "test_all": "cargo test --workspace",
            "test_single": "cargo test -p <crate> -- <test_name>",
            "lint": "cargo clippy --workspace -- -D warnings && cargo fmt --check",
            "sec_audit": "cargo audit",
        },
        "boundary_tool": "Cargo Workspace crate isolation (`manga-core` pure domain/ports, `manga-ui` presentation, `manga-switch` entrypoint) + cargo-deny",
        "domain_forbidden_imports": ["eframe", "egui", "sdl2", "winit"],
        "scaffold_dirs": {
            "modular-clean": [
                "crates/manga-core/src/models", "crates/manga-core/src/providers",
                "crates/manga-core/src/cache", "crates/manga-core/src/reader",
                "crates/manga-ui/src/views", "crates/manga-ui/src/widgets",
                "crates/manga-switch/src",
            ],
            "clean": [
                "crates/core/src/domain", "crates/core/src/ports", "crates/core/src/models",
                "crates/adapters/src/remote", "crates/adapters/src/storage",
                "crates/app/src/views", "crates/app/src/widgets",
            ],
        },
    },
}

ARCH_CHOICES: list[tuple[str, str]] = [
    ("clean", "Clean Architecture (3-Layer: Presentation -> Domain <- Data)"),
    ("modular-clean", "Modular Clean Architecture (Multi-module :feature:* + :core:*)"),
    ("vertical-slice", "Vertical Slice / Feature-First (Pragmatic feature slices, minimal ceremony)"),
    ("hexagonal", "Hexagonal / Ports & Adapters + DDD"),
    ("lightweight", "Lightweight Modular (KISS/YAGNI for CLI, scripts & small utilities)"),
]

FEATURE_CHOICES: list[tuple[str, str, bool]] = [
    ("solid-dry", "Core SOLID + Pragmatic DRY (AHA) + Layer Model Isolation + Anti-God-File (300/450 LOC)", True),
    ("typed-errors", "Typed Error Handling & Result Wrapper (Result<T, DomainError> / RFC 9457)", True),
    ("di-core", "Dependency Injection + Validated Env Config + Secret-Redacted Logging Base", True),
    ("network-storage", "Network Client (Auth/Retry Interceptors) + Local DB/Storage Repository Base", True),
    ("ui-nav", "Design System Tokens + Type-Safe Navigation (Client) / OpenAPI + Healthchecks (Backend)", True),
    ("arch-lint", "Strict Compiler Flags + Linter/Formatter + Architecture Boundary Tests", True),
    ("testing-ci", "Testing Harness (Fakes over Mocks + State/Service tests) + GitHub Actions CI", False),
]

AGENT_CHOICES: list[tuple[str, str, bool]] = [
    ("agents-root", "Universal Root & Execution Harness (AGENTS.md + execution-harness.md + security-gate.md + layer rules)", True),
    ("persistent-memory", "Cross-Session Memory & Codebase Map (.agents/CODEBASE_MAP.md + memory/active-plan.md + lessons.md)", True),
    ("claude-gemini", "Claude Code & Antigravity/Gemini Bridges (CLAUDE.md + GEMINI.md)", True),
    ("git-security-hooks", "Git Security & Quality Hooks (pre-commit, commit-msg, pre-push + .gitignore secret guard)", True),
    ("agent-runtime-hooks", "AI Agent Anti-Bypass Runtime Hooks (.agents/hooks.json + .claude/settings.json)", True),
    ("adr-docs", "Architecture Decision Record (docs/architecture/ADR-0001-architecture.md)", True),
    ("cursor-ide", "Cursor / Windsurf / Cline / Roo / DeepSeek Rules (.cursor/rules/*.mdc + .clinerules)", False),
]

SOURCE_EXTENSIONS = {".kt", ".kts", ".dart", ".swift", ".ts", ".tsx", ".js", ".jsx", ".vue", ".py", ".go", ".rs"}
IGNORE_DIRS = {
    ".git", ".githooks", ".agents", ".claude", ".cursor", ".idea", ".vscode", "node_modules", "build", ".gradle",
    ".dart_tool", ".build", "DerivedData", "dist", ".next", "__pycache__", ".venv", "venv", "vendor", "Pods", "target",
}
