import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import config  # noqa: E402

TASK = """# TASK-01 — Add greeting
Status: Todo
Priority: P1

## Goal
Print hello.

## Acceptance criteria
- [ ] prints hello
  check: `test "$(cat hello.txt)" = hello`
- [ ] second
  check: true
"""


def sh(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


def make_repo(task_text=TASK):
    tmp = tempfile.mkdtemp()
    root = Path(tmp)
    sh(root, "git", "init", "-q", "-b", "main")
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/tasks/TASK-01.md").write_text(task_text)
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-qm", "base")
    sh(root, "git", "checkout", "-qb", "feat")
    (root / "hello.txt").write_text("hello")
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-qm", "feat")
    return root


def fake_cli(name, body):
    """Create an executable `name` in a temp dir and return the dir (to prepend to PATH)."""
    d = Path(tempfile.mkdtemp())
    p = d / name
    p.write_text("#!/usr/bin/env python3\n" + body)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return d


APPROVE = ('{"verdict":"approve","findings":[],"tautological_tests":[],"summary":"ok"}')
CHANGES = ('{"verdict":"changes_requested","findings":[{"severity":"high","file":"a.py","line":3,'
           '"issue":"bug","criterion":"AC1"}],"tautological_tests":["t"],"summary":"no"}')


def codex_body(reply):
    # mimics `codex exec ... -o FILE -`: reads stdin, writes the last message to FILE.
    return ("import sys\na=sys.argv\nsys.stdin.read()\n"
            "open(a[a.index('-o')+1],'w').write(%r)\n" % reply)


def ctx_for(root):
    return config.Ctx(root)
