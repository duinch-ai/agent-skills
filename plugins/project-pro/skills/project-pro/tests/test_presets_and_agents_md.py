import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from catalog import AGENT_CHOICES, FEATURE_CHOICES  # noqa: E402
from presets import resolve_selection  # noqa: E402
from scaffolder import init_project  # noqa: E402
from wizard import parse_multi_input  # noqa: E402

PLAN_NAME = "active" + "-plan"  # removed artifact; built by concatenation so repo greps stay clean
CLI = SCRIPTS / "project_pro.py"


def run_init(root, *extra, stack="python"):
    return subprocess.run([sys.executable, str(CLI), "init", "--target", str(root), "--stack", stack, *extra],
                          capture_output=True, text=True)


class WizardAllTests(unittest.TestCase):
    def test_numeric_fallback_accepts_all_tokens(self):
        for tok in ("a", "all", "*", "A", "1,all"):
            self.assertEqual(parse_multi_input(tok, 4), [1, 2, 3, 4], tok)
        self.assertEqual(parse_multi_input("2,9,x,1", 4), [1, 2])
        self.assertIsNone(parse_multi_input("  ", 4))


class PresetTests(unittest.TestCase):
    def test_all_expands_to_every_choice(self):
        feats = resolve_selection("all", "recommended", "go", None, "features")
        agents = resolve_selection("all", "recommended", "go", None, "agents")
        self.assertEqual(feats, [k for k, _, _ in FEATURE_CHOICES])
        self.assertEqual(agents, [k for k, _, _ in AGENT_CHOICES])

    def test_explicit_overrides_preset_and_minimal_defined(self):
        self.assertEqual(resolve_selection("solid-dry,i18n", "all", "go", None, "features"), ["solid-dry", "i18n"])
        self.assertEqual(resolve_selection(None, "minimal", "go", None, "agents"), ["agents-root"])
        self.assertIn("testing-ci", resolve_selection(None, "recommended", "rust", None, "features"))
        self.assertNotIn("testing-ci", resolve_selection(None, "recommended", "go", None, "features"))

    def test_cli_all_prints_resolved_list_and_writes_everything(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_init(d, "--features", "all", "--agents", "all", "--force")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("features: " + ", ".join(k for k, _, _ in FEATURE_CHOICES), r.stdout)
            profile = json.loads((Path(d) / ".agents/project-profile.json").read_text())
            self.assertEqual(profile["selectedFeatures"], [k for k, _, _ in FEATURE_CHOICES])
            self.assertTrue((Path(d) / ".cursor/rules/00-project-architecture.mdc").is_file())

    def test_cli_minimal_preset_audit_has_no_errors(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_init(d, "--preset", "minimal")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(d) / "AGENTS.md").is_file())
            self.assertFalse((Path(d) / ".githooks").exists())
            a = subprocess.run([sys.executable, str(CLI), "audit", "--target", d, "--fail-on-error"],
                               capture_output=True, text=True)
            self.assertEqual(a.returncode, 0, a.stdout)


class AgentsMdTests(unittest.TestCase):
    def gen(self, stack="python", workflow=False):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        if workflow:
            (root / ".agents/rules").mkdir(parents=True)
            (root / ".agents/rules/agent-workflow.md").write_text("x")
        init_project(root, stack, "clean", "service-repo" if stack == "python" else "mvi",
                     ["solid-dry"], ["agents-root", "persistent-memory", "claude-gemini", "cursor-ide"])
        return root

    def test_no_behaviour_section_and_no_active_plan(self):
        for stack in ("python", "rust", "android"):
            root = self.gen(stack)
            agents = (root / "AGENTS.md").read_text()
            for banned in ("6-Gate", "karpathy", "obra/superpowers", "gstack", "caveman", "3-Strike", PLAN_NAME,
                           "Behavioral Guardrails"):
                self.assertNotIn(banned, agents, (stack, banned))
            self.assertIn("Coding Standards Checklist", agents)
            self.assertFalse((root / ".agents/memory" / (PLAN_NAME + ".md")).exists())
            self.assertTrue((root / ".agents/memory/lessons.md").is_file())
            for f in (".agents/rules/execution-harness.md", "CLAUDE.md", "GEMINI.md", ".cursor/rules/00-project-architecture.mdc"):
                text = (root / f).read_text()
                self.assertNotIn("6-Gate", text, f)
                self.assertNotIn(PLAN_NAME, text, f)

    def test_working_method_line_is_conditional(self):
        neutral = (self.gen().joinpath("AGENTS.md")).read_text()
        self.assertIn("Agent working method: agent-team skill (optional)", neutral)
        self.assertNotIn("agent-workflow.md", neutral)
        linked = self.gen(workflow=True).joinpath("AGENTS.md").read_text()
        self.assertIn("Agent working method: see [`.agents/rules/agent-workflow.md`]", linked)


if __name__ == "__main__":
    unittest.main()


class DataIntegrityTests(unittest.TestCase):
    RULE = "Data Integrity — Never Invent Values"

    def agents(self, features):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        init_project(Path(d.name), "python", "clean", "service-repo", features, ["agents-root"])
        return (Path(d.name) / "AGENTS.md").read_text()

    def test_off_by_default_and_in_all_only(self):
        self.assertNotIn(self.RULE, self.agents(["solid-dry"]))
        self.assertNotIn("data-integrity", resolve_selection(None, "recommended", "python", None, "features"))
        self.assertNotIn("data-integrity", resolve_selection(None, "minimal", "python", None, "features"))
        self.assertIn("data-integrity", resolve_selection(None, "all", "python", None, "features"))
        self.assertIn("data-integrity", resolve_selection("all", "recommended", "python", None, "features"))
        self.assertFalse(dict((k, d) for k, _, d in FEATURE_CHOICES)["data-integrity"])

    def test_ticked_adds_rule(self):
        text = self.agents(["solid-dry", "data-integrity"])
        self.assertIn(self.RULE, text)
        for phrase in ("verifiable source", "recorded from real runs", "CLI name + version + date", "not verified"):
            self.assertIn(phrase, text)


class CatalogSplitTests(unittest.TestCase):
    def test_all_ten_stacks_keep_order_and_init(self):
        from catalog import STACK_CATALOG
        self.assertEqual(list(STACK_CATALOG), ["android", "kmp", "flutter", "ios", "web", "python", "go", "nestjs", "rust", "cpp-switch"])
        for stack, info in STACK_CATALOG.items():
            self.assertIn("i18n", info)
            with tempfile.TemporaryDirectory() as d:
                init_project(Path(d), stack, info["recommended_arch"], info["recommended_pattern"], ["solid-dry"], ["agents-root"])
                self.assertTrue((Path(d) / "AGENTS.md").is_file(), stack)
