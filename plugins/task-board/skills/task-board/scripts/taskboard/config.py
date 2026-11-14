"""Config discovery. Precedence (unchanged): CLI flags > env vars > config file > git remote/fs detection.

Config files, first match wins:
  .agents/task-board.json   (new; carries `provider`)
  .github/project.json      (legacy; treated as provider github)
  .agents/project.json, .agents/workflow.json, project.json (legacy)
"""
import json
import os
import re
import subprocess
import sys

PROVIDER_NAMES = ("github", "gitlab", "local")
DEFAULT_PROVIDER = "github"
NEW_CONFIG_PATH = os.path.join(".agents", "task-board.json")


def detect_git_repo():
    """Extract (owner, repo) from git remote origin if available."""
    try:
        res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, check=False
        )
        url = res.stdout.strip()
        if not url:
            return None, None
        m = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)(?:\.git)?$", url)
        if m:
            return m.group(1), m.group(2)
    except Exception:
        pass
    return None, None


def find_config_file():
    """Locate project configuration file in standard repository locations."""
    candidates = [
        NEW_CONFIG_PATH,
        os.path.join(".github", "project.json"),
        os.path.join(".agents", "project.json"),
        os.path.join(".agents", "workflow.json"),
        "project.json",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


ENV_MAPPINGS = {
    "provider": "TASK_BOARD_PROVIDER",
    "owner": "GH_PROJECT_OWNER",
    "repo": "GH_PROJECT_REPO",
    "project_number": "GH_PROJECT_NUMBER",
    "project_id": "GH_PROJECT_ID",
    "tasks_dir": "GH_TASKS_DIR",
    "backlog_doc": "GH_BACKLOG_DOC",
    "cache_dir": "GH_CACHE_DIR",
}


def resolve_config(args=None):
    config = {
        "provider": None,
        "owner": None,
        "repo": None,
        "project_number": None,
        "project_id": None,
        "tasks_dir": None,
        "backlog_doc": None,
        "cache_dir": ".local-artifacts",
    }

    # 1. Config file (new .agents/task-board.json, else legacy files)
    cfg_file = getattr(args, "config", None) or find_config_file()
    if cfg_file and os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
            config.update({k: v for k, v in file_cfg.items() if v is not None})
        except Exception as e:
            print(f"[WARN] Failed to read config file {cfg_file}: {e}", file=sys.stderr)
    config["_config_file"] = cfg_file if cfg_file and os.path.exists(cfg_file) else None

    # 2. Environment variables
    for key, env_var in ENV_MAPPINGS.items():
        val = os.environ.get(env_var)
        if val:
            config[key] = val

    # 3. CLI flag overrides
    if args:
        for key in ENV_MAPPINGS:
            arg_val = getattr(args, key, None)
            if arg_val is not None:
                config[key] = arg_val

    # Legacy configs (and no config at all) mean provider github.
    config["provider"] = (config["provider"] or DEFAULT_PROVIDER).strip().lower()

    # 4. owner/repo from git remote
    if config["provider"] == "github" and (not config["owner"] or not config["repo"]):
        git_owner, git_repo = detect_git_repo()
        config["owner"] = config["owner"] or git_owner
        config["repo"] = config["repo"] or git_repo

    # 5. tasks_dir / 6. backlog_doc
    if not config["tasks_dir"]:
        for d in ["docs/tasks", "tasks", "specs", "docs/specs", ".tasks"]:
            if os.path.isdir(d):
                config["tasks_dir"] = d
                break
        config["tasks_dir"] = config["tasks_dir"] or "docs/tasks"
    if not config["backlog_doc"]:
        for doc in ["docs/BACKLOG.md", "BACKLOG.md", "docs/ROADMAP.md", "ROADMAP.md"]:
            if os.path.isfile(doc):
                config["backlog_doc"] = doc
                break
        config["backlog_doc"] = config["backlog_doc"] or "docs/BACKLOG.md"

    return config
