# Coding Standards Checklist

What every code change in a project-pro repo must satisfy. It is the former Gates 2 to 5 of
the old "6-Gate" loop; grounding (old Gate 1) and delivery/lessons (old Gate 6) are the working
method of the `agent-team` skill (`references/working-method.md`, generated into the repo as
`.agents/rules/agent-workflow.md`). The generated `.agents/rules/execution-harness.md` keeps its
file name so existing detection and audit keep working; its content is this checklist.

---

## 1. File split (anti-God-file)

Before creating or editing source files, plan the exact file breakdown:

1. **One file = one primary responsibility**:
   - Never bundle `Dto` + `Mapper` + `RepositoryImpl` into one file.
   - Never bundle `UiState`/`Intent` + `ViewModel`/`Reducer` + `Screen` + sub-components into one
     giant file (extract sub-components into `components/` once a screen exceeds ~200 lines).
2. **2-tier file length lock** *(excluding auto-generated files like `*.g.dart`, `*.freezed.dart`,
   `*.gen.ts`, `*_pb2.py`, `*.pb.go`, and migrations)*:
   - **Target**: `< 250-300 LOC` per file.
   - **`> 300 LOC` (`[WARN]`)**: stop adding responsibilities; extract collaborators or UI sub-components.
   - **`> 450 LOC` (`[FAIL]`)**: hard block in `audit` and the Git `pre-commit` hook. Split before finishing.
3. **Surgical scope**: touch only files required by the task; no unrelated reformatting.

---

## 2. Disciplined coding by change type

### A. New feature: inside-out (contract-first)
1. **`Domain`**: entities/value objects, narrow repository port, `DomainError` cases, use case if needed.
2. **`Data`**: remote `*Dto` / local `*Entity`, stateless mappers (`toDomain`, `toEntity`), `RepositoryImpl`
   with boundary error translation.
3. **`Presentation State`**: immutable sealed `UiState` (no boolean soup) + `Intent`/`Event` + `Effect`,
   in the `ViewModel`/`BLoC`/`Reducer`/`Store`.
4. **`Stateless UI`**: declarative screen/widget taking state + event lambdas + preview.
5. **`Composition root`**: DI bindings and type-safe route registration.

### B. Bugfix
Fix the root cause and add a regression test that failed before the fix. Banned: blind `try/catch`,
arbitrary `delay(300)`, unsafe `!!` / `as any` casts. The debugging method, the reproduce-first rule and
the 3-strike stop are stated once, in the agent-team working method.

### C. Refactor: behaviour-preserving micro-steps
1. Existing tests pass first (or add characterization tests around untested logic).
2. Restructure without changing public observable behaviour.

### Universal prohibitions
- **Zero unfinished stubs**: no `// TODO: implement later`, hardcoded mock arrays in production paths, or `throw NotImplementedError()`.
- **Zero dead code**: delete unused imports, commented-out blocks and debug `print`/`console.log`.
- **Security by design**: see section 3.

---

## 3. Security

Zero hardcoded keys/tokens/passwords or committed `.env`/keystores; parameterized SQL/ORM queries only;
validate untrusted input at trust boundaries; redact tokens and PII in logs; never run `--no-verify`.
Enforced by the Git hooks and `agent-guard` (see `security-and-hooks.md`).

---

## 4. Tests (fakes over mocks)

Add or update fast unit tests covering:
- Happy path (`Content` / `200 OK`)
- Empty state (`Empty list`)
- Failure and offline states (`NetworkUnavailable`, `Unauthorized`, `ValidationError`)
- Boundary inputs and concurrency cancellation

Then run, in order, and fix every failure before finishing:
- Targeted unit test (`commands.test_single` in `.agents/project-profile.json`)
- Compiler/typecheck and linter (`commands.lint`)
- Architecture, file-size and security audit:
  ```bash
  python3 "<SKILL_DIR>/scripts/project_pro.py" audit --target "<PROJECT_DIR>" --fail-on-error
  ```
- If new modules or directories were added, refresh the map:
  ```bash
  python3 "<SKILL_DIR>/scripts/project_pro.py" map --target "<PROJECT_DIR>" --write
  ```

---

## 5. Task tracking (optional)

Only when the profile ticks `task-tracking`: specs live in `docs/tasks/TASK-<n>.md`, the backlog in
`docs/BACKLOG.md`, and board sync is done by the `task-board` skill (`project_board.py list|move|push|sync`).
project-pro only creates the folders at setup time. Multi-agent team work (lead, coders, verifier,
cross-vendor review, done gate) is the `agent-team` skill.
