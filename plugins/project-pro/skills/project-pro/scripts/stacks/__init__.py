"""STACK_CATALOG assembled from one data module per stack (same key order as before)."""

from __future__ import annotations

from typing import Any

from . import android, cpp_switch, flutter, go, ios, kmp, nestjs, python, rust, web

_MODULES = {
    "android": android,
    "kmp": kmp,
    "flutter": flutter,
    "ios": ios,
    "web": web,
    "python": python,
    "go": go,
    "nestjs": nestjs,
    "rust": rust,
    "cpp-switch": cpp_switch,
}

STACK_CATALOG: dict[str, dict[str, Any]] = {
    key: {**mod.STACK, "i18n": mod.I18N} for key, mod in _MODULES.items()
}
