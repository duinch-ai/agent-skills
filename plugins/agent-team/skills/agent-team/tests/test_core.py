import json
import os
import unittest
from pathlib import Path
from unittest import mock

import helpers as h
import gate
import report
import review
import safety
import store
import tasks
import verify


class TaskTests(unittest.TestCase):
    def test_parse_and_lint(self):
        root = h.make_repo()
        t = tasks.load_task(h.ctx_for(root), "TASK-01")
        self.assertEqual((t.id, t.status, len(t.criteria)), ("TASK-01", "Todo", 2))
        self.assertEqual(t.criteria[0]["check"], 'test "$(cat hello.txt)" = hello')
        self.assertEqual(tasks.lint_task(t), [])

    def test_lint_missing_check(self):
        root = h.make_repo("# TASK-01 — x\nType: bug\n\n## Acceptance criteria\n- nothing\n")
        t = tasks.load_task(h.ctx_for(root), "TASK-01")
        probs = tasks.lint_task(t)
        self.assertTrue(any("no `check:`" in p for p in probs))
        self.assertTrue(any("Repro" in p for p in probs))


class VerifyTests(unittest.TestCase):
    def test_pass_fail_timeout_tail(self):
        r = verify.run_check("echo hi", ".", 5, 100)
        self.assertTrue(r["ok"])
        r = verify.run_check("echo boom; exit 3", ".", 5, 100)
        self.assertEqual((r["ok"], r["exit"]), (False, 3))
        r = verify.run_check("sleep 5", ".", 1, 100)
        self.assertTrue(r["timed_out"])
        r = verify.run_check("python3 -c \"print('x'*5000)\"", ".", 5, 100)
        self.assertLess(len(r["output_tail"]), 200)

    def test_env_scrubbed_and_redacted(self):
        with mock.patch.dict(os.environ, {"MY_API_TOKEN": "sekret123"}):
            r = verify.run_check("echo $MY_API_TOKEN; echo password=hunter22222", ".", 5, 500)
        self.assertNotIn("sekret123", r["output_tail"])
        self.assertNotIn("hunter22222", r["output_tail"])

    def test_verify_task_and_repro(self):
        root = h.make_repo()
        ctx = h.ctx_for(root)
        t = tasks.load_task(ctx, "TASK-01")
        res = verify.verify_task(ctx, t, root)
        self.assertTrue(res["ok"])
        (root / "hello.txt").write_text("nope")
        self.assertFalse(verify.verify_task(ctx, t, root)["ok"])
        self.assertEqual(store.count(ctx.runs("TASK-01"), "verify"), 2)


