"""Guided-mode recommendation rules: DATA ONLY (interpreted by `recommend.py`).

IMPORTANT: every rule below is a project-pro POLICY choice (an opinionated default that keeps
the supported stacks easy to explain), not a statement of fact about any external tool and not
a ranking of frameworks. The reason sentences say "project-pro's default" for that reason.
Rules are evaluated in order per goal; the first rule whose `when` matches wins.

`when` keys: goal (required), platforms_all, platforms_any, platforms_none_of,
             knows_any, knows_none_of, needs_any, maintainers.
"""

from __future__ import annotations

from typing import Any

GOALS = (
    "mobile-app", "web-app", "desktop-app", "backend-api", "cli-tool", "bot", "library",
    "embedded-homebrew", "multiplatform-app", "unsure",
)
PLATFORMS = ("ios", "android", "web", "windows", "macos", "linux", "switch")
NEEDS = ("offline", "realtime", "many-users", "multi-language-ui", "heavy-compute")
LANGUAGES = (
    "kotlin", "swift", "dart", "typescript", "javascript", "python", "go", "rust", "cpp",
    "java", "csharp", "php", "ruby", "none",
)
UNSUPPORTED_LANGUAGES = ("java", "csharp", "php", "ruby")
MAINTAINERS = ("solo-with-ai", "small-team", "team")

# goal -> product category (a key of PRODUCT_CATEGORIES)
GOAL_CATEGORY = {
    "mobile-app": "mobile-app", "web-app": "web-app", "desktop-app": "desktop-app",
    "backend-api": "backend-api", "cli-tool": "cli-tool", "bot": "service-worker",
    "library": "library-sdk", "embedded-homebrew": "embedded-homebrew",
    "multiplatform-app": "multiplatform-app",
}

# goals where "no rule matched" means we must ask the user, not guess
NO_MATCH_ERRORS = {"library": "need-language", "embedded-homebrew": "unsupported-platform"}

BOTH = ["ios", "android"]


def _r(when: dict[str, Any], stack: str, reasons: list[str], alt: tuple[str, list[str]] | None = None,
       notes: list[str] | None = None) -> dict[str, Any]:
    return {"when": when, "stack": stack, "reasons": reasons, "notes": notes or [],
            "alternative": {"stack": alt[0], "reasons": alt[1]} if alt else None}


RULES: list[dict[str, Any]] = [
    # mobile-app
    _r({"goal": "mobile-app", "platforms_all": BOTH, "knows_any": ["kotlin"]}, "kmp",
       ["one-codebase-two-platforms", "knows-kotlin"], ("flutter", ["alt-flutter"])),
    _r({"goal": "mobile-app", "platforms_all": BOTH, "knows_any": ["dart"]}, "flutter",
       ["one-codebase-two-platforms", "knows-dart"], ("kmp", ["alt-kmp"])),
    _r({"goal": "mobile-app", "platforms_all": BOTH}, "flutter",
       ["one-codebase-two-platforms", "mobile-default"], ("kmp", ["alt-kmp"])),
    _r({"goal": "mobile-app", "platforms_all": ["ios"], "platforms_none_of": ["android"]}, "ios",
       ["only-ios"], ("flutter", ["alt-flutter"])),
    _r({"goal": "mobile-app", "platforms_all": ["android"], "platforms_none_of": ["ios"]}, "android",
       ["only-android"], ("kmp", ["alt-kmp"])),
    _r({"goal": "mobile-app"}, "flutter", ["one-codebase-two-platforms", "mobile-default"], ("kmp", ["alt-kmp"])),
    # multiplatform-app
    _r({"goal": "multiplatform-app", "knows_any": ["kotlin"]}, "kmp",
       ["multi-shared-codebase", "knows-kotlin"], ("flutter", ["alt-flutter"])),
    _r({"goal": "multiplatform-app"}, "flutter", ["multi-shared-codebase", "multi-default"], ("kmp", ["alt-kmp"])),
    # web-app
    _r({"goal": "web-app", "needs_any": ["realtime", "many-users"]}, "web", ["web-standard"],
       notes=["separate-backend"]),
    _r({"goal": "web-app"}, "web", ["web-standard"]),
    # desktop-app
    _r({"goal": "desktop-app", "knows_any": ["kotlin"]}, "kmp", ["knows-kotlin", "desktop-kmp"],
       ("rust", ["alt-rust-desktop"]), notes=["desktop-limited"]),
    _r({"goal": "desktop-app"}, "rust", ["desktop-rust"], ("kmp", ["alt-kmp-desktop"]), notes=["desktop-limited"]),
    # backend-api
    _r({"goal": "backend-api", "knows_any": ["go"]}, "go", ["knows-go"], ("python", ["alt-python-service"])),
    _r({"goal": "backend-api", "knows_any": ["typescript", "javascript"]}, "nestjs", ["knows-typescript"],
       ("go", ["alt-go-service"])),
    _r({"goal": "backend-api", "knows_any": ["python"]}, "python", ["knows-python"], ("go", ["alt-go-service"])),
    _r({"goal": "backend-api", "needs_any": ["many-users", "realtime"]}, "go", ["backend-many-users"],
       ("python", ["alt-python-service"])),
    _r({"goal": "backend-api"}, "python", ["backend-easy-start"], ("go", ["alt-go-service"])),
    # cli-tool
    _r({"goal": "cli-tool", "knows_any": ["rust"]}, "rust", ["knows-rust"], ("go", ["alt-go-cli"])),
    _r({"goal": "cli-tool", "knows_any": ["python"]}, "python", ["knows-python"], ("go", ["alt-go-cli"])),
    _r({"goal": "cli-tool", "needs_any": ["heavy-compute"]}, "rust", ["cli-heavy-compute"], ("go", ["alt-go-cli"])),
    _r({"goal": "cli-tool"}, "go", ["cli-single-binary"], ("rust", ["alt-rust-cli"])),
    # bot
    _r({"goal": "bot", "knows_any": ["typescript", "javascript"]}, "nestjs", ["knows-typescript"],
       ("python", ["alt-python-bot"])),
    _r({"goal": "bot"}, "python", ["bot-default"], ("nestjs", ["alt-nestjs-bot"])),
    # library (no default: an unknown language must be asked, never guessed)
    _r({"goal": "library", "knows_any": ["rust"]}, "rust", ["knows-rust", "library-language"]),
    _r({"goal": "library", "knows_any": ["go"]}, "go", ["knows-go", "library-language"]),
    _r({"goal": "library", "knows_any": ["python"]}, "python", ["knows-python", "library-language"]),
    _r({"goal": "library", "knows_any": ["kotlin"]}, "kmp", ["knows-kotlin", "library-language"]),
    _r({"goal": "library", "knows_any": ["typescript", "javascript"]}, "web", ["knows-typescript", "library-language"]),
    # embedded-homebrew
    _r({"goal": "embedded-homebrew", "platforms_none_of": ["ios", "android", "web", "windows", "macos", "linux"]},
       "cpp-switch", ["switch-homebrew"]),
]

