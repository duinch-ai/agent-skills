#!/usr/bin/env bash
# Cài 15 Agent Skills của repo này vào Gemini CLI / Antigravity / Codex CLI.
# Claude Code KHÔNG dùng script này — xem README (/plugin marketplace add).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="symlink"
TARGETS=()

usage() {
  cat <<'USAGE'
Usage: ./install.sh [gemini|antigravity|codex|all] [--copy] [--force]

  gemini       -> ~/.gemini/skills      (Gemini CLI)
  antigravity  -> ~/.agents/skills      (Antigravity CLI, alias chuẩn mới)
  codex        -> ~/.codex/skills       (Codex CLI)
  all          -> cả ba (mặc định)

  --copy   Sao chép thay vì tạo symlink (symlink giúp `git pull` cập nhật ngay).
  --force  Ghi đè skill đã tồn tại ở thư mục đích.
USAGE
}

FORCE=0
for arg in "$@"; do
  case "$arg" in
    gemini)      TARGETS+=("$HOME/.gemini/skills") ;;
    antigravity) TARGETS+=("$HOME/.agents/skills") ;;
    codex)       TARGETS+=("$HOME/.codex/skills") ;;
    all)         TARGETS+=("$HOME/.gemini/skills" "$HOME/.agents/skills" "$HOME/.codex/skills") ;;
    --copy)      MODE="copy" ;;
    --force)     FORCE=1 ;;
    -h|--help)   usage; exit 0 ;;
    *)           echo "Tham số không hợp lệ: $arg" >&2; usage; exit 2 ;;
  esac
done

if [ ${#TARGETS[@]} -eq 0 ]; then
  TARGETS=("$HOME/.gemini/skills" "$HOME/.agents/skills" "$HOME/.codex/skills")
fi

installed=0
skipped=0
for target in "${TARGETS[@]}"; do
  mkdir -p "$target"
  for skill_dir in "$REPO_ROOT"/plugins/*/skills/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    name="$(basename "$skill_dir")"
    dest="$target/$name"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      if [ "$FORCE" -eq 1 ]; then
        rm -rf "$dest"
      else
        echo "  ~ bỏ qua (đã tồn tại): $dest"
        skipped=$((skipped + 1))
        continue
      fi
    fi
    if [ "$MODE" = "copy" ]; then
      cp -R "${skill_dir%/}" "$dest"
    else
      ln -s "${skill_dir%/}" "$dest"
    fi
    echo "  + $dest"
    installed=$((installed + 1))
  done
done

echo "Xong: $installed skill đã cài, $skipped bỏ qua (dùng --force để ghi đè)."
