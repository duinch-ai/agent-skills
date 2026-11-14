"""The single choke point for every `gh` CLI call, so tests can swap it (set_runner)."""
import subprocess


def _subprocess_runner(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


_runner = _subprocess_runner


def set_runner(fn=None):
    """Install fn(cmd) -> (returncode, stdout, stderr); None restores the real subprocess runner."""
    global _runner
    _runner = fn or _subprocess_runner


def run_gh(cmd, check=True):
    """Run a gh CLI command and return (returncode, stdout, stderr)."""
    rc, out, err = _runner(cmd)
    out, err = (out or "").strip(), (err or "").strip()
    if check and rc != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{err}")
    return rc, out, err
