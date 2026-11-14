"""Stack data for `rust`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
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
        "build": "cargo build --workspace",
        "test_all": "cargo test --workspace",
        "test_single": "cargo test -p <crate> -- <test_name>",
        "lint": "cargo fmt --all -- --check && cargo clippy --workspace --all-targets -- -D warnings",
        "sec_audit": "cargo audit",
    },
    "boundary_tool": "Cargo Workspace crate isolation (pure domain crate, framework adapters, app entrypoint) + cargo-deny when dependency policy requires it",
    "domain_forbidden_imports": ["eframe::", "egui::", "sdl2::", "winit::", "iced::", "tauri::"],
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
}

I18N: dict[str, Any] = {
    "standard": "Centralized Type-Safe String Catalog (AppLanguage enum + strings::* module) or fluent-rs",
    "tooling": "AppLanguage::{Vietnamese, English} + strings::<module>::<key>(lang) / fluent-rs",
    "guidance": "Define AppLanguage { English, Vietnamese, ... } in crates/ui/src/strings/. Provide type-safe functions or match-based string catalogs returning &'static str or Cow<'static, str>. For rich plurals/genders, integrate fluent-rs (.ftl). Ban raw hardcoded strings in UI views.",
    "dirs": ["crates/ui/src/strings"],
    "sample_files": {
        "crates/ui/src/strings/mod.rs": '//! Centralized type-safe strings catalog for multi-language support (i18n).\n\n#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]\npub enum AppLanguage {\n    #[default]\n    Vietnamese,\n    English,\n}\n\nimpl AppLanguage {\n    pub fn code(&self) -> &\'static str {\n        match self {\n            Self::Vietnamese => "vi",\n            Self::English => "en",\n        }\n    }\n}\n\npub fn confirm(lang: AppLanguage) -> &\'static str {\n    match lang {\n        AppLanguage::Vietnamese => "Xác nhận",\n        AppLanguage::English => "Confirm",\n    }\n}\n\npub fn cancel(lang: AppLanguage) -> &\'static str {\n    match lang {\n        AppLanguage::Vietnamese => "Hủy",\n        AppLanguage::English => "Cancel",\n    }\n}\n',
    },
}
