# ⚡ Universal Agent Skills Catalog

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent Skills Standard](https://img.shields.io/badge/Standard-Agent%20Skills-brightgreen.svg)](https://agentskills.org)
[![Compatible With](https://img.shields.io/badge/Compatible%20With-Claude%20Code%20|%20Antigravity%20|%20Gemini%20|%20Codex%20|%20Cursor-orange.svg)](#-platform-compatibility)
[![Total Skills](https://img.shields.io/badge/Skills%20Catalog-16%20Production%20Skills-purple.svg)](#-skills-catalog)

> **A curated, production-grade monorepo of 16 modular AI Agent Skills & Plugins crafted by [@nchungdev](https://github.com/nchungdev).**  
> Built strictly on the open **Agent Skills Standard (`SKILL.md`)**, ready to install, distribute, and execute across any AI coding assistant or autonomous runtime: **Claude Code, Google Antigravity / Gemini CLI, OpenAI Codex, Cursor, Windsurf**, and custom agent frameworks.

---

## 🌟 Core Architectural Principles

* 🔌 **Zero Vendor Lock-in (Universal Interoperability):** Fully adheres to the open `SKILL.md` specification (YAML frontmatter + procedural guidelines + standalone executables). Write once, equip any LLM agent.
* ⚡ **Zero Runtime Bloat:** All core helper scripts are powered by the **Python 3 Standard Library**. Instant execution with zero startup latency and no third-party package dependencies (`pip install`).
* 🛡️ **Zero Secret Leakage (Built-in Redaction):** Hardened with automated pattern-based secret sanitization (`mask_sensitive_data`). Automatically redacts API keys, Bearer tokens, passwords, and private credentials in CLI transcripts, project reports, and shared state files.
* 📦 **1-Command Multi-Agent Installer:** Instant deployment via `./install.sh`. Generates dynamic symlinks into target skill directories across all major AI agent CLIs (`~/.gemini/skills`, `~/.agents/skills`, `~/.codex/skills`) or through the Claude Code Plugin Marketplace.
* 📊 **Uniform `report` Command Across All Skills:** Every single skill features a standard `report` sub-command, rendering clean, real-time Markdown dashboards.
* 🔑 **Interactive `setup` with Masked Input:** Dedicated setup wizards for skills requiring credentials or preferences (`tmdb-catalog`, `media-downloader`, `media-sync`, `media-advisor`), masking secrets while typing and testing live API connectivity.
* 🩺 **0.1s Zero-Config Device Auto-Detection:** Automatically diagnoses host environment (macOS workstation, Linux NAS/Server, or dev machine) without tedious CLI flags.

---

## 🏛️ Skills Catalog (16 Consolidated Skills)

The catalog features **16 production-ready Agent Skills**, consolidated into a clean, non-overlapping suite:

| # | Skill | Superpower & Description | Core Stack / Tooling |
|:---:|---|---|---|
| 1 | **`ffmpeg-toolkit`** | Comprehensive media processing engine: Muxed subtitle extraction from MKV/MP4, zero-token voice activity alignment (VAD), and W3C WebVTT conversion with CSS tag sanitization. Supports local and remote SSH execution. | FFmpeg, FFprobe, VAD Silencedetect, WebVTT |
| 2 | **`tmdb-catalog`** | Cinema & TV knowledge graph: Rich metadata resolution, HD artwork downloader, Kodi/Plex NFO generation, visual 2-column movie cards with local poster thumbnails, season storage tracking (`Local / NAS / Drive`), and universal franchise classification (IP, Auteur, Studio Ghibli). | TMDb API v3, TheTVDB, NFO Generator |
| 3 | **`media-downloader`** | Universal media ingestion pipeline: Torrent census & disk estimation, Prowlarr multi-indexer search, accelerated BitTorrent downloads via Aria2c RPC, and TorBox Debrid Cloud API. Supports local download and remote dispatch to NAS storage. | Aria2c RPC, TorBox API, Prowlarr, MeTube |
| 4 | **`media-sync`** | Media destination dispatcher & library standardizer: Normalizes Plex/TheTVDB directory hierarchies, auto-discovers NAS library targets via SSH, performs parallel high-throughput transfers to NAS (SSH/SFTP) and Google Drive (Rclone), guides account onboarding, and enforces post-sync auto-purging. | Rclone, SSH/SFTP, Rsync, Plex Naming Standard |
| 5 | **`translate-subtitle`** | Two-stage deep neural subtitle translation engine tailored for cinema and anime: Preserves typography tags and timecode integrity while syncing with centralized glossaries (Subtitle Glossary Hub). | LLM Prompting, Typography Parser, Glossary Hub |
| 6 | **`distributed-infra`** | Comprehensive self-hosted infrastructure & distributed compute manager: OpenMediaVault 7 NAS architecture, MergerFS storage pools, Docker Compose media automation, distributed Tdarr transcoding nodes, and ephemeral Cloudflare Tunnel (`cloudflared`) integration. | OMV 7, Docker Compose, MergerFS, Tdarr, Cloudflared |
| 7 | **`project-reporter`** | Multi-conversation orchestrator, context synchronizer, and progress reporter. Eliminates context drift across concurrent chat sessions via a centralized ledger (`.agent/project_status.json`), scrubs secret tokens, and provides project visibility (`report`, `report all`). | SQLite Metadata, Transcript Parser, JSON Ledger |
| 8 | **`system-doctor`** | Autonomous system optimizer & SRE diagnostic engine (CleanMyMac X meets Site Reliability Engineering). Auto-detects device signatures in 0.1s (macOS, Linux Server/NAS, Workstation) to clean OS/developer caches, purge RAM, kill runaway CPU hogs, hunt port conflicts, inspect Docker crashloops, and execute 1-click auto-healing. | SRE Diagnostics, OS Cleaner, Docker Forensics, Inode/RAM |
| 9 | **`media-advisor`** | Zero-API cinema & series recommendation concierge: Reads local Plex/Jellyfin SQLite DB directly in read-only mode to extract authentic watch history, in-progress items, personal ratings, and unwatched library gems. Integrates real-time theatrical releases, OTT streaming drops, and community buzz with anti-seeding sentiment verification. Renders recommendations as 2-column visual cards with local poster thumbnails. | SQLite Read-Only (`mode=ro`), Plex/Jellyfin DB, TMDb Trends, Anti-Seeding Filter |
| 10 | **`film-oracle`** | Truth-seeking cinema auditor & honest film evaluation engine: Multi-source synthesis across Rotten Tomatoes, Metacritic, YouTube/Blog reviewers, and audience pulse to answer 7 critical questions for any film: Worth watching or skip, critic consensus, reviewer takeaways, audience reception, polarizing flaws, buzz lifecycle timing, and demographic matchmaking. | Multi-Source Scraping, RT/Metacritic Consensus, Reviewer Pulse, Lifecycle Timing |
| 11 | **`project-bootstrap`** | Universal AI project scaffolding and cross-agent orchestrator: Generates tailored `AGENTS.md` conventions, scaffolds project-specific skills (`.agents/skills/`), and links them via zero-drift relative symlinks across Claude Code (`CLAUDE.md`), Gemini CLI (`GEMINI.md`), OpenAI Codex (`CODEX.md`), Cursor (`.cursorrules`), and Windsurf (`.windsurfrules`). | Repo Inspection, Single Source of Truth, Cross-Agent Symlinks, Python 3 Stdlib |
| 12 | **`hardsub-extractor`** | Autonomous video hardsub extraction and OCR alignment engine: Uses FFmpeg memory streaming and Gemini Multimodal Vision API to extract high-accuracy Vietnamese subtitles with exact timecodes and exports clean .vi.OCR.srt files. | FFmpeg Memory Streaming, Gemini 3.5 Flash Lite Vision, Timecode Snapping, Spanning Deduplication |
| 13 | **`github-project-workflow`** | Universal GitHub Project v2 lifecycle & task spec workflow engine with anti-rate-limit resilience: Zero-API local spec listing, persistent schema & item caching, 1-point targeted issue queries, offline outbox mutation queue, and unified Markdown status reporting. | GitHub Projects v2, GraphQL, REST Issues, Local-First Spec |
| 14 | **`project-pro`** | Interactive project base architect, 6-Gate task execution harness, Clean Architecture & UDF standardizer (MVI, MVVM, TCA, BLoC, Riverpod, FSD, Hexagonal), SOLID & pragmatic DRY enforcer, famous open-source reference-repo lookup, persistent cross-session codebase map (`.agents/CODEBASE_MAP.md`), zero-dependency secret/OWASP scanner, and Git/AI runtime anti-bypass hooks (`pre-commit`, `commit-msg`, `pre-push`, `PreToolUse`). | Python 3 Stdlib, Clean Arch, 8 Tech Stacks, Secret/OWASP Scanner, Git & Agent Hooks |
| 15 | **`dailylog`** | Long-term memory shared by every agent: automatic session records through hooks at zero model tokens, daily logs, project state, durable knowledge, decision records and a weekly history, with diacritic-insensitive search and secret refusal. | Python 3 Stdlib, Claude Code / Codex / Antigravity Hooks, Markdown |
| 16 | **`cache-idle-guard`** | Universal idle session & prompt cache expiration shield: Monitors session idle time and intercepts user messages when prompt cache expires (Anthropic Claude 5m, Google Gemini 5m/60m), prompting users to run `/compact` or `/clear` to preserve 90% cache read discounts, evade API rate limits, and maintain context hygiene. | Python 3 Stdlib, Claude Code / Antigravity / Codex Hooks, Prompt Cache Shield |

---

## 🎨 Visual Cards & Season Reporting in `tmdb-catalog`

`tmdb-catalog` enforces clean 2-column Markdown tables using locally cached thumbnails (`w185`) to avoid Content Security Policy (CSP) blocking:

### 1. Movie / Series Card
| Poster | Movie Details |
|:---:|---|
| `<img src="/path/to/poster_w185.jpg" width="120" />` | **🎬 The Westward (西行纪) — 2018**<br>⭐ **Rating**: `7.6/10` \| 🎬 **Scale**: 5 Seasons (134 Episodes)<br>🏷️ **IDs**: TMDb `83031` • TheTVDB `371131`<br>🎭 **Genres**: Animation, Action & Adventure, 3D Fantasy<br><br>📖 *Overview: The journey to the West was a conspiracy of heaven...* |

### 2. Season Storage Matrix
| Season Poster | Season Details | Storage Status (Local / NAS / Drive) |
|:---:|---|---|
| `<img src="/path/s1_w185.jpg" width="85" />` | **Season 01** — 2018<br>🎬 **Total**: 16 Episodes (Complete) | 💻 **Local**: `0/16`<br>🏠 **NAS**: `16/16` eps (Complete)<br>☁️ **Drive**: `16/16` eps (Complete) |
| `<img src="/path/s5_w185.jpg" width="85" />` | **Season 05** — 2023 - 2024<br>🎬 **Total**: 64 Episodes (Airing) | 💻 **Local**: `0/64`<br>🏠 **NAS**: `33/64` eps *(downloading)*<br>☁️ **Drive**: `0/64` eps |

*(Note: When the agent is running directly on the NAS, the `Local` row is omitted automatically).*

---

## 🌐 Platform Compatibility

| AI Agent Platform | Discovery Mechanism | Default Target Directory |
|---|---|---|
| **Claude Code** | Marketplace (`/plugin marketplace add`) or local plugin | `${CLAUDE_PLUGIN_ROOT}/skills/` |
| **Google Antigravity CLI** | Automated symlink script | `~/.agents/skills/` or `~/.gemini/antigravity-cli/skills/` |
| **Gemini CLI** | Automated symlink script | `~/.gemini/skills/` |
| **OpenAI Codex CLI** | Automated symlink script | `~/.codex/skills/` |
| **Cursor / Windsurf / Custom Agents** | Project workspace mount or global rules | `./.agents/skills/` or `~/.cursor/rules/` |

---

## 🚀 Installation

### Option 1: Multi-Agent CLI Installer (Recommended)

Clone the repository and run the automated installer:

```bash
# 1. Clone the repository
git clone https://github.com/nchungdev/agent-skills.git ~/.agent-skills
cd ~/.agent-skills

# 2. Install all 8 skills across ALL supported CLIs (Gemini, Antigravity, Codex)
./install.sh all --force

# Or install for a specific agent:
./install.sh gemini --force       # Gemini CLI (~/.gemini/skills/)
./install.sh antigravity --force  # Antigravity CLI (~/.agents/skills/)
./install.sh codex --force        # OpenAI Codex CLI (~/.codex/skills/)
```

---

### Option 2: Claude Code Plugin Marketplace

```bash
# Register the marketplace in Claude Code
/plugin marketplace add nchungdev/agent-skills

# Install individual plugins as needed
/plugin install github-project-workflow@nchungdev-skills
/plugin install system-doctor@nchungdev-skills
/plugin install tmdb-catalog@nchungdev-skills
/plugin install media-downloader@nchungdev-skills
/plugin install ffmpeg-toolkit@nchungdev-skills
```

---

### Option 3: Per-Project / Workspace Embedding

To attach specific skills directly to a standalone project:

```bash
mkdir -p .agent/skills
ln -s ~/.agent-skills/plugins/github-project-workflow/skills/github-project-workflow .agent/skills/
```

---

## 📐 Monorepo Architecture

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json            # Claude Code Marketplace Manifest (16 plugins)
├── install.sh                      # Universal multi-agent installation script
├── plugins/
│   ├── cache-idle-guard/           # Universal idle session & prompt cache expiration shield
│   ├── dailylog/                   # Long-term memory shared by every agent
│   ├── project-pro/                # Interactive Clean Arch, 6-Gate harness & DevSecOps hooks
│   ├── github-project-workflow/    # GitHub Project v2 lifecycle, spec workflow & rate-limit shield
│   ├── project-bootstrap/          # Cross-agent project bootstrapper & AGENTS.md conventions
│   ├── hardsub-extractor/          # Video hardsub OCR & subtitle synchronizer via Gemini Vision
│   ├── ffmpeg-toolkit/             # Muxed sub extractor, VAD aligner, WebVTT converter
│   ├── tmdb-catalog/               # TMDb lookup, cards, season matrix, franchise taxonomy
│   ├── media-downloader/           # Ingestion: Aria2 RPC, TorBox, Prowlarr, census
│   ├── media-sync/                 # Dispatcher: Plex naming, Rclone, NAS sync, auto-purge
│   ├── translate-subtitle/         # Two-stage AI translation & Subtitle Glossary Hub
│   ├── distributed-infra/          # OMV 7 NAS, Docker, Tdarr cluster, Cloudflared tunnel
│   ├── project-reporter/           # Multi-conversation orchestrator & ledger
│   ├── system-doctor/              # CleanMyMac + SRE Homelab diagnostic & auto-heal
│   ├── media-advisor/              # Zero-API cinema concierge & streaming recommendations
│   └── film-oracle/                # Truth-seeking film auditor & cinema reviews
└── README.md
```

---

## 📄 License

Distributed under the [MIT License](LICENSE) — © 2026 **Chung Nguyen Hoai ([@nchungdev](https://github.com/nchungdev))**.  
Free to use, customize, and distribute for the entire AI developer and agentic engineering community.