REASONS: dict[str, str] = {
    "existing-code": "This folder already contains a project that looks like it uses this technology, so project-pro keeps it.",
    "one-codebase-two-platforms": "You want both iPhone and Android, and one shared codebase can serve both, so you build and maintain it once.",
    "mobile-default": "With no stronger signal, project-pro's default for phone apps on both platforms is Flutter.",
    "knows-kotlin": "You already know Kotlin, and this choice is written in Kotlin.",
    "knows-dart": "You already know Dart, and this choice is written in Dart.",
    "knows-go": "You already know Go, and this choice is written in Go.",
    "knows-python": "You already know Python, and this choice is written in Python.",
    "knows-typescript": "You already know TypeScript/JavaScript, and this choice is written in it.",
    "knows-rust": "You already know Rust, and this choice is written in Rust.",
    "only-ios": "You only need iPhone/iPad, so project-pro's native iOS stack is the most direct fit.",
    "only-android": "You only need Android, so project-pro's native Android stack is the most direct fit.",
    "multi-shared-codebase": "You want one app on phones and computers, so project-pro picks a stack that shares code between them.",
    "multi-default": "With no stronger signal, project-pro's default for phone-plus-computer apps is Flutter.",
    "web-standard": "A website or web app uses project-pro's web stack, its standard route for this goal.",
    "desktop-kmp": "Since you know Kotlin, project-pro's Kotlin Multiplatform stack lets you build desktop apps with it.",
    "desktop-rust": "project-pro's default for programs on Windows, Mac and Linux is Rust.",
    "backend-many-users": "You expect many users or live updates, so project-pro's default for such services is Go.",
    "backend-easy-start": "With no language preference, project-pro's default for a back-end service is Python.",
    "cli-single-binary": "project-pro's default for command-line tools is Go, which builds a single program file you can hand to anyone.",
    "cli-heavy-compute": "You need heavy computation, so project-pro's default for command-line tools like that is Rust.",
    "bot-default": "project-pro's default for bots and background automation is Python.",
    "library-language": "A reusable library is best written in a language you already know, so project-pro follows your language.",
    "switch-homebrew": "Nintendo Switch homebrew uses project-pro's C++ Switch stack, the only console stack it supports.",
    "multi-language-ui": "You want the app in several languages, so the multi-language (i18n) module is switched on.",
    "alt-flutter": "Flutter shares one codebase across phones and does not require you to know Kotlin.",
    "alt-kmp": "Kotlin Multiplatform shares logic across platforms and suits you if you know or want to learn Kotlin.",
    "alt-rust-desktop": "Rust is project-pro's default for desktop programs if you prefer it over Kotlin.",
    "alt-kmp-desktop": "Kotlin Multiplatform is the alternative for desktop programs, especially if you know Kotlin.",
    "alt-python-service": "Python is project-pro's other stack for back-end services.",
    "alt-go-service": "Go is project-pro's other stack for back-end services.",
    "alt-go-cli": "Go builds a single program file, which is easy to distribute.",
    "alt-rust-cli": "Rust is project-pro's other stack for command-line tools.",
    "alt-python-bot": "Python is the alternative for bots and quick automation scripts.",
    "alt-nestjs-bot": "NestJS (TypeScript) is the alternative if you or your team prefer TypeScript.",
}

NOTES: dict[str, str] = {
    "unsupported-language": "project-pro has no stack for {langs} yet. It picked the closest supported stack, which uses a different language than the one you know.",
    "separate-backend": "A web app with live updates or many users usually also needs a back-end service. Run project-pro again with the goal 'backend-api' to set that up.",
    "desktop-limited": "project-pro's desktop-app support is limited to Rust and Kotlin Multiplatform (Flutter also appears in the catalog).",
    "existing-stack-unusual": "The existing project looks like '{stack}', which is not a typical match for this goal; project-pro keeps your existing stack.",
}

ERRORS: dict[str, str] = {
    "need-goal": "Tell project-pro what you want to build (answers field 'goal'); it will not guess. Allowed: " + ", ".join(g for g in GOALS if g != "unsure"),
    "need-language": "A reusable library follows the language you write it in, and project-pro supports libraries in rust, go, python, kotlin, typescript or javascript. Which of these do you know (answers field 'known_languages')?",
    "unsupported-platform": "project-pro supports console homebrew only for Nintendo Switch; the platforms you listed are not supported for this goal.",
    "invalid-answers": "Invalid answers.",
}
