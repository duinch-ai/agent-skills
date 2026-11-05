#!/usr/bin/env bash
# Installer for the dailylog skill: Claude Code, Codex, Antigravity, Gemini CLI, Cursor, OpenCode.
set -euo pipefail

SKILL_NAME="dailylog"
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SKILL_ROOT/scripts/dailylog.py"
MODE="symlink"; FORCE=0; ACTION="install"; HOOKS=0; WORKSPACE=""; HOOK_ARGS=(); TARGETS=()

usage() {
  cat <<'USAGE'
Usage: ./install.sh [targets...] [options]

Targets (default: all):
  all       Every agent below whose config folder exists on this machine
  claude    ~/.claude/skills
  codex     ~/.codex/skills
  agy       ~/.gemini/config/skills and ~/.agents/skills
  gemini    ~/.gemini/skills
  cursor    ~/.cursor/skills
  opencode  ~/.config/opencode/skills

Options:
  --workspace <dir>  Install for one project: skill, memory/, AGENTS.md block, project hooks
  --hooks            Also record every session automatically (global scope)
  --context-off      With hooks: inject nothing at session start
  --capture-meta     With hooks: leave prompt and reply text out of session records
  --copy             Copy instead of symlink
  --force            Replace an existing real folder at the destination
  --uninstall        Remove the skill, the command and dailylog's hooks
  --status           Show where it is installed
USAGE
}

add_all() {
  [ -d "$HOME/.claude" ] && TARGETS+=("$HOME/.claude/skills")
  [ -d "$HOME/.codex" ] && TARGETS+=("$HOME/.codex/skills")
  [ -d "$HOME/.gemini/config" ] && TARGETS+=("$HOME/.gemini/config/skills" "$HOME/.agents/skills")
  [ -d "$HOME/.gemini" ] && TARGETS+=("$HOME/.gemini/skills")
  [ -d "$HOME/.cursor" ] && TARGETS+=("$HOME/.cursor/skills")
  [ -d "$HOME/.config/opencode" ] && TARGETS+=("$HOME/.config/opencode/skills")
  return 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    all) add_all ;;
    claude) TARGETS+=("$HOME/.claude/skills") ;;
    codex) TARGETS+=("$HOME/.codex/skills") ;;
    agy) TARGETS+=("$HOME/.gemini/config/skills" "$HOME/.agents/skills") ;;
    gemini) TARGETS+=("$HOME/.gemini/skills") ;;
    cursor) TARGETS+=("$HOME/.cursor/skills") ;;
    opencode) TARGETS+=("$HOME/.config/opencode/skills") ;;
    --workspace) shift; WORKSPACE="${1:?--workspace needs a folder}" ;;
    --hooks) HOOKS=1 ;;
    --context-off) HOOK_ARGS+=(--context off) ;;
    --capture-meta) HOOK_ARGS+=(--capture meta) ;;
    --copy) MODE="copy" ;;
    --force) FORCE=1 ;;
    --uninstall) ACTION="uninstall" ;;
    --status) ACTION="status" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

if [ -n "$WORKSPACE" ]; then
  WORKSPACE="$(cd "$WORKSPACE" && pwd)"
  TARGETS=("$WORKSPACE/.agents/skills")
elif [ ${#TARGETS[@]} -eq 0 ]; then
  add_all
fi

place_skill() {
  local dest="$1/$SKILL_NAME"
  mkdir -p "$1"
  if [ -L "$dest" ]; then
    rm "$dest"
  elif [ -e "$dest" ]; then
    if [ "$FORCE" -ne 1 ]; then
      echo "  ~ skipped, a real folder is there (use --force): $dest"
      return 0
    fi
    rm -rf "$dest"
  fi
  if [ "$MODE" = "copy" ]; then cp -R "$SKILL_ROOT" "$dest"; else ln -s "$SKILL_ROOT" "$dest"; fi
  echo "  + $dest"
}

case "$ACTION" in
  status)
    for target in "${TARGETS[@]:-}"; do
      if [ -e "$target/$SKILL_NAME/SKILL.md" ]; then echo "  installed  $target/$SKILL_NAME"; else echo "  missing    $target/$SKILL_NAME"; fi
    done
    command -v dailylog >/dev/null 2>&1 && echo "  command    $(command -v dailylog)" || echo "  command    not on PATH"
    ;;
  uninstall)
    for target in "${TARGETS[@]:-}"; do
      dest="$target/$SKILL_NAME"
      if [ -L "$dest" ] || [ -e "$dest" ]; then rm -rf "$dest"; echo "  - $dest"; fi
    done
    if [ -n "$WORKSPACE" ]; then
      python3 "$SCRIPT" install-hooks --scope project --root "$WORKSPACE" --remove
      python3 "$SCRIPT" wire --root "$WORKSPACE" --remove
    else
      python3 "$SCRIPT" install-hooks --remove
      [ -L "$HOME/.local/bin/dailylog" ] && rm "$HOME/.local/bin/dailylog" && echo "  - $HOME/.local/bin/dailylog"
    fi
    echo "memory/ folders were left in place."
    ;;
  install)
    for target in "${TARGETS[@]:-}"; do place_skill "$target"; done
    chmod +x "$SCRIPT"
    if [ -n "$WORKSPACE" ]; then
      python3 "$SCRIPT" init --root "$WORKSPACE" --wire
      python3 "$SCRIPT" install-hooks --scope project --root "$WORKSPACE" "${HOOK_ARGS[@]+"${HOOK_ARGS[@]}"}"
    else
      mkdir -p "$HOME/.local/bin"
      ln -sf "$SCRIPT" "$HOME/.local/bin/dailylog"
      echo "  + $HOME/.local/bin/dailylog"
      if [ "$HOOKS" -eq 1 ]; then
        python3 "$SCRIPT" install-hooks "${HOOK_ARGS[@]+"${HOOK_ARGS[@]}"}"
      else
        echo "Skill installed. To record every session automatically, run again with --hooks."
      fi
    fi
    ;;
esac
