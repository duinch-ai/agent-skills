import io
import os
import unittest
from contextlib import redirect_stderr
from unittest import mock

import helpers as h
import gate
import review
import store
import tasks

CODER_TASK = h.TASK.replace("Priority: P1\n", "Priority: P1\nCoder: Codex\n")


def run(root, coder=None, cfg=None, reply=h.APPROVE):
    ctx = h.ctx_for(root)
    ctx.cfg["base_branch"] = "main"
    ctx.cfg.update(cfg or {})
    t = tasks.load_task(ctx, "TASK-01")
    d = h.fake_cli("codex", h.codex_body(reply))
    with mock.patch.dict(os.environ, {"PATH": f"{d}{os.pathsep}{os.environ['PATH']}"}):
        return ctx, review.review_task(ctx, t, root, coder)


class CoderTests(unittest.TestCase):
    def test_field_parsed(self):
        root = h.make_repo(CODER_TASK)
        self.assertEqual(tasks.load_task(h.ctx_for(root), "TASK-01").coder, "codex")
        root = h.make_repo()
        self.assertIsNone(tasks.load_task(h.ctx_for(root), "TASK-01").coder)

    def test_task_coder_used(self):
        # coder codex -> codex excluded; a stdout vendor takes over
        root = h.make_repo(CODER_TASK)
        d = h.fake_cli("fakegem", "import sys\nsys.stdin.read()\nprint('%s')\n" % h.APPROVE)
        _, (_, rec) = run(root, cfg={"reviewer_preference": ["codex", "gemini"],
                                     "reviewer_commands": {"gemini": [str(d / "fakegem")]}})
        self.assertEqual((rec["coder"], rec["vendor"]), ("codex", "gemini"))

    def test_arg_when_task_has_none(self):
        _, (_, rec) = run(h.make_repo(), coder="claude")
        self.assertEqual((rec["coder"], rec["coder_family"], rec["reviewer_family"]),
                         ("claude", "claude", "codex"))

    def test_conflict_and_missing(self):
        with self.assertRaises(SystemExit) as e:
            run(h.make_repo(CODER_TASK), coder="claude")
        self.assertIn("conflicts", str(e.exception))
        with self.assertRaises(SystemExit) as e:
            run(h.make_repo())
        self.assertIn("Coder:", str(e.exception))

    def test_agy_family(self):
        cfg = dict(h.config.DEFAULTS)
        cfg["reviewer_preference"] = ["agy", "codex"]
        cfg["reviewer_commands"] = {"agy": ["agy"]}
        with mock.patch.object(h.config, "which", lambda n: "/x/" + n):
            self.assertEqual(review.available_reviewers(cfg, "gemini"), ["codex"])
            cfg["vendor_family"] = {"agy": "claude"}
            self.assertEqual(review.available_reviewers(cfg, "gemini"), ["agy", "codex"])
            self.assertEqual(review.available_reviewers(cfg, "claude"), ["codex"])

    def test_old_config_warns(self):
        err = io.StringIO()
        with redirect_stderr(err):
            _, (_, rec) = run(h.make_repo(CODER_TASK.replace("Codex", "Claude")),
                              cfg={"coder_vendor": "claude"})
        self.assertIn("coder_vendor", err.getvalue())
        self.assertEqual(rec["coder"], "claude")

    def _gate(self, **rev):
        root = h.make_repo(CODER_TASK)
        ctx = h.ctx_for(root)
        ctx.cfg["base_branch"] = "main"
        ctx.cfg["review_mode"] = "cross-vendor"
        t = tasks.load_task(ctx, "TASK-01")
        d = ctx.runs("TASK-01")
        head = store.head_info(root)
        store.write(d, "verify", {"ok": True, **head})
        store.write(d, "review", {"verdict": "approve", "findings": [], **rev, **head})
        return gate.evaluate(ctx, t, root, run_audit=False)[1]

    def test_gate_missing_coder_and_family(self):
        self.assertIn("review has no recorded coder", self._gate(vendor="codex"))
        self.assertIn("reviewer and coder are from the same vendor family",
                      self._gate(vendor="agy", coder="gemini"))
        self.assertEqual(self._gate(vendor="codex", coder="claude"), [])


if __name__ == "__main__":
    unittest.main()
