# Setup and cost

## What each piece does

| Piece | Effect | Model tokens |
|---|---|---|
| Skill files (`install.sh`) | Agents can use dailylog when it is relevant | Only the skill description, plus the body when triggered |
| `dailylog install-hooks` | Records **every** session automatically | Zero for recording |
| Lean start context (hook default) | Each new session starts with about 2000 characters of memory | Input only, once per session; `--context off` removes it |
| `dailylog wire` | Tells agents without hooks how to use memory | About 200 input tokens per session |

## Scope

```bash
./install.sh all --hooks                    # global: every project on this machine
./install.sh --workspace /path/to/project   # one project: skill, memory/, block in AGENTS.md, project hooks
```

Where a session is written: `$DAILYLOG_ROOT/memory`, else the nearest `memory/` at or above the working folder, else `~/.dailylog` (flat, no `memory/` inside). A global install therefore still uses a project's own `memory/` when it has one.

Do not install hooks at both scopes for the same agent: sessions are de-duplicated, but the start context is injected twice.

## Hook support

| Agent | Skill folder | Hook file (global / project) | Automatic recording |
|---|---|---|---|
| Claude Code | `~/.claude/skills` | `~/.claude/settings.json` / `.claude/settings.json` | Yes |
| Codex | `~/.codex/skills` | `~/.codex/hooks.json` / `.codex/hooks.json` | Yes; Codex may ask you to trust new hooks first |
| Antigravity | `~/.gemini/config/skills`, `~/.agents/skills` | `~/.gemini/config/hooks.json` / `.agents/hooks.json` | Yes |
| Gemini CLI, Cursor, OpenCode, others | their skill folder | none yet | No: agent records only when it follows the skill or AGENTS.md block |

Hook settings are merged, other hooks are kept, and the first change saves `<file>.dailylog-backup`. `dailylog install-hooks --remove` takes dailylog's hooks out again.

## What a session record contains

```
- [session] (Claude) 12:44-13:10, 6 turns, ~/repo: "first prompt" -> last reply (commits: abc123) <!-- session:ab12 -->
```

Prompt and reply are cut to 140 characters and secret-like strings are redacted. `--capture meta` leaves their text out entirely, which is the right choice if `memory/` may be pushed to a shared repo. A record states what was asked and how it ended; it does not explain why, which is what `knowledge/` and `decisions/` are for.

## Importing past sessions

`dailylog import` scans each agent's own history and adds one session line per day. It reads those sources without changing them, uses no model tokens and is safe to re-run; `--dry-run` shows the counts first, and `--since`, `--agents` and `--capture meta` narrow it.

Subagent sessions are skipped. Antigravity reports steps rather than turns, and its start time is the last user message. Running it now and then also fills gaps when an agent's hook did not fire. These agents' files are internal formats, so a new version can break a scanner.

## Reading a day

`dailylog report [--day YYYY-MM-DD] [--agent NAME]` groups a day by hour and totals sessions, turns and minutes per agent. It only reads files. Lines written by hand before dailylog have no time or agent and are counted, not shown.

Set `DAILYLOG_INSTANCE` (for example `Primary`) to tell instances of one agent apart. The model appears when the agent's hook supplies it.

## Limits by design

- `INDEX.md` lists the 20 most recently updated projects and 30 knowledge notes, then points to search. Set `status: archived` on finished projects to drop them from the table.
- `dailylog search` ranks by BM25 over sections in a local SQLite index (`.index.db`, refreshed on each search, safe to delete). It covers the current store and `~/.dailylog` (`--here` for one store) and falls back to partial matches, or a plain scan on Python builds without FTS5. It uses no model.
- It matches words, not meaning. To bridge wording: `--aliases` on a note, `dailylog alias "a" "b"` for logs too, and clear titles and summaries. `dailylog related <file>` follows links, projects, tags and rare shared words.

## Where the tokens go

1. **Hook recording:** none. It is a local script and the model never sees it.
2. **Start context:** input tokens once, then carried in the conversation like any other context. Lower it with `--context-chars`, or use `--context off` and let agents search on demand.
3. **Agent-written notes:** output tokens for the text, plus one replay of the conversation if the note takes its own turn. Batching notes with other tool calls avoids the replay.
4. **Closing a week:** the most expensive step, because the agent reads that week's logs. It runs weekly and only when you agree.
