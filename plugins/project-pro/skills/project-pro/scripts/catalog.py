"""Curated reference repositories, architecture presets, and stack metadata for project-pro."""

from __future__ import annotations

import json
from typing import Any

SUPPORTED_LOCALES_CHOICES: list[tuple[str, str, bool]] = [
    ("vi", "Tiếng Việt (vi / vi-VN)", True),
    ("en", "English (en / en-US)", True),
    ("ja", "日本語 / Japanese (ja / ja-JP)", False),
    ("zh", "中文 / Chinese Simplified (zh / zh-CN)", False),
    ("ko", "한국어 / Korean (ko / ko-KR)", False),
    ("fr", "Français / French (fr / fr-FR)", False),
    ("es", "Español / Spanish (es / es-ES)", False),
    ("de", "Deutsch / German (de / de-DE)", False),
]

LOCALE_TRANSLATIONS: dict[str, dict[str, str]] = {
    "vi": {"confirm": "Xác nhận", "cancel": "Hủy", "settings": "Cài đặt", "language": "Ngôn ngữ", "save": "Lưu"},
    "en": {"confirm": "Confirm", "cancel": "Cancel", "settings": "Settings", "language": "Language", "save": "Save"},
    "ja": {"confirm": "確認", "cancel": "キャンセル", "settings": "設定", "language": "言語", "save": "保存"},
    "zh": {"confirm": "确认", "cancel": "取消", "settings": "设置", "language": "语言", "save": "保存"},
    "ko": {"confirm": "확인", "cancel": "취소", "settings": "설정", "language": "언어", "save": "저장"},
    "fr": {"confirm": "Confirmer", "cancel": "Annuler", "settings": "Paramètres", "language": "Langue", "save": "Enregistrer"},
    "es": {"confirm": "Confirmar", "cancel": "Cancelar", "settings": "Ajustes", "language": "Idioma", "save": "Guardar"},
    "de": {"confirm": "Bestätigen", "cancel": "Abbrechen", "settings": "Einstellungen", "language": "Sprache", "save": "Speichern"},
}

