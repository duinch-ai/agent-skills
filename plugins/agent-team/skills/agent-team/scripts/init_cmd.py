"""`init`: write config, ignore run artifacts, install subagent templates."""
import json
import shutil
from pathlib import Path

import config

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "agents"
RULES = Path(__file__).resolve().parent.parent / "assets" / "rules"
WORKFLOW_REL = ".agents/rules/agent-workflow.md"
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


def init(ctx, force=False):
    root = ctx.root
    msgs = []
    cfg_path = root / config.CONFIG_REL
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.exists() and not force:
        msgs.append(f"kept {config.CONFIG_REL}")
    else:
        keep = {k: v for k, v in config.DEFAULTS.items()}
        cfg_path.write_text(json.dumps(keep, indent=2) + "\n", encoding="utf-8")
        msgs.append(f"wrote {config.CONFIG_REL}")
    gi = root / ".gitignore"
    line = ctx.cfg["runs_dir"].rstrip("/") + "/"
    text = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if line not in text.splitlines():
        gi.write_text(text + ("" if text.endswith("\n") or not text else "\n") + line + "\n", encoding="utf-8")
        msgs.append(f"added {line} to .gitignore")
    dest = root / ".claude" / "agents"
    dest.mkdir(parents=True, exist_ok=True)
    for src in sorted(ASSETS.glob("*.md")):
        target = dest / src.name
        if target.exists() and not force:
            msgs.append(f"kept .claude/agents/{src.name}")
        else:
            shutil.copyfile(src, target)
            msgs.append(f"installed .claude/agents/{src.name}")
    wf = root / WORKFLOW_REL
    if wf.exists() and not force:
        msgs.append(f"kept {WORKFLOW_REL}")
    else:
        wf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RULES / "agent-workflow.md", wf)
        msgs.append(f"wrote {WORKFLOW_REL}")
        msgs.append(link_agents_md(root))
    for cli in ("codex", "gemini", "claude", "agy"):
        v = config.cli_version(cli)
        msgs.append(f"cli {cli}: {v if v else 'not found'}")
    msgs.append("note: only codex has built-in reviewer flags; for gemini/claude add reviewer_commands "
                "after confirming flags with `<cli> --help`; agy cannot take a prompt on stdin.")
    return msgs
