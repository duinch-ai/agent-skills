"""START_HERE.md for the non-technical owner (guided preset only): plain words, only real files and commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from catalog import PRODUCT_CATEGORIES
from safety import CHECK_COMMAND, CHECK_SCRIPT_PATH, safety_lines

ARCH_PLAIN = {
    "clean": "The code is split into three layers: screens, the rules of your product, and data storage. The rules never depend on the screens.",
    "modular-clean": "The code is split into separate modules, one per feature, plus shared building blocks; each feature has screens, rules and data parts.",
    "vertical-slice": "The code is grouped by feature: everything one feature needs lives together, so features can change without breaking each other.",
    "hexagonal": "The core rules of your product sit in the middle and know nothing about databases or the web; adapters connect them to the outside world.",
    "lightweight": "A small, simple layout: the core logic is kept apart from the parts that talk to files, the network or the user.",
}

FOLDERS = {
    "src": "the main program code", "lib": "the main program code", "app": "the main program code",
    "source": "the main program code", "cmd": "program entry points", "internal": "the main program code (private to this project)",
    "tests": "automatic tests that prove the code works", "test": "automatic tests that prove the code works",
    "docs": "documents, including the architecture decision record", "scripts": "helper scripts, including check.sh",
    "migrations": "database change history", "locales": "translated texts for each language",
    ".agents": "the project profile, rules and memory your AI agent reads",
    ".githooks": "automatic guards that run when you save (commit) or share (push) code",
    ".github": "automatic checks that run on GitHub", ".claude": "settings that keep the Claude agent inside the safety rules",
}


def _folders(target: Path) -> list[str]:
    names = sorted(p.name for p in target.iterdir() if p.is_dir() and p.name != ".git"
                   and (not p.name.startswith(".") or p.name in FOLDERS))
    return [f"- `{n}/` - {FOLDERS.get(n, 'project files; ask your agent what lives here')}." for n in names]


def _env_ignored(target: Path) -> bool:
    gi = target / ".gitignore"
    return gi.is_file() and ".env" in gi.read_text(encoding="utf-8", errors="ignore").splitlines()


def render_start_here(
    target: Path, name: str, info: dict[str, Any], arch: str, category: str, features: list[str], agents: list[str],
    check_present: bool,
) -> str:
    cat_label = PRODUCT_CATEGORIES.get(category, {}).get("label", category)
    cmds = info["commands"]
    run_lines = [f"- Build: `{cmds['build']}`"] if cmds.get("build") else []
    run_lines += [f"- {k.capitalize()}: `{cmds[k]}`" for k in ("run", "dev") if cmds.get(k)]
    run_lines.append("- To start the app itself, ask your agent: \"how do I run this project?\"")
    if check_present:
        check = [f"Run `{CHECK_COMMAND}` in a terminal. It runs the project's own checks one after another and prints one line each.",
                 "- `ALL CHECKS PASSED` means everything works. `CHECKS FAILED` means something broke; it stops at the first problem.",
                 "- If a step fails, tell your agent: \"fix the failing check\"."]
    else:
        check = [f"`{CHECK_SCRIPT_PATH}` already existed, so it was not replaced. Run it with `{CHECK_COMMAND}` if it is there."]
    secrets = ["- Never paste passwords, keys or tokens into the chat or into code."]
    if _env_ignored(target):
        secrets[0] += " Put secrets in a `.env` file instead; it is ignored by git, so it is never shared."
    safety = [f"- {s}" for s in safety_lines(features, agents)]
    if check_present:
        safety.append("- check.sh also runs the project-pro structure audit when project-pro is installed on this computer.")
    lines = [
        f"# {name} - start here", "",
        "This page is for the owner of the project, not for developers. No coding knowledge is needed.", "",
        "## 1. What this project is",
        f"- Name: {name}", f"- Kind of product: {cat_label}", f"- Built with: {info['label']}",
        f"- How the code is organised: {ARCH_PLAIN.get(arch, 'see AGENTS.md')}", "",
        "## 2. How to run it", *run_lines, "",
        "## 3. How to know it works", *check, "",
        "## 4. Working with an AI agent",
        "- Describe what you want in plain words, one small change at a time.",
        f"- Ask the agent to keep `{CHECK_COMMAND}` passing after every change.",
        "- For bigger work, the agent-team skill writes a task with its checks first, then does it.",
        *secrets, "",
        "## 5. Safety net that is switched on", *safety, "",
        "## 6. Where things are", *_folders(target), "",
        "## 7. Getting expert help",
        "- `AGENTS.md` is the technical description of this project for developers.",
        "- `docs/architecture/ADR-0001-architecture.md` explains why it is built this way." if "adr-docs" in agents else
        "- A developer can start from `AGENTS.md`; it lists the stack, commands and rules.",
    ]
    return "\n".join(lines) + "\n"
