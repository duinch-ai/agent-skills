"""Stack data for `ios`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
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
}

I18N: dict[str, Any] = {
    "standard": "Modern String Catalog (.xcstrings) + LocalizedStringKey",
    "tooling": "Text(\"key\") + String(localized: \"key\", bundle: .module)",
    "guidance": "Manage translations via Localizable.xcstrings at the app or SPM package level. In SwiftUI, use Text(\"key\") or String(localized: \"key\"). When inside SPM modules, pass bundle: .module. Forbid raw hardcoded UI strings.",
    "dirs": ["Packages/CoreDesignSystem/Sources/CoreDesignSystem/Resources"],
    "sample_files": {
        "Packages/CoreDesignSystem/Sources/CoreDesignSystem/Resources/Localizable.xcstrings": '{\n  "sourceLanguage" : "en",\n  "strings" : {\n    "common.confirm" : {\n      "localizations" : {\n        "en" : { "stringUnit" : { "state" : "translated", "value" : "Confirm" } },\n        "vi" : { "stringUnit" : { "state" : "translated", "value" : "Xác nhận" } }\n      }\n    },\n    "common.cancel" : {\n      "localizations" : {\n        "en" : { "stringUnit" : { "state" : "translated", "value" : "Cancel" } },\n        "vi" : { "stringUnit" : { "state" : "translated", "value" : "Hủy" } }\n      }\n    }\n  },\n  "version" : "1.0"\n}\n',
    },
}
