"""Stack data for `kmp`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
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
}

I18N: dict[str, Any] = {
    "standard": "Compose Multiplatform Resources (Res.string.*) or MOKO Resources",
    "tooling": "org.jetbrains.compose.resources.stringResource(Res.string.<id>, *args) + UiText sealed wrapper",
    "guidance": "Place shared translations in composeApp/src/commonMain/composeResources/values/strings.xml (and values-vi/). Access via Res.string.<id> in commonMain Compose. Shared ViewModels return UiText.DynamicString or UiText.StringResourceId to remain context-free.",
    "dirs": ["composeApp/src/commonMain/composeResources/values", "composeApp/src/commonMain/composeResources/values-vi"],
    "sample_files": {
        "composeApp/src/commonMain/composeResources/values/strings.xml": '<resources>\n    <string name="app_name">App</string>\n    <string name="common_confirm">Confirm</string>\n    <string name="common_cancel">Cancel</string>\n</resources>\n',
        "composeApp/src/commonMain/composeResources/values-vi/strings.xml": '<resources>\n    <string name="app_name">App</string>\n    <string name="common_confirm">Xác nhận</string>\n    <string name="common_cancel">Hủy</string>\n</resources>\n',
    },
}
