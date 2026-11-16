import json
import unittest
from pathlib import Path

import helpers as h  # noqa: E402
import gate  # noqa: E402
import init_cmd  # noqa: E402
import report  # noqa: E402
import review_same  # noqa: E402
import safety  # noqa: E402
import tasks  # noqa: E402
import verify  # noqa: E402


class EscapeHatchScannerTests(unittest.TestCase):
    def test_detects_added_suppressions_and_ignores_docs_and_removals(self):
        diff = "\n".join([
            "+++ b/src/app.ts",
            "+// eslint-disable-next-line no-console",
            "+const x = foo as any;",
            "+setTimeout(() => go(), 0);",
            "-// @ts-ignore old",
            "+++ b/src/mod.py",
            "+x = 1  # noqa",
            "+# workaround: skip validation",
            "+++ b/README.md",
            "+eslint-disable @ts-ignore as any",
        ])
        hits = safety.scan_escape_hatches(diff)
        rules = {(x["file"], x["rule"]) for x in hits}
        self.assertEqual(rules, {
            ("src/app.ts", "eslint-disable"),
            ("src/app.ts", "ts-any"),
            ("src/app.ts", "timing-workaround"),
            ("src/mod.py", "python-suppression"),
            ("src/mod.py", "workaround-comment"),
        })

    def test_verify_and_gate_warn_vs_fail(self):
        root = h.make_repo()
        (root / ".gitignore").write_text(".agent-team/\n")
        (root / "app.ts").write_text("export const x = 1 as any;\n")
        h.sh(root, "git", "add", "-A")
        h.sh(root, "git", "commit", "-qm", "add ts any")

        # Default policy: warn
        ctx = h.ctx_for(root)
        t = tasks.load_task(ctx, "TASK-01")
        res = verify.verify_task(ctx, t, root)
        self.assertTrue(res["ok"])
        self.assertEqual(len(res["escape_hatches"]), 1)

        verdict_file = root.parent / "verdict.json"
        verdict_file.write_text(h.APPROVE)
        review_same.record(ctx, t, root, str(verdict_file), reviewer="sub")
        ok, reasons, warns = gate.evaluate(ctx, t, root, run_audit=False)
        self.assertTrue(ok, reasons)
        self.assertTrue(any("escape hatch" in w for w in warns))

        # Strict policy: fail
        (root / ".agent-team").mkdir(exist_ok=True)
        (root / ".agent-team/config.json").write_text(json.dumps({"escape_hatch_policy": "fail"}))
        ctx_fail = h.ctx_for(root)
        res_fail = verify.verify_task(ctx_fail, t, root)
        self.assertFalse(res_fail["ok"])
        ok2, reasons2, _ = gate.evaluate(ctx_fail, t, root, run_audit=False)
        self.assertFalse(ok2)
        self.assertTrue(any("escape hatch" in r for r in reasons2))


class ArtifactsAndVerifySkillTests(unittest.TestCase):
    def test_gate_requires_artifacts_when_declared(self):
        task_text = h.TASK.replace("Priority: P1\n", "Priority: P1\nArtifacts: required\nRisk: low\n")
        root = h.make_repo(task_text)
        (root / ".gitignore").write_text(".agent-team/\n")
        h.sh(root, "git", "add", "-A")
        h.sh(root, "git", "commit", "-qm", "gitignore")
        ctx = h.ctx_for(root)
        t = tasks.load_task(ctx, "TASK-01")
        self.assertEqual(t.artifacts, "required")
        self.assertEqual(t.risk, "low")

        verify.verify_task(ctx, t, root)
        vf = root.parent / "v.json"
        vf.write_text(h.APPROVE)
        review_same.record(ctx, t, root, str(vf), reviewer="sub")

        ok, reasons, _ = gate.evaluate(ctx, t, root, run_audit=False)
        self.assertFalse(ok)
        self.assertTrue(any("artifact" in r for r in reasons))

        adir = ctx.runs("TASK-01") / "artifacts"
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "shot.png").write_bytes(b"PNGDATA")
        ok2, reasons2, _ = gate.evaluate(ctx, t, root, run_audit=False)
        self.assertTrue(ok2, reasons2)

    def test_init_verify_skill_scaffolds_feature_map(self):
        root = h.make_repo()
        msgs = init_cmd.init(h.ctx_for(root), verify_skill=True)
        self.assertTrue((root / ".agents/skills/verify-app/SKILL.md").is_file())
        self.assertTrue((root / ".agents/skills/verify-app/references/features/README.md").is_file())
        self.assertTrue((root / ".agents/skills/verify-app/references/features/_template.md").is_file())
        self.assertTrue(any("verify-app/SKILL.md" in m for m in msgs))

    def test_report_includes_inner_loop_health(self):
        root = h.make_repo()
        ctx = h.ctx_for(root)
        t = tasks.load_task(ctx, "TASK-01")
        verify.verify_task(ctx, t, root)
        md = report.render(report.collect(ctx), root=root)
        self.assertIn("## Inner-loop health", md)
        self.assertIn("avg verify rounds:", md)
        self.assertIn("recent reverts:", md)


if __name__ == "__main__":
    unittest.main()