class ReviewTests(unittest.TestCase):
    def _run(self, root, reply, extra_cfg=None, coder="claude"):
        ctx = h.ctx_for(root)
        ctx.cfg["base_branch"] = "main"
        ctx.cfg.update(extra_cfg or {})
        t = tasks.load_task(ctx, "TASK-01")
        d = h.fake_cli("codex", h.codex_body(reply))
        with mock.patch.dict(os.environ, {"PATH": f"{d}{os.pathsep}{os.environ['PATH']}"}):
            return ctx, t, review.review_task(ctx, t, root, coder)

    def test_never_same_vendor(self):
        cfg = dict(h.config.DEFAULTS)
        with mock.patch.object(h.config, "which", lambda n: "/x/" + n):
            cfg["reviewer_commands"] = {"claude": ["claude"], "gemini": ["gemini"]}
            self.assertNotIn("codex", review.available_reviewers(cfg, "codex"))
            self.assertNotIn("claude", review.available_reviewers(cfg, "claude"))
            self.assertEqual(review.available_reviewers(cfg, "claude")[0], "codex")

    def test_missing_cli_detected(self):
        cfg = dict(h.config.DEFAULTS)
        with mock.patch.object(h.config, "which", lambda n: None):
            self.assertEqual(review.available_reviewers(cfg, "claude"), [])

    def test_codex_fake_approve_and_flags(self):
        root = h.make_repo()
        ctx, t, (path, rec) = self._run(root, h.APPROVE)
        self.assertEqual(rec["verdict"], "approve")
        self.assertEqual(rec["vendor"], "codex")
        cmd, mode = review.command_for(ctx.cfg, "codex", root, "s.json", "o.txt")
        self.assertIn("read-only", cmd)
        self.assertEqual(cmd[-1], "-")
        self.assertEqual(mode, "file")

    def test_stdout_vendor_via_config(self):
        root = h.make_repo()
        d = h.fake_cli("fakegem", "import sys\nsys.stdin.read()\nprint('```json\\n%s\\n```')\n" % h.APPROVE)
        ctx = h.ctx_for(root)
        ctx.cfg.update({"reviewer_preference": ["gemini"], "base_branch": "main",
                        "reviewer_commands": {"gemini": [str(d / "fakegem")]}})
        t = tasks.load_task(ctx, "TASK-01")
        _, rec = review.review_task(ctx, t, root, "claude")
        self.assertEqual(rec["vendor"], "gemini")

    def test_malformed_rejected(self):
        root = h.make_repo()
        with self.assertRaises(SystemExit):
            self._run(root, "not json at all")
        self.assertEqual(store.count(root / ".agent-team/runs/TASK-01", "review"), 0)

    def test_validate(self):
        self.assertTrue(review.validate_verdict({"verdict": "maybe"}))
        bad = json.loads(h.APPROVE)
        bad["findings"] = [{"severity": "high", "file": "a", "line": 1, "issue": "i", "criterion": "c"}]
        self.assertTrue(any("inconsistent" in p for p in review.validate_verdict(bad)))
        self.assertEqual(review.validate_verdict(json.loads(h.APPROVE)), [])

    def test_review_round_limit(self):
        root = h.make_repo()
        self._run(root, h.CHANGES)
        self._run(root, h.CHANGES)
        with self.assertRaises(SystemExit):
            self._run(root, h.CHANGES)

    def test_diff_redacts_secrets(self):
        root = h.make_repo()
        (root / "c.py").write_text("password = 'hunter2hunter2'\n")
        h.sh(root, "git", "add", "-A")
        h.sh(root, "git", "commit", "-qm", "c")
        ctx = h.ctx_for(root)
        ctx.cfg["base_branch"] = "main"
        diff = review.get_diff(ctx, tasks.load_task(ctx, "TASK-01"), root)
        self.assertNotIn("hunter2hunter2", diff)


class GateTests(unittest.TestCase):
    def test_gate_flow_and_report(self):
        root = h.make_repo()
        ctx = h.ctx_for(root)
        ctx.cfg["base_branch"] = "main"
        ctx.cfg["review_mode"] = "cross-vendor"
        t = tasks.load_task(ctx, "TASK-01")
        ok, reasons, _ = gate.evaluate(ctx, t, root, run_audit=False)
        self.assertFalse(ok)
        self.assertIn("no verify run", reasons)
        verify.verify_task(ctx, t, root)
        d = h.fake_cli("codex", h.codex_body(h.APPROVE))
        with mock.patch.dict(os.environ, {"PATH": f"{d}{os.pathsep}{os.environ['PATH']}"}):
            review.review_task(ctx, t, root, "claude")
        ok, reasons, warns = gate.evaluate(ctx, t, root, run_audit=True)
        self.assertTrue(ok, reasons)
        self.assertTrue(any("not configured" in w for w in warns))
        (root / "hello.txt").write_text("changed")
        h.sh(root, "git", "commit", "-qam", "more")
        ok, reasons, _ = gate.evaluate(ctx, t, root, run_audit=False)
        self.assertFalse(ok)
        md = report.render(report.collect(ctx, 3600))
        self.assertIn("TASK-01", md)
        self.assertIn("| state | count |", md)

    def test_blocked_after_verify_rounds(self):
        root = h.make_repo()
        ctx = h.ctx_for(root)
        t = tasks.load_task(ctx, "TASK-01")
        (root / "hello.txt").write_text("bad")
        for _ in range(3):
            verify.verify_task(ctx, t, root)
        self.assertEqual(store.task_state(ctx, t)[0], "blocked")

    def test_bug_requires_repro_record(self):
        txt = ("# TASK-01 — bug\nType: bug\n\n## Repro\ncheck: test -f nope.txt\n\n"
               "## Acceptance criteria\n- ok\n  check: true\n")
        root = h.make_repo(txt)
        ctx = h.ctx_for(root)
        t = tasks.load_task(ctx, "TASK-01")
        ok, reasons, _ = gate.evaluate(ctx, t, root, run_audit=False)
        self.assertTrue(any("never shown to fail" in r for r in reasons))
        res = verify.verify_task(ctx, t, root, repro_before=True)
        self.assertTrue(res["ok"])

    def test_redact(self):
        self.assertNotIn("AKIAABCDEFGHIJKLMNOP", safety.redact("k AKIAABCDEFGHIJKLMNOP"))


if __name__ == "__main__":
    unittest.main()
