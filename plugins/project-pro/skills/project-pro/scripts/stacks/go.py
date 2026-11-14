"""Stack data for `go`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
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
    "boundary_config": "go-depguard",
    "scaffold_dirs": {
        "hexagonal": ["cmd/api", "internal/domain", "internal/usecase", "internal/adapter/postgres", "internal/adapter/external", "internal/controller/http", "migrations"],
    },
}

I18N: dict[str, Any] = {
    "standard": "nicksnyder/go-i18n/v2 + golang.org/x/text/language",
    "tooling": "i18n.Bundle + i18n.Localizer + Localize(&i18n.LocalizeConfig{MessageID: \"key\"})",
    "guidance": "Load JSON/TOML message catalogs from locales/active.en.json and locales/active.vi.json into an i18n.Bundle at startup. Inject an i18n.Localizer into each request context based on Accept-Language header.",
    "dirs": ["locales"],
    "sample_files": {
        "locales/active.en.json": '{\n  "common.confirm": "Confirm",\n  "common.cancel": "Cancel"\n}\n',
        "locales/active.vi.json": '{\n  "common.confirm": "Xác nhận",\n  "common.cancel": "Hủy"\n}\n',
    },
}
