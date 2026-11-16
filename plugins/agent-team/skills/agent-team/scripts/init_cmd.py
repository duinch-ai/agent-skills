"""`init`: write config, ignore run artifacts, install subagent templates."""
import json
import os
import shutil
from pathlib import Path

import config

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "agents"
RULES = Path(__file__).resolve().parent.parent / "assets" / "rules"
WORKFLOW_REL = ".agents/rules/agent-workflow.md"
AGENTS_DIR_REL = ".agents/agents"
AGENT_LINK_VENDORS = (".claude", ".codex", ".gemini", ".agy")
# Must match project-pro's templates (agents_md.py): the neutral line and its link variant.
NEUTRAL_LINE = "Agent working method: agent-team skill (optional)"
LINK_LINE = "Agent working method: see [`.agents/rules/agent-workflow.md`](./.agents/rules/agent-workflow.md)"


def link_agents_md(root):
    """Swap the neutral AGENTS.md line for the link line once the workflow file exists; touch nothing else."""
    path = root / "AGENTS.md"
    if not path.is_file():
        return "hint: no AGENTS.md; add this line to it: " + LINK_LINE
    text = path.read_text(encoding="utf-8")
    if LINK_LINE in text:
        return "kept AGENTS.md (working-method link already present)"
    lines = text.split("\n")
    hits = [i for i, ln in enumerate(lines) if ln.strip() in (NEUTRAL_LINE, "- " + NEUTRAL_LINE)]
    if len(hits) != 1:
        return f"hint: AGENTS.md has no '{NEUTRAL_LINE}' line; add yourself: {LINK_LINE}"
    i = hits[0]
    lines[i] = lines[i].replace(NEUTRAL_LINE, LINK_LINE)
    path.write_text("\n".join(lines), encoding="utf-8")
    return "updated AGENTS.md (working-method line now links .agents/rules/agent-workflow.md)"


def ensure_gitignore(root, dirs):
    """Add each `<dir>/` to .gitignore if missing (idempotent); one message per line added."""
    gi = root / ".gitignore"
    text = gi.read_text(encoding="utf-8") if gi.exists() else ""
    msgs = []
    for d in dirs:
        line = d.rstrip("/") + "/"
        if line not in text.splitlines():
            text += ("" if text.endswith("\n") or not text else "\n") + line + "\n"
            msgs.append(f"added {line} to .gitignore")
    if msgs:
        gi.write_text(text, encoding="utf-8")
    return msgs


def install_agents(root, force=False):
    """Install canonical subagent templates in .agents/agents/ and symlink vendor dirs to them."""
    msgs = []
    canonical_dir = root / AGENTS_DIR_REL
    canonical_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted(ASSETS.glob("*.md"))
    for src in sources:
        target = canonical_dir / src.name
        if target.exists() and not force:
            msgs.append(f"kept {AGENTS_DIR_REL}/{src.name}")
        else:
            shutil.copyfile(src, target)
            msgs.append(f"installed {AGENTS_DIR_REL}/{src.name}")
    for vendor in AGENT_LINK_VENDORS:
        vdir = root / vendor / "agents"
        vdir.mkdir(parents=True, exist_ok=True)
        for src in sources:
            link = vdir / src.name
            rel_target = os.path.relpath(canonical_dir / src.name, vdir)
            if link.is_symlink():
                if os.readlink(link) == rel_target and not force:
                    msgs.append(f"kept {vendor}/agents/{src.name}")
                    continue
                link.unlink()
            elif link.exists():
                if not force:
                    msgs.append(f"kept {vendor}/agents/{src.name}")
                    continue
                link.unlink()
            try:
                link.symlink_to(rel_target)
                msgs.append(f"linked {vendor}/agents/{src.name} -> {rel_target}")
            except OSError:
                shutil.copyfile(canonical_dir / src.name, link)
                msgs.append(f"copied {vendor}/agents/{src.name} (symlink unavailable)")
    return msgs


_VERIFY_SKILL_MD = """---
name: verify-app
description: Project-local runtime verification skill with a custom driver CLI, doctor preflight, and user-POV feature map.
---

# Verify App

## 1. Doctor (preflight before driving)
Run the doctor command first to confirm the app, runtime dependencies, and test fixtures are healthy.

## 2. Proof bar
- Exercise the real user path (CLI, API, or UI driver), never a stale build.
- Use state inspection only to assert side effects after driving the real flow.
- Save screenshots, logs, or recordings to `.agent-team/runs/TASK-n/artifacts/` when the task has `Artifacts:`.

## 3. Feature map
Read `references/features/README.md` before driving a feature so you use the shared vocabulary and known gotchas.
"""

_FEATURES_README = """# Feature Map

User-POV map of app surfaces. Keep one file per feature using `_template.md`.
"""

_FEATURE_TEMPLATE = """# <Feature Name>

## Sub-features
- ...

## How to get to it (user POV)
1. ...

## Driving it with <cli>
```bash
# doctor + drive commands
```

## Gotchas
- ...
"""


def install_verify_skill(root, force=False):
    """Scaffold .agents/skills/verify-app/ with SKILL.md and feature map template."""
    msgs = []
    base = root / ".agents" / "skills" / "verify-app"
    files = {
        base / "SKILL.md": _VERIFY_SKILL_MD,
        base / "references" / "features" / "README.md": _FEATURES_README,
        base / "references" / "features" / "_template.md": _FEATURE_TEMPLATE,
    }
    for path, content in files.items():
        rel = path.relative_to(root).as_posix()
        if path.exists() and not force:
            msgs.append(f"kept {rel}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            msgs.append(f"wrote {rel}")
    return msgs


def init(ctx, force=False, profile="dev", verify_skill=False):
    if profile not in config.PROFILE_PRESETS:
        raise SystemExit(f"invalid profile {profile!r}; allowed: {', '.join(config.PROFILES)}")
    root = ctx.root
    msgs = []
    preset = config.PROFILE_PRESETS[profile]
    cfg_path = root / config.CONFIG_REL
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.exists() and not force:
        msgs.append(f"kept {config.CONFIG_REL}")
    else:
        keep = {**config.DEFAULTS, **preset}
        cfg_path.write_text(json.dumps(keep, indent=2) + "\n", encoding="utf-8")
        msgs.append(f"wrote {config.CONFIG_REL} (profile={profile})")
    ig_dirs = [ctx.cfg["runs_dir"]]
    if preset["workspace_mode"] == "git-worktree":
        ig_dirs.append(ctx.cfg["worktrees_dir"])
    msgs.extend(ensure_gitignore(root, ig_dirs))
    msgs.extend(install_agents(root, force=force))
    wf = root / WORKFLOW_REL
    if wf.exists() and not force:
        msgs.append(f"kept {WORKFLOW_REL}")
    else:
        wf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RULES / "agent-workflow.md", wf)
        msgs.append(f"wrote {WORKFLOW_REL}")
        msgs.append(link_agents_md(root))
    if verify_skill:
        msgs.extend(install_verify_skill(root, force=force))
    for cli in ("codex", "gemini", "claude", "agy"):
        v = config.cli_version(cli)
        msgs.append(f"cli {cli}: {v if v else 'not found'}")
    msgs.append("note: only codex has built-in reviewer flags; for gemini/claude add reviewer_commands "
                "after confirming flags with `<cli> --help`; agy cannot take a prompt on stdin.")
    return msgs