def generate_i18n_scaffold_files(stack: str, locales: list[str] | None = None, project_name: str = "App") -> dict[str, str]:
    """Generate canonical platform-tailored i18n file paths and starter contents for requested locales."""
    clean_locales = list(dict.fromkeys(locales or ["vi", "en"]))
    if not clean_locales:
        clean_locales = ["vi", "en"]
    files: dict[str, str] = {}

    def tr(loc: str, key: str, fallback: str) -> str:
        base = loc.split("-")[0].lower()
        return LOCALE_TRANSLATIONS.get(base, {}).get(key, fallback)

    if stack == "android":
        base_confirm = tr("en", "confirm", "Confirm")
        base_cancel = tr("en", "cancel", "Cancel")
        files["core/designsystem/src/main/res/values/strings.xml"] = (
            f'<resources>\n'
            f'    <string name="app_name">{project_name}</string>\n'
            f'    <string name="common_confirm">{base_confirm}</string>\n'
            f'    <string name="common_cancel">{base_cancel}</string>\n'
            f'</resources>\n'
        )
        for loc in clean_locales:
            c = tr(loc, "confirm", "Confirm")
            x = tr(loc, "cancel", "Cancel")
            folder = f"core/designsystem/src/main/res/values-{loc}"
            files[f"{folder}/strings.xml"] = (
                f'<resources>\n'
                f'    <string name="app_name">{project_name}</string>\n'
                f'    <string name="common_confirm">{c}</string>\n'
                f'    <string name="common_cancel">{x}</string>\n'
                f'</resources>\n'
            )
    elif stack == "kmp":
        base_confirm = tr("en", "confirm", "Confirm")
        base_cancel = tr("en", "cancel", "Cancel")
        files["composeApp/src/commonMain/composeResources/values/strings.xml"] = (
            f'<resources>\n'
            f'    <string name="app_name">{project_name}</string>\n'
            f'    <string name="common_confirm">{base_confirm}</string>\n'
            f'    <string name="common_cancel">{base_cancel}</string>\n'
            f'</resources>\n'
        )
        for loc in clean_locales:
            c = tr(loc, "confirm", "Confirm")
            x = tr(loc, "cancel", "Cancel")
            folder = f"composeApp/src/commonMain/composeResources/values-{loc}"
            files[f"{folder}/strings.xml"] = (
                f'<resources>\n'
                f'    <string name="app_name">{project_name}</string>\n'
                f'    <string name="common_confirm">{c}</string>\n'
                f'    <string name="common_cancel">{x}</string>\n'
                f'</resources>\n'
            )
    elif stack == "flutter":
        files["l10n.yaml"] = (
            "arb-dir: lib/l10n\n"
            "template-arb-file: app_en.arb\n"
            "output-localization-file: app_localizations.dart\n"
        )
        for loc in clean_locales:
            c = tr(loc, "confirm", "Confirm")
            x = tr(loc, "cancel", "Cancel")
            files[f"lib/l10n/app_{loc}.arb"] = (
                f'{{\n'
                f'  "@@locale": "{loc}",\n'
                f'  "appTitle": "{project_name}",\n'
                f'  "confirm": "{c}",\n'
                f'  "cancel": "{x}"\n'
                f'}}\n'
            )
    elif stack == "ios":
        strings_map: dict[str, Any] = {
            "common.confirm": {"localizations": {}},
            "common.cancel": {"localizations": {}},
            "common.settings": {"localizations": {}},
        }
        for loc in clean_locales:
            strings_map["common.confirm"]["localizations"][loc] = {
                "stringUnit": {"state": "translated", "value": tr(loc, "confirm", "Confirm")}
            }
            strings_map["common.cancel"]["localizations"][loc] = {
                "stringUnit": {"state": "translated", "value": tr(loc, "cancel", "Cancel")}
            }
            strings_map["common.settings"]["localizations"][loc] = {
                "stringUnit": {"state": "translated", "value": tr(loc, "settings", "Settings")}
            }
        xcstrings = {
            "sourceLanguage": "en",
            "strings": strings_map,
            "version": "1.0",
        }
        files["Packages/CoreDesignSystem/Sources/CoreDesignSystem/Resources/Localizable.xcstrings"] = (
            json.dumps(xcstrings, indent=2, ensure_ascii=False) + "\n"
        )
    elif stack == "web":
        for loc in clean_locales:
            c = tr(loc, "confirm", "Confirm")
            x = tr(loc, "cancel", "Cancel")
            s = tr(loc, "settings", "Settings")
            payload = {
                "common": {
                    "appName": project_name,
                    "confirm": c,
                    "cancel": x,
                    "settings": s,
                }
            }
            files[f"messages/{loc}.json"] = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    elif stack == "python":
        for loc in clean_locales:
            c = tr(loc, "confirm", "Confirm")
            x = tr(loc, "cancel", "Cancel")
            files[f"locales/{loc}/LC_MESSAGES/messages.po"] = (
                f'msgid ""\n'
                f'msgstr ""\n'
                f'"Content-Type: text/plain; charset=UTF-8\\n"\n'
                f'"Language: {loc}\\n"\n\n'
                f'msgid "common.confirm"\nmsgstr "{c}"\n\n'
                f'msgid "common.cancel"\nmsgstr "{x}"\n'
            )
    elif stack == "go":
        for loc in clean_locales:
            c = tr(loc, "confirm", "Confirm")
            x = tr(loc, "cancel", "Cancel")
            payload = {"common.confirm": c, "common.cancel": x}
            files[f"locales/active.{loc}.json"] = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    elif stack == "nestjs":
        for loc in clean_locales:
            c = tr(loc, "confirm", "Confirm")
            x = tr(loc, "cancel", "Cancel")
            payload = {"confirm": c, "cancel": x}
            files[f"src/i18n/{loc}/common.json"] = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    elif stack == "rust":
        variant_names = {
            "vi": "Vietnamese", "en": "English", "ja": "Japanese",
            "zh": "Chinese", "ko": "Korean", "fr": "French",
            "es": "Spanish", "de": "German",
        }
        variants = []
        code_arms = []
        from_code_arms = []
        confirm_arms = []
        cancel_arms = []
        for loc in clean_locales:
            vname = variant_names.get(loc, loc.capitalize())
            variants.append(vname)
            code_arms.append(f'            Self::{vname} => "{loc}",')
            from_code_arms.append(f'            "{loc}" => Some(Self::{vname}),')
            conf = tr(loc, "confirm", "Confirm")
            canc = tr(loc, "cancel", "Cancel")
            confirm_arms.append(f'        AppLanguage::{vname} => "{conf}",')
            cancel_arms.append(f'        AppLanguage::{vname} => "{canc}",')

        enum_def = "\n".join(f"    {v}," for v in variants)
        code_body = "\n".join(code_arms)
        from_code_body = "\n".join(from_code_arms)
        confirm_body = "\n".join(confirm_arms)
        cancel_body = "\n".join(cancel_arms)
        all_slice = ", ".join(f"AppLanguage::{v}" for v in variants)

        files["crates/ui/src/strings/mod.rs"] = (
            "//! Centralized type-safe strings catalog for multi-language support (i18n).\n\n"
            "#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]\n"
            "pub enum AppLanguage {\n"
            f"    #[default]\n"
            f"{enum_def}\n"
            "}\n\n"
            "impl AppLanguage {\n"
            "    pub fn code(&self) -> &'static str {\n"
            "        match self {\n"
            f"{code_body}\n"
            "        }\n"
            "    }\n\n"
            "    pub fn from_code(code: &str) -> Option<Self> {\n"
            "        match code {\n"
            f"{from_code_body}\n"
            "            _ => None,\n"
            "        }\n"
            "    }\n\n"
            "    pub fn all() -> &'static [Self] {\n"
            f"        &[{all_slice}]\n"
            "    }\n"
            "}\n\n"
            "pub fn confirm(lang: AppLanguage) -> &'static str {\n"
            "    match lang {\n"
            f"{confirm_body}\n"
            "    }\n"
            "}\n\n"
            "pub fn cancel(lang: AppLanguage) -> &'static str {\n"
            "    match lang {\n"
            f"{cancel_body}\n"
            "    }\n"
            "}\n"
        )
    elif stack == "cpp-switch":
        for loc in clean_locales:
            c = tr(loc, "confirm", "Confirm")
            x = tr(loc, "cancel", "Cancel")
            tag = f"{loc}-VN" if loc == "vi" else (f"{loc}-US" if loc == "en" else (f"{loc}-JP" if loc == "ja" else f"{loc}-{loc.upper()}"))
            payload = {"common_confirm": c, "common_cancel": x}
            files[f"resources/romfs/i18n/{tag}/strings.json"] = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    return files

