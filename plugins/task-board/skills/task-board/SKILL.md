---
name: task-board
description: Quản lý task board, backlog và trạng thái task (task status) theo kiểu local-first với docs/tasks/TASK-*.md và docs/BACKLOG.md; đồng bộ GitHub Projects v2 chống cạn kiệt rate-limit qua provider github, chạy thuần local qua provider local, GitLab boards chưa hỗ trợ (stub). Dùng khi người dùng nhắc task board, backlog, task status, chuyển task sang In Progress/Done, GitHub Projects hoặc GitLab boards. Kèm quy trình 4 bước chuẩn (Tạo task, Do task, Code review gate, Release).
---

# Task Board Skill

Kỹ năng quản lý vòng đời task, đặc tả kỹ thuật (spec-driven development) theo kiểu local-first, với lớp **provider** để đồng bộ board từ xa:

| Provider | Trạng thái | Ghi chú |
|---|---|---|
| `github` (mặc định) | Hoàn chỉnh | GitHub Projects v2 qua `gh`, thiết kế **chống cạn kiệt Rate Limit** |
| `local` | Hoàn chỉnh | Không có remote: `list/move/report` chạy trên file Markdown; `push/sync/rate-limit` là no-op có thông báo (0 API call) |
| `gitlab` | Stub | Báo `GitLab provider not implemented yet`; chưa có lời gọi API nào |

Mã nguồn: `scripts/project_board.py` (CLI) + `scripts/taskboard/` (lõi: config/specs/store/commands; `providers/`: github, local, gitlab).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📂 TẦNG NỘI BỘ DỰ ÁN (LOCAL-FIRST & ZERO-API)                               │
│    ├── 📄 docs/tasks/TASK-*.md   -> Đặc tả chi tiết từng task (Spec files)  │
│    ├── 📑 docs/BACKLOG.md        -> Bảng phân bổ task & ánh xạ Issue ID     │
│    └── ⚡ CLI `list`              -> Đọc trực tiếp từ ổ cứng (0 API CALLS)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (1 GraphQL Point / REST)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🛡️ TẦNG BẢO VỆ RATE-LIMIT (CACHE & OFFLINE OUTBOX)                         │
│    ├── 🗄️ project_board_cache.json  -> Cache Field ID, Option ID, Item ID   │
│    ├── 📮 project_board_outbox.json -> Hàng đợi đột biến khi rate-limited    │
│    └── 🔄 CLI `sync`                -> Flush hàng đợi sau khi hồi quota     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ☁️ GITHUB PROJECTS (v2) KANBAN BOARD                                         │
│    Backlog ──▶ Todo ──▶ In Progress ──▶ Done ──▶ Released                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Các Cơ Chế Chống Cạn Kiệt Rate-Limit (Anti-Rate-Limit Defenses)

1. **Luôn Đồng Bộ Kèm Smart TTL Cache (`list`)**:
   - Lệnh `list` và `report` tự động đồng bộ trạng thái mới nhất từ GitHub Project board, nhưng được bảo vệ bởi **Smart TTL Cache** (mặc định 120s, tùy chỉnh qua `--ttl <giây>` hoặc biến môi trường `GH_PROJECT_CACHE_TTL`).
   - **Cache Hit (< TTL)**: Phục vụ tức thì từ cache cục bộ (`.local-artifacts/project_board_cache.json`) — **tiêu tốn đúng 0 điểm API**, không thể bị dính rate-limit.
   - **Cache Stale (>= TTL) hoặc `--refresh`**:
     - Tự động kiểm tra hạn ngạch trước (0 quota cost `gh api rate_limit`).
     - Kéo live snapshot từ GitHub Project v2 và lưu cache kèm timestamp.
     - **Tự động Reconcile**: Tự động cập nhật `Status: ...` vào file markdown spec cục bộ nếu trạng thái trên GitHub Project có thay đổi từ web UI, đảm bảo mã nguồn local luôn khớp 100% với Project board!
     - Nếu gặp sự cố rate limit hoặc mạng: Tự động fallback về cache trước đó mà không gây gián đoạn hay crash.
   - **`--local-only`**: Chế độ thuần offline (0 API calls, chỉ đọc file markdown).
2. **Persistent Schema & Item Cache**:
   - Lưu trữ `ProjectV2SingleSelectField` ID và ánh xạ `TASK_ID -> item_id` tại `.local-artifacts/project_board_cache.json`.
   - Cập nhật cache cục bộ ngay lập tức khi thực hiện `move` hoặc `push`, giúp các lệnh đọc tiếp theo thấy ngay trạng thái mới mà không cần chờ hết TTL.
