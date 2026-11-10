"""Interactive terminal checkbox TUI wizard for project-pro."""

from __future__ import annotations

from pathlib import Path
import sys

from catalog import (
    AGENT_CHOICES,
    ARCH_CHOICES,
    FEATURE_CHOICES,
    PRODUCT_CATEGORIES,
    PRODUCT_CATEGORY_CHOICES,
    STACK_CATALOG,
    SUPPORTED_LOCALES_CHOICES,
)
from detector import detect_project
from scaffolder import init_project


def _read_key() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            return "UP" if seq == "[A" else ("DOWN" if seq == "[B" else "ESC")
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == " ":
            return "SPACE"
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _select_single(title: str, choices: list[tuple[str, str]], default_key: str | None = None) -> str:
    idx = next((i for i, (k, _) in enumerate(choices) if k == default_key), 0)
    if not sys.stdin.isatty():
        return choices[idx][0]
    try:
        while True:
            sys.stdout.write(f"\r\033[J\n{title} (↑/↓ di chuyển, Enter chọn):\n")
            for i, (key, label) in enumerate(choices):
                sys.stdout.write(f"  {'❯' if i == idx else ' '} {'◉' if i == idx else '◯'} {label} [{key}]\n")
            sys.stdout.flush()
            key = _read_key()
            sys.stdout.write(f"\033[{len(choices) + 2}A")
            if key == "UP":
                idx = (idx - 1) % len(choices)
            elif key == "DOWN":
                idx = (idx + 1) % len(choices)
            elif key == "ENTER":
                sys.stdout.write(f"\033[{len(choices) + 2}B\n")
                return choices[idx][0]
    except Exception:
        print(f"\n{title}:")
        for i, (k, label) in enumerate(choices, 1):
            print(f"  {i}. {label} [{k}]{' (default)' if i - 1 == idx else ''}")
        raw = input(f"Chọn số [1-{len(choices)}]: ").strip()
        return choices[int(raw) - 1][0] if raw.isdigit() and 1 <= int(raw) <= len(choices) else choices[idx][0]


def _select_multi(title: str, choices: list[tuple[str, str, bool]]) -> list[str]:
    selected = [default for _, _, default in choices]
    idx = 0
    if not sys.stdin.isatty():
        return [choices[i][0] for i, on in enumerate(selected) if on]
    try:
        while True:
            sys.stdout.write(f"\r\033[J\n{title} (↑/↓, SPACE tick [x], 'a' chọn hết, Enter xác nhận):\n")
            for i, (_, label, _) in enumerate(choices):
                sys.stdout.write(f"  {'❯' if i == idx else ' '} {'[x]' if selected[i] else '[ ]'} {label}\n")
            sys.stdout.flush()
            key = _read_key()
            sys.stdout.write(f"\033[{len(choices) + 2}A")
            if key == "UP":
                idx = (idx - 1) % len(choices)
            elif key == "DOWN":
                idx = (idx + 1) % len(choices)
            elif key == "SPACE":
                selected[idx] = not selected[idx]
            elif key in ("a", "A"):
                all_on = all(selected)
                selected = [not all_on for _ in selected]
            elif key == "ENTER":
                sys.stdout.write(f"\033[{len(choices) + 2}B\n")
                return [choices[i][0] for i, on in enumerate(selected) if on]
    except Exception:
        print(f"\n{title}:")
        for i, (_, label, default) in enumerate(choices, 1):
            print(f"  {i}. {'[x]' if default else '[ ]'} {label}")
        raw = input("Nhập số cách nhau bởi dấu phẩy (Enter = mặc định): ").strip()
        if not raw:
            return [choices[i][0] for i, on in enumerate(selected) if on]
        picked = {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}
        return [choices[i - 1][0] for i in sorted(picked) if 1 <= i <= len(choices)]


