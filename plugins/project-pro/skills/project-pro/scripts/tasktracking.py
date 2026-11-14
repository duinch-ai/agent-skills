"""Optional `task-tracking` capability: wires docs/tasks + docs/BACKLOG.md for a task-board skill.

project-pro only prepares folders and tells the user the next step. All board sync belongs to the
provider skill (it needs the user's project number and calls the provider API, so it is never run
from here). Provider specifics live ONLY in TASK_PROVIDERS; add `gitlab` there once task-board implements it.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_PROVIDER = "github"
_SKILL_SUBDIRS = [".agent-skills/plugins/{skill}/skills/{skill}", ".claude/skills/{skill}",
                  ".codex/skills/{skill}", ".gemini/skills/{skill}", ".agents/skills/{skill}",
                  ".copilot/skills/{skill}"]
_PLUGIN_GLOBS = [".claude/plugins/*/{skill}/skills/{skill}", ".claude/plugins/*/*/{skill}/skills/{skill}"]
_COMMON = {
    "skill": "task-board",
    "skill_subdirs": _SKILL_SUBDIRS,
    "plugin_globs": _PLUGIN_GLOBS,
    "env_dir": "TASK_BOARD_DIR",
    "config_file": ".agents/task-board.json",
    "tasks_dir": "docs/tasks",
    "backlog_doc": "docs/BACKLOG.md",
}
TASK_PROVIDERS: dict[str, dict] = {
    "github": {
        **_COMMON,
        "label": "GitHub Project",
        "init_cmd": "python3 {skill_dir}/scripts/project_board.py init --provider github --project <N>",
        "init_note": "creates {config_file}; needs your project number and the provider API",
        # Transition fallback: the skill was called github-project-workflow and read .github/project.json.
        "legacy_skills": ["github-project-workflow"],
        "legacy_env_dirs": ["GITHUB_PROJECT_WORKFLOW_DIR"],
        "legacy_config_files": [".github/project.json"],
        "legacy_init_cmd": "python3 {skill_dir}/scripts/project_board.py init --project <N>",
    },
    "local": {
        **_COMMON,
        "label": "Local only (no remote board)",
        "init_cmd": "python3 {skill_dir}/scripts/project_board.py init --provider local",
        "init_note": "creates {config_file}; no remote, no API",
    },
    # gitlab: coming (task-board ships a stub only); add an entry here once the provider is implemented.
}

# BACKLOG row format parsed by project_board.parse_backlog_issue_map:  | TASK-01 | [#12](url) | ...
BACKLOG_TEMPLATE = """# Backlog

> Managed with the `{skill}` skill. Specs live in `docs/tasks/TASK-<n>.md`.
> The skill records each issue as `[#<n>](url)` in the second column.

| Task | Issue | Status | Title |
|---|---|---|---|
"""


def provider_info(provider: str | None) -> dict:
    return TASK_PROVIDERS[provider or DEFAULT_PROVIDER]


def profile_provider(profile: dict | None) -> str:
    p = ((profile or {}).get("taskTracking") or {}).get("provider")
    return p if p in TASK_PROVIDERS else DEFAULT_PROVIDER


def agents_md_section(provider: str | None) -> str:
    pi = provider_info(provider)
    return (
        "## 6. Task Workflow\n"
        f"- Task board (provider: {provider or DEFAULT_PROVIDER}, skill `{pi['skill']}`): specs in `{pi['tasks_dir']}/`, "
        f"backlog in `{pi['backlog_doc']}`; use that skill for board sync and the `agent-team` skill for multi-agent team work.\n"
    )


def _candidate_dirs(pi: dict) -> list[tuple[Path, bool]]:
    """(dir, is_legacy) in priority order: current name/env first, legacy fallbacks after."""
    home = Path.home()
    cands: list[tuple[Path, bool]] = []
    for legacy, skill in [(False, pi["skill"])] + [(True, n) for n in pi.get("legacy_skills", [])]:
        envs = [pi["env_dir"]] if not legacy else pi.get("legacy_env_dirs", [])
        cands += [(Path(os.environ[e]), legacy) for e in envs if os.environ.get(e)]
        cands += [(home / sub.format(skill=skill), legacy) for sub in pi["skill_subdirs"]]
        for pat in pi["plugin_globs"]:
            cands += [(d, legacy) for d in sorted(home.glob(pat.format(skill=skill)))]
    return cands


def find_skill(provider: str | None = None) -> tuple[Path | None, bool]:
    for d, legacy in _candidate_dirs(provider_info(provider)):
        if (d / "SKILL.md").is_file():
            return d, legacy
    return None, False


def find_skill_dir(provider: str | None = None) -> Path | None:
    return find_skill(provider)[0]


def scaffold(target: Path, write_safe, provider: str | None = None) -> list[str]:
    """Create tasks dir and backlog doc (never overwriting) and return guidance lines."""
    pi = provider_info(provider)
    notes: list[str] = []
    tasks_dir = target / pi["tasks_dir"]
    tasks_dir.mkdir(parents=True, exist_ok=True)
    # .gitkeep, not a README.md: the board tool treats every *.md in the tasks dir as a task spec.
    if not (tasks_dir / ".gitkeep").exists():
        (tasks_dir / ".gitkeep").write_text("", encoding="utf-8")
        notes.append(f"MKDIR: {pi['tasks_dir']}/")
    write_safe(pi["backlog_doc"], BACKLOG_TEMPLATE.format(skill=pi["skill"]))
    skill_dir, legacy = find_skill(provider)
    if skill_dir is None:
        notes.append(
            f"NOTE: skill `{pi['skill']}` not found. Install it (never auto-installed): copy or symlink its folder to "
            f"~/.claude/skills/{pi['skill']} (or set {pi['env_dir']}), then run the next step below."
        )
        shown = f"<{pi['skill']} skill dir>"
    else:
        notes.append(f"OK: `{pi['skill']}` found at {skill_dir}")
        shown = str(skill_dir)
    init_cmd, config_file = pi["init_cmd"], pi["config_file"]
    if legacy:  # old github-project-workflow install: no --provider flag, writes the old config file
        init_cmd, config_file = pi["legacy_init_cmd"], pi["legacy_config_files"][0]
        notes.append(f"NOTE: found the old `{skill_dir.name}` install; update to `{pi['skill']}` when you can.")
    notes.append(f"NEXT: {init_cmd.format(skill_dir=shown)}   ({pi['init_note'].format(config_file=config_file)})")
    return notes


def tracking_state(target: Path, profile: dict | None) -> str:
    """off | configured | ticked-not-initialized."""
    ticked = "task-tracking" in ((profile or {}).get("selectedFeatures") or [])
    pi = provider_info(profile_provider(profile))
    if any((target / f).is_file() for f in [pi["config_file"], *pi.get("legacy_config_files", [])]):
        return "configured"
    return "ticked-not-initialized" if ticked else "off"
