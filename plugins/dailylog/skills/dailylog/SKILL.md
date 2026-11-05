---
name: dailylog
description: >-
  Long-term memory shared by every agent and session in a workspace: daily work logs,
  automatic session records, project state, durable knowledge, decision records and a
  weekly history, all as Markdown in memory/. Use this whenever the user asks what was
  done before, what happened in a past session, why something was decided, or where a
  project stands; whenever they say to remember, log, note or record something for later;
  when starting work in a workspace that has a memory/ folder; when finishing work whose
  findings a later session would need; and when they want to set up, install, consolidate
  or review agent memory or a work journal (nhật ký, ghi nhớ, lịch sử làm việc), even if
  they never say "dailylog".
---

# Dailylog

Agents forget everything between sessions and lose detail when context runs out. Dailylog keeps a Markdown memory that any agent can read, so each session starts from what earlier ones learned.

Commands below use `dailylog`. If it is not on PATH, run `python3 <this skill>/scripts/dailylog.py`. `dailylog help` lists every command with examples, and `dailylog help <command>` shows its options.

When invoked with arguments, such as `/dailylog help` or `/dailylog search lru cache`, run `dailylog` with those arguments and show the result in the user's language.

## The layers

| Where | Answers | How it changes |
|---|---|---|
| `memory/INDEX.md` | What exists, what is active? | Generated block + free notes |
| `memory/projects/<slug>.md` | Where does it stand, what is open? | Rewritten to stay current |
| `memory/knowledge/<slug>.md` | What is durably true? | Edited, with a `verified` date |
| `memory/decisions/<date>-<slug>.md` | Why this and not that? | Superseded, never deleted |
| `memory/HISTORY.md` | What happened over the months? | One line per closed week |
| `memory/YYYY-Www/YYYY-MM-DD.md` | What happened that day? | Append-only |
| `memory/YYYY-Www/summary.md` | What mattered that week? | Written when closing the week |

Logs are the record. The other layers are what makes the record useful later, so a fact that only lives in a log is effectively lost after that week.

## Keep token use low

Every extra tool call replays the whole conversation, so a turn spent only on logging usually costs more than the text it writes.

- Do not log routine steps. Hooks and `dailylog import` already record each session's time, prompts, files, commands, commits and last reply, using no model tokens. Users can wrap text in `<private>` tags to keep it out.
- Write only what those records cannot infer: durable facts, decisions with rejected alternatives, open tasks.
- Send memory commands in parallel with other tool calls, and put several findings in one call.
- Read through `dailylog context` and `dailylog search`. Do not read old weeks wholesale.

## During a session

**At the start**, if no memory context was injected, run `dailylog context`. If a task you plan to touch is marked `[/]`, another instance has claimed it: leave those files alone unless the user asks.

**When you need the past**, search first, then read only the files named:

```bash
dailylog search "lru cache borealis"
dailylog search "quyet dinh hook" --layer decisions
```

Search ranks by relevance, ignores case and Vietnamese diacritics, covers this store and `~/.dailylog`, and matches words rather than meaning. So before concluding something is absent, try two or three other wordings, including English and the project's own terms. When a different wording finally finds it, save the link so the next search does not need the detour:

```bash
dailylog alias "phình cache" "tràn bộ nhớ"
```

Search results for sessions print an id. To read that session, run `dailylog show <id> --grep "<term>"`; it renders from the agent's transcript, so narrow it with `--grep`, `--prompts` or `--day` rather than reading it all.

To widen from one result, run `dailylog related <file>`: it follows links, projects, tags and rare shared words. Superseded decisions are flagged; do not treat them as current.

**When you learn something durable:**

```bash
dailylog new knowledge switch-ftp --title "Switch FTP access" --summary "Where to reach the console over LAN" --project switchfin --tags "switch, network" --aliases "nap file len may" --body "..."
dailylog new decision calendar-memory --title "..." --summary "..." --context "..." --choice "..." --alternatives "..." --consequences "..."
dailylog verify knowledge/switch-ftp.md
```

Before creating a note, search for one that covers it and update that instead. A note should say how you know and hold one topic. Link related notes with `[[file-name]]`, since search and `related` use those links. Text containing `$`, backticks or quotes is safer through stdin: pass `-` as the value and pipe it in.

**To track work:**

```bash
dailylog todo add switchfin "Fix cast header overflow"
dailylog todo start switchfin "cast header"
dailylog todo done switchfin "cast header"
```

**To add a line the session record would miss:** `dailylog log "<what, files, commit>" -p <project> -s done`. If context is running low, write this before anything else.

**To import past sessions:** run `dailylog import` (add `--agents claude` to narrow it) and show the user what it found: sessions per agent, dates, new lines and where they go. Ask whether to import, and run it again with `--yes` only after they confirm, even when they asked for the import themselves. If it reports nothing new, say so and stop.

## What does not belong here

- Secrets. Dailylog refuses tokens, keys and passwords on write, redacts them from session records, and `dailylog lint` scans for them. Record where a secret lives instead.
- Diffs or anything git already holds. Give the commit hash and the reason.
- Knowledge about one repo's internals. Put it in that repo's docs and link to it, so it travels with the code.
- Trivial/no-op sessions. Prompts like "hi", "hello", "ping", "test", or failed credit runs are filtered automatically.
- Foreign workspace sessions. Sessions outside the target project's root are routed to `~/.dailylog` instead of polluting the project's `memory/`. Duplicate mirror prompts on the same day are deduplicated.

## Closing a week

`dailylog context` reminds you when a past week is still open. Offer to close it rather than doing so unasked, since it costs tokens. Then:

```bash
dailylog consolidate --week 2026-W45
```

This prints the files to read and the steps. Finish with `dailylog consolidate --week 2026-W45 --done --headline "<one line>"`.

## Setup

Installing the skill alone records nothing, because skills load only when triggered. Read `references/setup.md` when the user wants installation, importing past sessions from agents' history, automatic recording, a specific agent's hook behaviour, or a cost explanation. Run `dailylog lint` when the user asks whether memory is healthy, and `dailylog report --day <date>` when they ask what happened on a day, by hour or by agent.
