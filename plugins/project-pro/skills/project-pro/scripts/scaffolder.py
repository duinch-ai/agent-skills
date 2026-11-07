"""Project harness, memory, Git hooks, and AI runtime guard scaffolder."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import stat
import subprocess

from catalog import STACK_CATALOG
from detector import generate_codebase_map
import templates as tpl


def init_project(
    target: Path,
    stack: str,
    arch: str,
    pattern: str,
    features: list[str],
    agents: list[str],
    ref_repo: str | None = None,
    project_name: str | None = None,
    scaffold_dirs: bool = False,
    force: bool = False,
) -> list[str]:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    info = STACK_CATALOG[stack]
    chosen_repo = ref_repo or info["repos"][0]["repo"]
    chosen_repo_url = next(
        (r["url"] for r in info["repos"] if r["repo"] == chosen_repo),
        f"https://github.com/{chosen_repo}",
    )
    name = project_name or target.name
    agent_set = set(agents)
    if "precommit" in agent_set:
        agent_set.add("git-security-hooks")

    created: list[str] = []
    skill_script = Path(__file__).resolve().parent / "project_pro.py"

    def write_safe(rel_path: str, content: str, executable: bool = False) -> None:
        dest = target / rel_path
        if dest.exists() and not force:
            created.append(f"SKIP (exists): {rel_path}")
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        if executable:
            dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        created.append(f"WRITE: {rel_path}")

    profile = {
        "schemaVersion": "1.2.0",
        "generator": "project-pro",
        "updatedAt": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "projectName": name,
        "stack": stack,
        "stackLabel": info["label"],
        "architecture": arch,
        "pattern": pattern,
        "referenceRepo": chosen_repo,
        "referenceRepoUrl": chosen_repo_url,
        "fileLineLimits": {"warn": 300, "fail": 450},
        "selectedFeatures": features,
        "selectedAgentTargets": sorted(agent_set),
        "commands": info["commands"],
    }

    if "agents-root" in agent_set:
        write_safe(".agents/project-profile.json", json.dumps(profile, indent=2, ensure_ascii=False) + "\n")
        write_safe("AGENTS.md", tpl.render_agents_md(name, info, arch, pattern, chosen_repo, chosen_repo_url, features))
        write_safe(".agents/rules/execution-harness.md", tpl.render_execution_harness_rule(info))
        write_safe(".agents/rules/security-gate.md", tpl.render_security_rule())
        write_safe(".agents/rules/domain-layer.md", tpl.render_domain_rule(info, arch))
        write_safe(".agents/rules/data-layer.md", tpl.render_data_rule(features, info))
        write_safe(".agents/rules/presentation-layer.md", tpl.render_presentation_rule(pattern, info))
        write_safe(".editorconfig", tpl.render_editorconfig())
        _ensure_gitignore_secrets(target, created)

    if stack == "rust" and "testing-ci" in features:
        write_safe(".github/workflows/rust.yml", tpl.render_rust_ci_workflow())
    elif stack == "cpp-switch" and "testing-ci" in features:
        write_safe(".github/workflows/switch-build.yml", tpl.render_cpp_switch_ci_workflow(name))

    if "claude-gemini" in agent_set:
        write_safe(
            "CLAUDE.md",
            (
                f"# {name} — Claude Code Instructions\n\n@AGENTS.md\n\n"
                "- Follow the 6-Gate coding workflow in `.agents/rules/execution-harness.md`.\n"
                "- Enforce `.agents/rules/security-gate.md` (zero hardcoded secrets, <= 450 LOC per file).\n"
                f"- Reference baseline: `{chosen_repo}` ({chosen_repo_url}).\n"
            ),
        )
        write_safe(
            "GEMINI.md",
            (
                f"# {name} — Antigravity & Gemini Instructions\n\n@[AGENTS.md](./AGENTS.md)\n\n"
                "- Execute EVERY coding request through [`.agents/rules/execution-harness.md`](./.agents/rules/execution-harness.md).\n"
                "- Enforce [`.agents/rules/security-gate.md`](./.agents/rules/security-gate.md) and `.agents/rules/`.\n"
                f"- Reference baseline: `{chosen_repo}` ({chosen_repo_url}).\n"
            ),
        )

    if "git-security-hooks" in agent_set:
        _ensure_gitignore_secrets(target, created)
        write_safe(".githooks/pre-commit", tpl.render_pre_commit_hook(skill_script), executable=True)
        write_safe(".githooks/commit-msg", tpl.render_commit_msg_hook(skill_script), executable=True)
        write_safe(".githooks/pre-push", tpl.render_pre_push_hook(skill_script, info), executable=True)
        if (target / ".git").exists():
            try:
                subprocess.run(
                    ["git", "-C", str(target), "config", "core.hooksPath", ".githooks"],
                    check=True,
                    capture_output=True,
                )
                created.append("GIT-CONFIG: core.hooksPath = .githooks")
            except Exception as exc:
                created.append(f"WARN: Could not set core.hooksPath automatically ({exc})")

    if "agent-runtime-hooks" in agent_set:
        guard_cmd = f'python3 "{skill_script}" agent-guard'
        agy_hooks = {
            "project-pro-safety-guard": {
                "enabled": True,
                "PreToolUse": [
                    {"matcher": "run_command", "hooks": [{"type": "command", "command": guard_cmd, "timeout": 10}]}
                ],
            }
        }
        write_safe(".agents/hooks.json", json.dumps(agy_hooks, indent=2) + "\n")
        _write_or_merge_claude_settings(target, guard_cmd, force, created)

    if "adr-docs" in agent_set:
        write_safe(
            "docs/architecture/ADR-0001-architecture.md",
            tpl.render_adr(name, info, arch, pattern, chosen_repo, chosen_repo_url, features),
        )

    if "cursor-ide" in agent_set:
        write_safe(
            ".cursor/rules/00-project-architecture.mdc",
            (
                "---\n"
                f"description: Core architecture ({arch} + {pattern}), 6-Gate Execution Harness & Security rules for {name}\n"
                "globs:\nalwaysApply: true\n---\n\n"
                "Strictly follow `AGENTS.md`, `.agents/rules/execution-harness.md`, and `.agents/rules/security-gate.md`.\n"
                f"- **Stack**: {info['label']} | **Arch**: `{arch}` | **Pattern**: `{pattern}` | **Ref**: `{chosen_repo}`\n"
                "- **Hard File Cap**: Warn > 300 LOC, Fail > 450 LOC. Zero hardcoded secrets.\n"
            ),
        )
        pointer_text = (
            f"# {name} — AI Coding & Security Rules\n\n"
            "Strictly follow `AGENTS.md`, `.agents/rules/execution-harness.md`, and `.agents/rules/security-gate.md`.\n"
            f"Architecture: `{arch}` | Pattern: `{pattern}` | Reference Repo: `{chosen_repo}` | Max File Lines: `450`.\n"
        )
        write_safe(".clinerules", pointer_text)
        write_safe(".windsurfrules", pointer_text)

    if scaffold_dirs:
        dirs = info.get("scaffold_dirs", {}).get(arch) or next(iter(info.get("scaffold_dirs", {}).values()), [])
        for d in dirs:
            dir_path = target / d
            dir_path.mkdir(parents=True, exist_ok=True)
            if not any(dir_path.iterdir()):
                (dir_path / ".gitkeep").write_text("", encoding="utf-8")
                created.append(f"MKDIR: {d}/")

    if "persistent-memory" in agent_set:
        write_safe(
            ".agents/memory/lessons.md",
            (
                f"# {name} — Continuous Learning & Mistake Ledger\n\n"
                "> Read during Gate 1. Append 2-line prevention rules (`Symptom -> Root Cause & Rule`) whenever a subtle bug or user correction occurs.\n\n"
            ),
        )
        write_safe(
            ".agents/memory/active-plan.md",
            (
                f"# {name} — Active Multi-Step Plan (`planning-with-files`)\n\n"
                "## Goal\n- _No multi-step task active._\n\n## Planned File Slices\n- [ ] `path/to/file` — responsibility\n"
            ),
        )
        write_safe(".agents/CODEBASE_MAP.md", generate_codebase_map(target, write_file_out=False))

    return created


def _ensure_gitignore_secrets(target: Path, created: list[str]) -> None:
    gitignore = target / ".gitignore"
    entries = [
        "# Security & Secret Hygiene (managed by project-pro)",
        ".env", ".env.*", "!.env.example", "!.env.sample", "!.env.template",
        "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore", "service-account*.json",
    ]
    if not gitignore.exists():
        gitignore.write_text("\n".join(entries) + "\n", encoding="utf-8")
        created.append("WRITE: .gitignore (secret protection rules)")
        return
    existing = gitignore.read_text(encoding="utf-8", errors="ignore")
    missing = [ln for ln in entries[1:] if ln not in existing.splitlines()]
    if missing:
        gitignore.write_text(existing.rstrip("\n") + "\n\n" + entries[0] + "\n" + "\n".join(missing) + "\n", encoding="utf-8")
        created.append("UPDATE: .gitignore (+secret protection entries)")


def _write_or_merge_claude_settings(target: Path, guard_cmd: str, force: bool, created: list[str]) -> None:
    settings_path = target / ".claude" / "settings.json"
    hook_entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": guard_cmd, "timeout": 10}]}
    if settings_path.is_file() and not force:
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            created.append("SKIP (invalid JSON): .claude/settings.json")
            return
        pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
        if not any(guard_cmd in json.dumps(item) for item in pre):
            pre.append(hook_entry)
            settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            created.append("UPDATE: .claude/settings.json (+PreToolUse agent-guard)")
        return
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps({"hooks": {"PreToolUse": [hook_entry]}}, indent=2) + "\n", encoding="utf-8")
    created.append("WRITE: .claude/settings.json")
