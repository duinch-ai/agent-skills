import json
import subprocess
import sys
import unittest
from pathlib import Path

import helpers as h
import init_cmd
import review
import tasks

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "agent_team.py"


class InitWorkflowTests(unittest.TestCase):
    def test_init_writes_workflow_rule_without_overwriting(self):
        root = h.make_repo()
        ctx = h.ctx_for(root)
        msgs = init_cmd.init(ctx)
        wf = root / ".agents/rules/agent-workflow.md"
        self.assertTrue(wf.is_file())
        self.assertLessEqual(len(wf.read_text().splitlines()), 120)
        self.assertIn("wrote .agents/rules/agent-workflow.md", msgs)
        wf.write_text("custom")
        self.assertIn("kept .agents/rules/agent-workflow.md", init_cmd.init(ctx))
        self.assertEqual(wf.read_text(), "custom")
        init_cmd.init(ctx, force=True)
        self.assertNotEqual(wf.read_text(), "custom")


class SuggestChecksTests(unittest.TestCase):
    def profile(self, root, cmds):
        (root / ".agents").mkdir(exist_ok=True)
        (root / ".agents/project-profile.json").write_text(json.dumps({"commands": cmds}))

    def lint(self, root):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "lint", "TASK-01"],
                              capture_output=True, text=True)

    def test_suggestions_printed_never_inserted(self):
        root = h.make_repo("# TASK-01 — x\nStatus: Todo\n\n## Acceptance criteria\n- nothing\n")
        self.profile(root, {"test_all": "pytest -q", "lint": "ruff check .", "build": "", "sec_audit": "pip-audit"})
        before = (root / "docs/tasks/TASK-01.md").read_text()
        r = self.lint(root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("check: `pytest -q`", r.stdout)
        self.assertIn("check: `ruff check .`", r.stdout)
        self.assertNotIn("pip-audit", r.stdout)
        self.assertEqual((root / "docs/tasks/TASK-01.md").read_text(), before)

    def test_no_suggestions_when_checks_exist_or_no_profile(self):
        root = h.make_repo()
        self.profile(root, {"test_all": "pytest -q"})
        self.assertNotIn("suggested", self.lint(root).stdout)
        root2 = h.make_repo("# TASK-01 — x\n\n## Acceptance criteria\n- nothing\n")
        self.assertNotIn("suggested", self.lint(root2).stdout)
        self.assertEqual(tasks.suggest_checks(h.ctx_for(root2)), [])


class ReviewLensTests(unittest.TestCase):
    def test_prompt_contains_lens(self):
        root = h.make_repo()
        t = tasks.load_task(h.ctx_for(root), "TASK-01")
        p = review.build_prompt(t, "diff")
        for word in ("Concurrency", "Unbounded data", "Idempotency", "Trust boundaries"):
            self.assertIn(word, p)


if __name__ == "__main__":
    unittest.main()


class AgentsMdLinkTests(unittest.TestCase):
    NEUTRAL = "Agent working method: agent-team skill (optional)"

    def test_neutral_line_replaced_and_nothing_else_touched(self):
        root = h.make_repo()
        before = f"# X\n\n- Other: a\n- {self.NEUTRAL}\n\nTail\n"
        (root / "AGENTS.md").write_text(before)
        msgs = init_cmd.init(h.ctx_for(root))
        after = (root / "AGENTS.md").read_text()
        self.assertEqual(after, before.replace(self.NEUTRAL, init_cmd.LINK_LINE))
        self.assertTrue(any(m.startswith("updated AGENTS.md") for m in msgs))

    def test_hint_when_neutral_line_absent_or_no_agents_md(self):
        root = h.make_repo()
        (root / "AGENTS.md").write_text("# X\nno such line\n")
        msgs = init_cmd.init(h.ctx_for(root))
        self.assertEqual((root / "AGENTS.md").read_text(), "# X\nno such line\n")
        self.assertTrue(any(m.startswith("hint:") for m in msgs))
        root2 = h.make_repo()
        self.assertTrue(any(m.startswith("hint: no AGENTS.md") for m in init_cmd.init(h.ctx_for(root2))))
