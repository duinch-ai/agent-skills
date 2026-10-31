# Agentic Engineering Patterns — Distilled from Top Open-Source Harnesses

This reference synthesizes the highest-leverage engineering mechanisms from leading open-source AI agent harnesses (`karpathy-skills`, `obra/superpowers`, `ECC`, `gstack`, `planning-with-files`, `graphify`/`codegraph`, and `caveman`) into cross-agent rules that work identically on **Antigravity, Claude Code, OpenAI Codex, Gemini CLI, Cursor, and DeepSeek**.

---

## 1. Karpathy's 4 Behavioral Guardrails (`karpathy-skills`)

Prevent the 4 classic psychological failure modes of coding LLMs:

1. **Think Before Coding (No Silent Assumptions)**:
   - Never silently pick one interpretation when requirements have multiple valid meanings — surface assumptions explicitly or ask upfront.
   - **Push Back When Warranted**: If a prompt asks for an architectural anti-pattern (e.g., querying SQL inside a UI view, disabling auth/TLS, hardcoding secrets), politely flag the risk and propose the clean alternative instead of blindly complying.
2. **Simplicity First (Anti-Overengineering)**:
   - Write the minimum clean code required to solve the current problem.
   - Do not build speculative plugin registries, generic factories, or multi-provider abstractions for a single concrete use case (YAGNI).
3. **Surgical Changes (Minimal Diff Blast Radius)**:
   - Touch **only** the lines and files necessary for the request.
   - Never reformat untouched functions, reorder unrelated imports, rewrite working comments, or "clean up" neighboring code that wasn't part of the task.
   - Remove dead imports/helpers created by *your own* change, leaving orthogonal code untouched.
4. **Goal-Driven Execution**:
   - Convert vague prompts (*"fix checkout bug"*, *"optimize feed"*) into concrete, verifiable pass/fail criteria before editing files, then loop until every criterion is proven green.

---

## 2. Systematic 4-Phase Debugging & The "3-Strike Stop" (`obra/superpowers`)

**Iron Law**: *Never propose or apply a bugfix without locating the root cause first.*

1. **Phase 1 — Reproduce & Trace Dataflow**: Read the full error/stacktrace; trace bad values backward from symptom to origin across `UI -> State -> Domain -> Data`.
2. **Phase 2 — Reference & Working-Code Comparison**: Compare the broken path against a working sibling module or the project's anchored `referenceRepo`.
3. **Phase 3 — Single-Variable Hypothesis & The 3-Strike Rule**:
   - Test **one** hypothesis at a time.
   - **3-Strike Architectural Stop**: If **3 consecutive fix attempts fail**, **STOP CODING IMMEDIATELY**. Revert failed patches, summarize what was proven false, and re-evaluate the underlying architecture/assumption with the user instead of stacking hack #4 on top of hack #3!
4. **Phase 4 — Regression Test + Clean Fix**: Lock the bug with a deterministic unit test so it can never silently regress.

---

## 3. Paranoid Staff Engineer Review Lens (`gstack` & `ECC`)

Before declaring any non-trivial feature or backend endpoint finished, run a fast mental pass for **production-only failure modes** that unit tests often miss:

- **Concurrency & Race Conditions**: Double-tap button submissions (debounce/disable while submitting?), concurrent token refresh stampede (mutex/single-flight?), stale async response overwriting newer search query (`collectLatest` / `AbortController` / `restartable`?).
- **N+1 & Unbounded Data**: Querying inside a loop? Returning an unbounded `SELECT *` list without pagination or limit? Rendering 5,000 items without `LazyColumn` / `ListView.builder` / virtualization?
- **Idempotency & Partial Failure**: What happens if the network drops *after* the server commits a payment/order, and the client retries? What if step 2 of a 3-step DB write fails (missing transaction / `UnitOfWork`)?
- **Trust Boundaries**: Could user A access user B's resource by changing an ID parameter (IDOR / missing ownership check)?

---

## 4. Persistent Disk Memory Across Sessions & Agents (`planning-with-files` + `ECC` + `graphify`)

Context windows compact and developers switch tools mid-project (`Claude Code` ↔ `Codex` ↔ `Antigravity` via `cc-switch`). Keep long-lived memory **on disk inside `.agents/`**, never trapped inside chat history:

1. **`.agents/CODEBASE_MAP.md` (`graphify` / `codegraph` pattern)**:
   - Generated/refreshed via `python3 "<SKILL_DIR>/scripts/project_pro.py" map --target "<PROJECT_DIR>" --write`.
   - Gives any agent an instant ~100-line structural map & Mermaid module dependency graph, saving 10,000–30,000 tokens of blind `grep`/`ls` exploration per session.
2. **`.agents/memory/active-plan.md` (`planning-with-files` pattern)**:
   - For multi-file features (> 3 files) or multi-session work, write the checklist of planned file slices, architectural decisions, and `[x]`/`[ ]` progress directly to `.agents/memory/active-plan.md`. Any agent resuming the repo picks up effortlessly from the exact next unchecked step.
3. **`.agents/memory/lessons.md` (`ECC` Continuous Learning Ledger)**:
   - Whenever a subtle bug, build quirk, SDK pitfall, or user correction occurs, append a 2-line rule (`Symptom -> Root Cause & Prevention Rule`) to `.agents/memory/lessons.md`. Read this file during **Gate 1** so the project never suffers the same mistake twice.

---

## 5. Token & Output Economy (`caveman` & `ponytail`)

Maximize reasoning quality per token and respect human reading time:
- **Zero Filler Narration**: Never output meta-commentary (*"Let me read the file now"*, *"Great question!"*, *"I will now think carefully"*). Execute tools directly and speak with high signal.
- **Targeted Context Reads**: Read `.agents/CODEBASE_MAP.md` + targeted line ranges (`StartLine`–`EndLine`) or symbol searches instead of dumping entire large files into context unnecessarily.
- **Terse Auditable Summaries**: Report *what changed, why, and verification proof* using clickable file links — never paste 100-line code blocks into chat that were already written to disk.

---

## 6. Ecosystem Synergy (Keep Skills Modular — Do Not Duplicate)

`project-pro` intentionally focuses on **Architecture, Code Quality, Execution Discipline, Memory & Security**. Pair it cleanly with specialized sibling tools when installed:
- **Visual Design, Color Palettes, Typography & UX Polish** → Pair with **`ui-ux-pro-max`** while `project-pro` governs state management (`UiState`), component splitting, and Clean Architecture boundaries.
- **Real Browser E2E Verification** → Pair with **`playwright-mcp`** / browser tools for end-to-end UI flows after `project-pro` unit/state tests pass.
