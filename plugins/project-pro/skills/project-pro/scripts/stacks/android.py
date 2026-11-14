"""Stack data for `android`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
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
}

I18N: dict[str, Any] = {
    "standard": "Android Resource System (res/values/strings.xml)",
    "tooling": "androidx.compose.ui.res.stringResource(R.string.<id>, *args) + AppCompatDelegate.setApplicationLocales() / LocaleManager",
    "guidance": "Centralize all user-facing strings in res/values/strings.xml and res/values-<bcp47>/strings.xml (in :core:designsystem or :core:resources). Use stringResource() in Compose views. In ViewModels, emit typed StringResource or sealed UiText to avoid leaking Context.",
    "dirs": ["core/designsystem/src/main/res/values", "core/designsystem/src/main/res/values-vi"],
    "sample_files": {
        "core/designsystem/src/main/res/values/strings.xml": '<resources>\n    <string name="app_name">App</string>\n    <string name="common_confirm">Confirm</string>\n    <string name="common_cancel">Cancel</string>\n</resources>\n',
        "core/designsystem/src/main/res/values-vi/strings.xml": '<resources>\n    <string name="app_name">App</string>\n    <string name="common_confirm">Xác nhận</string>\n    <string name="common_cancel">Hủy</string>\n</resources>\n',
    },
}
