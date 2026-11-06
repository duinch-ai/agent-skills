#!/usr/bin/env bash
# Universal Multi-Agent Installer for `project-pro`
# Supports: Antigravity (IDE + CLI), GitHub Copilot, Claude Code, OpenAI Codex,
#           Gemini CLI, Cursor, OpenCode, Workspace (.agents/skills), and prompt export.
set -euo pipefail

SKILL_NAME="project-pro"
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="symlink"
FORCE=0
ACTION="install"
WORKSPACE_DIR=""
EXPORT_FILE=""
TARGETS=()

usage() {
  cat <<'USAGE'
Usage: ./install.sh [targets...] [options]

Targets:
  all             Install to Antigravity, GitHub Copilot, .agents, Gemini CLI, Claude Code, Codex (+ Cursor/OpenCode if present) [DEFAULT]
  agy             Google Antigravity IDE (~/.gemini/config/skills) + .agents (~/.agents/skills)
  copilot         GitHub Copilot personal skills (~/.copilot/skills)
  claude          Claude Code (~/.claude/skills)
  codex           OpenAI Codex (~/.codex/skills)
  gemini          Gemini CLI (~/.gemini/skills)
  cursor          Cursor (~/.cursor/skills)
  opencode        OpenCode (~/.config/opencode/skills)

Options:
  --workspace <dir>      Install into a specific project (<dir>/.agents/skills/project-pro)
  --export-prompt <out>  Export a single compiled Markdown prompt for DeepSeek / Chat / Aider / Roo / Cline
  --copy                 Copy files instead of creating symlinks
  --force                Overwrite existing installation
  --uninstall            Remove installed skill from selected targets
  --status               Check installation status across all AI agents
  -h, --help             Show this help message
USAGE
}

add_target() {
  local dir="$1"
  for existing in "${TARGETS[@]:-}"; do
    [ "$existing" = "$dir" ] && return 0
  done
  TARGETS+=("$dir")
}

while [ $# -gt 0 ]; do
  case "$1" in
    all)
      add_target "$HOME/.gemini/config/skills"
      add_target "$HOME/.agents/skills"
      add_target "$HOME/.copilot/skills"
      add_target "$HOME/.gemini/skills"
      add_target "$HOME/.claude/skills"
      add_target "$HOME/.codex/skills"
      [ -d "$HOME/.cursor" ] && add_target "$HOME/.cursor/skills"
      [ -d "$HOME/.config/opencode" ] && add_target "$HOME/.config/opencode/skills"
      ;;
    agy|antigravity)
      add_target "$HOME/.gemini/config/skills"
      add_target "$HOME/.agents/skills"
      ;;
    copilot)
      add_target "$HOME/.copilot/skills"
      ;;
    claude)
      add_target "$HOME/.claude/skills"
      ;;
    codex)
      add_target "$HOME/.codex/skills"
      ;;
    gemini)
      add_target "$HOME/.gemini/skills"
      ;;
    cursor)
      add_target "$HOME/.cursor/skills"
      ;;
    opencode)
      add_target "$HOME/.config/opencode/skills"
      ;;
    --workspace)
      shift
      WORKSPACE_DIR="${1:?Missing directory for --workspace}"
      add_target "$WORKSPACE_DIR/.agents/skills"
      ;;
    --export-prompt)
      shift
      EXPORT_FILE="${1:?Missing output path for --export-prompt}"
      ACTION="export"
      ;;
    --copy)
      MODE="copy"
      ;;
    --force)
      FORCE=1
      ;;
    --uninstall)
      ACTION="uninstall"
      ;;
    --status)
      ACTION="status"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option or target: $1" >&2
      usage
      exit 2
      ;;
  esac
  shift
done

if [ "$ACTION" = "export" ]; then
  mkdir -p "$(dirname "$EXPORT_FILE")"
  {
    cat "$SKILL_ROOT/SKILL.md"
    printf "\n\n---\n\n"
    cat "$SKILL_ROOT/references/execution-harness.md"
    printf "\n\n---\n\n"
    cat "$SKILL_ROOT/references/agentic-patterns.md"
    printf "\n\n---\n\n"
    cat "$SKILL_ROOT/references/security-and-hooks.md"
    printf "\n\n---\n\n"
    cat "$SKILL_ROOT/references/clean-arch-and-solid.md"
    printf "\n\n---\n\n"
    cat "$SKILL_ROOT/references/presentation-patterns.md"
    printf "\n\n---\n\n"
    cat "$SKILL_ROOT/references/agent-harness-spec.md"
  } > "$EXPORT_FILE"
  echo "[OK] Exported standalone system rule/prompt (for DeepSeek / Aider / Cline / API) -> $EXPORT_FILE"
  exit 0
fi

if [ ${#TARGETS[@]} -eq 0 ]; then
  add_target "$HOME/.gemini/config/skills"
  add_target "$HOME/.agents/skills"
  add_target "$HOME/.copilot/skills"
  add_target "$HOME/.gemini/skills"
  add_target "$HOME/.claude/skills"
  add_target "$HOME/.codex/skills"
  [ -d "$HOME/.cursor" ] && add_target "$HOME/.cursor/skills"
  [ -d "$HOME/.config/opencode" ] && add_target "$HOME/.config/opencode/skills"
fi

if [ "$ACTION" = "status" ]; then
  echo "=== Installation Status for $SKILL_NAME ==="
  for base in "${TARGETS[@]}"; do
    dest="$base/$SKILL_NAME"
    if [ -L "$dest" ]; then
      echo "  [SYMLINK] $dest -> $(readlink "$dest")"
    elif [ -d "$dest" ]; then
      echo "  [COPIED]  $dest"
    else
      echo "  [MISSING] $dest"
    fi
  done
  exit 0
fi

if [ "$ACTION" = "uninstall" ]; then
  for base in "${TARGETS[@]}"; do
    dest="$base/$SKILL_NAME"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      rm -rf "$dest"
      echo "  [-] Removed: $dest"
    fi
  done
  exit 0
fi

installed=0
skipped=0
for base in "${TARGETS[@]}"; do
  mkdir -p "$base"
  dest="$base/$SKILL_NAME"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ "$FORCE" -eq 1 ]; then
      rm -rf "$dest"
    else
      echo "  [~] Skipped (already exists, use --force to overwrite): $dest"
      skipped=$((skipped + 1))
      continue
    fi
  fi
  if [ "$MODE" = "copy" ]; then
    cp -R "$SKILL_ROOT" "$dest"
  else
    ln -s "$SKILL_ROOT" "$dest"
  fi
  echo "  [+] Installed ($MODE): $dest"
  installed=$((installed + 1))
done

echo "Done: $installed target(s) installed, $skipped skipped."
