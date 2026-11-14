"""Stack data for `flutter`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
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
}

I18N: dict[str, Any] = {
    "standard": "Official Flutter Localizations (flutter_localizations) + intl + l10n.yaml + ARB",
    "tooling": "AppLocalizations.of(context)!.key (with generate: true in pubspec.yaml)",
    "guidance": "Define message catalogs in lib/l10n/app_en.arb and lib/l10n/app_vi.arb. Configure l10n.yaml. Reference strings in widgets via AppLocalizations.of(context). Zero hardcoded UI strings.",
    "dirs": ["lib/l10n"],
    "sample_files": {
        "lib/l10n/app_en.arb": '{\n  "@@locale": "en",\n  "appTitle": "App",\n  "confirm": "Confirm",\n  "cancel": "Cancel"\n}\n',
        "lib/l10n/app_vi.arb": '{\n  "@@locale": "vi",\n  "appTitle": "App",\n  "confirm": "Xác nhận",\n  "cancel": "Hủy"\n}\n',
        "l10n.yaml": "arb-dir: lib/l10n\ntemplate-arb-file: app_en.arb\noutput-localization-file: app_localizations.dart\n",
    },
}
