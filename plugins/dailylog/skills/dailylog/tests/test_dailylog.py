"""End-to-end tests: run the real CLI and installer in temporary folders."""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "dailylog.py"
THURSDAY = "2026-11-05T12:30:00"
NEXT_MONDAY = "2026-11-09T09:00:00"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(os.path.realpath(self.tmp.name))
        self.root = self.base / "work"
        self.home = self.base / "home"
        self.root.mkdir()
        self.home.mkdir()
        self.mem = self.root / "memory"

    def run_cli(self, *args, stdin="", when=THURSDAY, ok=True, cwd=None):
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("DAILYLOG_", "CLAUDE", "CODEX_", "ANTIGRAVITY", "AGY_", "GEMINI_CLI"))}
        env.update(HOME=str(self.home), DAILYLOG_NOW=when, DAILYLOG_INSTANCE="Test", TZ="UTC")
        done = subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, text=True, capture_output=True,
                              cwd=str(cwd or self.root), env=env)
        if ok:
            self.assertEqual(done.returncode, 0, done.stderr)
        return done

    def init(self):
        self.run_cli("init")


class Layers(Base):
    def test_init_keeps_existing_logs_and_is_repeatable(self):
        week = self.mem / "2026-W45"
        week.mkdir(parents=True)
        (week / "2026-11-05.md").write_text("old log\n", encoding="utf-8")
        self.init()
        self.init()
        self.assertEqual((week / "2026-11-05.md").read_text(encoding="utf-8"), "old log\n")
        self.assertTrue((self.mem / "INDEX.md").exists())

    def test_iso_week_at_year_boundary(self):
        self.init()
        self.run_cli("log", "note", when="2027-01-01T10:00:00")
        self.assertTrue((self.mem / "2026-W53" / "2027-01-01.md").exists())

    def test_plex_tags_survive(self):
        self.init()
        text = "Fixed Wataru (1988) {tvdb-227501} {tmdb-19612}"
        self.run_cli("log", text, "-p", "subs", "-s", "done")
        self.run_cli("new", "knowledge", "wataru", "--summary", "{tvdb-227501}", "--body", text)
        self.assertIn(text, (self.mem / "2026-W45" / "2026-11-05.md").read_text(encoding="utf-8"))
        self.assertIn("{tvdb-227501}", (self.mem / "INDEX.md").read_text(encoding="utf-8"))

    def test_stdin_text_keeps_shell_characters(self):
        self.init()
        self.run_cli("log", "-", stdin="costs $5 and `rm` 'x'")
        self.assertIn("costs $5 and `rm` 'x'", (self.mem / "2026-W45" / "2026-11-05.md").read_text(encoding="utf-8"))

    def test_secrets_are_refused_and_linted(self):
        self.init()
        token = "ghp_" + "a" * 30
        done = self.run_cli("log", f"token {token}", ok=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertFalse((self.mem / "2026-W45" / "2026-11-05.md").exists())
        (self.mem / "knowledge" / "leak.md").write_text(f"{token}\n", encoding="utf-8")
        lint = self.run_cli("lint", ok=False)
        self.assertEqual(lint.returncode, 1)
        self.assertNotIn(token, lint.stdout)

    def test_environment_secret_is_refused(self):
        self.init()
        text = 'export TORBOX_API_TOKEN="abc123def456"'
        self.assertNotEqual(self.run_cli("log", text, ok=False).returncode, 0)
        self.assertNotEqual(self.run_cli("log", "mật khẩu là abc12345", ok=False).returncode, 0)
        self.assertNotEqual(self.run_cli("log", "token la 11111111-2222-4333-8444-555555555555", ok=False).returncode, 0)
        self.assertNotEqual(self.run_cli("log", "Token cua ban:\n11111111-2222-4333-8444-555555555555", ok=False).returncode, 0)
        self.run_cli("log", "set TORBOX_API_TOKEN in the keychain")
        self.run_cli("log", "export FOO_TOKEN=$VALUE")

    def test_todo_lifecycle(self):
        self.init()
        self.run_cli("todo", "add", "Switchfin", "Fix cast header")
        self.run_cli("todo", "add", "Switchfin", "Fix cast footer")
        self.assertNotEqual(self.run_cli("todo", "done", "switchfin", "Fix cast", ok=False).returncode, 0)
        self.run_cli("todo", "start", "switchfin", "header")
        project = (self.mem / "projects" / "switchfin.md").read_text(encoding="utf-8")
        self.assertIn("- [/] [IN_PROGRESS] (Test) Fix cast header", project)
        self.assertIn("IN_PROGRESS", self.run_cli("context").stdout)
        self.run_cli("todo", "done", "switchfin", "header")
        self.assertNotIn("header", (self.mem / "projects" / "switchfin.md").read_text(encoding="utf-8"))
        log = (self.mem / "2026-W45" / "2026-11-05.md").read_text(encoding="utf-8")
        self.assertIn("[DONE] (Test) 12:30 [switchfin] Fix cast header", log)

    def test_search_ignores_diacritics_and_ranks_knowledge_first(self):
        self.init()
        self.run_cli("log", "Quyết định dùng deadzone")
        self.run_cli("new", "knowledge", "joycon", "--summary", "x", "--body", "Quyết định deadzone 25%")
        out = self.run_cli("search", "quyet", "dinh", "deadzone").stdout
        self.assertLess(out.index("knowledge/joycon.md"), out.index("2026-11-05.md"))

    def test_superseded_decision_is_flagged_and_leaves_index(self):
        self.init()
        self.run_cli("new", "decision", "old-way", "--title", "Old way", "--choice", "A")
        self.run_cli("new", "decision", "new-way", "--title", "New way", "--choice", "B", "--supersedes", "old-way",
                     when="2026-11-06T10:00:00")
        self.assertIn("[SUPERSEDED]", self.run_cli("search", "old", "way").stdout)
        index = (self.mem / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("New way", index)
        self.assertNotIn("Old way", index)

    def test_index_keeps_human_notes(self):
        self.init()
        with open(self.mem / "INDEX.md", "a", encoding="utf-8") as handle:
            handle.write("my own note\n")
        self.run_cli("new", "project", "ting", "--summary", "App")
        index = (self.mem / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("my own note", index)
        self.assertIn("[ting](projects/ting.md)", index)


class NewWeek(Base):
    def test_monday_still_sees_last_week_and_gets_reminded(self):
        self.init()
        self.run_cli("log", "Friday finding")
        (self.mem / "2026-W45" / "summary.md").write_text("Week summary here\n", encoding="utf-8")
        out = self.run_cli("context", "--max-chars", "6000", when=NEXT_MONDAY).stdout
        self.assertIn("Friday finding", out)
        self.assertIn("Week summary here", out)
        self.assertIn("2026-W45 is not consolidated", out)

    def test_consolidate_flow(self):
        self.init()
        self.run_cli("log", "Thing")
        self.assertIn("2026-W45", self.run_cli("consolidate", when=NEXT_MONDAY).stdout)
        self.assertNotEqual(self.run_cli("consolidate", "--week", "2026-W45", "--done", "--headline", "H",
                                         ok=False, when=NEXT_MONDAY).returncode, 0)
        (self.mem / "2026-W45" / "summary.md").write_text("S\n", encoding="utf-8")
        self.assertIn("2026-11-05.md", self.run_cli("consolidate", "--week", "2026-W45", when=NEXT_MONDAY).stdout)
        self.run_cli("consolidate", "--week", "2026-W45", "--done", "--headline", "Good week", when=NEXT_MONDAY)
        self.assertIn("2026-11-02 to 2026-11-08", (self.mem / "HISTORY.md").read_text(encoding="utf-8"))
        self.assertIn("Good week", (self.mem / "INDEX.md").read_text(encoding="utf-8"))
        self.assertEqual(self.run_cli("consolidate", when=NEXT_MONDAY).stdout.strip(), "nothing to consolidate")

    def test_lint_flags_stale_and_misfiled(self):
        self.init()
        self.run_cli("new", "knowledge", "old", "--summary", "x", when="2026-01-01T10:00:00")
        wrong = self.mem / "2026-W45" / "2026-11-01.md"
        wrong.parent.mkdir(exist_ok=True)
        wrong.write_text("x\n", encoding="utf-8")
        out = self.run_cli("lint").stdout
        self.assertIn("knowledge/old.md", out)
        self.assertIn("belongs in 2026-W44", out)


class Hooks(Base):
    def hook(self, agent, event, payload, *extra, cwd=None):
        return self.run_cli("hook", "--agent", agent, "--event", event, *extra, stdin=json.dumps(payload), cwd=cwd).stdout

    def log(self):
        return (self.mem / "2026-W45" / "2026-11-05.md").read_text(encoding="utf-8")

    def test_claude_session_is_one_updated_line(self):
        self.init()
        base = {"session_id": "abc123", "cwd": str(self.root)}
        self.hook("claude", "SessionStart", {**base, "source": "startup"})
        self.hook("claude", "UserPromptSubmit", {**base, "prompt": "Fix {tvdb-1} bug"})
        self.hook("claude", "Stop", {**base, "last_assistant_message": "Fixed it"})
        self.hook("claude", "UserPromptSubmit", {**base, "prompt": "Second"})
        self.hook("claude", "Stop", {**base, "last_assistant_message": "All done"})
        lines = [l for l in self.log().splitlines() if "session:abc123" in l]
        self.assertEqual(len(lines), 1)
        self.assertIn("2 turns", lines[0])
        self.assertIn('"Fix {tvdb-1} bug" -> All done', lines[0])

    def test_empty_session_is_not_logged(self):
        self.init()
        self.hook("claude", "SessionStart", {"session_id": "idle", "cwd": str(self.root)})
        self.assertFalse((self.mem / "2026-W45" / "2026-11-05.md").exists())

    def test_prompt_secrets_are_redacted_and_meta_omits_text(self):
        self.init()
        token = "ghp_" + "b" * 30
        self.hook("codex", "UserPromptSubmit", {"session_id": "s1", "cwd": str(self.root), "prompt": f"use {token}"})
        self.assertNotIn(token, self.log())
        self.assertIn("[redacted]", self.log())
        self.hook("codex", "UserPromptSubmit", {"session_id": "s2", "cwd": str(self.root), "prompt": "QUIET-PROMPT"},
                  "--capture", "meta")
        self.assertNotIn("QUIET-PROMPT", self.log())

    def test_antigravity_contract(self):
        self.init()
        self.run_cli("new", "project", "ting", "--summary", "App")
        payload = {"conversationId": "ec33ebf9", "workspacePaths": [str(self.root)], "lastUserInput": "Do it"}
        start = json.loads(self.hook("agy", "SessionStart", payload, "--context-chars", "1500"))
        self.assertIn("ting", start["injectSteps"][0]["systemMessage"]["systemMessage"])
        self.assertEqual(json.loads(self.hook("agy", "Stop", payload)), {})
        self.assertIn('(Antigravity:Test)', self.log())
        self.assertIn('"Do it"', self.log())

    def test_context_budget_and_resume(self):
        self.init()
        for i in range(30):
            self.run_cli("new", "project", f"project-{i}", "--summary", "s" * 100)
        base = {"session_id": "c1", "cwd": str(self.root)}
        out = self.hook("claude", "SessionStart", {**base, "source": "startup"}, "--context-chars", "2000")
        self.assertLessEqual(len(out), 2300)
        self.assertEqual(self.hook("claude", "SessionStart", {**base, "source": "resume"}, "--context-chars", "2000"), "")

    def test_no_project_memory_falls_back_to_global(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        self.hook("claude", "UserPromptSubmit", {"session_id": "g1", "cwd": str(elsewhere), "prompt": "hi"}, cwd=elsewhere)
        store = self.home / ".dailylog"
        self.assertTrue((store / "2026-W45" / "2026-11-05.md").exists())
        self.assertFalse((store / "memory").exists())
        self.run_cli("log", "by hand", "--root", str(store), cwd=elsewhere)
        self.assertIn("by hand", (store / "2026-W45" / "2026-11-05.md").read_text(encoding="utf-8"))
        self.assertIn("by hand", self.run_cli("search", "by hand", "--root", str(store), "--lines", "1", cwd=elsewhere).stdout)

    def test_bad_input_never_breaks_the_agent(self):
        done = self.run_cli("hook", "--agent", "claude", "--event", "Stop", stdin="not json")
        self.assertEqual(done.returncode, 0)

    def test_install_hooks_merges_and_removes(self):
        settings = self.home / ".claude" / "settings.json"
        settings.parent.mkdir()
        other = {"matcher": "", "hooks": [{"type": "command", "command": "other.sh"}]}
        settings.write_text(json.dumps({"model": "x", "hooks": {"Stop": [other]}}), encoding="utf-8")
        for _ in range(2):
            self.run_cli("install-hooks", "--agents", "claude,codex,agy")
        data = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(data["model"], "x")
        self.assertEqual(len(data["hooks"]["Stop"]), 2)
        self.assertIn(other, data["hooks"]["Stop"])
        self.assertTrue((self.home / ".claude" / "settings.json.dailylog-backup").exists())
        self.assertIn("SessionStart", json.loads((self.home / ".codex" / "hooks.json").read_text(encoding="utf-8"))["hooks"])
        self.assertIn("Stop", json.loads((self.home / ".gemini/config/hooks.json").read_text(encoding="utf-8"))["dailylog"])
        self.run_cli("install-hooks", "--agents", "claude,codex,agy", "--remove")
        data = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(data["hooks"], {"Stop": [other]})

    def test_invalid_settings_are_not_overwritten(self):
        settings = self.home / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text("{broken", encoding="utf-8")
        self.assertNotEqual(self.run_cli("install-hooks", "--agents", "claude", ok=False).returncode, 0)
        self.assertEqual(settings.read_text(encoding="utf-8"), "{broken")


class Limits(Base):
    def hook(self, agent, event, payload):
        args = ["hook", "--agent", agent, "--event", event]
        return self.run_cli(*args, stdin=json.dumps(payload))

    def test_report_sorts_by_hour_and_totals_by_agent(self):
        self.init()
        week = self.mem / "2026-W45"
        week.mkdir(exist_ok=True)
        (week / "2026-11-05.md").write_text(
            "# Log\n\n- legacy line without time\n"
            "- [session] (Claude, opus) 14:00-14:30, 3 turns, ~/a: \"late\" <!-- session:a -->\n"
            "- [session] (Codex) 09:00-09:10, 1 turn, ~/b: \"early\" <!-- session:b -->\n"
            "- [x] [DONE] (Claude) 14:10 [ting] Finished\n", encoding="utf-8")
        out = self.run_cli("report", "--day", "2026-11-05").stdout
        self.assertLess(out.index("## 09:00"), out.index("## 14:00"))
        self.assertIn("| Claude | 1 | 3 | 30 | 2 |", out)
        self.assertIn("| Codex | 1 | 1 | 10 | 1 |", out)
        self.assertIn("1 older lines", out)
        self.assertNotIn("session:a", out)
        only = self.run_cli("report", "--day", "2026-11-05", "--agent", "codex").stdout
        self.assertIn("early", only)
        self.assertNotIn("late", only)

    def test_session_line_has_model_and_instance(self):
        self.init()
        env_payload = {"session_id": "m1", "cwd": str(self.root), "model": "claude-opus-5-5", "prompt": "**Bold** ask"}
        self.hook("claude", "UserPromptSubmit", env_payload)
        log = (self.mem / "2026-W45" / "2026-11-05.md").read_text(encoding="utf-8")
        self.assertIn("(Claude:Test, claude-opus-5-5)", log)
        self.assertIn("1 turn,", log)
        self.assertIn('"Bold ask"', log)

    def test_index_stays_in_budget(self):
        self.init()
        for i in range(45):
            (self.mem / "knowledge" / f"note-{i}.md").write_text(
                f"---\ntitle: Note {i}\nsummary: s\nverified: 2026-11-05\nupdated: 2026-10-{i % 28 + 1:02d}\n---\nbody\n", encoding="utf-8")
            (self.mem / "projects" / f"p-{i}.md").write_text(
                f"---\ntitle: P{i}\nstatus: active\nupdated: 2026-10-{i % 28 + 1:02d}\n---\n", encoding="utf-8")
        self.run_cli("index")
        index = (self.mem / "INDEX.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(index.splitlines()), 100)
        self.assertIn("15 older notes", index)
        self.assertIn("25 older or archived projects", index)
        self.assertNotIn("INDEX.md has", self.run_cli("lint").stdout)

    def test_search_partial_and_global_store(self):
        self.init()
        self.run_cli("new", "knowledge", "cache", "--summary", "phinh cache anh", "--body", "x")
        out = self.run_cli("search", "cache", "anh", "tran").stdout
        self.assertIn("partial matches", out)
        self.assertIn("knowledge/cache.md", out)
        store = self.home / ".dailylog"
        self.run_cli("init", "--root", str(store))
        self.run_cli("log", "global-only finding", "--root", str(store))
        self.assertIn("~/.dailylog: 2026-W45/2026-11-05.md", self.run_cli("search", "global-only").stdout)
        self.assertIn("no matches", self.run_cli("search", "global-only", "--here").stdout)


class Find(Base):
    def note(self, slug, **fields):
        args = ["new", "knowledge", slug, "--summary", fields.get("summary", "s"), "--body", fields.get("body", "x")]
        for key in ("project", "tags", "aliases"):
            if key in fields:
                args += [f"--{key}", fields[key]]
        self.run_cli(*args)

    def test_whole_words_not_substrings(self):
        self.init()
        self.note("a", body="sua trang chu")
        self.note("b", body="tran bo dem")
        out = self.run_cli("search", "tran").stdout
        self.assertIn("knowledge/b.md", out)
        self.assertNotIn("knowledge/a.md", out)

    def test_camel_case_and_section_heading(self):
        self.init()
        self.note("cache", body="## Borealis\n\nFixed LRUCache capacity\n\n## Other\n\nunrelated text")
        out = self.run_cli("search", "lru", "cache").stdout
        self.assertIn("knowledge/cache.md", out)
        self.assertIn("[Borealis]", out)
        self.assertIn("Fixed LRUCache capacity", out)
        self.assertNotIn("unrelated text", out)

    def test_rare_word_and_phrase_rank_higher(self):
        self.init()
        for i in range(8):
            self.run_cli("log", f"tim kiem cau hinh lan {i}")
        self.run_cli("log", "tim hieu mo hinh ngu nghia")
        self.note("semantic", body="tim kiem ngu nghia cho ghi chu")
        lines = self.run_cli("search", "tìm kiếm ngữ nghĩa").stdout.splitlines()
        self.assertEqual(lines[0], "knowledge/semantic.md")

    def test_alias_finds_other_wording_and_index_updates(self):
        self.init()
        self.note("cache", body="phinh cache anh 900MB")
        self.assertIn("no matches", self.run_cli("search", "tran", "bo", "nho", "--layer", "history").stdout)
        self.assertNotIn("knowledge/cache.md", self.run_cli("search", "tran", "bo", "nho").stdout)
        self.run_cli("alias", "phình cache", "tràn bộ nhớ")
        self.assertIn("knowledge/cache.md", self.run_cli("search", "tràn bộ nhớ").stdout)
        (self.mem / "knowledge" / "cache.md").unlink()
        self.assertNotIn("knowledge/cache.md", self.run_cli("search", "phinh", "cache").stdout)

    def test_note_aliases_and_edit_are_seen(self):
        self.init()
        self.note("joycon", body="stick deadzone", aliases="trôi cần analog")
        self.assertIn("knowledge/joycon.md", self.run_cli("search", "troi can").stdout)
        path = self.mem / "knowledge" / "joycon.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nmoi them hexagonal\n", encoding="utf-8")
        os.utime(path, (1, 1))
        self.assertIn("hexagonal", self.run_cli("search", "hexagonal").stdout)

    def test_related_explains_why(self):
        self.init()
        self.note("target", project="ting", tags="audio, net", body="See [[linked]]. uniqueword rarething")
        self.note("linked", body="plain")
        self.note("backlink", body="Back to [[target]]")
        self.note("sameproject", project="ting", body="plain")
        self.note("sametag", tags="net", body="plain")
        self.note("sharedwords", body="uniqueword rarething here")
        self.note("nothing", body="totally different")
        out = self.run_cli("related", "target").stdout
        self.assertIn("linked.md (linked from it", out)
        self.assertIn("backlink.md (links to it", out)
        self.assertIn("project ting", out)
        self.assertIn("tag net", out)
        self.assertIn("shared: rarething, uniqueword", out)
        self.assertNotIn("nothing.md", out)
        self.assertNotEqual(self.run_cli("related", "missing", ok=False).returncode, 0)

    def test_corrupt_index_rebuilds_and_is_ignored_by_git(self):
        self.init()
        self.note("a", body="findme")
        self.run_cli("search", "findme")
        self.assertIn(".index.db", (self.mem / ".gitignore").read_text(encoding="utf-8"))
        (self.mem / ".index.db").write_bytes(b"not a database")
        self.assertIn("knowledge/a.md", self.run_cli("search", "findme").stdout)

    def test_plain_scan_without_fts(self):
        self.init()
        self.note("a", body="findme")
        env_old = os.environ.get("DAILYLOG_NO_FTS")
        os.environ["DAILYLOG_NO_FTS"] = "1"
        try:
            done = subprocess.run([sys.executable, str(SCRIPT), "search", "findme", "--root", str(self.root)],
                                  text=True, capture_output=True, env={**os.environ, "HOME": str(self.home)})
        finally:
            del os.environ["DAILYLOG_NO_FTS"]
        self.assertIn("knowledge/a.md", done.stdout)
        self.assertIsNone(env_old)


class FindNoise(Base):
    def test_partial_needs_half_the_terms_and_paths_stay_out_of_view(self):
        self.init()
        self.run_cli("new", "knowledge", "one", "--summary", "s", "--body", "chi co bo thoi")
        self.assertIn("no matches", self.run_cli("search", "tran", "bo", "nho", "anh").stdout)
        self.run_cli("hook", "--agent", "claude", "--event", "UserPromptSubmit",
                     stdin=json.dumps({"session_id": "v1", "cwd": str(self.root), "prompt": "zebra ask"}))
        out = self.run_cli("search", "zebra").stdout
        self.assertIn('1 turn: "zebra ask"', out)
        self.assertNotIn(str(self.root), out)
        self.assertNotIn("Work log", out)


class Import(Base):
    def write_jsonl(self, path, records):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")

    def seed(self):
        self.init()
        cwd = str(self.root)
        def claude(ts, kind, content, **extra):
            message = {"content": content}
            if kind == "assistant":
                message["model"] = "claude-opus-5-5"
            return {"type": kind, "timestamp": ts, "cwd": cwd, "message": message, **extra}
        self.write_jsonl(self.home / ".claude/projects/x/claude-sess-1.jsonl", [
            claude("2026-10-01T09:00:00Z", "user", "<command-name>/model</command-name>"),
            claude("2026-10-01T09:01:00Z", "user", "Fix {tvdb-1} bug"),
            claude("2026-10-01T09:02:00Z", "assistant", [{"type": "text", "text": "Working"}]),
            claude("2026-10-01T09:03:00Z", "user", [{"type": "tool_result", "content": "out"}], toolUseResult={"a": 1}),
            claude("2026-10-01T09:30:00Z", "assistant", [{"type": "text", "text": "**Fixed** it"}]),
            claude("2026-10-01T09:40:00Z", "user", "sub", isSidechain=True),
            claude("2026-10-02T10:00:00Z", "user", "ghp_" + "c" * 30 + " next day"),
            claude("2026-10-02T10:05:00Z", "assistant", [{"type": "text", "text": "Done"}]),
        ])
        codex = self.home / ".codex/sessions/2026/10/03"
        self.write_jsonl(codex / "rollout-main.jsonl", [
            {"type": "session_meta", "timestamp": "2026-10-03T08:00:00Z", "payload": {"id": "codex-main-1", "cwd": cwd, "source": "vscode"}},
            {"type": "turn_context", "timestamp": "2026-10-03T08:00:01Z", "payload": {"model": "gpt-x", "cwd": cwd}},
            {"type": "response_item", "timestamp": "2026-10-03T08:00:02Z", "payload": {"type": "message", "role": "user", "content": [{"text": "<recommended_plugins>x"}]}},
            {"type": "event_msg", "timestamp": "2026-10-03T08:00:03Z", "payload": {"type": "item_completed", "item": {"type": "UserMessage", "content": [{"text": "Codex ask"}]}}},
            {"type": "event_msg", "timestamp": "2026-10-03T08:20:00Z", "payload": {"type": "task_complete", "last_agent_message": "Codex done"}},
        ])
        self.write_jsonl(codex / "rollout-sub.jsonl", [
            {"type": "session_meta", "timestamp": "2026-10-03T08:00:00Z", "payload": {"id": "codex-sub", "cwd": cwd, "source": {"subagent": {"other": "guardian"}}}},
            {"type": "event_msg", "timestamp": "2026-10-03T08:00:03Z", "payload": {"type": "user_message", "message": "hidden"}},
        ])
        db = self.home / ".gemini/antigravity/conversation_summaries.db"
        db.parent.mkdir(parents=True)
        con = sqlite3.connect(db)
        con.execute("create table conversation_summaries (conversation_id,title,preview,step_count,last_modified_time,last_user_input_time,workspace_uris,nesting_depth,parent_conversation_id,raw_summary)")
        uri = json.dumps(["file://" + cwd.replace(" ", "%20")])
        prompt = "Agy opening prompt".encode()
        rows = [("agy-top-1", "", "", 42, "2026-10-04 07:30:00.123456789+00:00", "2026-10-04 07:00:00+00:00", uri, 0, "", b"\n" + bytes([len(prompt)]) + prompt),
                ("agy-sub", "Sub", "", 5, "2026-10-04 07:30:00+00:00", "2026-10-04 07:00:00+00:00", uri, 1, "agy-top-1", b""),
                ("agy-bad", "Bad", "", 5, "0001-01-01 00:00:00+00:00", "", uri, 0, "", b"")]
        con.executemany("insert into conversation_summaries values (?,?,?,?,?,?,?,?,?,?)", rows)
        con.execute("create table conversations_fts_content (c0,c1,c14)")
        con.execute("insert into conversations_fts_content values ('agy-top-1',0,'first\nAgy final line')")
        con.commit()
        con.close()

    def day(self, week, day):
        return (self.mem / week / f"{day}.md").read_text(encoding="utf-8")

    def test_without_confirmation_it_reports_and_writes_nothing(self):
        self.seed()
        out = self.run_cli("import").stdout
        self.assertIn("claude: 1 sessions, 2 day lines, 2026-10-01 to 2026-10-02", out)
        self.assertIn("4 new", out)
        self.assertIn("once they confirm, run this again with --yes", out)
        self.assertFalse((self.mem / "2026-W40").exists())

    def answer_prompt(self, reply):
        import pty
        master, slave = pty.openpty()
        env = {**{k: v for k, v in os.environ.items() if not k.startswith("DAILYLOG_")}, "HOME": str(self.home), "TZ": "UTC"}
        process = subprocess.Popen([sys.executable, str(SCRIPT), "import"], cwd=str(self.root), env=env, stdin=slave,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        os.close(slave)
        os.write(master, reply)
        out, _ = process.communicate(timeout=30)
        os.close(master)
        return out

    def test_terminal_prompt_needs_yes(self):
        self.seed()
        self.assertIn("Cancelled, nothing written", self.answer_prompt(b"n\n"))
        self.assertFalse((self.mem / "2026-W40").exists())
        self.assertIn("Cancelled, nothing written", self.answer_prompt(b"\n"))
        self.assertIn("Imported: 4 new", self.answer_prompt(b"y\n"))
        self.assertTrue((self.mem / "2026-W40" / "2026-10-01.md").exists())
        self.assertIn("Already up to date", self.run_cli("import").stdout)

    def test_dry_run_writes_nothing(self):
        self.seed()
        out = self.run_cli("import", "--dry-run").stdout
        self.assertIn("Dry run", out)
        self.assertFalse((self.mem / "2026-W40").exists())

    def test_import_each_agent_and_rerun_is_stable(self):
        self.seed()
        out = self.run_cli("import", "--yes").stdout
        self.assertIn("claude: 1 sessions, 2 day lines", out)
        self.assertIn("codex: 1 sessions, 1 day lines, 2026-10-03 to 2026-10-03, 1 subagents skipped", out)
        self.assertIn("agy: 1 sessions, 1 day lines, 2026-10-04 to 2026-10-04, 1 subagents skipped, 1 undated skipped", out)
        first = self.day("2026-W40", "2026-10-01")
        self.assertIn("(Claude, claude-opus-5-5) 09:00-09:30, 1 turn,", first)
        self.assertIn('"Fix {tvdb-1} bug" -> Fixed it', first)
        self.assertNotIn("sub", first.split('"')[1])
        second = self.day("2026-W40", "2026-10-02")
        self.assertIn("[redacted]", second)
        self.assertNotIn("ghp_", second)
        codex = self.day("2026-W40", "2026-10-03")
        self.assertIn('(Codex, gpt-x) 08:00-08:20, 1 turn,', codex)
        self.assertIn('"Codex ask" -> Codex done', codex)
        self.assertNotIn("hidden", codex)
        agy = self.day("2026-W40", "2026-10-04")
        self.assertIn('(Antigravity) 07:00-07:30, 42 steps,', agy)
        self.assertIn('"Agy opening prompt" -> Agy final line', agy)
        again = self.run_cli("import", "--yes").stdout
        self.assertIn("0 new, 0 updated, 4 unchanged", again)
        self.assertEqual(first, self.day("2026-W40", "2026-10-01"))
        report = self.run_cli("report", "--day", "2026-10-01").stdout
        self.assertIn("| Claude | 1 | 1 | 30 | 1 |", report)

    def test_keeps_handwritten_log_and_live_line(self):
        self.seed()
        week = self.mem / "2026-W40"
        week.mkdir()
        marker = "<!-- session:claude-sess- -->"
        (week / "2026-10-01.md").write_text(
            f"# Mine\n\n- handwritten note\n- [session] (Claude) 09:00-09:59, 9 turns, ~/x: \"live\" {marker}\n", encoding="utf-8")
        self.run_cli("import", "--yes")
        text = self.day("2026-W40", "2026-10-01")
        self.assertIn("- handwritten note", text)
        self.assertIn("9 turns", text)
        self.assertEqual(text.count("session:claude-sess-"), 1)

    def test_codex_continuation_file_joins_its_session(self):
        self.seed()
        codex = self.home / ".codex/sessions/2026/10/04"
        ask = {"type": "event_msg", "timestamp": "2026-10-03T08:00:03Z", "payload": {"type": "item_completed", "item": {"type": "UserMessage", "content": [{"text": "Codex ask"}]}}}
        self.write_jsonl(codex / "rollout-main_part2.jsonl", [
            {"type": "session_meta", "timestamp": "2026-10-04T08:00:00Z", "payload": {"id": "codex-main-1", "cwd": str(self.root), "source": "vscode"}},
            ask,
            {"type": "event_msg", "timestamp": "2026-10-04T09:00:00Z", "payload": {"type": "user_message", "message": "Next day ask"}},
        ])
        week = self.mem / "2026-W40"
        week.mkdir()
        old = "- [session] (Codex) 08:00-08:01, 1 turn, ~/x <!-- session:codex-main-1 -->\n"
        (week / "2026-10-03.md").write_text("# Mine\n\n" + old + old, encoding="utf-8")
        self.run_cli("import", "--yes")
        first = self.day("2026-W40", "2026-10-03")
        self.assertEqual(first.count("session:codex-main-"), 1)
        self.assertIn('1 turn,', first)
        self.assertIn('"Next day ask"', self.day("2026-W40", "2026-10-04"))
        self.assertIn("0 updated", self.run_cli("import", "--yes").stdout)

    def test_since_meta_and_missing_sources(self):
        self.seed()
        self.run_cli("import", "--yes", "--since", "2026-10-03", "--capture", "meta")
        self.assertFalse((self.mem / "2026-W40" / "2026-10-01.md").exists())
        self.assertNotIn("Codex ask", self.day("2026-W40", "2026-10-03"))
        empty = self.base / "empty"
        empty.mkdir()
        self.home = empty
        self.assertIn("0 new", self.run_cli("import", "--yes").stdout)

    def test_import_filters_trivial_and_foreign_sessions(self):
        self.seed()
        # 1. Trivial session in current workspace
        self.write_jsonl(self.home / ".claude/projects/x/claude-sess-trivial.jsonl", [
            {"type": "user", "timestamp": "2026-10-05T09:00:00Z", "cwd": str(self.root), "message": {"content": "hello"}},
            {"type": "assistant", "timestamp": "2026-10-05T09:01:00Z", "cwd": str(self.root), "message": {"model": "claude", "content": [{"type": "text", "text": "Hi"}]}},
        ])
        # 2. Foreign workspace session
        cwd_foreign = str(self.base / "other-project")
        foreign_dir = self.home / ".claude/projects/other"
        foreign_dir.mkdir(parents=True)
        self.write_jsonl(foreign_dir / "claude-sess-foreign.jsonl", [
            {"type": "user", "timestamp": "2026-10-05T10:00:00Z", "cwd": cwd_foreign, "message": {"content": "Build foreign app"}},
            {"type": "assistant", "timestamp": "2026-10-05T10:05:00Z", "cwd": cwd_foreign, "message": {"model": "claude", "content": [{"type": "text", "text": "Done foreign"}]}},
        ])
        out = self.run_cli("import", "--yes").stdout
        self.assertIn("trivial skipped", out)
        # Trivial session was ignored
        day_text = self.day("2026-W41", "2026-10-05") if (self.mem / "2026-W41" / "2026-10-05.md").exists() else ""
        self.assertNotIn('"hello"', day_text)
        # Foreign session did not contaminate workspace memory
        self.assertNotIn("Build foreign app", day_text)
        # Foreign session was routed to global store
        global_day = self.home / ".dailylog/2026-W41/2026-10-05.md"
        self.assertTrue(global_day.exists())
        self.assertIn("Build foreign app", global_day.read_text(encoding="utf-8"))

    def test_many_pending_weeks_stay_short_in_context(self):
        self.seed()
        self.run_cli("import", "--yes")
        for week in ("2026-W41", "2026-W42", "2026-W43"):
            (self.mem / week).mkdir()
        out = self.run_cli("context").stdout
        self.assertIn("weeks are not consolidated (2026-W40 to 2026-W43)", out)


class Help(Base):
    def test_guide_lists_every_command(self):
        out = self.run_cli("help").stdout
        listed = self.run_cli("--help").stdout
        import re
        names = re.search(r"\{([a-z,-]+)\}", listed).group(1).split(",")
        self.assertGreater(len(names), 15)
        for name in names:
            self.assertIn(f"  {name} ", out)
        self.assertIn('dailylog search "cloudflare tunnel"', out)
        self.assertEqual(self.run_cli().stdout, out)

    def test_one_command_and_unknown_topic(self):
        self.assertIn("--dry-run", self.run_cli("help", "import").stdout)
        self.assertNotEqual(self.run_cli("help", "nope", ok=False).returncode, 0)


class Details(Base):
    def seed_claude(self):
        self.init()
        cwd = str(self.root)
        def rec(ts, kind, content, **extra):
            return {"type": kind, "timestamp": ts, "cwd": cwd, "message": {"content": content, "model": "claude-opus-5-5"}, **extra}
        long_reply = "Done. " + "x" * 300
        path = self.home / ".claude/projects/x/abcd1234-sess.jsonl"
        path.parent.mkdir(parents=True)
        records = [
            rec("2026-10-01T09:00:00Z", "user", "First ask"),
            rec("2026-10-01T09:01:00Z", "assistant", [{"type": "tool_use", "name": "Edit", "input": {"file_path": "/a/b/core.py"}},
                                                     {"type": "tool_use", "name": "Bash", "input": {"command": "cd /a && git commit -m x"}}]),
            rec("2026-10-01T09:02:00Z", "user", [{"type": "tool_result", "content": "ok"}], toolUseResult={"stdout": "[main abc1234] x\n 1 file changed"}),
            rec("2026-10-01T09:03:00Z", "user", "Second ask <private>hunter2 plan</private> tail"),
            rec("2026-10-01T09:04:00Z", "assistant", [{"type": "text", "text": long_reply}]),
        ]
        path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
        return long_reply

    def test_day_file_has_prompts_files_commands_commits_result(self):
        self.seed_claude()
        self.run_cli("import", "--yes")
        text = (self.mem / "2026-W40" / "2026-10-01.md").read_text(encoding="utf-8")
        self.assertIn('"First ask" (commits: abc1234) <!-- session:abcd1234-ses -->', text)
        self.assertIn("  - 09:03 Second ask [private] tail", text)
        self.assertNotIn("hunter2", text)
        self.assertIn("  - Changed 1 file: core.py", text)
        self.assertIn("  - Ran 1 command: git commit x1", text)
        self.assertIn("  - Result: Done.", text)
        self.assertIn("0 updated", self.run_cli("import", "--yes").stdout)

    def test_report_search_and_handwritten_lines_understand_blocks(self):
        self.seed_claude()
        week = self.mem / "2026-W40"
        week.mkdir()
        (week / "2026-10-01.md").write_text("# Mine\n\n- my note\n", encoding="utf-8")
        self.run_cli("import", "--yes")
        report = self.run_cli("report", "--day", "2026-10-01").stdout
        self.assertIn("1 older lines", report)
        self.assertIn("- my note", (week / "2026-10-01.md").read_text(encoding="utf-8"))
        found = self.run_cli("search", "Second", "ask").stdout
        self.assertIn("Second ask", found)
        self.assertIn("[show abcd1234-ses]", found)

    def test_hook_keeps_details_and_adds_prompts(self):
        self.seed_claude()
        self.run_cli("import", "--yes")
        day = self.mem / "2026-W40" / "2026-10-01.md"
        when = "2026-10-01T10:00:00"
        payload = {"session_id": "abcd1234-sess", "cwd": str(self.root), "prompt": "Live ask"}
        self.run_cli("hook", "--agent", "claude", "--event", "UserPromptSubmit", stdin=json.dumps(payload), when=when)
        text = day.read_text(encoding="utf-8")
        self.assertIn("  - Changed 1 file: core.py", text)
        self.assertEqual(text.count("session:abcd1234-ses"), 1)
        payload["prompt"] = "Later ask"
        self.run_cli("hook", "--agent", "claude", "--event", "UserPromptSubmit", stdin=json.dumps(payload), when=when)
        self.assertIn("  - 10:00 Later ask", day.read_text(encoding="utf-8"))

    def test_many_prompts_are_trimmed_with_a_pointer(self):
        self.init()
        path = self.home / ".claude/projects/x/many5678-sess.jsonl"
        path.parent.mkdir(parents=True)
        rows = [{"type": "user", "timestamp": f"2026-10-01T09:{i:02d}:00Z", "cwd": str(self.root), "message": {"content": f"ask number {i}"}} for i in range(30)]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        self.run_cli("import", "--yes")
        text = (self.mem / "2026-W40" / "2026-10-01.md").read_text(encoding="utf-8")
        self.assertIn("more prompts; `dailylog show many5678-ses`", text)
        self.assertIn("ask number 29", text)
        self.assertNotIn("ask number 15", text)

    def test_show_reads_the_transcript(self):
        long_reply = self.seed_claude()
        out = self.run_cli("show", "abcd1234").stdout
        self.assertIn("you: First ask", out)
        self.assertIn("tool: Edit: /a/b/core.py", out)
        self.assertIn(long_reply, out)
        self.assertNotIn("hunter2", self.run_cli("show", "abcd1234", "--grep", "Second").stdout)
        prompts = self.run_cli("show", "abcd1234", "--prompts").stdout
        self.assertNotIn("agent:", prompts)
        self.assertIn("more entries", self.run_cli("show", "abcd1234", "--max-chars", "50").stdout)
        self.assertNotEqual(self.run_cli("show", "zzzz9999", ok=False).returncode, 0)

    def test_antigravity_transcript_gives_real_times_and_work(self):
        self.init()
        root = self.home / ".gemini/antigravity"
        logs = root / "brain/agy-real-1/.system_generated/logs"
        logs.mkdir(parents=True)
        steps = [
            {"type": "USER_INPUT", "source": "USER_EXPLICIT", "created_at": "2026-10-04T07:00:00Z", "content": "<USER_REQUEST>\nWrite tests\n</USER_REQUEST>\n<ADDITIONAL>x</ADDITIONAL>"},
            {"type": "PLANNER_RESPONSE", "source": "MODEL", "created_at": "2026-10-04T07:05:00Z", "tool_calls": [
                {"name": "run_command", "args": {"CommandLine": '"./gradlew test"'}},
                {"name": "write_to_file", "args": {"TargetFile": '"/a/Foo.kt"'}},
                {"name": "edit_file", "args": {"Path": '"/a/Bar.kt"'}}]},
            {"type": "GENERIC", "source": "MODEL", "created_at": "2026-10-04T07:06:00Z", "content": "[dev 1234abc] msg"},
            {"type": "PLANNER_RESPONSE", "source": "MODEL", "created_at": "2026-10-04T09:00:00Z", "content": "All green"},
        ]
        (logs / "transcript.jsonl").write_text("".join(json.dumps(r) + "\n" for r in steps), encoding="utf-8")
        con = sqlite3.connect(root / "conversation_summaries.db")
        con.execute("create table conversation_summaries (conversation_id,title,preview,step_count,last_modified_time,last_user_input_time,workspace_uris,nesting_depth,parent_conversation_id,raw_summary)")
        con.execute("insert into conversation_summaries values (?,?,?,?,?,?,?,?,?,?)",
                    ("agy-real-1", "Tests", "", 4, "2026-10-04 09:00:00+00:00", "2026-10-04 08:59:00+00:00", json.dumps(["file://" + str(self.root)]), 0, "", b""))
        con.commit()
        con.close()
        self.run_cli("import", "--yes", "--agents", "agy")
        text = (self.mem / "2026-W40" / "2026-10-04.md").read_text(encoding="utf-8")
        self.assertIn("(Antigravity) 07:00-09:00, 4 steps,", text)
        self.assertIn('"Tests" -> All green (commits: 1234abc)', text)
        self.assertIn("  - Changed 2 files: Bar.kt, Foo.kt", text)
        self.assertIn("  - Ran 1 command: gradlew x1", text)
        self.assertIn("you: Write tests", self.run_cli("show", "agy-real").stdout)


class Wire(Base):
    def test_symlinked_file_updated_once_and_stays_a_link(self):
        agents = self.root / "AGENTS.md"
        agents.write_text("# Rules\n", encoding="utf-8")
        (self.root / "GEMINI.md").symlink_to("AGENTS.md")
        self.init()
        self.run_cli("wire")
        self.assertIn("unchanged", self.run_cli("wire").stdout)
        text = agents.read_text(encoding="utf-8")
        self.assertEqual(text.count("dailylog:start"), 1)
        self.assertTrue(text.startswith("# Rules"))
        self.assertTrue((self.root / "GEMINI.md").is_symlink())
        self.run_cli("wire", "--remove")
        self.assertNotIn("dailylog", agents.read_text(encoding="utf-8"))


class Installer(Base):
    def run_install(self, *args):
        env = {**os.environ, "HOME": str(self.home)}
        done = subprocess.run(["bash", str(SKILL / "install.sh"), *args], text=True, capture_output=True, env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def test_global_install_only_touches_agents_present(self):
        (self.home / ".codex").mkdir()
        self.run_install("--hooks")
        self.assertTrue((self.home / ".codex/skills/dailylog/SKILL.md").exists())
        self.assertTrue((self.home / ".codex/hooks.json").exists())
        self.assertFalse((self.home / ".claude").exists())
        self.assertTrue((self.home / ".local/bin/dailylog").is_symlink())
        self.run_install("--uninstall")
        self.assertFalse((self.home / ".codex/skills/dailylog").exists())
        self.assertFalse((self.home / ".local/bin/dailylog").exists())

    def test_workspace_install(self):
        (self.home / ".claude").mkdir()
        self.run_install("--workspace", str(self.root))
        self.assertTrue((self.root / ".agents/skills/dailylog/SKILL.md").exists())
        self.assertTrue((self.mem / "INDEX.md").exists())
        self.assertIn("dailylog:start", (self.root / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertTrue((self.root / ".claude/settings.json").exists())
        self.assertFalse((self.home / ".claude/settings.json").exists())


if __name__ == "__main__":
    unittest.main()
