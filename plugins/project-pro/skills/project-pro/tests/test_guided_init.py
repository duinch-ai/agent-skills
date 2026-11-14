import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
CLI = SCRIPTS / "project_pro.py"


def cli(*args, stdin=None):
    return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, input=stdin)


def profile(root):
    return json.loads((Path(root) / ".agents" / "project-profile.json").read_text())


class GuidedInitTests(unittest.TestCase):
    def test_end_to_end_via_stdin(self):
        answers = {"goal": "mobile-app", "platforms": ["ios", "android"], "needs": ["multi-language-ui"]}
        with tempfile.TemporaryDirectory() as d:
            r = cli("init", "--mode", "guided", "--answers", "-", "--target", d, stdin=json.dumps(answers))
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            p = profile(d)
            self.assertEqual((p["stack"], p["architecture"], p["pattern"], p["productCategory"]),
                             ("flutter", "clean", "bloc", "mobile-app"))
            self.assertIn("i18n", p["selectedFeatures"])
            self.assertIn("solid-dry", p["selectedFeatures"])
            self.assertEqual(p["i18n"]["supportedLocales"], ["vi", "en"])
            self.assertIn("preset=guided", r.stdout)
            self.assertNotIn("NOTICE", r.stdout)

    def test_answers_file_and_audit_clean(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "answers.json"
            f.write_text(json.dumps({"goal": "cli-tool", "known_languages": ["rust"]}))
            proj = Path(d) / "proj"
            self.assertEqual(cli("init", "--mode", "guided", "--answers", str(f), "--target", str(proj)).returncode, 0)
            p = profile(proj)
            self.assertEqual((p["stack"], p["productCategory"]), ("rust", "cli-tool"))
            self.assertEqual(cli("audit", "--target", str(proj), "--fail-on-error").returncode, 0)

    def test_explicit_stack_overrides_with_notice(self):
        with tempfile.TemporaryDirectory() as d:
            r = cli("init", "--mode", "guided", "--answers", "-", "--target", d, "--stack", "go",
                    stdin=json.dumps({"goal": "mobile-app", "platforms": ["ios", "android"]}))
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertIn("NOTICE: explicit flags override the recommendation (--stack)", r.stdout)
            p = profile(d)
            self.assertEqual((p["stack"], p["architecture"], p["pattern"]), ("go", "hexagonal", "service-repo"))

    def test_guided_errors_are_clear(self):
        with tempfile.TemporaryDirectory() as d:
            r = cli("init", "--mode", "guided", "--answers", "-", "--target", d, stdin='{"goal": "unsure"}')
            self.assertEqual(r.returncode, 2)
            self.assertIn("need-goal", r.stdout)
            self.assertEqual(cli("init", "--mode", "guided", "--target", d).returncode, 2)
            self.assertFalse((Path(d) / ".agents").exists())

    def test_recommend_json_cli_and_error(self):
        r = cli("recommend", "--answers", "-", "--json", stdin='{"goal": "bot"}')
        self.assertEqual(json.loads(r.stdout)["category"], "service-worker")
        r = cli("recommend", "--answers", "-", "--json", stdin='{"goal": "library"}')
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["error"]["code"], "need-language")


class ExpertUnchangedTests(unittest.TestCase):
    def test_expert_requires_stack(self):
        with tempfile.TemporaryDirectory() as d:
            r = cli("init", "--target", d)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("--stack is required", r.stderr)

    def test_expert_default_flow_still_works(self):
        with tempfile.TemporaryDirectory() as d:
            r = cli("init", "--target", d, "--stack", "python")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(profile(d)["stack"], "python")
            self.assertNotIn("recommended stack", r.stdout)


if __name__ == "__main__":
    unittest.main()
