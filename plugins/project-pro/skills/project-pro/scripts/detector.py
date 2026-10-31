"""Project mode detector, reference repository lookup, and codebase topology map generator."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
from typing import Any

from catalog import IGNORE_DIRS, SOURCE_EXTENSIONS, STACK_CATALOG


def _any_file_contains(paths: list[Path], needle: str) -> bool:
    for p in paths:
        if p.is_file() and needle.lower() in p.read_text(encoding="utf-8", errors="ignore").lower():
            return True
    return False


def detect_project(target: Path) -> dict[str, Any]:
    target = target.resolve()
    profile_path = target / ".agents" / "project-profile.json"
    existing_profile = None
    if profile_path.is_file():
        try:
            existing_profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except Exception:
            existing_profile = None

    files_top = [p.name for p in target.iterdir() if p.name not in {".git", ".DS_Store"}] if target.exists() else []
    is_greenfield = len(files_top) == 0

    detected_stack = None
    if existing_profile and existing_profile.get("stack") in STACK_CATALOG:
        detected_stack = existing_profile["stack"]
    elif target.exists():
        if (target / "pubspec.yaml").is_file():
            detected_stack = "flutter"
        elif (
            (target / "composeApp").is_dir()
            or _any_file_contains([target / "build.gradle.kts", target / "settings.gradle.kts"], 'kotlin("multiplatform")')
            or _any_file_contains([target / "gradle/libs.versions.toml"], "kotlinMultiplatform")
        ):
            detected_stack = "kmp"
        elif (target / "build.gradle.kts").is_file() or (target / "build.gradle").is_file() or (target / "app/build.gradle.kts").is_file():
            detected_stack = "android"
        elif (target / "Package.swift").is_file() or list(target.glob("*.xcodeproj")) or list(target.glob("*.xcworkspace")):
            detected_stack = "ios"
        elif (target / "go.mod").is_file():
            detected_stack = "go"
        elif (target / "package.json").is_file():
            pkg_text = (target / "package.json").read_text(encoding="utf-8", errors="ignore")
            detected_stack = "nestjs" if "@nestjs/core" in pkg_text else "web"
        elif (target / "pyproject.toml").is_file() or (target / "requirements.txt").is_file() or list(target.glob("*.py")):
            detected_stack = "python"

    harness_files = {
        "AGENTS.md": (target / "AGENTS.md").is_file(),
        "CLAUDE.md": (target / "CLAUDE.md").is_file(),
        "GEMINI.md": (target / "GEMINI.md").is_file(),
        ".agents/project-profile.json": profile_path.is_file(),
        ".agents/CODEBASE_MAP.md": (target / ".agents" / "CODEBASE_MAP.md").is_file(),
        ".agents/rules/execution-harness.md": (target / ".agents" / "rules" / "execution-harness.md").is_file(),
        ".agents/hooks.json": (target / ".agents" / "hooks.json").is_file(),
        ".githooks/pre-commit": (target / ".githooks" / "pre-commit").is_file(),
        ".githooks/pre-push": (target / ".githooks" / "pre-push").is_file(),
    }

    mode = "configured" if existing_profile else ("greenfield" if is_greenfield else "brownfield")
    stack_info = STACK_CATALOG.get(detected_stack or "")

    return {
        "target": str(target),
        "mode": mode,
        "detected_stack": detected_stack,
        "stack_label": stack_info["label"] if stack_info else None,
        "recommended_arch": stack_info["recommended_arch"] if stack_info else "clean",
        "recommended_pattern": stack_info["recommended_pattern"] if stack_info else "mvi",
        "recommended_ref_repo": stack_info["repos"][0]["repo"] if stack_info else None,
        "harness_present": harness_files,
        "existing_profile": existing_profile,
    }


def format_lookup_markdown(stack: str, query: str | None = None) -> str:
    stacks = list(STACK_CATALOG.keys()) if stack == "all" else [stack]
    lines: list[str] = []
    for st in stacks:
        info = STACK_CATALOG[st]
        lines.append(f"## {info['label']} (`--stack {st}`)")
        lines.append(f"- **Recommended Architecture**: `{info['recommended_arch']}`")
        lines.append(f"- **Recommended Flow Pattern**: `{info['recommended_pattern']}`")
        lines.append(f"- **Boundary Enforcement**: {info['boundary_tool']}\n")
        lines.append("### Available Presentation / Flow Patterns")
        for key, desc in info["patterns"]:
            lines.append(f"- `{key}`: {desc}")
        lines.append("\n### Gold-Standard Famous Reference Repositories")
        for r in info["repos"]:
            lines.append(f"- **[`{r['repo']}`]({r['url']})** — {r['why']}")
        if query:
            top_repo = info["repos"][0]["repo"]
            lines.append("\n### Suggested Live Verification Queries")
            lines.append(f"- GitHub Code Search: `gh search code \"{query}\" --repo {top_repo}`")
            lines.append(f"- Web Query: `site:github.com/{top_repo} {query}`")
        lines.append("")
    return "\n".join(lines).strip()


def generate_codebase_map(target: Path, write_file_out: bool = False) -> str:
    target = target.resolve()
    det = detect_project(target)
    module_stats: dict[str, dict[str, int]] = {}
    layer_counts = {"domain": 0, "data": 0, "presentation": 0, "core_shared": 0, "tests": 0, "other": 0}
    key_contracts: list[str] = []

    contract_re = re.compile(
        r"^\s*(?:public\s+|internal\s+|export\s+)?(?:sealed\s+)?(?:interface|protocol|abstract\s+class|class\s+\w+Repository|class\s+\w+UseCase|type\s+\w+Port)\s+([A-Za-z0-9_]+)"
    )

    for root, dirs, files in os.walk(target):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not d.startswith("."))
        root_path = Path(root)
        rel_dir = root_path.relative_to(target)
        parts = rel_dir.parts
        bucket = "/".join(parts[:3]) if parts else "."
        parts_lower = [p.lower() for p in parts]

        for fname in sorted(files):
            fpath = root_path / fname
            if fpath.suffix.lower() not in SOURCE_EXTENSIONS:
                continue
            try:
                lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue

            st = module_stats.setdefault(bucket, {"files": 0, "loc": 0})
            st["files"] += 1
            st["loc"] += len(lines)

            if any(t in parts_lower or t in fname.lower() for t in ("test", "tests", "spec")):
                layer_counts["tests"] += 1
            elif "domain" in parts_lower or any("coredomain" in p for p in parts_lower):
                layer_counts["domain"] += 1
            elif any(x in parts_lower for x in ("data", "adapter", "adapters", "infrastructure", "remote", "local")):
                layer_counts["data"] += 1
            elif any(x in parts_lower for x in ("presentation", "ui", "entrypoints", "controller", "pages", "components")):
                layer_counts["presentation"] += 1
            elif any(x in parts_lower for x in ("core", "shared", "common", "lib")):
                layer_counts["core_shared"] += 1
            else:
                layer_counts["other"] += 1

            if len(key_contracts) < 25:
                rel_file = fpath.relative_to(target)
                for ln in lines[:60]:
                    m = contract_re.search(ln)
                    if m:
                        key_contracts.append(f"- `{m.group(1)}` (`{rel_file}`)")
                        break

    now_str = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = [
        f"# Codebase Architecture Map — `{target.name}`\n",
        f"> Auto-generated by `project-pro map` ({now_str}). Read this first to save exploration tokens.",
        f"- **Detected Stack**: `{det['detected_stack'] or 'generic'}` | **Mode**: `{det['mode']}`\n",
        "## 1. Canonical Layer Dependency Flow",
        "```mermaid\nflowchart TD",
        '    UI["Presentation / Entrypoints"] --> DOM["Domain (Pure Policy & Ports)"]',
        '    DATA["Data / Adapters / Infra"] --> DOM',
        '    UI -.-> CORE["Core / Shared Primitives"]',
        "    DATA -.-> CORE\n```\n",
        "## 2. Layer Distribution (Code Files)",
        f"- **Domain**: `{layer_counts['domain']}` | **Data/Infra**: `{layer_counts['data']}` | "
        f"**Presentation/UI**: `{layer_counts['presentation']}` | **Core/Shared**: `{layer_counts['core_shared']}` | "
        f"**Tests**: `{layer_counts['tests']}` | **Other**: `{layer_counts['other']}`\n",
        "## 3. Module / Directory Index (Top Slices)",
    ]
    if module_stats:
        for mod, st in sorted(module_stats.items()):
            out.append(f"- `{mod}/` — `{st['files']}` files (`{st['loc']}` LOC)")
    else:
        out.append("- _(No source files yet — scaffolded skeleton)_")

    if key_contracts:
        out.extend(["", "## 4. Key Contracts & Entry Interfaces", *key_contracts])

    md = "\n".join(out) + "\n"
    if write_file_out:
        dest = target / ".agents" / "CODEBASE_MAP.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(md, encoding="utf-8")
    return md
