---
name: cache-idle-guard
description: >-
  Monitors session idle time and intercepts messages when prompt cache has expired (Anthropic 5m, Gemini 5m/60m).
  Prompts users to /compact or /clear before sending messages to preserve prompt cache read discounts (up to 90%),
  prevent cold-start latency, avoid API rate-limit quota exhaustion, and eliminate context drift.
  Use when user asks about prompt cache, cache expiration, idle sessions, or configuring /compact reminders.
---

# Cache Idle Guard

Coding agents (Claude Code, Antigravity, Codex) retain full conversation context through prompt caching:
* **Anthropic Claude**: Prompt Cache TTL is **5 minutes** (refreshed on cache hits).
* **Google Gemini (Antigravity)**: Context Cache TTL is **5 minutes** (implicit/default) or configured session duration.

When a session idles past the TTL, subsequent user prompts trigger full context rewrites at full price/quota and high latency (cold starts).

`cache-idle-guard` intercepts user prompts at the lifecycle hook level **before tokens are transmitted**:
1. Checks elapsed time since the previous agent response (Stop hook).
2. If idle duration exceeds `CACHE_IDLE_MINUTES` (default: 60m, or 5m for strict cache matching), it blocks the prompt once with an informative message.
3. Guides the user to run `/compact` (preserve task flow with compressed context) or `/clear` (start fresh).
4. If the user decides to proceed anyway, sending the exact same message again passes through immediately (single-interception policy).

## Quick Start

### Check Status
```bash
python3 <this-skill>/scripts/cache-idle-guard.py status
```

### Install Hooks Globally
```bash
./install.sh --hooks --minutes 5
```
Automatically registers hooks into:
* **Claude Code**: `~/.claude/settings.json` (`UserPromptSubmit` & `Stop`)
* **Antigravity**: `~/.gemini/config/hooks.json` (`PreInvocation` & `Stop`)
* **Codex**: `~/.codex/hooks.json` (`UserPromptSubmit` & `Stop`)

### Uninstall Hooks
```bash
./install.sh --uninstall
```

## Threshold Configuration

Set the environment variable `CACHE_IDLE_MINUTES`:
* **`CACHE_IDLE_MINUTES=5`**: Strict cache alignment. Blocks as soon as prompt cache expires.
* **`CACHE_IDLE_MINUTES=30` / `60`**: Session hygiene mode. Blocks when stepping away for lunch or leaving a session overnight.
