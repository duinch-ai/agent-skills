"""task-board tests: stdlib unittest, temp dirs, no network (every `gh` call goes through a fake runner)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import project_board  # noqa: E402
from taskboard import config as cfgmod  # noqa: E402
from taskboard import store  # noqa: E402
from taskboard.providers import get_provider, runner  # noqa: E402

SPEC = "# TASK-01 — First\nStatus: Backlog\nPriority: P0\n"


class FakeGh:
    """Records every gh call; replies via handler(cmd) -> (rc, out, err)."""

    def __init__(self, handler=None):
        self.calls = []
        self.handler = handler or (lambda cmd: (0, "{}", ""))

    def __call__(self, cmd):
        self.calls.append(cmd)
        return self.handler(cmd)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old_cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(os.chdir, self.old_cwd)
        env = mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        for k in list(os.environ):
            if k.startswith("GH_") or k == "TASK_BOARD_PROVIDER":
                del os.environ[k]
        self.gh = FakeGh()
        runner.set_runner(self.gh)
        self.addCleanup(runner.set_runner, None)
        # no real git remote lookups
        p = mock.patch.object(cfgmod, "detect_git_repo", return_value=(None, None))
        p.start()
        self.addCleanup(p.stop)

    def write(self, rel, text):
        p = Path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def spec(self, status="Backlog"):
        self.write("docs/tasks/TASK-01.md", SPEC.replace("Backlog", status))

    def run_cli(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            project_board.main(list(argv))
        return buf.getvalue()


class ConfigTests(Base):
    def test_no_config_defaults_to_github(self):
        c = cfgmod.resolve_config()
        self.assertEqual(c["provider"], "github")
        self.assertEqual(c["tasks_dir"], "docs/tasks")

    def test_legacy_github_project_json_is_github(self):
        self.write(".github/project.json", json.dumps({"owner": "o", "repo": "r", "project_number": "3", "project_id": "PVT_x"}))
        c = cfgmod.resolve_config()
        self.assertEqual((c["provider"], c["owner"], c["project_id"]), ("github", "o", "PVT_x"))

    def test_new_file_wins_over_legacy(self):
        self.write(".github/project.json", json.dumps({"owner": "old", "repo": "r"}))
        self.write(".agents/task-board.json", json.dumps({"provider": "local", "owner": "new"}))
        self.assertEqual(cfgmod.find_config_file(), os.path.join(".agents", "task-board.json"))
        c = cfgmod.resolve_config()
        self.assertEqual((c["provider"], c["owner"]), ("local", "new"))

    def test_other_legacy_locations_still_found(self):
        for rel in (".agents/project.json", ".agents/workflow.json", "project.json"):
            with self.subTest(rel=rel):
                self.write(rel, "{}")
                self.assertEqual(cfgmod.find_config_file(), rel)
                os.remove(rel)

    def test_precedence_cli_over_env_over_file(self):
        self.write(".agents/task-board.json", json.dumps({"provider": "github", "owner": "file"}))
        self.assertEqual(cfgmod.resolve_config()["owner"], "file")
        os.environ["GH_PROJECT_OWNER"] = "env"
        self.assertEqual(cfgmod.resolve_config()["owner"], "env")
        args = project_board.build_parser().parse_args(["--owner", "cli", "list"])
        self.assertEqual(cfgmod.resolve_config(args)["owner"], "cli")

    def test_provider_env_and_flag(self):
        self.write(".agents/task-board.json", json.dumps({"provider": "github"}))
        os.environ["TASK_BOARD_PROVIDER"] = "local"
        self.assertEqual(cfgmod.resolve_config()["provider"], "local")
        args = project_board.build_parser().parse_args(["--provider", "gitlab", "list"])
        self.assertEqual(cfgmod.resolve_config(args)["provider"], "gitlab")

    def test_init_local_writes_new_file_and_keeps_legacy(self):
        self.write(".github/project.json", json.dumps({"owner": "o"}))
        self.run_cli("init", "--provider", "local")
        new = json.loads(Path(".agents/task-board.json").read_text())
        self.assertEqual(new["provider"], "local")
        self.assertEqual(new["tasks_dir"], "docs/tasks")
        self.assertTrue(Path(".github/project.json").exists())
        self.assertEqual(self.gh.calls, [])

    def test_init_github_default_provider_via_runner(self):
        reply = {"data": {"user": {"projectV2": {"id": "PVT_1", "title": "T"}}, "organization": None}}
        self.gh.handler = lambda cmd: (0, json.dumps(reply), "")
        self.run_cli("--owner", "o", "--repo", "r", "init", "--project", "7")
        new = json.loads(Path(".agents/task-board.json").read_text())
        self.assertEqual((new["provider"], new["owner"], new["project_number"], new["project_id"]),
                         ("github", "o", "7", "PVT_1"))
        self.assertTrue(all(c[:2] == ["gh", "api"] for c in self.gh.calls))

    def test_init_unknown_provider_rejected(self):
        with self.assertRaises(SystemExit):
            get_provider("nope")


class LocalProviderTests(Base):
    def setUp(self):
        super().setUp()
        self.write(".agents/task-board.json", json.dumps({"provider": "local"}))
        self.spec()
        self.gh.handler = lambda cmd: self.fail(f"gh must not run for provider local: {cmd}")

    def test_round_trip_zero_api_calls(self):
        out = self.run_cli("list")
        self.assertIn("TASK-01", out)
        self.assertIn("Backlog", out)
        self.run_cli("move", "task-01", "In Progress")
        self.assertIn("Status: IN_PROGRESS", Path("docs/tasks/TASK-01.md").read_text())
        out = self.run_cli("list", "--status", "In Progress")
        self.assertIn("TASK-01", out)
        rep = self.run_cli("report")
        self.assertIn("**In Progress** | 1", rep)
        self.assertIn("local", rep)
        for sub in ("sync", "rate-limit"):
            self.assertIn("local", self.run_cli(sub))
        self.run_cli("push", "docs/tasks/TASK-01.md", "--status", "Todo")
        self.assertEqual(self.gh.calls, [])
        # no cache/outbox files for a remote-less provider
        self.assertFalse(Path(".local-artifacts").exists())

    def test_move_without_status_line_fails_loudly(self):
        self.write("docs/tasks/TASK-02.md", "# TASK-02 — No status here\nPriority: P1\n")
        before = Path("docs/tasks/TASK-02.md").read_text()
        with self.assertRaises(SystemExit) as cm:
            self.run_cli("move", "TASK-02", "Done")
        self.assertIn("Status:", str(cm.exception))
        self.assertNotEqual(cm.exception.code, 0)
        self.assertEqual(Path("docs/tasks/TASK-02.md").read_text(), before)
        with self.assertRaises(SystemExit):
            self.run_cli("push", "docs/tasks/TASK-02.md", "--status", "Todo")

    def test_provider_object_never_uses_runner(self):
        p = get_provider("local")
        self.assertFalse(p.uses_cache)
        self.assertEqual(p.flush_outbox({}), 0)


class GitlabStubTests(Base):
    def test_not_implemented_message(self):
        self.write(".agents/task-board.json", json.dumps({"provider": "gitlab"}))
        self.spec()
        for argv in (["list"], ["move", "TASK-01", "Done"], ["sync"], ["report"], ["init"]):
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit) as cm:
                    self.run_cli(*argv)
                self.assertIn("GitLab provider not implemented yet", str(cm.exception))
        self.assertIn("Backlog", Path("docs/tasks/TASK-01.md").read_text())
        self.assertIn("TASK-01", self.run_cli("list", "--local-only"))
        self.assertEqual(self.gh.calls, [])


class GithubProviderTests(Base):
    CFG = {"provider": "github", "owner": "o", "repo": "r", "project_number": "1", "project_id": "PVT_1"}

    def setUp(self):
        super().setUp()
        self.write(".agents/task-board.json", json.dumps(self.CFG))
        self.spec()
        self.real_spawn = store.spawn_auto_sync_daemon
        spawn = mock.patch.object(store, "spawn_auto_sync_daemon", return_value=None)
        spawn.start()
        self.addCleanup(spawn.stop)

    def handler(self, cmd):
        text = " ".join(cmd)
        if "rate_limit" in text:
            res = {"resources": {"core": {"remaining": 4000, "limit": 5000, "reset": 0},
                                 "graphql": {"remaining": 4000, "limit": 5000, "reset": 0}}}
            return 0, json.dumps(res), ""
        if "ProjectV2SingleSelectField" in text:
            data = {"data": {"node": {"fields": {"nodes": [
                {"id": "F1", "name": "Status", "options": [{"id": "O1", "name": "Todo"}, {"id": "O2", "name": "In Progress"}]}]}}}}
            return 0, json.dumps(data), ""
        if "projectItems" in text:
            return 0, json.dumps({"data": {"repository": {"issue": {"id": "I", "projectItems": {"nodes": [
                {"id": "ITEM1", "project": {"id": "PVT_1"}}]}}}}}), ""
        if "updateProjectV2ItemFieldValue" in text:
            return 0, "{}", ""
        return 1, "", "unexpected"

    def test_move_goes_through_runner(self):
        self.write("docs/BACKLOG.md", "| TASK-01 | [#5](u) | x |\n")
        self.gh.handler = self.handler
        out = self.run_cli("move", "TASK-01", "In Progress")
        self.assertIn("on GitHub Project #1", out)
        self.assertTrue(self.gh.calls)
        self.assertTrue(all(c[0] == "gh" for c in self.gh.calls))
        self.assertTrue(any("updateProjectV2ItemFieldValue" in " ".join(c) and "ITEM1" in " ".join(c) for c in self.gh.calls))
        self.assertIn("Status: IN_PROGRESS", Path("docs/tasks/TASK-01.md").read_text())

    def test_move_failure_defers_to_outbox(self):
        self.gh.handler = lambda cmd: (1, "", "HTTP 403 rate limit")
        out = self.run_cli("move", "TASK-01", "Todo")
        self.assertIn("Deferred GitHub Project update", out)
        outbox = json.loads(Path(".local-artifacts/project_board_outbox.json").read_text())
        self.assertEqual([(e["action"], e["task_id"], e["status"]) for e in outbox], [("move", "TASK-01", "Todo")])
        self.assertIn("Status: TODO", Path("docs/tasks/TASK-01.md").read_text())

    def test_list_local_only_makes_no_calls(self):
        self.run_cli("list", "--local-only")
        self.assertEqual(self.gh.calls, [])

    def test_list_remote_sync_reconciles_spec(self):
        items = {"items": [{"id": "ITEM1", "title": "TASK-01 — First", "status": "Done", "content": {"number": 5}}]}

        def h(cmd):
            if cmd[:3] == ["gh", "project", "item-list"]:
                return 0, json.dumps(items), ""
            return self.handler(cmd)

        self.gh.handler = h
        out = self.run_cli("list", "--refresh")
        self.assertIn("REMOTE SYNC", out)
        self.assertIn("#5", out)
        self.assertIn("Status: DONE", Path("docs/tasks/TASK-01.md").read_text())

    def test_legacy_config_behaves_as_github(self):
        os.remove(".agents/task-board.json")
        self.write(".github/project.json", json.dumps({k: v for k, v in self.CFG.items() if k != "provider"}))
        self.gh.handler = self.handler
        self.write("docs/BACKLOG.md", "| TASK-01 | [#5](u) | x |\n")
        self.assertIn("on GitHub Project #1", self.run_cli("move", "TASK-01", "Todo"))

    def test_daemon_spawn_command_parses(self):
        with mock.patch.object(store.subprocess, "Popen") as popen:
            popen.return_value.pid = 4242
            self.real_spawn(cfgmod.resolve_config(), 9999999999)
            cmd = popen.call_args[0][0]
        # global flags must precede the subcommand, otherwise argparse rejects the daemon launch
        args = project_board.build_parser().parse_args(cmd[2:])
        self.assertEqual((args.cmd, args.until, args.owner, args.project_number), ("daemon", 9999999999.0, "o", "1"))


if __name__ == "__main__":
    unittest.main()
