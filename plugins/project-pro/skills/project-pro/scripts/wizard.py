"""Interactive terminal checkbox TUI wizard for project-pro."""

from __future__ import annotations

from pathlib import Path
import sys

from catalog import AGENT_CHOICES, ARCH_CHOICES, FEATURE_CHOICES, STACK_CATALOG
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
    stack = _select_single("1. Chọn Tech Stack", [(k, v["label"]) for k, v in STACK_CATALOG.items()], det["detected_stack"] or "kmp")
    info = STACK_CATALOG[stack]
    arch = _select_single("2. Chọn Kiến trúc (Architecture Style)", ARCH_CHOICES, info["recommended_arch"])
    pattern = _select_single("3. Chọn Flow / State Pattern", info["patterns"], info["recommended_pattern"])
    repo_choices = [(r["repo"], f"{r['repo']} — {r['why'][:72]}...") for r in info["repos"]]
    ref_repo = _select_single("4. Chọn Famous Reference Repo chuẩn để neo theo", repo_choices, info["repos"][0]["repo"])
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
    features = _select_multi("5. Tick chọn các Base Modules & Quality Gates muốn dựng", feature_choices)
    agents = _select_multi("6. Tick chọn các AI Agent & Security Hooks cần khởi tạo", AGENT_CHOICES)
    scaffold = _select_single(
        "7. Tạo sẵn cây thư mục chuẩn theo kiến trúc?",
        [("yes", "Có — tạo luôn cây thư mục mẫu"), ("no", "Không — chỉ tạo bộ cấu hình Agent, Hooks & ADR")],
        "yes" if det["mode"] == "greenfield" else "no",
    )
    results = init_project(
        target=target, stack=stack, arch=arch, pattern=pattern, features=features,
        agents=agents, ref_repo=ref_repo, scaffold_dirs=(scaffold == "yes"), force=force,
    )
    print("\n=== Hoàn tất khởi tạo Project Pro ===")
    for line in results:
        print(f"  {line}")
    return 0
