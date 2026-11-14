"""Stack data for `python`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
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
    "boundary_config": "python-importlinter",
    "scaffold_dirs": {
        "vertical-slice": ["src/shared", "src/modules/health", "src/modules/users", "migrations", "tests/unit", "tests/integration"],
        "hexagonal": ["src/shared", "src/modules/users/domain", "src/modules/users/application", "src/modules/users/adapters", "src/modules/users/entrypoints", "migrations", "tests/unit", "tests/integration"],
    },
}

I18N: dict[str, Any] = {
    "standard": "GNU gettext + Babel (pybabel) + Accept-Language Middleware",
    "tooling": "gettext.gettext / _(\"translatable_text\") + Babel PO/MO catalogs",
    "guidance": "Configure Babel catalogs in locales/{en,vi}/LC_MESSAGES/. Resolve client locale from Accept-Language header via request middleware into contextvars. Wrap user-facing exception details and messages with _(...).",
    "dirs": ["locales/en/LC_MESSAGES", "locales/vi/LC_MESSAGES"],
    "sample_files": {
        "locales/en/LC_MESSAGES/messages.po": 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n"Language: en\\n"\n\nmsgid "common.confirm"\nmsgstr "Confirm"\n\nmsgid "common.cancel"\nmsgstr "Cancel"\n',
        "locales/vi/LC_MESSAGES/messages.po": 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n"Language: vi\\n"\n\nmsgid "common.confirm"\nmsgstr "Xác nhận"\n\nmsgid "common.cancel"\nmsgstr "Hủy"\n',
    },
}