I18N_PRESETS: dict[str, dict[str, Any]] = {
    "android": {
        "standard": "Android Resource System (res/values/strings.xml)",
        "tooling": "androidx.compose.ui.res.stringResource(R.string.<id>, *args) + AppCompatDelegate.setApplicationLocales() / LocaleManager",
        "guidance": "Centralize all user-facing strings in res/values/strings.xml and res/values-<bcp47>/strings.xml (in :core:designsystem or :core:resources). Use stringResource() in Compose views. In ViewModels, emit typed StringResource or sealed UiText to avoid leaking Context.",
        "dirs": ["core/designsystem/src/main/res/values", "core/designsystem/src/main/res/values-vi"],
        "sample_files": {
            "core/designsystem/src/main/res/values/strings.xml": '<resources>\n    <string name="app_name">App</string>\n    <string name="common_confirm">Confirm</string>\n    <string name="common_cancel">Cancel</string>\n</resources>\n',
            "core/designsystem/src/main/res/values-vi/strings.xml": '<resources>\n    <string name="app_name">App</string>\n    <string name="common_confirm">Xác nhận</string>\n    <string name="common_cancel">Hủy</string>\n</resources>\n',
        },
    },
    "kmp": {
        "standard": "Compose Multiplatform Resources (Res.string.*) or MOKO Resources",
        "tooling": "org.jetbrains.compose.resources.stringResource(Res.string.<id>, *args) + UiText sealed wrapper",
        "guidance": "Place shared translations in composeApp/src/commonMain/composeResources/values/strings.xml (and values-vi/). Access via Res.string.<id> in commonMain Compose. Shared ViewModels return UiText.DynamicString or UiText.StringResourceId to remain context-free.",
        "dirs": ["composeApp/src/commonMain/composeResources/values", "composeApp/src/commonMain/composeResources/values-vi"],
        "sample_files": {
            "composeApp/src/commonMain/composeResources/values/strings.xml": '<resources>\n    <string name="app_name">App</string>\n    <string name="common_confirm">Confirm</string>\n    <string name="common_cancel">Cancel</string>\n</resources>\n',
            "composeApp/src/commonMain/composeResources/values-vi/strings.xml": '<resources>\n    <string name="app_name">App</string>\n    <string name="common_confirm">Xác nhận</string>\n    <string name="common_cancel">Hủy</string>\n</resources>\n',
        },
    },
    "flutter": {
        "standard": "Official Flutter Localizations (flutter_localizations) + intl + l10n.yaml + ARB",
        "tooling": "AppLocalizations.of(context)!.key (with generate: true in pubspec.yaml)",
        "guidance": "Define message catalogs in lib/l10n/app_en.arb and lib/l10n/app_vi.arb. Configure l10n.yaml. Reference strings in widgets via AppLocalizations.of(context). Zero hardcoded UI strings.",
        "dirs": ["lib/l10n"],
        "sample_files": {
            "lib/l10n/app_en.arb": '{\n  "@@locale": "en",\n  "appTitle": "App",\n  "confirm": "Confirm",\n  "cancel": "Cancel"\n}\n',
            "lib/l10n/app_vi.arb": '{\n  "@@locale": "vi",\n  "appTitle": "App",\n  "confirm": "Xác nhận",\n  "cancel": "Hủy"\n}\n',
            "l10n.yaml": "arb-dir: lib/l10n\ntemplate-arb-file: app_en.arb\noutput-localization-file: app_localizations.dart\n",
        },
    },
    "ios": {
        "standard": "Modern String Catalog (.xcstrings) + LocalizedStringKey",
        "tooling": "Text(\"key\") + String(localized: \"key\", bundle: .module)",
        "guidance": "Manage translations via Localizable.xcstrings at the app or SPM package level. In SwiftUI, use Text(\"key\") or String(localized: \"key\"). When inside SPM modules, pass bundle: .module. Forbid raw hardcoded UI strings.",
        "dirs": ["Packages/CoreDesignSystem/Sources/CoreDesignSystem/Resources"],
        "sample_files": {
            "Packages/CoreDesignSystem/Sources/CoreDesignSystem/Resources/Localizable.xcstrings": '{\n  "sourceLanguage" : "en",\n  "strings" : {\n    "common.confirm" : {\n      "localizations" : {\n        "en" : { "stringUnit" : { "state" : "translated", "value" : "Confirm" } },\n        "vi" : { "stringUnit" : { "state" : "translated", "value" : "Xác nhận" } }\n      }\n    },\n    "common.cancel" : {\n      "localizations" : {\n        "en" : { "stringUnit" : { "state" : "translated", "value" : "Cancel" } },\n        "vi" : { "stringUnit" : { "state" : "translated", "value" : "Hủy" } }\n      }\n    }\n  },\n  "version" : "1.0"\n}\n',
        },
    },
    "web": {
        "standard": "next-intl (Next.js App Router) or react-i18next (Vite/SPA) or vue-i18n",
        "tooling": "useTranslations(\"namespace\") / t(\"key\") + messages/*.json catalogs",
        "guidance": "Store translations in messages/en.json and messages/vi.json. In Next.js App Router, implement next-intl middleware for /[locale]/ routing and server component translations. Enforce type-safety via TypeScript declaration files.",
        "dirs": ["messages"],
        "sample_files": {
            "messages/en.json": '{\n  "common": {\n    "confirm": "Confirm",\n    "cancel": "Cancel"\n  }\n}\n',
            "messages/vi.json": '{\n  "common": {\n    "confirm": "Xác nhận",\n    "cancel": "Hủy"\n  }\n}\n',
        },
    },
    "python": {
        "standard": "GNU gettext + Babel (pybabel) + Accept-Language Middleware",
        "tooling": "gettext.gettext / _(\"translatable_text\") + Babel PO/MO catalogs",
        "guidance": "Configure Babel catalogs in locales/{en,vi}/LC_MESSAGES/. Resolve client locale from Accept-Language header via request middleware into contextvars. Wrap user-facing exception details and messages with _(...).",
        "dirs": ["locales/en/LC_MESSAGES", "locales/vi/LC_MESSAGES"],
        "sample_files": {
            "locales/en/LC_MESSAGES/messages.po": 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n"Language: en\\n"\n\nmsgid "common.confirm"\nmsgstr "Confirm"\n\nmsgid "common.cancel"\nmsgstr "Cancel"\n',
            "locales/vi/LC_MESSAGES/messages.po": 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n"Language: vi\\n"\n\nmsgid "common.confirm"\nmsgstr "Xác nhận"\n\nmsgid "common.cancel"\nmsgstr "Hủy"\n',
        },
    },
    "go": {
        "standard": "nicksnyder/go-i18n/v2 + golang.org/x/text/language",
        "tooling": "i18n.Bundle + i18n.Localizer + Localize(&i18n.LocalizeConfig{MessageID: \"key\"})",
        "guidance": "Load JSON/TOML message catalogs from locales/active.en.json and locales/active.vi.json into an i18n.Bundle at startup. Inject an i18n.Localizer into each request context based on Accept-Language header.",
        "dirs": ["locales"],
        "sample_files": {
            "locales/active.en.json": '{\n  "common.confirm": "Confirm",\n  "common.cancel": "Cancel"\n}\n',
            "locales/active.vi.json": '{\n  "common.confirm": "Xác nhận",\n  "common.cancel": "Hủy"\n}\n',
        },
    },
    "nestjs": {
        "standard": "nestjs-i18n + JSON/YAML catalogs + Accept-Language Resolver",
        "tooling": "I18nService.translate(\"common.KEY\", { lang }) + @I18nLang() lang: string",
        "guidance": "Store translations in src/i18n/{en,vi}/*.json. Configure I18nModule with AcceptLanguageResolver and HeaderResolver. Inject I18nService into controllers and exception filters. Ban hardcoded response strings.",
        "dirs": ["src/i18n/en", "src/i18n/vi"],
        "sample_files": {
            "src/i18n/en/common.json": '{\n  "confirm": "Confirm",\n  "cancel": "Cancel"\n}\n',
            "src/i18n/vi/common.json": '{\n  "confirm": "Xác nhận",\n  "cancel": "Hủy"\n}\n',
        },
    },
    "rust": {
        "standard": "Centralized Type-Safe String Catalog (AppLanguage enum + strings::* module) or fluent-rs",
        "tooling": "AppLanguage::{Vietnamese, English} + strings::<module>::<key>(lang) / fluent-rs",
        "guidance": "Define AppLanguage { English, Vietnamese, ... } in crates/ui/src/strings/. Provide type-safe functions or match-based string catalogs returning &'static str or Cow<'static, str>. For rich plurals/genders, integrate fluent-rs (.ftl). Ban raw hardcoded strings in UI views.",
        "dirs": ["crates/ui/src/strings"],
        "sample_files": {
            "crates/ui/src/strings/mod.rs": '//! Centralized type-safe strings catalog for multi-language support (i18n).\n\n#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]\npub enum AppLanguage {\n    #[default]\n    Vietnamese,\n    English,\n}\n\nimpl AppLanguage {\n    pub fn code(&self) -> &\'static str {\n        match self {\n            Self::Vietnamese => "vi",\n            Self::English => "en",\n        }\n    }\n}\n\npub fn confirm(lang: AppLanguage) -> &\'static str {\n    match lang {\n        AppLanguage::Vietnamese => "Xác nhận",\n        AppLanguage::English => "Confirm",\n    }\n}\n\npub fn cancel(lang: AppLanguage) -> &\'static str {\n    match lang {\n        AppLanguage::Vietnamese => "Hủy",\n        AppLanguage::English => "Cancel",\n    }\n}\n',
        },
    },
    "cpp-switch": {
        "standard": "Borealis built-in i18n (brls::loadTranslations) + JSON translation catalogs",
        "tooling": "brls::loadTranslations(\"romfs:/i18n\") + brls::getStr(\"key\")",
        "guidance": "Store translation catalogs in resources/romfs/i18n/{en-US,vi-VN}/strings.json. Load them during application init via brls::loadTranslations(). Fetch strings using brls::getStr(\"key\"). Ban raw string literals in view XML or C++ frames.",
        "dirs": ["resources/romfs/i18n/en-US", "resources/romfs/i18n/vi-VN"],
        "sample_files": {
            "resources/romfs/i18n/en-US/strings.json": '{\n  "common_confirm": "Confirm",\n  "common_cancel": "Cancel"\n}\n',
            "resources/romfs/i18n/vi-VN/strings.json": '{\n  "common_confirm": "Xác nhận",\n  "common_cancel": "Hủy"\n}\n',
        },
    },
}

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
    },
    "cpp-switch": {
        "label": "C++ / Nintendo Switch Homebrew (CMake + libnx + Borealis)",
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvc-borealis",
        "patterns": [
            ("mvc-borealis", "Borealis MVC + Tab/Navigation Frame + Async Event Worker — ref: dragonflylee/switchfin, PoloNX/TinWoo"),
            ("clean-layered", "Clean Layered (Presentation Borealis -> Domain Interfaces -> Data/libnx Providers) — ref: XorTroll/Goldleaf"),
        ],
        "repos": [
            {"repo": "dragonflylee/switchfin", "url": "https://github.com/dragonflylee/switchfin", "why": "Production multi-platform Borealis client for Switch (deko3d/opengl) & desktop, async networking, custom recycling views, CMake."},
            {"repo": "PoloNX/TinWoo", "url": "https://github.com/PoloNX/TinWoo", "why": "Production Nintendo Switch NSP/NSZ/XCI installer using Borealis & libnx (USB/MTP/Network install, content management)."},
            {"repo": "XorTroll/Goldleaf", "url": "https://github.com/XorTroll/Goldleaf", "why": "Gold standard multipurpose homebrew file, title and content manager for Horizon OS using libnx."},
            {"repo": "ITotalJustice/aio-switch-updater", "url": "https://github.com/ITotalJustice/aio-switch-updater", "why": "Clean Borealis-based updater, libcurl download pipeline, JSON API parsing and extraction."},
        ],
        "commands": {
            "build": "cmake --build build -j$(nproc)",
            "test_all": "ctest --test-dir build --output-on-failure",
            "test_single": "ctest --test-dir build -R <test_name>",
            "lint": "clang-format --dry-run -Werror $(find app -name '*.cpp' -o -name '*.hpp') && clang-tidy -p build app/src/*.cpp",
            "sec_audit": "flawfinder --minlevel=3 app/src/",
        },
        "boundary_tool": "CMake target boundary isolation (domain pure C++ library, presentation Borealis app) + clang-tidy check",
        "domain_forbidden_imports": ["switch.h", "borealis.hpp", "curl/curl.h"],
        "scaffold_dirs": {
            "modular-clean": [
                "app/include/domain/model", "app/include/domain/repository", "app/include/domain/usecase",
                "app/include/data/remote", "app/include/data/installer", "app/include/data/parser",
                "app/include/view/tabs", "app/include/view/widgets", "app/include/view/dialogs",
                "app/src/domain", "app/src/data/remote", "app/src/data/installer", "app/src/data/parser",
                "app/src/view/tabs", "app/src/view/widgets", "app/src/view/dialogs",
                "tests/unit", "resources/romfs/i18n/en-US", "resources/romfs/i18n/vi-VN",
            ],
            "clean": [
                "app/include/api", "app/include/view", "app/include/installer", "app/include/utils",
                "app/src/api", "app/src/view", "app/src/installer", "app/src/utils",
                "tests/unit", "resources/romfs",
            ],
        },
    },
}

