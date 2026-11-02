# Security Gateways, Git Hooks & AI Agent Runtime Hooks

`project-pro` enforces a **4-Shield Defense-in-Depth Architecture** so insecure code, leaked credentials, God-files (`> 450 LOC`), and Clean Architecture violations are blocked **during AI execution**, **before `git commit`**, and **before `git push`**.

---

## Shield 1: Shift-Left Security Rules (During Coding)

1. **Zero Hardcoded Secrets & Personal Environment Identifiers**:
   - API keys, Bearer/JWT tokens, OAuth client secrets, signing keystores, and DB URLs with credentials MUST come from validated environment variables or platform secret stores (`Keychain`, `EncryptedSharedPreferences`/`Keystore`, Vault/Secret Manager).
   - Never hardcode developer LAN IPs (e.g., `192.168.1.13`), static room/pairing/OTP codes (e.g., `883-716`, `482-195`), private/internal domains, or personal physical device serials/model IDs (`R5CX11ABNMH`, `SM-S926B`) as default values in code. Use dynamic discovery, random session generators, or RFC-5737/standard example placeholders in UI hints only.
   - Commit `.env.example` with dummy placeholders only; `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.jks`, `*.keystore`, and `service-account*.json` MUST stay in `.gitignore`.
2. **Injection & RCE Prevention (OWASP Top 10)**:
   - **SQL**: Use parameterized queries / prepared statements / ORM bound parameters ONLY. Never concatenate or interpolate user strings into SQL (`SELECT ... ${input}` / `f"SELECT ... {input}"`).
   - **OS Commands**: Avoid shell execution (`shell=True`, `sh -c`) with dynamic input; pass argument arrays (`["git", "diff", "--", path]`). Ban `eval()` / `exec()` on untrusted payloads.
   - **XSS / WebViews**: Escape/sanitize untrusted HTML before `dangerouslySetInnerHTML`; never enable universal file access on mobile `WebView`s loading remote content.
3. **Transport & Auth Hardening**:
   - Ban disabling TLS verification (`InsecureSkipVerify: true`, `verify=False`, `TrustAllCerts`) or enabling cleartext HTTP in production builds.
   - Redact `Authorization`, `Cookie`, `password`, `token`, `secret`, and PII fields in structured logs and crash reports.

---

## Shield 2: Built-In Zero-Dependency Scanner (`project_pro.py audit`)

`project_pro.py audit` scans either the **staged git index (`--staged`)** or the **entire repository**:
- **Secret & Identifier Signatures**: RSA/EC/OpenSSH/PGP private keys, AWS (`AKIA...`), Google/Firebase (`AIza...`), GitHub PAT (`ghp_...`, `github_pat_...`), Anthropic (`sk-ant-...`), OpenAI (`sk-proj-...`), Slack (`xox...`), Stripe live keys (`sk_live_...`), hardcoded JWTs, credentialed DB URIs (`postgres://user:pass@...`), literal `password`/`api_key`/`secret` assignments, hardcoded developer private LAN IPs (`192.168.x.x` / `172.16-31.x.x` in variable/default assignments), static room/pairing/PIN codes (`xxx-xxx`), and personal hardware serials/identifiers.
- **Forbidden Sensitive Files**: `.env` variants (except `.example`/`.sample`/`.template`), `.pem`, `.key`, `.p12`, `.jks`, `.keystore`, `id_rsa`, `id_ed25519`.
- **OWASP Code Heuristics**: Raw SQL string interpolation, unsafe `eval(`/shell interpolation, disabled TLS verification, and unresolved Git conflict markers (`<<<<<<<`).
- **Clean Architecture & Anti-God-File Gates**: Domain outer-layer/framework import leaks (`[FAIL]`), `> 300 LOC` (`[WARN]`), `> 450 LOC` (`[FAIL]`, auto-skipping generated files).

---

## Shield 3: Automated 3-Stage Git Hooks (`.githooks/`)

`project_pro.py init` writes executable hooks into `.githooks/` and automatically activates `git config core.hooksPath .githooks`:

| Git Hook | Speed | What It Enforces |
|----------|-------|------------------|
| **`pre-commit`** | `< 1s` | Runs `project_pro.py audit --staged --fail-on-error` (blocks staged secrets, `.env`/keystores, Domain leaks, files `> 450 LOC`, conflict markers) + runs `gitleaks protect --staged --redact` if `gitleaks` is installed |
| **`commit-msg`** | `< 0.2s` | Enforces **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `security:`, `test:`, `docs:`, `chore:`, `perf:`, `ci:`, `build:`) and blocks secrets pasted into commit messages |
| **`pre-push`** | `5–30s` | Runs full-repo `project_pro.py audit --fail-on-error` + stack-native **CVE dependency audit** (`npm audit --audit-level=high`, `govulncheck`, `pip-audit`, `gitleaks`) + project lint/typecheck & unit tests |

---

## Shield 4: AI Agent Runtime Lifecycle Hooks (Anti-Bypass Lock)

AI agents occasionally attempt `git commit --no-verify` or `git push --no-verify` when a hook blocks their commit. `project-pro` closes this loophole via native `PreToolUse` runtime hooks:

- **Antigravity (`.agents/hooks.json`)** & **Claude Code (`.claude/settings.json`)** invoke `project_pro.py agent-guard` before every shell command:
  - **Hard-denies** `git commit --no-verify` / `git commit -n`
  - **Hard-denies** `git push --no-verify`
  - **Hard-denies** `git push --force` / `-f` targeting `main` or `master`
  - **Hard-denies** disabling `core.hooksPath` or `rm -rf .githooks`
