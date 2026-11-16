"""Configuration, repo discovery and CLI detection for agent-team.

CLI facts (verified on this machine with `--help`):
  codex-cli 0.153.4  `codex exec` flags used: -s/--sandbox read-only, -C/--cd,
                     -o/--output-last-message, --output-schema, --ephemeral,
                     --color, -m/--model; prompt read from stdin when the
                     PROMPT argument is `-`.
  agy 1.5.7          `-p/--print` takes the prompt as a flag VALUE (argv), has no
                     stdin mode and no read-only flag -> not supported as reviewer.
  gemini, claude     not installed here -> only usable through
                     `reviewer_commands` in the config, with flags the user
                     confirmed from `<cli> --help`.
"""
import json
import shutil
import subprocess
from pathlib import Path

CONFIG_REL = ".agent-team/config.json"

REVIEW_MODES = ("same-vendor", "cross-vendor")
PROFILES = ("dev", "research", "content", "ops", "general")
ESCAPE_HATCH_POLICIES = ("off", "warn", "fail")
AUTO_MERGE_TIERS = ("off", "low-risk")
PROFILE_PRESETS = {
    "dev": {"profile": "dev", "workspace_mode": "git-worktree", "require_git": True, "run_audit": True},
    "research": {"profile": "research", "workspace_mode": "dir", "require_git": False, "run_audit": False},
    "content": {"profile": "content", "workspace_mode": "dir", "require_git": False, "run_audit": False},
    "ops": {"profile": "ops", "workspace_mode": "dir", "require_git": False, "run_audit": False},
    "general": {"profile": "general", "workspace_mode": "dir", "require_git": False, "run_audit": False},
}

DEFAULTS = {
    # same-vendor: reviewer is a fresh-context read-only subagent of the lead's own vendor (default).
    # cross-vendor: reviewer is a CLI from another vendor (codex, ...); see references/cross-review.md.
    "review_mode": "same-vendor",
    "profile": "dev",
    "workspace_mode": "git-worktree",
    "require_git": True,
    "run_audit": True,
    "base_branch": "main",
    "max_verify_rounds": 3,
    "max_review_rounds": 2,
    "max_parallel": 3,
    "reviewer_preference": ["codex", "agy", "gemini", "claude"],
    "tasks_dir": "docs/tasks",
    "runs_dir": ".agent-team/runs",
    "worktrees_dir": ".worktrees",
    "check_timeout": 300,
    "review_timeout": 900,
    "max_diff_bytes": 200000,
    "output_tail_chars": 4000,
    "escape_hatch_policy": "warn",
    "auto_merge_tier": "off",
    # vendor -> argv list; prompt is piped on stdin, reply must be JSON on stdout.
    # Antigravity (agy) usually runs Gemini models; override to e.g. {"agy": "claude"} if yours differs.
    "vendor_family": {"agy": "gemini"},
    "reviewer_commands": {},
    "reviewer_models": {},
}


def find_root(start=None):
    start = Path(start or ".").resolve()
    try:
        out = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return start


def load_config(root):
    cfg = dict(DEFAULTS)
    path = Path(root) / CONFIG_REL
    if path.is_file():
        try:
            cfg.update(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            raise SystemExit(f"invalid {path}: {exc}")
    if cfg["review_mode"] not in REVIEW_MODES:
        raise SystemExit(f"invalid review_mode {cfg['review_mode']!r} in {path}; "
                         f"allowed: {', '.join(REVIEW_MODES)}")
    if cfg["profile"] not in PROFILES:
        raise SystemExit(f"invalid profile {cfg['profile']!r} in {path}; "
                         f"allowed: {', '.join(PROFILES)}")
    if cfg["escape_hatch_policy"] not in ESCAPE_HATCH_POLICIES:
        raise SystemExit(f"invalid escape_hatch_policy {cfg['escape_hatch_policy']!r} in {path}; "
                         f"allowed: {', '.join(ESCAPE_HATCH_POLICIES)}")
    if cfg["auto_merge_tier"] not in AUTO_MERGE_TIERS:
        raise SystemExit(f"invalid auto_merge_tier {cfg['auto_merge_tier']!r} in {path}; "
                         f"allowed: {', '.join(AUTO_MERGE_TIERS)}")
    return cfg


def family(cfg, vendor):
    """Model family of a vendor CLI; reviewer and coder must differ in family."""
    return cfg["vendor_family"].get(vendor, vendor)


class Ctx:
    def __init__(self, root=None):
        self.root = find_root(root)
        self.cfg = load_config(self.root)

    @property
    def tasks_dir(self):
        return self.root / self.cfg["tasks_dir"]

    def runs(self, task_id):
        return self.root / self.cfg["runs_dir"] / task_id


def which(name):
    return shutil.which(name)


def cli_version(name):
    path = which(name)
    if not path:
        return None
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else "unknown"
    except (OSError, subprocess.SubprocessError, IndexError):
        return "unknown"
