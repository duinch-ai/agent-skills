# ⚡ `project-pro` — Interactive Clean Architecture & Multi-Agent Skill

> **Universal Agent Skill (`SKILL.md` Standard)** dành cho **Antigravity, GitHub Copilot, Claude Code, OpenAI Codex, Gemini CLI, Cursor, Windsurf, Cline, Roo Code, DeepSeek, Aider**.
> Giúp bạn **tích chọn (checkbox) dựng base dự án mới**, **chuẩn hoá dự án có sẵn**, **tra cứu repo mẫu nổi tiếng thay vì tự bịa cấu trúc**, ép chuẩn **Clean Architecture / MVI / MVVM / UDF / SOLID / DRY**, và **khởi tạo đầy đủ hệ sinh thái cho AI Agent** (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/rules/`).

---

## ✨ Tính năng cốt lõi

1. **Interactive Option Picker (Tick chọn cấu hình Base Project)**:
   - Tự động phát hiện dự án **Tạo mới (Greenfield)** hay **Đã tồn tại (Brownfield)** và nhận diện Tech Stack.
   - Cho phép tick chọn (`[x]`):
     - **Kiến trúc**: `Clean Architecture`, `Modular Clean (:feature + :core)`, `Vertical Slice / FSD`, `Hexagonal + DDD`, hoặc `Lightweight Modular (KISS/YAGNI)`.
     - **State / Flow Pattern**: `MVI Strict UDF`, `MVVM + UDF`, `TCA`, `BLoC / Cubit`, `Riverpod`, `TanStack Query + Zustand`, `CQRS`.
     - **Base Modules**: `Result<T, DomainError>`, `DI + Validated Config + Logging`, `Network (Auth/Retry) + Local DB`, `Design System + Typed Nav` (hoặc `OpenAPI + Healthcheck`), `Strict Linter + Boundary Tests`, `Testing Fakes + CI`.
     - **AI Agent Ecosystem**: `AGENTS.md` + `.agents/project-profile.json` + `.agents/rules/`, `CLAUDE.md`, `GEMINI.md`, `ADR-0001`, `.cursor/rules`, Pre-commit hook.
2. **Reference-First ("Tham khảo Repo nổi tiếng — Không tự nghĩ lại bánh xe")**:
   - Đóng gói sẵn danh mục repo chuẩn ngành cho **9 hệ sinh thái**:
     - **Android**: `android/nowinandroid`, `chrisbanes/tivi`, `slackhq/circuit`
     - **KMP / CMP**: `chrisbanes/tivi`, `JetBrains/kotlinconf-app`, `touchlab/KaMPKit`, `philipplackner/CMP-Bookpedia`
     - **Flutter**: `bizz84/starter_architecture_flutter_firebase`, `felangel/bloc`, `VGVentures/very_good_cli`
     - **iOS / Swift**: `pointfreeco/swift-composable-architecture`, `nalexn/clean-architecture-swiftui`
     - **Web (React / Next / Vue)**: `alan2207/bulletproof-react`, `feature-sliced/documentation`, `antfu/vitesse`
     - **Python / Go / NestJS**: `zhanymkanov/fastapi-best-practices`, `cosmicpython/code`, `evrone/go-clean-template`, `ThreeDotsLabs/wild-workouts-go-ddd-example`, `Sairyss/domain-driven-hexagon`
     - **Rust**: `emilk/egui`, `iced-rs/iced`, `LukeMathWalker/zero-to-production`
   - Hướng dẫn Rust riêng về ownership/borrowing, typed errors, async/unsafe, Cargo workspace, các target Linux/macOS/Windows/Android/iOS/Wasm/embedded, cùng CI đa nền tảng và chiến lược release theo loại artifact: [`references/stacks-rust.md`](./references/stacks-rust.md).
3. **6-Gate Execution Harness & Chống phình file cứng (300/450 LOC)**:
   - Mọi yêu cầu code bất kỳ (Feature mới, Fix bug, Refactor) đều đi qua 6 bước khóa cứng (`execution-harness.md`): Grounding repo mẫu → Kế hoạch tách file (`1 File = 1 Trách nhiệm`, `> 300 dòng = WARN`, `> 450 dòng = FAIL`) → Code Inside-Out / Root-Cause → Test biên với Fakes → Vòng lặp tự sửa lỗi.
4. **4-Shield Security & Multi-Layer Hooks (Trước khi Code, Commit & Push)**:
   - **Quét bảo mật Zero-Dependency**: Tự động bắt lộ API Keys, JWT, Private Keys, DB URI chứa password, chặn commit nhầm `.env` / `*.pem` / `*.keystore`, bắt lỗi SQL Injection nối chuỗi, tắt TLS verify, xung đột merge `<<<<<<<`.
   - **3 Git Hooks tự động kích hoạt (`core.hooksPath = .githooks`)**:
     - `pre-commit` (< 1s): Quét file staged (`--staged` + `gitleaks` nếu có), chặn lộ secret, chặn leak tầng `Domain`, chặn God-file `> 450 dòng`.
     - `commit-msg`: Ép chuẩn `Conventional Commits` + chống dán nhầm secret vào commit message.
     - `pre-push`: Quét toàn bộ repo + kiểm tra lỗ hổng thư viện CVE (`npm audit`, `govulncheck`, `pip-audit`) + chạy Lint/Typecheck & Unit Tests trước khi đẩy code lên remote.
   - **AI Agent Runtime Hooks (`.agents/hooks.json` & `.claude/settings.json`)**: Khóa cứng `PreToolUse` chặn không cho AI Agent lách luật bằng `git commit --no-verify`, `git push --no-verify` hoặc `git push --force` lên `main`/`master`.

---

## 🚀 Cài đặt đa nền tảng (1 Lệnh duy nhất)

```bash
chmod +x ./install.sh scripts/project_pro.py

# Cài đặt đồng loạt cho Antigravity, GitHub Copilot, .agents, Claude Code, Codex, Gemini CLI:
./install.sh all --force

# Kiểm tra trạng thái cài đặt trên máy:
./install.sh --status
```

### Dành riêng cho từng nền tảng khác:
- **npx skills (Vercel / Universal Skills CLI)** *(khi đã đẩy lên GitHub)*:
  ```bash
  npx skills add <your-github-user>/project-pro
  ```
- **Claude Code Plugin Marketplace**:
  ```text
  /plugin marketplace add /path/to/project-pro
  ```
- **DeepSeek / Chat / Aider / Roo / Cline (Xuất 1 file System Prompt độc lập)**:
  ```bash
  ./install.sh --export-prompt ./dist/project-pro-system-prompt.md
  ```
- **Gắn riêng vào 1 dự án cụ thể (Share qua Git cho cả team)**:
  ```bash
  ./install.sh --workspace /path/to/your-project --copy
  ```

---

## 🛠️ Sử dụng trực tiếp CLI (`project_pro.py` — Zero Dependencies)

Ngoài việc để AI Agent tự động kích hoạt, bạn có thể chạy trực tiếp bằng Python 3 chuẩn (không cần `pip install`):

```bash
# 1. Mở giao diện Checkbox TUI trực tiếp trên Terminal (↑/↓, Space để tick [x], Enter):
python3 scripts/project_pro.py wizard --target /path/to/my-app

# 2. Tra cứu nhanh repo chuẩn & pattern theo stack:
python3 scripts/project_pro.py lookup --stack kmp --query "pagination"

# 3. Kiểm toán (Audit) dự án xem có leak tầng Domain hoặc thiếu cấu hình Agent không:
python3 scripts/project_pro.py audit --target /path/to/my-app
```

---

## 📂 Cấu trúc gói Skill

```text
project-pro/
├── .claude-plugin/             # Manifest tương thích Claude Code Marketplace
│   ├── marketplace.json
│   └── plugin.json
├── SKILL.md                    # Core Skill instructions (Progressive Disclosure)
├── install.sh                  # Multi-agent symlink/copy/export installer
├── scripts/
│   └── project_pro.py          # Zero-dep Python 3 CLI: detect, lookup, init, wizard, audit
└── references/
    ├── clean-arch-and-solid.md # Luật Clean Arch, chống False DRY, SOLID & Conventions
    ├── presentation-patterns.md# MVI vs MVVM vs TCA vs BLoC/Riverpod vs FSD & UDF
    ├── agent-harness-spec.md   # Chuẩn khởi tạo đầy đủ AI Agent Harness & Base Modules
    ├── stacks-mobile.md        # Gold-standard repos & cấu trúc: Android, KMP, Flutter, iOS
    ├── stacks-web-backend.md   # Gold-standard repos & cấu trúc: Web, Python, Go, NestJS
    └── stacks-rust.md          # Rust idioms, cross-platform targets, CI/CD & releases
```