3. **Single-Issue Targeted Lookup**:
   - Khi cần tìm Item ID của một task chưa cache, script chỉ tra cứu 1 issue cụ thể qua GraphQL (tốn **1 điểm** duy nhất thay vì quét toàn bộ 150 item).
4. **Tự Động Lưu Local & Push Lại Sau Khi Hết Rate Limit (Auto-Save & Background Retry Daemon)**:
   - Khi chuyển trạng thái task hoặc tạo issue, nếu gặp lỗi mạng, mã `429 (Rate Limit)` hoặc `403 (Abuse/Secondary Rate Limit)`:
     - **Lưu cục bộ ngay lập tức**: Cập nhật file spec trên ổ cứng và ghi nhận thao tác vào `project_board_outbox.json` để tiến trình công việc của Agent không bao giờ bị nghẽn.
     - **Tự động khởi chạy Daemon ngầm (`daemon`)**: Script tự động tra cứu mốc thời gian quota hồi phục (`reset_ts`) và kích hoạt một tiến trình nền detached (`project_board.py daemon --until <ts>`). Tiến trình này sẽ ngủ cho đến đúng thời điểm GitHub cấp lại quota, tự động thức dậy, đẩy toàn bộ thay đổi lên GitHub Project và thoát an toàn.
     - **Đồng bộ cơ hội (Opportunistic Auto-Sync)**: Mỗi khi bất kỳ lệnh CLI nào (`list`, `move`, `push`, `report`) được thực thi sau khi quota đã hồi, script sẽ tự động xả sạch các task còn đọng trong outbox.
5. **Đồng Bộ Hai Chiều Toàn Diện (`sync`)**:
   - Lệnh `sync` thực hiện đồng bộ 2 chiều trọn vẹn:
     - Chiều 1 (Local -> Remote): Xả các tác vụ tồn đọng trong outbox lên GitHub.
     - Chiều 2 (Remote -> Local): Kéo trạng thái live mới nhất từ GitHub Project về, làm mới cache và cập nhật các file spec cục bộ.
6. **Tách Biệt REST & GraphQL**:
   - Lệnh `push` tạo issue qua REST (`gh issue create` — dùng hạn ngạch REST 5.000 req/giờ độc lập) trước khi gắn card vào Project qua GraphQL.

---

## 🛠️ Cấu Hình & Khởi Tạo Dự Án

### 1. Tự động khởi tạo cấu hình (`init`)
Chạy lệnh khởi tạo ngay tại thư mục gốc của repository:

```bash
python3 <skill_dir>/scripts/project_board.py init --project <PROJECT_NUMBER>          # provider github (mặc định)
python3 <skill_dir>/scripts/project_board.py init --provider local                    # không remote
```

Script sẽ (provider github):
- Tự động nhận diện `owner` và `repo` từ `git remote origin`.
- Tự động truy vấn GraphQL lấy Node ID dạng `PVT_kw...` của GitHub Project #`<PROJECT_NUMBER>`.
- Ghi cấu hình vào `.agents/task-board.json` (có trường `provider`).

### 2. File cấu hình `.agents/task-board.json` mẫu
Nếu muốn cấu hình thủ công hoặc tùy biến thư mục:

```json
{
  "provider": "github",
  "owner": "your-org-or-username",
  "repo": "your-repo-name",
  "project_number": "1",
  "project_id": "PVT_kw...",
  "tasks_dir": "docs/tasks",
  "backlog_doc": "docs/BACKLOG.md",
  "cache_dir": ".local-artifacts"
}
```

Provider `local`: `{"provider": "local", "tasks_dir": "docs/tasks", "backlog_doc": "docs/BACKLOG.md"}`.

> **Tương thích ngược**: repo cũ chỉ có `.github/project.json` (không có `provider`) vẫn chạy nguyên như cũ và được coi là provider `github`. File tìm theo thứ tự: `.agents/task-board.json` > `.github/project.json` > `.agents/project.json` > `.agents/workflow.json` > `project.json`.
>
> **Thứ tự ưu tiên nạp cấu hình** (đúng như code): CLI flags (`--provider`, `--owner`, `--repo`, `--project`...) > Biến môi trường (`TASK_BOARD_PROVIDER`, `GH_PROJECT_OWNER`, `GH_PROJECT_REPO`, `GH_PROJECT_NUMBER`, `GH_PROJECT_ID`...) > file cấu hình > Tự động dò `git remote` (chỉ github).

---

## 🔄 4 Vòng Đời Task Chuẩn (Standard Task Workflow)

### Bước 1: Tạo task (`Tạo task`)
1. Nghiên cứu yêu cầu, thống nhất kiến trúc và chia nhỏ sub-tasks.
2. Viết tài liệu đặc tả (spec) tại `docs/tasks/<TASK_ID>.md`:
   ```markdown
   # TASK-01 — Triển khai Module A
   Status: Backlog
   Priority: P0
   ```