for _stack_key, _preset in I18N_PRESETS.items():
    if _stack_key in STACK_CATALOG:
        STACK_CATALOG[_stack_key]["i18n"] = _preset

PRODUCT_CATEGORIES: dict[str, dict[str, Any]] = {
    "mobile-app": {
        "label": "Mobile App (Android / iOS / Cross-Platform)",
        "description": "Native hoặc Cross-platform app di động cho iOS/Android (Offline-first, reactive state, permissions, gestures)",
        "recommended_stacks": ["android", "ios", "flutter", "kmp"],
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvi",
        "key_features": ["solid-dry", "typed-errors", "i18n", "network-storage", "ui-nav", "arch-lint"],
        "guidance": "Thiết kế offline-first với single source of truth từ local database; ViewModel decoupled khỏi Context; hỗ trợ dark mode & dynamic locales.",
    },
    "desktop-app": {
        "label": "Desktop App (macOS / Windows / Linux GUI)",
        "description": "Phần mềm cài đặt máy tính (Window state, native file dialogs, system tray, drag-and-drop, multi-threading)",
        "recommended_stacks": ["rust", "flutter", "kmp", "ios"],
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvi",
        "key_features": ["solid-dry", "typed-errors", "i18n", "ui-nav", "testing-ci", "arch-lint"],
        "guidance": "Tách biệt luồng UI và worker threads/threadpool cho tác vụ nặng I/O; lưu trạng thái cửa sổ; hỗ trợ native menus và file dialogs.",
    },
    "multiplatform-app": {
        "label": "Multi-Platform Universal App (Mobile + Desktop + Web)",
        "description": "Ứng dụng đa nền tảng dùng chung code core logic, domain và một phần hoặc toàn bộ UI",
        "recommended_stacks": ["kmp", "flutter", "rust", "web"],
        "recommended_arch": "clean",
        "recommended_pattern": "mvi",
        "key_features": ["solid-dry", "typed-errors", "i18n", "network-storage", "ui-nav", "testing-ci"],
        "guidance": "Cô lập domain & business logic không phụ thuộc platform SDK; thiết kế UI tự thích ứng (responsive layout) giữa mobile touch và desktop mouse/keyboard.",
    },
    "web-app": {
        "label": "Web Application / SaaS Portal (SPA / SSR / Dashboard)",
        "description": "Ứng dụng web người dùng, admin portal, SaaS dashboard với SEO hoặc trải nghiệm tương tác cao",
        "recommended_stacks": ["web"],
        "recommended_arch": "vertical-slice",
        "recommended_pattern": "query-zustand",
        "key_features": ["solid-dry", "typed-errors", "i18n", "ui-nav", "arch-lint"],
        "guidance": "Phân chia rõ server vs client state; dùng server cache (TanStack Query) cho API data và store cục bộ (Zustand) cho UI state; tối ưu Core Web Vitals.",
    },
    "backend-api": {
        "label": "Backend Service / API (REST / gRPC / GraphQL / Microservice)",
        "description": "Dịch vụ máy chủ cung cấp API cho web, mobile hoặc các hệ thống khác",
        "recommended_stacks": ["python", "go", "nestjs"],
        "recommended_arch": "hexagonal",
        "recommended_pattern": "service-repo",
        "key_features": ["solid-dry", "typed-errors", "di-core", "network-storage", "arch-lint"],
        "guidance": "Chuẩn hóa API contracts (OpenAPI); endpoint /healthz và /readyz; chuẩn lỗi RFC 9457 Problem Details; quản lý DB connection pool và transactions.",
    },
    "service-worker": {
        "label": "Background Worker / Queue Consumer / Scheduled Daemon",
        "description": "Tác vụ chạy ngầm, worker đọc message từ Queue (Kafka/RabbitMQ/Redis), cron jobs tự động",
        "recommended_stacks": ["python", "go", "rust", "nestjs"],
        "recommended_arch": "hexagonal",
        "recommended_pattern": "service-repo",
        "key_features": ["solid-dry", "typed-errors", "di-core", "testing-ci"],
        "guidance": "Xử lý graceful shutdown (SIGINT/SIGTERM); thiết kế xử lý idempotent (tránh lặp); cơ chế retry exponential backoff + Dead Letter Queue (DLQ).",
    },
    "cli-tool": {
        "label": "CLI Tool / Developer Utility / TUI",
        "description": "Công cụ dòng lệnh, scripting, interactive TUI, compiler tool hoặc công cụ lập trình",
        "recommended_stacks": ["rust", "go", "python"],
        "recommended_arch": "lightweight",
        "recommended_pattern": "service-repo",
        "key_features": ["solid-dry", "typed-errors", "arch-lint"],
        "guidance": "Khởi động cực nhanh (< 50ms); chuẩn POSIX flags (-h, --help, --json) & exit codes; tự nhận diện TTY; tách riêng parser CLI khỏi logic nghiệp vụ.",
    },
    "library-sdk": {
        "label": "Reusable Library / Client SDK / Shared Package",
        "description": "Thư viện tái sử dụng, SDK kết nối dịch vụ, hoặc package phát hành lên registry",
        "recommended_stacks": ["rust", "web", "python", "kmp", "go"],
        "recommended_arch": "clean",
        "recommended_pattern": "service-repo",
        "key_features": ["solid-dry", "typed-errors", "testing-ci", "arch-lint"],
        "guidance": "Tối thiểu hóa diện tích Public API; tuân thủ nghiêm ngặt SemVer; zero unsolicited side-effects (không in bừa bãi ra stdout); tối thiểu hóa dependencies bên ngoài.",
    },
    "embedded-homebrew": {
        "label": "Embedded / Console Homebrew / Low-Level / Game",
        "description": "Ứng dụng chạy trên thiết bị chuyên biệt (Nintendo Switch homebrew, embedded, vi điều khiển)",
        "recommended_stacks": ["cpp-switch", "rust"],
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvc-borealis",
        "key_features": ["solid-dry", "typed-errors", "i18n", "testing-ci"],
        "guidance": "Quản lý bộ nhớ nghiêm ngặt không rò rỉ; hỗ trợ gamepad controller và cảm ứng; đóng gói RomFS assets; quản lý cross-compilation toolchain.",
    },
}

