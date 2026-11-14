"""Supported locales, starter translations and per-platform i18n scaffold file generation."""

from __future__ import annotations

import json

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
