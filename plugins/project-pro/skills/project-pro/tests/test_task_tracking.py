import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from auditor import audit_project  # noqa: E402
from detector import detect_project  # noqa: E402
from scaffolder import init_project  # noqa: E402
import tasktracking  # noqa: E402

BASE = ["solid-dry"]
AGENTS = ["agents-root"]


def init(target, features, force=False, **kw):
    return init_project(target=Path(target), stack="python", arch="clean", pattern="service-repo",
                        features=features, agents=AGENTS, force=force, **kw)


class TaskTrackingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        self.home = Path(home.name)
        p = mock.patch.object(Path, "home", return_value=self.home)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_off_has_no_board_text(self):
        init(self.root, BASE)
        agents = (self.root / "AGENTS.md").read_text()
        for word in ("board", "Board", "workflow.py", "task-workflow", "task-board", "github-project-workflow"):
            self.assertNotIn(word, agents)
        self.assertFalse((self.root / "docs/tasks").exists())
        self.assertEqual(detect_project(self.root)["task_tracking"], "off")
        rep = audit_project(self.root)
        self.assertFalse([m for m in rep["errors"] + rep["warnings"] if "task-tracking" in m or "task-board.json" in m])

    def test_on_creates_files_and_pointer(self):
        out = init(self.root, BASE + ["task-tracking"])
        self.assertTrue((self.root / "docs/tasks/.gitkeep").is_file())
        self.assertFalse(list((self.root / "docs/tasks").glob("*.md")))
        backlog = (self.root / "docs/BACKLOG.md").read_text()
        self.assertIn("| Task | Issue |", backlog)
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("`task-board`", agents)
        self.assertNotIn("github-project-workflow", agents)
        self.assertIn("agent-team", agents)
        self.assertTrue(any("NEXT:" in line and "init --provider github --project" in line for line in out))
        self.assertTrue(any("not found" in line for line in out))  # fake empty home
        profile = json.loads((self.root / ".agents/project-profile.json").read_text())
        self.assertIn("task-tracking", profile["selectedFeatures"])
        self.assertEqual(profile["taskTracking"], {"provider": "github"})
        self.assertIn("provider: github", agents)

    def test_not_overwritten(self):
        (self.root / "docs").mkdir()
        (self.root / "docs/BACKLOG.md").write_text("mine\n")
        out = init(self.root, BASE + ["task-tracking"])
        self.assertEqual((self.root / "docs/BACKLOG.md").read_text(), "mine\n")
        self.assertTrue(any("SKIP (exists): docs/BACKLOG.md" in line for line in out))

    def test_skill_detected(self):
        d = self.home / ".claude/skills/task-board"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("x")
        out = init(self.root, BASE + ["task-tracking"])
        self.assertTrue(any(line.startswith("OK:") for line in out))
        self.assertTrue(any(str(d) in line and "NEXT:" in line for line in out))

    def test_agent_team_hint_when_missing_and_detected(self):
        out_missing = init(self.root, BASE)
        self.assertTrue(any("skill `agent-team` not found" in line for line in out_missing))
        d = self.home / ".gemini/config/skills/agent-team"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("x")
        out_found = init(self.root, BASE)
        self.assertTrue(any(f"OK: `agent-team` found at {d}" == line for line in out_found))
        self.assertTrue(any("agent_team.py init" in line and "NEXT:" in line for line in out_found))

    def test_detector_and_audit_states(self):
        init(self.root, BASE + ["task-tracking"])
        self.assertEqual(detect_project(self.root)["task_tracking"], "ticked-not-initialized")
        rep = audit_project(self.root)
        self.assertTrue(any("task-board.json" in w for w in rep["warnings"]))
        self.assertFalse(any("task-board.json" in e for e in rep["errors"]))
        (self.root / ".github").mkdir()
        (self.root / ".github/project.json").write_text("{}")  # legacy location
        self.assertEqual(detect_project(self.root)["task_tracking"], "configured")
        rep = audit_project(self.root)
        self.assertFalse(any("task-board.json" in w for w in rep["warnings"]))

    def test_new_config_location_detected(self):
        init(self.root, BASE + ["task-tracking"])
        (self.root / ".agents/task-board.json").write_text('{"provider": "github"}')
        self.assertEqual(detect_project(self.root)["task_tracking"], "configured")
        self.assertFalse(any("task-board.json" in w for w in audit_project(self.root)["warnings"]))

    def test_local_provider_scaffold_and_detection(self):
        self.assertEqual(sorted(tasktracking.TASK_PROVIDERS), ["github", "local"])
        out = init(self.root, BASE + ["task-tracking"], task_provider="local")
        self.assertTrue((self.root / "docs/tasks/.gitkeep").is_file())
        self.assertTrue((self.root / "docs/BACKLOG.md").is_file())
        self.assertTrue(any("NEXT:" in line and "init --provider local" in line for line in out))
        self.assertFalse(any("--project" in line for line in out if "NEXT:" in line))
        profile = json.loads((self.root / ".agents/project-profile.json").read_text())
        self.assertEqual(profile["taskTracking"], {"provider": "local"})
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("provider: local", agents)
        self.assertEqual(detect_project(self.root)["task_tracking"], "ticked-not-initialized")
        # a local project is not "configured" by the legacy github file
        (self.root / ".github").mkdir()
        (self.root / ".github/project.json").write_text("{}")
        self.assertEqual(detect_project(self.root)["task_tracking"], "ticked-not-initialized")
        (self.root / ".agents/task-board.json").write_text('{"provider": "local"}')
        self.assertEqual(detect_project(self.root)["task_tracking"], "configured")

    def test_legacy_skill_name_and_env_fallback(self):
        d = self.home / ".claude/skills/github-project-workflow"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("x")
        out = init(self.root, BASE + ["task-tracking"])
        self.assertTrue(any(line.startswith("OK:") and str(d) in line for line in out))
        nxt = [line for line in out if line.startswith("NEXT:")][0]
        self.assertNotIn("--provider", nxt)  # old script has no --provider flag
        self.assertIn(".github/project.json", nxt)
        # new name wins over legacy when both exist
        new = self.home / ".claude/skills/task-board"
        new.mkdir(parents=True)
        (new / "SKILL.md").write_text("x")
        self.assertEqual(tasktracking.find_skill_dir("github"), new)
        # legacy env var still honoured as fallback
        env_dir = self.home / "elsewhere"
        env_dir.mkdir()
        (env_dir / "SKILL.md").write_text("x")
        import shutil
        shutil.rmtree(new)
        shutil.rmtree(d)
        with mock.patch.dict(os.environ, {"GITHUB_PROJECT_WORKFLOW_DIR": str(env_dir)}):
            self.assertEqual(tasktracking.find_skill_dir("github"), env_dir)
        with mock.patch.dict(os.environ, {"TASK_BOARD_DIR": str(env_dir)}):
            self.assertEqual(tasktracking.find_skill_dir("local"), env_dir)


if __name__ == "__main__":
    unittest.main()