PRODUCT_CATEGORY_CHOICES: list[tuple[str, str]] = [
    (cat_id, f"{cat_info['label']} — {cat_info['description'][:65]}...")
    for cat_id, cat_info in PRODUCT_CATEGORIES.items()
]

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
    ("i18n", "Internationalization (i18n/l10n) Architecture Preset & Centralized Resource Catalog", False),
    ("di-core", "Dependency Injection + Validated Env Config + Secret-Redacted Logging Base", True),
    ("network-storage", "Network Client (Auth/Retry Interceptors) + Local DB/Storage Repository Base", True),
    ("ui-nav", "Design System Tokens + Type-Safe Navigation (Client) / OpenAPI + Healthchecks (Backend)", True),
    ("arch-lint", "Strict Compiler Flags + Linter/Formatter + Architecture Boundary Tests", True),
    ("testing-ci", "Testing Harness (Fakes over Mocks + State/Service tests) + GitHub Actions CI (Rust: Linux/macOS/Windows matrix)", False),
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

SOURCE_EXTENSIONS = {".kt", ".kts", ".dart", ".swift", ".ts", ".tsx", ".js", ".jsx", ".vue", ".py", ".go", ".rs", ".cpp", ".hpp", ".cc", ".cxx", ".c", ".h"}
IGNORE_DIRS = {
    ".git", ".githooks", ".agents", ".claude", ".cursor", ".idea", ".vscode", "node_modules", "build", "build-*", "cmake-build-*", ".gradle",
    ".dart_tool", ".build", "DerivedData", "dist", ".next", "__pycache__", ".venv", "venv", "vendor", "Pods", "target",
    "library", "libraries", "extern", "external", "third_party", "thirdparty",
}
