import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from catalog import PRODUCT_CATEGORIES, STACK_CATALOG  # noqa: E402
from guided import run_recommend  # noqa: E402
from recommend import RecommendError, recommend  # noqa: E402

BOTH = ["ios", "android"]

# (answers, expected stack, expected alternative stack or None)
CASES = {
    "mobile both + kotlin": ({"goal": "mobile-app", "platforms": BOTH, "known_languages": ["kotlin"]}, "kmp", "flutter"),
    "mobile both + dart": ({"goal": "mobile-app", "platforms": BOTH, "known_languages": ["dart"]}, "flutter", "kmp"),
    "mobile both no lang": ({"goal": "mobile-app", "platforms": BOTH, "known_languages": ["none"]}, "flutter", "kmp"),
    "mobile ios only": ({"goal": "mobile-app", "platforms": ["ios"]}, "ios", "flutter"),
    "mobile android only": ({"goal": "mobile-app", "platforms": ["android"]}, "android", "kmp"),
    "mobile no platform": ({"goal": "mobile-app"}, "flutter", "kmp"),
    "multiplatform kotlin": ({"goal": "multiplatform-app", "known_languages": ["kotlin"]}, "kmp", "flutter"),
    "multiplatform default": ({"goal": "multiplatform-app"}, "flutter", "kmp"),
    "web": ({"goal": "web-app"}, "web", None),
    "backend go": ({"goal": "backend-api", "known_languages": ["go", "python"]}, "go", "python"),
    "backend ts": ({"goal": "backend-api", "known_languages": ["typescript"]}, "nestjs", "go"),
    "backend js": ({"goal": "backend-api", "known_languages": ["javascript"]}, "nestjs", "go"),
    "backend python": ({"goal": "backend-api", "known_languages": ["python"]}, "python", "go"),
    "backend none many users": ({"goal": "backend-api", "needs": ["many-users"]}, "go", "python"),
    "backend none realtime": ({"goal": "backend-api", "needs": ["realtime"], "known_languages": ["none"]}, "go", "python"),
    "backend none": ({"goal": "backend-api"}, "python", "go"),
    "cli rust": ({"goal": "cli-tool", "known_languages": ["rust"]}, "rust", "go"),
    "cli python": ({"goal": "cli-tool", "known_languages": ["python"]}, "python", "go"),
    "cli js knower": ({"goal": "cli-tool", "known_languages": ["javascript"]}, "go", "rust"),
    "cli heavy compute": ({"goal": "cli-tool", "needs": ["heavy-compute"]}, "rust", "go"),
    "desktop kotlin": ({"goal": "desktop-app", "known_languages": ["kotlin"]}, "kmp", "rust"),
    "desktop default": ({"goal": "desktop-app"}, "rust", "kmp"),
    "bot ts": ({"goal": "bot", "known_languages": ["typescript"]}, "nestjs", "python"),
    "bot default": ({"goal": "bot"}, "python", "nestjs"),
    "library rust": ({"goal": "library", "known_languages": ["rust"]}, "rust", None),
    "library kotlin": ({"goal": "library", "known_languages": ["kotlin"]}, "kmp", None),
    "library ts": ({"goal": "library", "known_languages": ["typescript"]}, "web", None),
    "switch homebrew": ({"goal": "embedded-homebrew", "platforms": ["switch"]}, "cpp-switch", None),
}


class PolicyBranchTests(unittest.TestCase):
    def test_every_branch(self):
        for name, (answers, stack, alt) in CASES.items():
            with self.subTest(name):
                r = recommend(answers)
                self.assertEqual(r["stack"], stack)
                self.assertEqual(r["alternative"]["stack"] if r["alternative"] else None, alt)
                self.assertEqual(r["arch"], STACK_CATALOG[stack]["recommended_arch"])
                self.assertEqual(r["pattern"], STACK_CATALOG[stack]["recommended_pattern"])
                self.assertEqual(r["preset"], "guided")
                self.assertIn(r["category"], PRODUCT_CATEGORIES)
                self.assertIn(stack, PRODUCT_CATEGORIES[r["category"]]["recommended_stacks"])
                self.assertTrue(all(x["text"] for x in r["reasons"]))

    def test_bot_maps_to_service_worker(self):
        self.assertEqual(recommend({"goal": "bot"})["category"], "service-worker")

    def test_deterministic(self):
        a = {"goal": "backend-api", "needs": ["realtime", "many-users"], "known_languages": ["ruby", "none"]}
        self.assertEqual(json.dumps(recommend(a)), json.dumps(recommend(dict(a))))
        shuffled = {"known_languages": ["none", "ruby"], "needs": ["many-users", "realtime"], "goal": "backend-api"}
        self.assertEqual(recommend(a), recommend(shuffled))


