"""Product categories (purpose / lifecycle taxonomy) and the wizard choice list."""

from __future__ import annotations

from typing import Any

PRODUCT_CATEGORIES: dict[str, dict[str, Any]] = {
    "mobile-app": {
        "label": "Mobile App (Android / iOS / Cross-Platform)",
        "description": "Native hoặc Cross-platform app di động cho iOS/Android (Offline-first, reactive state, permissions, gestures)",
        "recommended_stacks": ["android", "ios", "flutter", "kmp"],
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvi",
        "key_features": ["solid-dry", "typed-errors", "i18n", "network-storage", "ui-nav", "arch-lint"],
        "guidance": "Thiết kế offline-first với single source of truth từ local database; ViewModel decoupled khỏi Context; hỗ trợ dark mode & dynamic locales.",
    },
    "desktop-app": {
        "label": "Desktop App (macOS / Windows / Linux GUI)",
        "description": "Phần mềm cài đặt máy tính (Window state, native file dialogs, system tray, drag-and-drop, multi-threading)",
        "recommended_stacks": ["rust", "flutter", "kmp", "ios"],
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvi",
        "key_features": ["solid-dry", "typed-errors", "i18n", "ui-nav", "testing-ci", "arch-lint"],
        "guidance": "Tách biệt luồng UI và worker threads/threadpool cho tác vụ nặng I/O; lưu trạng thái cửa sổ; hỗ trợ native menus và file dialogs.",
    },
    "multiplatform-app": {
        "label": "Multi-Platform Universal App (Mobile + Desktop + Web)",
        "description": "Ứng dụng đa nền tảng dùng chung code core logic, domain và một phần hoặc toàn bộ UI",
        "recommended_stacks": ["kmp", "flutter", "rust", "web"],
        "recommended_arch": "clean",
        "recommended_pattern": "mvi",
        "key_features": ["solid-dry", "typed-errors", "i18n", "network-storage", "ui-nav", "testing-ci"],
        "guidance": "Cô lập domain & business logic không phụ thuộc platform SDK; thiết kế UI tự thích ứng (responsive layout) giữa mobile touch và desktop mouse/keyboard.",
    },
    "web-app": {
        "label": "Web Application / SaaS Portal (SPA / SSR / Dashboard)",
        "description": "Ứng dụng web người dùng, admin portal, SaaS dashboard với SEO hoặc trải nghiệm tương tác cao",
        "recommended_stacks": ["web"],
        "recommended_arch": "vertical-slice",
        "recommended_pattern": "query-zustand",
        "key_features": ["solid-dry", "typed-errors", "i18n", "ui-nav", "arch-lint"],
        "guidance": "Phân chia rõ server vs client state; dùng server cache (TanStack Query) cho API data và store cục bộ (Zustand) cho UI state; tối ưu Core Web Vitals.",
    },
    "backend-api": {
        "label": "Backend Service / API (REST / gRPC / GraphQL / Microservice)",
        "description": "Dịch vụ máy chủ cung cấp API cho web, mobile hoặc các hệ thống khác",
        "recommended_stacks": ["python", "go", "nestjs"],
        "recommended_arch": "hexagonal",
        "recommended_pattern": "service-repo",
        "key_features": ["solid-dry", "typed-errors", "di-core", "network-storage", "arch-lint"],
        "guidance": "Chuẩn hóa API contracts (OpenAPI); endpoint /healthz và /readyz; chuẩn lỗi RFC 9457 Problem Details; quản lý DB connection pool và transactions.",
    },
    "service-worker": {
        "label": "Background Worker / Queue Consumer / Scheduled Daemon",
        "description": "Tác vụ chạy ngầm, worker đọc message từ Queue (Kafka/RabbitMQ/Redis), cron jobs tự động",
        "recommended_stacks": ["python", "go", "rust", "nestjs"],
        "recommended_arch": "hexagonal",
        "recommended_pattern": "service-repo",
        "key_features": ["solid-dry", "typed-errors", "di-core", "testing-ci"],
        "guidance": "Xử lý graceful shutdown (SIGINT/SIGTERM); thiết kế xử lý idempotent (tránh lặp); cơ chế retry exponential backoff + Dead Letter Queue (DLQ).",
    },
    "cli-tool": {
        "label": "CLI Tool / Developer Utility / TUI",
        "description": "Công cụ dòng lệnh, scripting, interactive TUI, compiler tool hoặc công cụ lập trình",
        "recommended_stacks": ["rust", "go", "python"],
        "recommended_arch": "lightweight",
        "recommended_pattern": "service-repo",
        "key_features": ["solid-dry", "typed-errors", "arch-lint"],
        "guidance": "Khởi động cực nhanh (< 50ms); chuẩn POSIX flags (-h, --help, --json) & exit codes; tự nhận diện TTY; tách riêng parser CLI khỏi logic nghiệp vụ.",
    },
    "library-sdk": {
        "label": "Reusable Library / Client SDK / Shared Package",
        "description": "Thư viện tái sử dụng, SDK kết nối dịch vụ, hoặc package phát hành lên registry",
        "recommended_stacks": ["rust", "web", "python", "kmp", "go"],
        "recommended_arch": "clean",
        "recommended_pattern": "service-repo",
        "key_features": ["solid-dry", "typed-errors", "testing-ci", "arch-lint"],
        "guidance": "Tối thiểu hóa diện tích Public API; tuân thủ nghiêm ngặt SemVer; zero unsolicited side-effects (không in bừa bãi ra stdout); tối thiểu hóa dependencies bên ngoài.",
    },
    "embedded-homebrew": {
        "label": "Embedded / Console Homebrew / Low-Level / Game",
        "description": "Ứng dụng chạy trên thiết bị chuyên biệt (Nintendo Switch homebrew, embedded, vi điều khiển)",
        "recommended_stacks": ["cpp-switch", "rust"],
        "recommended_arch": "modular-clean",
        "recommended_pattern": "mvc-borealis",
        "key_features": ["solid-dry", "typed-errors", "i18n", "testing-ci"],
        "guidance": "Quản lý bộ nhớ nghiêm ngặt không rò rỉ; hỗ trợ gamepad controller và cảm ứng; đóng gói RomFS assets; quản lý cross-compilation toolchain.",
    },
}

PRODUCT_CATEGORY_CHOICES: list[tuple[str, str]] = [
    (cat_id, f"{cat_info['label']} — {cat_info['description'][:65]}...")
    for cat_id, cat_info in PRODUCT_CATEGORIES.items()
]
