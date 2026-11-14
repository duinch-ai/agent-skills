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

DEFAULTS = {
    "base_branch": "main",
    "max_verify_rounds": 3,
    "max_review_rounds": 2,
    "max_parallel": 3,
    "coder_vendor": "claude",
    "reviewer_preference": ["codex", "agy", "gemini", "claude"],
    "tasks_dir": "docs/tasks",
    "runs_dir": ".agent-team/runs",
    "check_timeout": 300,
    "review_timeout": 900,
    "max_diff_bytes": 200000,
    "output_tail_chars": 4000,
    # vendor -> argv list; prompt is piped on stdin, reply must be JSON on stdout.
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
    return cfg


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
