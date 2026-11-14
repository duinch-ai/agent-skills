"""Stack data for `cpp-switch`: reference repos, patterns, commands, scaffold dirs and i18n preset."""

from __future__ import annotations

from typing import Any

STACK: dict[str, Any] = {
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
}

I18N: dict[str, Any] = {
    "standard": "Borealis built-in i18n (brls::loadTranslations) + JSON translation catalogs",
    "tooling": "brls::loadTranslations(\"romfs:/i18n\") + brls::getStr(\"key\")",
    "guidance": "Store translation catalogs in resources/romfs/i18n/{en-US,vi-VN}/strings.json. Load them during application init via brls::loadTranslations(). Fetch strings using brls::getStr(\"key\"). Ban raw string literals in view XML or C++ frames.",
    "dirs": ["resources/romfs/i18n/en-US", "resources/romfs/i18n/vi-VN"],
    "sample_files": {
        "resources/romfs/i18n/en-US/strings.json": '{\n  "common_confirm": "Confirm",\n  "common_cancel": "Cancel"\n}\n',
        "resources/romfs/i18n/vi-VN/strings.json": '{\n  "common_confirm": "Xác nhận",\n  "common_cancel": "Hủy"\n}\n',
    },
}
