#!/usr/bin/env python3
"""cache-idle-guard: Chặn gửi tin khi session nghỉ quá lâu (prompt cache hết hạn).

Hỗ trợ đồng thời:
  - Claude Code (hook UserPromptSubmit & Stop)
  - Antigravity / Gemini AGY (hook PreInvocation & Stop)
  - Codex CLI (hook UserPromptSubmit & Stop)

Sử dụng:
  python3 cache-idle-guard.py stamp [--agent claude|agy|codex]
  python3 cache-idle-guard.py check [--agent claude|agy|codex]
  python3 cache-idle-guard.py install [--minutes 5|60] [--agents all|claude|agy|codex]
  python3 cache-idle-guard.py uninstall [--agents all|claude|agy|codex]
  python3 cache-idle-guard.py status
"""

import json
import os
import sys
import time
from pathlib import Path


def get_state_dir() -> Path:
    base = Path.home() / ".cache-idle-guard" / "state"
    base.mkdir(parents=True, exist_ok=True)
    return base


def detect_payload():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def is_agy_agent(payload: dict) -> bool:
    if "--agent" in sys.argv:
        idx = sys.argv.index("--agent")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1] == "agy":
            return True
    return "conversationId" in payload


def get_session_id(payload: dict) -> str:
    return payload.get("session_id") or payload.get("conversationId") or "unknown"


def get_limit_seconds() -> float:
    minutes = float(os.environ.get("CACHE_IDLE_MINUTES", "60"))
    return minutes * 60.0


def cmd_stamp(payload: dict, is_agy: bool):
    sid = get_session_id(payload)
    state_file = get_state_dir() / sid
    now = time.time()
    try:
        state_file.write_text(str(now))
    except Exception as e:
        sys.stderr.write(f"cache-idle-guard: failed to write timestamp: {e}\n")

    if is_agy:
        print(json.dumps({}))
    sys.exit(0)


def cmd_check(payload: dict, is_agy: bool):
    sid = get_session_id(payload)
    state_file = get_state_dir() / sid
    now = time.time()
    limit = get_limit_seconds()

    idle = 0.0
    if state_file.exists():
        try:
            idle = now - float(state_file.read_text().strip())
        except Exception:
            idle = 0.0

    if idle > limit:
        mins = int(idle // 60)
        limit_mins = int(limit // 60)
        reason = (
            f"Session đã nghỉ {mins} phút, vượt thời hạn cache ({limit_mins} phút): "
            "gửi tiếp sẽ phải ghi lại toàn bộ ngữ cảnh với giá/quota đầy đủ. "
            "Chạy /compact (giữ mạch việc đang dở) hoặc /clear (sang việc mới) rồi gửi lại tin nhắn. "
            "Muốn bỏ qua thì gửi lại y nguyên, lần này sẽ không bị chặn."
        )
        try:
            state_file.write_text(str(now))
        except Exception:
            pass

        if is_agy:
            print(
                json.dumps({
                    "injectSteps": [
                        {"errorMessage": {"userMessage": reason}}
                    ],
                    "terminationBehavior": "terminate",
                })
            )
        else:
            print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)

    try:
        state_file.write_text(str(now))
    except Exception:
        pass

    if is_agy:
        print(json.dumps({}))
    sys.exit(0)


def install_claude(script_path: Path):
    settings_file = Path.home() / ".claude" / "settings.json"
    if not settings_file.parent.exists():
        settings_file.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text())
        except Exception:
            data = {}

    hooks = data.setdefault("hooks", {})
    user_submit = hooks.setdefault("UserPromptSubmit", [])
    stop_hooks = hooks.setdefault("Stop", [])

    cmd_check_str = f"python3 {script_path} check"
    cmd_stamp_str = f"python3 {script_path} stamp"

    user_submit = [
        item for item in user_submit
        if not any("cache-idle-guard" in h.get("command", "") for h in item.get("hooks", []))
    ]
    stop_hooks = [
        item for item in stop_hooks
        if not any("cache-idle-guard" in h.get("command", "") for h in item.get("hooks", []))
    ]

    user_submit.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": cmd_check_str, "timeout": 5}]
    })
    stop_hooks.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": cmd_stamp_str, "timeout": 5}]
    })

    hooks["UserPromptSubmit"] = user_submit
    hooks["Stop"] = stop_hooks
    data["hooks"] = hooks

    settings_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"  [✓] Claude Code: đã cấu hình tại {settings_file}")


def install_agy(script_path: Path):
    hooks_file = Path.home() / ".gemini" / "config" / "hooks.json"
    if not hooks_file.parent.exists():
        hooks_file.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if hooks_file.exists():
        try:
            data = json.loads(hooks_file.read_text())
        except Exception:
            data = {}

    cmd_check_str = f"python3 {script_path} check"
    cmd_stamp_str = f"python3 {script_path} stamp"

    data["cache-idle-guard"] = {
        "PreInvocation": [
            {"type": "command", "command": cmd_check_str, "timeout": 5}
        ],
        "Stop": [
            {"type": "command", "command": cmd_stamp_str, "timeout": 5}
        ]
    }

    hooks_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"  [✓] Antigravity (AGY): đã cấu hình tại {hooks_file}")


