---
name: crashlytics
description: >-
  Read and triage Firebase Crashlytics through the console (no API quota): for the current app
  repo or any Crashlytics link, list crash/ANR/non-fatal issues, download stack traces, triage,
  and note, close or mute issues. Use for Crashlytics links, issue ids, top crashes/ANRs,
  comparing releases.
---

# Crashlytics through the console

Drives the Firebase console in a dedicated Chrome profile, because the public API's quota is near zero.
`$CL` = `node <this skill's directory>/scripts/crashlytics.mjs` (Node >= 22, Google Chrome). Run `$CL --help` for
every option.

## Project

Stateless: nothing is saved between runs. The script takes the project and app from, in order:

1. `--project <id> --app <android:pkg | ios:bundle>`
2. a Crashlytics console link the user pasted (issue list or one issue), passed as the first argument; its filters
   (type, versions, search, time, state) apply unless an option overrides them
3. the Firebase config in the current repo: `google-services.json` (Android) or `GoogleService-Info.plist` (Apple)

Its first log line names the project, app and platform, detected from the repo: `Android`, `iOS`, or `Flutter`,
`React Native`, `Unity` with the app's platform. Use it to pick the triage hints below. If the repo has several apps
(flavors, or one config per platform), it lists them: pass `--platform android|ios` when the user's words say which
("iOS crashes"), otherwise ask. Turn the user's words into options each time ("top crashes of 2.4.0" ->
`--type crash --version "2.4.0 (<build>)"`). ANR exists only for Android; the script refuses it for other apps.

## Sign in

The user runs `$CL --login` once and signs in in the Chrome window; never type credentials. On "Not signed
in", ask them to run it again. On macOS the first run may wait on a Keychain prompt: Always Allow.

## Rules

- One run at a time; never kill a Chrome on the profile that you did not start.
- Run from the repo root (output goes to `build/crashlytics/`); use `--out` if `build/` is not git-ignored.
- Notes, close and mute change the project for everyone: show the issue ids, titles and exact note, and run only after
  the user confirms (`--dry-run` shows the plan).
- User data is masked in every file written (emails, phone numbers, long ids, tokens, IPs, URL queries, the session
  id); frames and versions stay. It is pattern-based, so names or free text in messages and logs can slip through:
  never paste crash data into public places. Use `--raw` only when the user asks for the unmasked data, and `--rpc`
  (logs, keys, breadcrumbs) only when the stack trace is not enough.

## Commands

```bash
$CL --type crash --version "2.4.0 (240)" --max 100    # issues + stack traces; ~6 s per issue
$CL <issue link>                                     # one issue -> build/crashlytics/issues/<id>.txt
$CL --issue <id> [--issue <id>] --note "<text>" [--close | --mute] [--dry-run]
```

Output: `build/crashlytics/<type>-<query>/<version>/index.tsv` (id, events, users, versions, title, stack file) and
`<id>.txt`. Reruns skip saved traces.

## Triage

Map frames to the source at the crashing release, then group each issue:

- **Needs a fix** - the user's code causes it: blocking the main/UI thread, wrong lifecycle, a missing null, bounds
  or state check (an NPE, a Swift force unwrap, an out-of-range index), a race.
- **Cannot fix** - not reachable from code: a modified or corrupted install (Android VerifyError or ClassNotFound for
  shipped classes, impossible stacks), the device out of memory or storage (OOM or a jetsam kill at an unrelated
  allocation, disk-full SQLite errors), an OS or framework bug with no app frame, or an ANR/hang whose main thread is
  idle (Android `nativePollOnce`, Apple `mach_msg_trap`).
- **Unreadable** - frames are not symbolicated (missing iOS dSYM, Android mapping or native symbols, Flutter
  `--split-debug-info` symbols): ask for the upload before judging.
- **Watch** - too few events or no proven cause.
- **Not ours** - the crashing frame is in code the user does not own (a third-party SDK, the OS, another team's
  module). Obfuscation and inlining can put a wrong name on a frame, so check the frames below it before deciding.

Cross-platform apps: the native stack often ends in the engine (Flutter, Hermes/JSC, Unity IL2CPP); the app-level
Dart, JavaScript or C# stack is usually reported as a non-fatal (`--type nonfatal`), so look there for the cause.

Group ANRs and hangs by the main thread's first app frame: the same frame across issues is one cause.