class ValidationTests(unittest.TestCase):
    def err(self, answers):
        with self.assertRaises(RecommendError) as cm:
            recommend(answers)
        return cm.exception

    def test_missing_and_unsure_goal(self):
        self.assertEqual(self.err({}).code, "need-goal")
        self.assertEqual(self.err({"goal": "unsure"}).code, "need-goal")

    def test_unknown_values_list_allowed(self):
        e = self.err({"goal": "mobile-app", "platforms": ["amiga"]})
        self.assertEqual(e.code, "invalid-answers")
        self.assertIn("ios", e.message)
        self.assertEqual(self.err({"goal": "toaster"}).code, "invalid-answers")
        self.assertEqual(self.err({"goal": "bot", "maintainers": "crowd"}).code, "invalid-answers")
        self.assertEqual(self.err({"goal": "bot", "needs": "offline"}).code, "invalid-answers")
        self.assertEqual(self.err({"goal": "bot", "mystery": 1}).code, "invalid-answers")

    def test_library_without_language_asks(self):
        self.assertEqual(self.err({"goal": "library"}).code, "need-language")
        self.assertEqual(self.err({"goal": "library", "known_languages": ["swift"]}).code, "need-language")

    def test_homebrew_wrong_platform(self):
        self.assertEqual(self.err({"goal": "embedded-homebrew", "platforms": ["web"]}).code, "unsupported-platform")


class NotesAndFeaturesTests(unittest.TestCase):
    def test_unsupported_language_note(self):
        r = recommend({"goal": "backend-api", "known_languages": ["java", "php"]})
        self.assertEqual(r["stack"], "python")
        note = next(n for n in r["notes"] if n["code"] == "unsupported-language")
        self.assertIn("java", note["text"])
        self.assertIn("php", note["text"])

    def test_no_note_when_a_supported_language_is_known(self):
        r = recommend({"goal": "backend-api", "known_languages": ["java", "go"]})
        self.assertEqual(r["notes"], [])

    def test_multi_language_ui_adds_i18n(self):
        r = recommend({"goal": "mobile-app", "needs": ["multi-language-ui"]})
        self.assertEqual(r["features_add"], ["i18n"])
        self.assertEqual(r["locales"], ["vi", "en"])
        self.assertIn("multi-language-ui", [x["code"] for x in r["reasons"]])
        self.assertEqual(recommend({"goal": "mobile-app"})["features_add"], [])

    def test_honest_notes_for_limited_goals(self):
        self.assertIn("desktop-limited", [n["code"] for n in recommend({"goal": "desktop-app"})["notes"]])
        r = recommend({"goal": "web-app", "needs": ["realtime"]})
        self.assertIn("separate-backend", [n["code"] for n in r["notes"]])


class DetectorPrecedenceTests(unittest.TestCase):
    def test_existing_go_project_wins(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "go.mod").write_text("module example.com/x\n\ngo 1.22\n")
            r = run_recommend({"goal": "backend-api", "known_languages": ["python"]}, Path(d))
            self.assertEqual(r["stack"], "go")
            self.assertEqual(r["reasons"][0]["code"], "existing-code")
            self.assertIsNone(r["alternative"])

    def test_existing_code_default_is_auto(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "go.mod").write_text("module example.com/x\n")
            self.assertEqual(run_recommend({"goal": "backend-api"}, Path(d))["stack"], "go")

    def test_empty_dir_uses_rules(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run_recommend({"goal": "backend-api"}, Path(d))["stack"], "python")

    def test_unsure_goal_with_existing_code(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Cargo.toml").write_text("[package]\nname='x'\n")
            self.assertEqual(run_recommend({"goal": "unsure"}, Path(d))["stack"], "rust")


if __name__ == "__main__":
    unittest.main()