def install_codex(script_path: Path):
    hooks_file = Path.home() / ".codex" / "hooks.json"
    if not hooks_file.parent.exists():
        return
    data = {}
    if hooks_file.exists():
        try:
            data = json.loads(hooks_file.read_text())
        except Exception:
            data = {}

    hooks = data.setdefault("hooks", {})
    user_submit = hooks.setdefault("UserPromptSubmit", [])
    stop_hooks = hooks.setdefault("Stop", [])

    cmd_check_str = f"python3 {script_path} check"
    cmd_stamp_str = f"python3 {script_path} stamp"

    user_submit = [
        item for item in user_submit
        if not any("cache-idle-guard" in h.get("command", "") for h in item.get("hooks", []))
    ]
    stop_hooks = [
        item for item in stop_hooks
        if not any("cache-idle-guard" in h.get("command", "") for h in item.get("hooks", []))
    ]

    user_submit.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": cmd_check_str, "timeout": 5}]
    })
    stop_hooks.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": cmd_stamp_str, "timeout": 5}]
    })

    hooks["UserPromptSubmit"] = user_submit
    hooks["Stop"] = stop_hooks
    data["hooks"] = hooks

    hooks_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"  [✓] Codex: đã cấu hình tại {hooks_file}")


def uninstall_claude():
    settings_file = Path.home() / ".claude" / "settings.json"
    if not settings_file.exists():
        return
    try:
        data = json.loads(settings_file.read_text())
        hooks = data.get("hooks", {})
        if "UserPromptSubmit" in hooks:
            hooks["UserPromptSubmit"] = [
                item for item in hooks["UserPromptSubmit"]
                if not any("cache-idle-guard" in h.get("command", "") for h in item.get("hooks", []))
            ]
        if "Stop" in hooks:
            hooks["Stop"] = [
                item for item in hooks["Stop"]
                if not any("cache-idle-guard" in h.get("command", "") for h in item.get("hooks", []))
            ]
        settings_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"  [✓] Claude Code: đã gỡ bỏ khỏi {settings_file}")
    except Exception as e:
        print(f"  [✗] Lỗi gỡ Claude Code: {e}")


def uninstall_agy():
    hooks_file = Path.home() / ".gemini" / "config" / "hooks.json"
    if not hooks_file.exists():
        return
    try:
        data = json.loads(hooks_file.read_text())
        if "cache-idle-guard" in data:
            del data["cache-idle-guard"]
            hooks_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            print(f"  [✓] Antigravity (AGY): đã gỡ bỏ khỏi {hooks_file}")
    except Exception as e:
        print(f"  [✗] Lỗi gỡ AGY: {e}")


def uninstall_codex():
    hooks_file = Path.home() / ".codex" / "hooks.json"
    if not hooks_file.exists():
        return
    try:
        data = json.loads(hooks_file.read_text())
        hooks = data.get("hooks", {})
        if "UserPromptSubmit" in hooks:
            hooks["UserPromptSubmit"] = [
                item for item in hooks["UserPromptSubmit"]
                if not any("cache-idle-guard" in h.get("command", "") for h in item.get("hooks", []))
            ]
        if "Stop" in hooks:
            hooks["Stop"] = [
                item for item in hooks["Stop"]
                if not any("cache-idle-guard" in h.get("command", "") for h in item.get("hooks", []))
            ]
        hooks_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"  [✓] Codex: đã gỡ bỏ khỏi {hooks_file}")
    except Exception as e:
        print(f"  [✗] Lỗi gỡ Codex: {e}")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "check"
    script_path = Path(__file__).resolve()

    if arg == "install":
        print(f"Đang cài đặt cache-idle-guard từ {script_path}...")
        install_claude(script_path)
        install_agy(script_path)
        install_codex(script_path)
        print("Hoàn tất cài đặt! Khởi động session mới để hook có hiệu lực.")
        return

    if arg == "uninstall":
        print("Đang gỡ bỏ cache-idle-guard...")
        uninstall_claude()
        uninstall_agy()
        uninstall_codex()
        print("Đã gỡ bỏ hook thành công!")
        return

    if arg == "status":
        limit_mins = int(get_limit_seconds() // 60)
        print(f"cache-idle-guard status:")
        print(f"  - Ngưỡng cache idle: {limit_mins} phút (CACHE_IDLE_MINUTES={os.environ.get('CACHE_IDLE_MINUTES', '60')})")
        print(f"  - Thư mục lưu state: {get_state_dir()}")
        print(f"  - Vị trí script: {script_path}")
        return

    payload = detect_payload()
    is_agy = is_agy_agent(payload)

    if arg == "stamp":
        cmd_stamp(payload, is_agy)
    elif arg == "check":
        cmd_check(payload, is_agy)
    else:
        sys.stderr.write(f"Unknown command: {arg}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