def run_wizard(target: Path, force: bool = False) -> int:
    det = detect_project(target)
    print(f"=== Project Pro Interactive Wizard ===\nTarget: {det['target']} (Mode: {det['mode']})")

    existing_profile = det.get("existing_profile") or {}
    default_cat = existing_profile.get("productCategory")
    if not default_cat:
        st = det["detected_stack"]
        if st in {"android", "ios"}:
            default_cat = "mobile-app"
        elif st in {"kmp", "flutter"}:
            default_cat = "multiplatform-app"
        elif st == "web":
            default_cat = "web-app"
        elif st in {"python", "go", "nestjs"}:
            default_cat = "backend-api"
        elif st == "rust":
            default_cat = "desktop-app"
        elif st == "cpp-switch":
            default_cat = "embedded-homebrew"
        else:
            default_cat = "mobile-app"

    category = _select_single(
        "1. Chọn Mục đích Dự án & Thể loại Sản phẩm (Product Category)",
        PRODUCT_CATEGORY_CHOICES,
        default_cat,
    )
    cat_info = PRODUCT_CATEGORIES[category]
    rec_stacks = cat_info["recommended_stacks"]

    stack_choices = [
        (k, f"{'★ ' if k in rec_stacks else '  '}{v['label']}")
        for k, v in STACK_CATALOG.items()
    ]
    default_stack = det["detected_stack"] if det["detected_stack"] in rec_stacks else rec_stacks[0]
    stack = _select_single(
        f"2. Chọn Tech Stack (Khuyên dùng: {', '.join(rec_stacks)})",
        stack_choices,
        default_stack,
    )
    info = STACK_CATALOG[stack]
    rec_arch = cat_info.get("recommended_arch") or info["recommended_arch"]
    arch = _select_single("3. Chọn Kiến trúc (Architecture Style)", ARCH_CHOICES, rec_arch)
    rec_pattern = cat_info.get("recommended_pattern") if any(k == cat_info.get("recommended_pattern") for k, _ in info["patterns"]) else info["recommended_pattern"]
    pattern = _select_single("4. Chọn Flow / State Pattern", info["patterns"], rec_pattern)
    repo_choices = [(r["repo"], f"{r['repo']} — {r['why'][:72]}...") for r in info["repos"]]
    ref_repo = _select_single("5. Chọn Famous Reference Repo chuẩn để neo theo", repo_choices, info["repos"][0]["repo"])
    i18n_info = info.get("i18n", {})
    i18n_standard = i18n_info.get("standard", "Platform Standard i18n")
    existing_feats = existing_profile.get("selectedFeatures") or []
    i18n_choice = _select_single(
        "6. Hỗ trợ đa ngôn ngữ (i18n/l10n)?",
        [
            ("yes", f"Có — Thiết lập sẵn kiến trúc đa ngôn ngữ ({i18n_standard})"),
            ("no", "Không — Chỉ dùng ngôn ngữ đơn bản mặc định"),
        ],
        "yes" if "i18n" in existing_feats or not existing_feats else "no",
    )
    chosen_locales = ["vi", "en"]
    if i18n_choice == "yes":
        existing_locs = existing_profile.get("i18n", {}).get("supportedLocales") or ["vi", "en"]
        loc_choices = [
            (code, label, code in existing_locs if existing_locs else default)
            for code, label, default in SUPPORTED_LOCALES_CHOICES
        ]
        chosen_locales = _select_multi("6b. Tick chọn các ngôn ngữ ứng dụng cần hỗ trợ (Locales)", loc_choices)
        if not chosen_locales:
            chosen_locales = ["vi", "en"]

    feature_choices = FEATURE_CHOICES
    if stack == "rust":
        feature_choices = [
            (
                key,
                "GitHub Actions CI (Linux/macOS/Windows matrix)" if key == "testing-ci" else label,
                default or key == "testing-ci",
            )
            for key, label, default in FEATURE_CHOICES
        ]
    feature_choices = [
        (
            key,
            label,
            True if (key == "i18n" and i18n_choice == "yes") else (False if (key == "i18n" and i18n_choice == "no") else default),
        )
        for key, label, default in feature_choices
    ]
    features = _select_multi("7. Tick chọn các Base Modules & Quality Gates muốn dựng", feature_choices)
    if i18n_choice == "yes" and "i18n" not in features:
        features.append("i18n")
    elif i18n_choice == "no" and "i18n" in features:
        features.remove("i18n")

    agents = _select_multi("8. Tick chọn các AI Agent & Security Hooks cần khởi tạo", AGENT_CHOICES)
    scaffold = _select_single(
        "9. Tạo sẵn cây thư mục chuẩn theo kiến trúc?",
        [("yes", "Có — tạo luôn cây thư mục mẫu"), ("no", "Không — chỉ tạo bộ cấu hình Agent, Hooks & ADR")],
        "yes" if det["mode"] == "greenfield" else "no",
    )
    results = init_project(
        target=target, stack=stack, arch=arch, pattern=pattern, features=features,
        agents=agents, ref_repo=ref_repo, scaffold_dirs=(scaffold == "yes"), force=force,
        locales=chosen_locales, category=category,
    )
    print("\n=== Hoàn tất khởi tạo Project Pro ===")
    for line in results:
        print(f"  {line}")
    return 0
