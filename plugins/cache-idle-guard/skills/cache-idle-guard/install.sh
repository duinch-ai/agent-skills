#!/usr/bin/env bash
# Installer for the cache-idle-guard skill: Claude Code, Antigravity, Codex CLI.
set -euo pipefail

SKILL_NAME="cache-idle-guard"
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SKILL_ROOT/scripts/cache-idle-guard.py"
MODE="symlink"; FORCE=0; ACTION="install"; HOOKS=0; TARGETS=()

usage() {
  cat <<'USAGE'
Usage: ./install.sh [targets...] [options]

Targets (default: all):
  all       Every agent below whose config folder exists on this machine
  claude    ~/.claude/skills
  codex     ~/.codex/skills
  agy       ~/.gemini/config/skills and ~/.agents/skills
  gemini    ~/.gemini/skills

Options:
  --hooks            Also register lifecycle hooks (UserPromptSubmit, PreInvocation, Stop)
  --minutes <N>      Idle threshold in minutes before blocking (default: 60)
  --copy             Copy instead of symlink
  --force            Replace existing destination
  --uninstall        Remove the skill and unregister hooks
  --status           Show current installation status
USAGE
}

add_all() {
  [ -d "$HOME/.claude" ] && TARGETS+=("$HOME/.claude/skills")
  [ -d "$HOME/.codex" ] && TARGETS+=("$HOME/.codex/skills")
  [ -d "$HOME/.gemini/config" ] && TARGETS+=("$HOME/.gemini/config/skills" "$HOME/.agents/skills")
  [ -d "$HOME/.gemini" ] && TARGETS+=("$HOME/.gemini/skills")
  return 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    all) add_all ;;
    claude) TARGETS+=("$HOME/.claude/skills") ;;
    codex) TARGETS+=("$HOME/.codex/skills") ;;
    agy) TARGETS+=("$HOME/.gemini/config/skills" "$HOME/.agents/skills") ;;
    gemini) TARGETS+=("$HOME/.gemini/skills") ;;
    --hooks) HOOKS=1 ;;
    --minutes) shift; export CACHE_IDLE_MINUTES="${1:-60}" ;;
    --copy) MODE="copy" ;;
    --force) FORCE=1 ;;
    --uninstall) ACTION="uninstall" ;;
    --status) ACTION="status" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

[ ${#TARGETS[@]} -eq 0 ] && add_all

if [ "$ACTION" = "status" ]; then
  python3 "$SCRIPT" status
  exit 0
fi

if [ "$ACTION" = "uninstall" ]; then
  echo "==> Gỡ cài đặt $SKILL_NAME..."
  for target in "${TARGETS[@]}"; do
    dest="$target/$SKILL_NAME"
    [ -e "$dest" ] || [ -L "$dest" ] && rm -rf "$dest" && echo "  - Đã xoá $dest"
  done
  python3 "$SCRIPT" uninstall
  echo "==> Đã gỡ bỏ thành công."
  exit 0
fi

echo "==> Cài đặt skill $SKILL_NAME..."
for target in "${TARGETS[@]}"; do
  mkdir -p "$target"
  dest="$target/$SKILL_NAME"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ "$FORCE" -eq 1 ]; then
      rm -rf "$dest"
    else
      echo "  ~ Bỏ qua (đã tồn tại): $dest"
      continue
    fi
  fi
  if [ "$MODE" = "copy" ]; then
    cp -R "$SKILL_ROOT" "$dest"
  else
    ln -s "$SKILL_ROOT" "$dest"
  fi
  echo "  + Đã liên kết: $dest"
done

if [ "$HOOKS" -eq 1 ]; then
  echo "==> Đăng ký lifecycle hooks..."
  python3 "$SCRIPT" install
fi

echo "==> Hoàn tất cài đặt $SKILL_NAME!"
