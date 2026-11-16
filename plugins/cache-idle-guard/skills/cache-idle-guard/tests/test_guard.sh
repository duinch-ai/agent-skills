#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/../scripts/cache-idle-guard.py"

echo "=== 1. Test Claude Code Payload ==="
echo '{"session_id":"test-claude"}' | python3 "$PYTHON_SCRIPT" stamp
sleep 1
OUT_BLOCK=$(echo '{"session_id":"test-claude"}' | CACHE_IDLE_MINUTES=0 python3 "$PYTHON_SCRIPT" check)
if [[ "$OUT_BLOCK" != *"\"decision\": \"block\""* ]]; then
  echo "LỖI: Claude Code không chặn đúng mong đợi!"
  exit 1
fi

OUT_PASS=$(echo '{"session_id":"test-claude"}' | CACHE_IDLE_MINUTES=0.01 python3 "$PYTHON_SCRIPT" check)
if [[ -n "$OUT_PASS" ]]; then
  echo "LỖI: Lần gửi thứ 2 phải được thông qua nhưng lại ra: $OUT_PASS"
  exit 1
fi
echo "[OK] Claude Code tests passed!"

echo ""
echo "=== 2. Test Antigravity (AGY) Payload ==="
echo '{"conversationId":"test-agy"}' | python3 "$PYTHON_SCRIPT" stamp
sleep 1
OUT_AGY_BLOCK=$(echo '{"conversationId":"test-agy"}' | CACHE_IDLE_MINUTES=0 python3 "$PYTHON_SCRIPT" check)
if [[ "$OUT_AGY_BLOCK" != *"terminationBehavior\": \"terminate"* ]]; then
  echo "LỖI: AGY không terminate đúng mong đợi!"
  exit 1
fi

OUT_AGY_PASS=$(echo '{"conversationId":"test-agy"}' | CACHE_IDLE_MINUTES=0.01 python3 "$PYTHON_SCRIPT" check)
if [[ "$OUT_AGY_PASS" != "{}" ]]; then
  echo "LỖI: Lần gửi thứ 2 của AGY phải trả về {} nhưng lại ra: $OUT_AGY_PASS"
  exit 1
fi
echo "[OK] Antigravity tests passed!"

rm -f ~/.cache-idle-guard/state/test-claude ~/.cache-idle-guard/state/test-agy

echo ""
echo "=== 3. Test /compact & /clear Bypass ==="
echo '{"session_id":"test-claude-compact"}' | python3 "$PYTHON_SCRIPT" stamp
sleep 1
OUT_CLAUDE_COMPACT=$(echo '{"session_id":"test-claude-compact","prompt":"/compact"}' | CACHE_IDLE_MINUTES=0 python3 "$PYTHON_SCRIPT" check)
if [[ -n "$OUT_CLAUDE_COMPACT" ]]; then
  echo "LỖI: Claude Code /compact không được bỏ qua! Output: $OUT_CLAUDE_COMPACT"
  exit 1
fi

echo '{"conversationId":"test-agy-compact"}' | python3 "$PYTHON_SCRIPT" stamp
sleep 1
OUT_AGY_COMPACT=$(echo '{"conversationId":"test-agy-compact","lastUserInput":"/compact keep context"}' | CACHE_IDLE_MINUTES=0 python3 "$PYTHON_SCRIPT" check)
if [[ "$OUT_AGY_COMPACT" != "{}" ]]; then
  echo "LỖI: AGY /compact không được bỏ qua! Output: $OUT_AGY_COMPACT"
  exit 1
fi

echo '{"conversationId":"test-agy-clear"}' | python3 "$PYTHON_SCRIPT" stamp
sleep 1
OUT_AGY_CLEAR=$(echo '{"conversationId":"test-agy-clear","lastUserInput":"/clear"}' | CACHE_IDLE_MINUTES=0 python3 "$PYTHON_SCRIPT" check)
if [[ "$OUT_AGY_CLEAR" != "{}" ]]; then
  echo "LỖI: AGY /clear không được bỏ qua! Output: $OUT_AGY_CLEAR"
  exit 1
fi

echo '{"conversationId":"test-agy-noncompact"}' | python3 "$PYTHON_SCRIPT" stamp
sleep 1
OUT_AGY_NONCOMPACT=$(echo '{"conversationId":"test-agy-noncompact","lastUserInput":"/compact-other"}' | CACHE_IDLE_MINUTES=0 python3 "$PYTHON_SCRIPT" check)
if [[ "$OUT_AGY_NONCOMPACT" != *"terminationBehavior\": \"terminate"* ]]; then
  echo "LỖI: AGY /compact-other phải bị chặn nhưng lại ra: $OUT_AGY_NONCOMPACT"
  exit 1
fi
echo "[OK] /compact & /clear bypass tests passed!"

rm -f ~/.cache-idle-guard/state/test-claude-compact ~/.cache-idle-guard/state/test-agy-compact ~/.cache-idle-guard/state/test-agy-clear ~/.cache-idle-guard/state/test-agy-noncompact

echo ""
echo "=== 4. Test Status ==="
python3 "$PYTHON_SCRIPT" status

echo ""
echo "=== ALL TESTS PASSED! ==="
