# Task Execution Harness — Mandatory 6-Gate Loop for Every Coding Request

Every coding request (New Feature, Bugfix, Refactor, Performance Optimization, or API Integration) MUST pass through all **6 Gates** in order. Skipping gates leads to monolithic files, architecture leaks, surface-level symptom patches, and unverified broken builds.

---

## Gate 1: Context, Memory & Reference Grounding ("Think Before Coding")

1. **Read Project Map & Lessons First**: Inspect `AGENTS.md`, `.agents/project-profile.json`, `.agents/CODEBASE_MAP.md` (if present), and `.agents/memory/lessons.md` (project mistake ledger), plus neighboring files in the target module.
2. **Consult Famous Reference Repo**: For non-trivial mechanics (pagination, offline sync, auth token refresh, deep links, queues, transactions), verify how the anchored `referenceRepo` implements it before designing classes.
3. **Surface Assumptions & Push Back on Anti-Patterns (`karpathy-skills`)**:
   - Never silently guess when requirements have conflicting interpretations — state assumptions or ask concisely upfront.
   - If asked to implement an unsafe or architectural anti-pattern, point out the risk and propose the clean solution.
4. **Disk-Backed Plan for Complex Tasks (`planning-with-files`)**:
   - If the task touches **> 3–4 files** or spans multiple milestones, write/update `.agents/memory/active-plan.md` with exact file targets and `[ ]` checkboxes so progress survives context compaction or agent switching.

---

## Gate 2: Impact Map & Anti-God-File Split Plan

Before creating or editing source files, plan the exact file breakdown:

1. **One File = One Primary Responsibility**:
   - Never bundle `Dto` + `Mapper` + `RepositoryImpl` into one file.
   - Never bundle `UiState`/`Intent` + `ViewModel`/`Reducer` + `Screen` + `Sub-components` into one giant file (extract sub-components into `components/` as soon as a screen exceeds ~200 lines).
2. **2-Tier File Length Hard Lock** *(excluding auto-generated files like `*.g.dart`, `*.freezed.dart`, `*.gen.ts`, `*_pb2.py`, `*.pb.go`, and migrations)*:
   - **Target**: `< 250–300 LOC` per file.
   - **`> 300 LOC` (`[WARN]`)**: Stop adding responsibilities; extract collaborators or UI sub-components.
   - **`> 450 LOC` (`[FAIL]`)**: Hard block in `audit` and Git `pre-commit` hook. Must split before finishing!
3. **Surgical Scope**: Touch only files required by the task. Do not reformat or refactor unrelated modules in the same change.

---

## Gate 3: Disciplined Implementation by Task Type

### A. New Feature → Inside-Out (Contract-First)
Build strictly from pure policy outward so every layer compiles against clean contracts:
1. **`Domain`**: Entities/Value Objects → narrow Repository port interface → `DomainError` cases → UseCase (if needed).
2. **`Data`**: Remote `*Dto` / Local `*Entity` → stateless Mappers (`toDomain`, `toEntity`) → `RepositoryImpl` with boundary error translation.
3. **`Presentation State`**: Immutable `Sealed UiState` (zero boolean soup) + `Intent`/`Event` + `Effect` → `ViewModel`/`BLoC`/`Reducer`/`Store`.
4. **`Stateless UI`**: Declarative screen/widget taking state + event lambdas + `@Preview`/`#Preview`/Storybook.
5. **`Composition Root`**: DI bindings & type-safe route registration.

### B. Bugfix → 4-Phase Root-Cause & 3-Strike Stop (`obra/superpowers`)
1. Trace the exact data/state flow backward to locate the **root cause** (never silence symptoms with blind `try/catch`, arbitrary `delay(300)`, or unsafe `!!` / `as any` casts).
2. Test **one hypothesis at a time**. **3-Strike Rule**: If **3 fix attempts fail**, **STOP CODING**, revert failed hacks, and re-evaluate the architectural assumption with the user.
3. Write or update an automated regression test that reproduces the bug alongside the clean fix.

### C. Refactor → Behavior-Preserving Micro-Steps
1. Ensure existing tests pass (or add characterization tests around untested logic first).
2. Restructure without altering public observable behavior.

### Universal Implementation Prohibitions
- **Zero Unfinished Stubs**: Never leave `// TODO: implement later`, hardcoded mock arrays in production paths, or `throw NotImplementedError()`.
- **Zero Dead Code**: Delete unused imports, commented-out old code blocks, and debug `print`/`console.log` statements.
- **Security-by-Design**: Zero hardcoded keys/tokens/passwords, parameterized queries only, strict input validation at trust boundaries, redact sensitive fields in logs.

---

## Gate 4: Deterministic Edge-Case Testing (Fakes over Mocks)

Add or update fast unit tests covering:
- Happy path (`Content` / `200 OK`)
- Empty state (`Empty list`)
- Failure & offline states (`NetworkUnavailable`, `Unauthorized`, `ValidationError`)
- Boundary inputs & concurrency cancellation

---

## Gate 5: Paranoid Review & Self-Healing Verification Loop

1. **Paranoid Staff Check (`gstack` / `ECC`)**: Check your diff for race conditions (double-submit, stale search overwrite, token refresh stampede), N+1 queries, unbounded unpaginated lists, missing DB transactions, and IDOR/auth gaps.
2. **Run Verification Commands Sequentially** (fix every failure before finishing):
   - **Targeted Unit Test** (`commands.test_single` in `.agents/project-profile.json`)
   - **Compiler / Typecheck & Linter** (`commands.lint`)
   - **Architecture, File-Size & Security Audit**:
     ```bash
     python3 "<SKILL_DIR>/scripts/project_pro.py" audit --target "<PROJECT_DIR>" --fail-on-error
     ```
   - *(If new modules/directories were added)* Refresh `.agents/CODEBASE_MAP.md`:
     ```bash
     python3 "<SKILL_DIR>/scripts/project_pro.py" map --target "<PROJECT_DIR>" --write
     ```
**Rule**: Never claim completion while tests, lint, or `audit` fail.

---

## Gate 6: Memory Update & Terse Auditable Delivery (`caveman` + `ECC`)

1. If a non-obvious SDK pitfall, build quirk, or user correction surfaced during the task, append a 2-line prevention rule to `.agents/memory/lessons.md`.
2. Report changes concisely grouped by layer with clickable file links and verification results — zero filler narration or giant pasted code blocks.
