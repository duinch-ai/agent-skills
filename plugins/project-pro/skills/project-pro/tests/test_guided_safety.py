import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
CLI = SCRIPTS / "project_pro.py"

from catalog import STACK_CATALOG, PRESET_RECOMMENDED_AGENTS, PRESET_RECOMMENDED_FEATURES  # noqa: E402
from presets import resolve_selection  # noqa: E402
from recommend import recommend  # noqa: E402
from safety import render_check_script  # noqa: E402


def cli(*args, stdin=None):
    return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, input=stdin)


def guided_init(target, goal, **extra):
    return cli("init", "--mode", "guided", "--answers", "-", "--target", str(target), "--scaffold-dirs",
               *extra.get("flags", []), stdin=json.dumps({"goal": goal, **extra.get("answers", {})}))


class PresetTests(unittest.TestCase):
    def test_guided_preset_resolution(self):
        for stack in STACK_CATALOG:
            feats = resolve_selection(None, "guided", stack, None, "features")
            self.assertEqual(set(feats), set(PRESET_RECOMMENDED_FEATURES) | {"testing-ci", "data-integrity"})
            self.assertEqual(resolve_selection(None, "guided", stack, None, "agents"), PRESET_RECOMMENDED_AGENTS)

    def test_recommend_preset_is_guided(self):
        self.assertEqual(recommend({"goal": "cli-tool", "known_languages": ["rust"]})["preset"], "guided")


class GuidedOutputTests(unittest.TestCase):
    def test_three_stacks(self):
        cases = [("python", {"goal": "backend-api", "known_languages": ["python"]}),
                 ("go", {"goal": "backend-api", "known_languages": ["go"]}),
                 ("flutter", {"goal": "mobile-app", "platforms": ["ios", "android"]})]
        for stack, answers in cases:
            with self.subTest(stack=stack), tempfile.TemporaryDirectory() as d:
                r = cli("init", "--mode", "guided", "--answers", "-", "--target", d, stdin=json.dumps(answers))
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                root = Path(d)
                prof = json.loads((root / ".agents/project-profile.json").read_text())
                self.assertEqual(prof["stack"], stack)
                self.assertEqual(prof["commands"]["check"], "sh scripts/check.sh")
                check = root / "scripts/check.sh"
                self.assertTrue(os.access(check, os.X_OK))
                self.assertTrue(check.stat().st_mode & stat.S_IXUSR)
                text = check.read_text()
                cmds = STACK_CATALOG[stack]["commands"]
                for key in ("lint", "build", "test_all"):
                    self.assertIn(cmds[key], text)
                for key in ("test_single", "sec_audit"):
                    self.assertNotIn(cmds[key], text)
                start = (root / "START_HERE.md").read_text()
                self.assertLessEqual(len(start.splitlines()), 80)
                self.assertIn("sh scripts/check.sh", start)
                self.assertIn(cmds["build"], start)
                self.assertIn("Non-technical owner guide: START_HERE.md", (root / "AGENTS.md").read_text())
                where = start.split("## 6. Where things are")[1].split("## 7.")[0]
                for line in where.splitlines():
                    if line.startswith("- `"):
                        self.assertTrue((root / line.split("`")[1].rstrip("/")).exists(), line)

    def test_no_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "START_HERE.md").write_text("mine\n")
            r = guided_init(d, "backend-api", answers={"known_languages": ["python"]})
            self.assertEqual(r.returncode, 0)
            self.assertEqual((Path(d) / "START_HERE.md").read_text(), "mine\n")
            self.assertIn("SKIP (exists): START_HERE.md", r.stdout)

    def test_dropped_safety_item_warns_and_stays_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            r = guided_init(d, "backend-api", answers={"known_languages": ["python"]},
                            flags=["--agents", "agents-root,persistent-memory"])
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("WARNING: guided mode normally keeps git-security-hooks:", r.stdout)
            self.assertIn("WARNING: guided mode normally keeps agent-runtime-hooks:", r.stdout)
            self.assertNotIn("keeps agents-root", r.stdout)
            self.assertFalse((Path(d) / ".githooks").exists())
            start = (Path(d) / "START_HERE.md").read_text()
            self.assertNotIn("Git hooks stop", start)

    def test_expert_default_has_no_guided_files(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli("init", "--target", d, "--stack", "python").returncode, 0)
            self.assertFalse((Path(d) / "START_HERE.md").exists())
            self.assertFalse((Path(d) / "scripts/check.sh").exists())
            self.assertNotIn("START_HERE", (Path(d) / "AGENTS.md").read_text())
            self.assertNotIn("check", json.loads((Path(d) / ".agents/project-profile.json").read_text())["commands"])
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli("init", "--target", d, "--stack", "rust").returncode, 0)
            self.assertFalse((Path(d) / "scripts/check.sh").exists())

    def test_expert_can_choose_guided_preset(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli("init", "--target", d, "--stack", "go", "--preset", "guided").returncode, 0)
            self.assertTrue((Path(d) / "scripts/check.sh").is_file())


class CheckScriptRunTests(unittest.TestCase):
    def run_script(self, commands):
        with tempfile.TemporaryDirectory() as d:
            script = Path(d) / "scripts/check.sh"
            script.parent.mkdir()
            script.write_text(render_check_script(commands, "/nonexistent/project_pro.py"))
            return subprocess.run(["sh", str(script)], capture_output=True, text=True)

    def test_all_pass(self):
        r = self.run_script({"lint": "true", "build": "true", "test_all": "true"})
        self.assertEqual(r.returncode, 0)
        self.assertIn("✔ tests passed", r.stdout)
        self.assertIn("structure audit skipped", r.stdout)
        self.assertTrue(r.stdout.rstrip().endswith("ALL CHECKS PASSED"))

    def test_first_failure_stops(self):
        r = self.run_script({"lint": "true", "build": "false", "test_all": "echo should-not-run"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('✘ build failed — ask your agent: "fix the failing check"', r.stdout)
        self.assertIn("CHECKS FAILED", r.stdout)
        self.assertNotIn("should-not-run", r.stdout)
        self.assertNotIn("ALL CHECKS PASSED", r.stdout)

    def test_missing_tool_and_missing_keys(self):
        r = self.run_script({"test_all": "definitely-not-a-tool-xyz"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not installed", r.stdout)
        r = self.run_script({"test_all": "true"})
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("lint", r.stdout)


if __name__ == "__main__":
    unittest.main()
