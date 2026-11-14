import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from auditor import audit_project  # noqa: E402


class IgnoreWorktreesTests(unittest.TestCase):
    def test_audit_ignores_task_worktrees(self):
        root = Path(tempfile.mkdtemp())
        (root / "ok.py").write_text("x = 1\n")
        big = root / ".worktrees/TASK-1/big.py"
        big.parent.mkdir(parents=True)
        big.write_text("x = 1\n" * 600)
        rep = audit_project(root)
        self.assertFalse(any(".worktrees" in e for e in rep["errors"] + rep["warnings"]), rep)
        (root / "big.py").write_text("x = 1\n" * 600)
        rep = audit_project(root)
        self.assertTrue(any("big.py" in e and ".worktrees" not in e for e in rep["errors"]), rep)


if __name__ == "__main__":
    unittest.main()