3. Đẩy lên Backlog của GitHub Project:
   ```bash
   python3 <skill_dir>/scripts/project_board.py push docs/tasks/TASK-01.md --status "Backlog"
   ```

### Bước 2: Thực thi task (`Do task`)
1. Đọc task cần làm từ cột `Todo`:
   ```bash
   python3 <skill_dir>/scripts/project_board.py list --status "Todo"
   ```
2. Chuyển task sang `In Progress`:
   ```bash
   python3 <skill_dir>/scripts/project_board.py move TASK-01 "In Progress"
   ```
3. Tiến hành implement mã nguồn.
4. Chạy Unit Test và Test trên môi trường/thiết bị thực tế:
   - Nếu **thất bại**: Giữ nguyên ở `In Progress`, sửa lỗi và ghi nhận bằng chứng kiểm thử.
   - Nếu **vượt qua**: Tiến hành bước Code Review Gate.

### Bước 3: Code Review Gate & Hoàn thành (`Done`)
1. Chạy linter, format code, kiểm tra tính toàn vẹn (SOLID, Clean Architecture, Conventions).
2. Chuyển task sang `Done`:
   ```bash
   python3 <skill_dir>/scripts/project_board.py move TASK-01 "Done"
   ```

### Bước 4: Đóng phiên bản (`Release`)
1. Gom các task hoàn thành, đóng tag/commit phiên bản mới.
2. Chuyển các task đã phát hành sang `Released`:
   ```bash
   python3 <skill_dir>/scripts/project_board.py move TASK-01 "Released"
   ```

---

## 📖 Bảng Lệnh CLI Chi Tiết

| Lệnh | Mục đích | API Quota sử dụng |
|---|---|---|
| `python3 <skill_dir>/scripts/project_board.py list` | Liệt kê task kèm smart TTL cache (tự động đồng bộ Project v2) | **0 điểm** khi cache hit / 1 điểm khi fetch |
| `python3 <skill_dir>/scripts/project_board.py list --refresh` | Ép buộc kéo trạng thái mới nhất từ Project v2 và reconcile local specs | 1 điểm GraphQL |
| `python3 <skill_dir>/scripts/project_board.py list --local-only` | Chế độ thuần offline, chỉ đọc file spec markdown | **0 điểm** (Zero-API) |
| `python3 <skill_dir>/scripts/project_board.py move <ID> "<Status>"` | Cập nhật spec cục bộ + cập nhật cache tức thì + di chuyển card Board | 1 điểm GraphQL (hoặc 0 nếu đẩy vào Outbox) |
| `python3 <skill_dir>/scripts/project_board.py push <spec-file>` | Tạo GitHub Issue qua REST, gắn card vào Project và ghi cache | 1 REST + 1 GraphQL |
| `python3 <skill_dir>/scripts/project_board.py sync` | Đồng bộ 2 chiều: Xả outbox (Local->Remote) + kéo live Project state (Remote->Local) | Tùy số lượng mutation |
| `python3 <skill_dir>/scripts/project_board.py report` | Xuất báo cáo Markdown tổng thể: Board, Specs, Quota, Cache & Outbox | **0 điểm** khi cache hit |
| `python3 <skill_dir>/scripts/project_board.py rate-limit` | Kiểm tra hạn ngạch REST/GraphQL còn lại và độ dài outbox | 0 điểm REST |
| `python3 <skill_dir>/scripts/project_board.py init --project <N> [--provider github\|local]` | Khởi tạo `.agents/task-board.json` | 1 điểm GraphQL (github) / 0 (local) |

---

## 💡 Lời Khuyên Cho AI Agent Khi Làm Việc

- **Luôn kiểm tra `rate-limit` trước khi chạy batch**: Chạy `project_board.py rate-limit` nếu nghi ngờ mạng chập chờn hoặc vừa thực hiện nhiều tác vụ.
- **Không ngần ngại khi outbox kích hoạt**: Nếu terminal báo `[RATE-LIMIT / SCOPE GUARD] Deferred GitHub Project update`, đừng lo lắng! File spec cục bộ đã được cập nhật chính xác trạng thái, Agent có thể tiếp tục công việc coding ngay mà không cần đợi.
- **Quy chuẩn định danh task**: Nên dùng định dạng `<PREFIX>-<NUMBER>` (ví dụ `TASK-01`, `FEAT-42`, `CORE-101`, `PROJ-10`) trong tiêu đề file markdown để script tự động nhận diện và sắp xếp khoa học.
