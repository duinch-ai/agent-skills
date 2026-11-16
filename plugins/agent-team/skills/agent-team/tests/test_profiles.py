import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import agent_team
import config
import helpers as h


class ProfileTests(unittest.TestCase):
    def _make_non_git_workspace(self):
        root = Path(tempfile.mkdtemp(prefix="agent_team_nongit_"))
        (root / "docs/tasks").mkdir(parents=True)
        (root / "docs/tasks/TASK-01.md").write_text(
            "# TASK-01 — Write report\nStatus: In Progress\n\n## Acceptance criteria\n"
            "- [ ] Report exists\n  check: `test -f report.md`\n",
            encoding="utf-8",
        )
        (root / "report.md").write_text("# Market Report\nSummary\n", encoding="utf-8")
        return root

    def _run(self, root, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = agent_team.main(["--root", str(root), *args])
        return rc, out.getvalue(), err.getvalue()

    def test_init_research_profile_without_git(self):
        root = self._make_non_git_workspace()
        rc, out, _ = self._run(root, "init", "--profile", "research")
        self.assertEqual(rc, 0)
        self.assertIn("profile=research", out)
        cfg = json.loads((root / config.CONFIG_REL).read_text(encoding="utf-8"))
        self.assertEqual(cfg["profile"], "research")
        self.assertEqual(cfg["workspace_mode"], "dir")
        self.assertFalse(cfg["require_git"])
        self.assertFalse(cfg["run_audit"])
        gi = (root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".agent-team/runs/", gi)
        self.assertNotIn(".worktrees/", gi)

    def test_non_dev_verify_review_gate_flow_without_git(self):
        root = self._make_non_git_workspace()
        self._run(root, "init", "--profile", "research")
        self.assertEqual(self._run(root, "verify", "TASK-01", "--cwd", str(root))[0], 0)
        rc, prompt_out, _ = self._run(root, "review", "TASK-01", "--cwd", str(root), "--prompt")
        self.assertEqual(rc, 0)
        self.assertIn("independent research reviewer", prompt_out)
        self.assertIn("=== report.md ===", prompt_out)
        self.assertIn("# Market Report", prompt_out)
        verdict = root / "verdict.json"
        verdict.write_text(h.APPROVE, encoding="utf-8")
        self.assertEqual(self._run(root, "review", "TASK-01", "--cwd", str(root), "--record", str(verdict))[0], 0)
        rc_gate, gate_out, _ = self._run(root, "gate", "TASK-01", "--cwd", str(root))
        self.assertEqual(rc_gate, 0, gate_out)
        self.assertIn("GATE PASSED", gate_out)


if __name__ == "__main__":
    unittest.main()
