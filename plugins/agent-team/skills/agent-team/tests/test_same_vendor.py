import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import helpers as h
import agent_team
import config
import gate
import store
import tasks
import init_cmd


def cli(root, *args, mode=None):
    if mode:
        p = Path(root) / config.CONFIG_REL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"review_mode": mode, "base_branch": "main"}))
    elif not (Path(root) / config.CONFIG_REL).exists():
        p = Path(root) / config.CONFIG_REL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"base_branch": "main"}))
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = agent_team.main(["--root", str(root), "review", "TASK-01", "--cwd", str(root), *args])
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 1
            err.write(str(e.code))
    return rc, out.getvalue(), err.getvalue()


def vfile(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    f.write(text)
    f.close()
    return f.name


class SameVendorTests(unittest.TestCase):
    def setUp(self):
        self.root = h.make_repo()
        self.runs = self.root / ".agent-team/runs/TASK-01"

    def test_default_and_invalid_mode(self):
        self.assertEqual(config.load_config(self.root)["review_mode"], "same-vendor")
        p = self.root / config.CONFIG_REL
        p.parent.mkdir(parents=True)
        p.write_text('{"review_mode": "x"}')
        with self.assertRaises(SystemExit) as e:
            config.load_config(self.root)
        self.assertIn("same-vendor", str(e.exception))

    def test_prompt_prints_and_writes_nothing(self):
        rc, out, _ = cli(self.root, "--prompt")
        self.assertEqual(rc, 0)
        self.assertIn("<<<DIFF", out)
        self.assertIn('"required"', out)
        self.assertIn("ONLY a JSON object", out)
        self.assertEqual(store.count(self.runs, "review"), 0)

    def test_record_valid_without_coder(self):
        rc, _, _ = cli(self.root, "--record", vfile("verdict:\n" + h.APPROVE + "\nthanks"), "--reviewer", "rv")
        self.assertEqual(rc, 0)
        rec = store.latest(self.runs, "review")
        self.assertEqual((rec["mode"], rec["reviewer"], rec["coder"], rec["vendor"]),
                         ("same-vendor", "rv", None, "same-vendor"))

    def test_record_invalid(self):
        rc, _, _ = cli(self.root, "--record", vfile("not json"))
        self.assertNotEqual(rc, 0)
        self.assertEqual(store.count(self.runs, "review-invalid"), 1)
        self.assertEqual(store.count(self.runs, "review"), 0)

    def test_round_limit(self):
        f = vfile(h.CHANGES)
        cli(self.root, "--record", f)
        cli(self.root, "--record", f)
        rc, _, err = cli(self.root, "--record", f)
        self.assertNotEqual(rc, 0)
        self.assertIn("exhausted", err)
        self.assertEqual(store.count(self.runs, "review"), 2)

    def test_neither_flag(self):
        self.assertEqual(cli(self.root)[0], 2)

    def test_flags_in_cross_vendor(self):
        rc, _, err = cli(self.root, "--prompt", mode="cross-vendor")
        self.assertEqual(rc, 2)
        self.assertIn("review_mode", err)

    def _gate(self, mode, rev_mode):
        ctx = h.ctx_for(self.root)
        ctx.cfg.update({"base_branch": "main", "review_mode": mode})
        t = tasks.load_task(ctx, "TASK-01")
        head = store.head_info(self.root)
        store.write(self.runs, "verify", {"ok": True, **head})
        rec = {"verdict": "approve", "findings": [], **head}
        if rev_mode:
            rec["mode"] = rev_mode
        store.write(self.runs, "review", rec)
        return gate.evaluate(ctx, t, self.root, run_audit=False)

    def test_gate_same_vendor_no_coder_needed(self):
        ok, reasons, _ = self._gate("same-vendor", "same-vendor")
        self.assertTrue(ok, reasons)

    def test_gate_same_vendor_accepts_old_record(self):
        self.assertTrue(self._gate("same-vendor", None)[0])

    def test_gate_cross_vendor_rejects_same_vendor_record(self):
        ok, reasons, _ = self._gate("cross-vendor", "same-vendor")
        self.assertFalse(ok)
        self.assertIn("review was same-vendor but review_mode is cross-vendor", reasons)

    def test_init_installs_reviewer(self):
        msgs = init_cmd.init(h.ctx_for(self.root))
        self.assertIn("installed .agents/agents/reviewer.md", msgs)
        canonical = self.root / ".agents/agents/reviewer.md"
        self.assertTrue(canonical.is_file())
        for vendor in (".claude", ".codex", ".gemini", ".agy"):
            link = self.root / vendor / "agents/reviewer.md"
            self.assertTrue(link.is_symlink(), f"{link} should be a symlink")
            self.assertEqual(link.resolve(), canonical.resolve())

    def test_init_falls_back_to_copy_when_symlink_fails(self):
        orig = Path.symlink_to
        def fail_symlink(self_path, target, *args, **kwargs):
            raise OSError("symlinks disabled")
        Path.symlink_to = fail_symlink
        try:
            msgs = init_cmd.init(h.ctx_for(self.root))
        finally:
            Path.symlink_to = orig
        canonical = self.root / ".agents/agents/reviewer.md"
        self.assertTrue(canonical.is_file())
        for vendor in (".claude", ".codex", ".gemini", ".agy"):
            copied = self.root / vendor / "agents/reviewer.md"
            self.assertTrue(copied.is_file())
            self.assertFalse(copied.is_symlink())
            self.assertEqual(copied.read_text(), canonical.read_text())
            self.assertIn(f"copied {vendor}/agents/reviewer.md (symlink unavailable)", msgs)

    def test_gate_auto_moves_task_board_when_configured(self):
        import os
        import subprocess
        (self.root / ".agents").mkdir(exist_ok=True)
        (self.root / ".agents/task-board.json").write_text('{"provider": "local"}')
        subprocess.run(["git", "-C", str(self.root), "add", ".agents/task-board.json"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-m", "board"], check=True, capture_output=True)
        self._gate("same-vendor", "same-vendor")
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "board_args.txt"
            fake = Path(td) / "fake_board.py"
            fake.write_text(f"import sys\nopen({str(log)!r}, 'w').write(' '.join(sys.argv[1:]))\n")
            old = os.environ.get("TASK_BOARD_SCRIPT")
            os.environ["TASK_BOARD_SCRIPT"] = str(fake)
            out, err = io.StringIO(), io.StringIO()
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    rc = agent_team.main(["--root", str(self.root), "gate", "TASK-01", "--cwd", str(self.root), "--no-audit"])
            finally:
                if old is None:
                    os.environ.pop("TASK_BOARD_SCRIPT", None)
                else:
                    os.environ["TASK_BOARD_SCRIPT"] = old
            self.assertEqual(rc, 0, out.getvalue() + err.getvalue())
            self.assertIn("task-board: moved TASK-01 -> Done", out.getvalue())
            self.assertEqual(log.read_text(), "move TASK-01 Done")


if __name__ == "__main__":
    unittest.main()
