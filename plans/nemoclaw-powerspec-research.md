# Project NemoClaw — PowerSpec Prototype Research Report

**Date:** 2026-04-12  
**Author:** Researcher Agent  
**Status:** Complete — ready for Planner

---

## 1. NemoClaw on Windows / WSL2 — Installation Path

### Key Finding: NemoClaw Does NOT Run Natively on Windows

NemoClaw relies on Linux kernel features (Landlock, seccomp, network namespaces) that do not exist on Windows. **WSL2 with Ubuntu 22.04+ is the only supported path on Windows.**

Official NVIDIA status from the GitHub README:

| OS | Container Runtime | Status | Notes |
|----|------------------|--------|-------|
| Linux | Docker | **Tested** | Primary path |
| macOS (Apple Silicon) | Colima, Docker Desktop | Tested with limitations | |
| **Windows WSL2** | **Docker Desktop (WSL backend)** | **Tested with limitations** | Requires WSL2 + Docker Desktop backend |

### What NemoClaw Actually Is

NemoClaw is **not** a standalone agent framework. It is a **security/sandboxing wrapper** around OpenClaw that adds:
- **OpenShell runtime** — kernel-level sandbox (Landlock + seccomp + netns)
- **Nemotron models** — NVIDIA's local inference models
- **Privacy Router** — routes inference traffic (local vs cloud) with credentials kept on host
- **Policy-based security** — egress control, filesystem isolation, operator approval flows
- **Guided onboarding wizard** — single-command install (`curl -fsSL https://nvidia.com/nemoclaw.sh | bash`)

**Critical:** NemoClaw creates a **fresh OpenClaw instance** inside the sandbox during onboarding. It does NOT migrate an existing OpenClaw setup. Eric's current Jarvis config would need manual migration into the sandbox.

### PowerSpec Readiness Assessment

| Requirement | Minimum | PowerSpec Has | Status |
|------------|---------|---------------|--------|
| CPU | 4 vCPU | 24 cores / 32 threads (i9-14900KF) | ✅ Exceeds |
| RAM | 8 GB (16 GB recommended) | 128 GB DDR5 | ✅ Exceeds |
| Disk | 20 GB free (40 GB recommended) | 1608 GB free (C:) | ✅ Exceeds |
| Node.js | 22.16+ | v24.14.1 (Windows native) | ✅ Meets |
| Docker | 24.0+ | Docker Desktop 29.3.1 | ✅ Meets |
| WSL2 | Required | docker-desktop distro present | ⚠️ Needs Ubuntu-22.04 |
| GPU | Optional but recommended | RTX 5080 16GB, CUDA 13.2 | ✅ Excellent |

### WSL2 Installation Steps Required

1. **Install Ubuntu-22.04 WSL2 distro** (PowerSpec only has `docker-desktop` distro today)
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```
2. **Enable systemd** in `/etc/wsl.conf` (required for NemoClaw)
3. **Configure Docker Desktop WSL Integration** — enable for the new Ubuntu distro
4. **NVIDIA GPU passthrough** — install nvidia-container-toolkit in WSL2 (do NOT install Linux NVIDIA driver — use Windows driver only)
5. **Run NemoClaw installer** from within WSL2 Ubuntu shell

### Known Issues (WSL2-Specific)

- **`nemoclaw onboard` was reported broken on WSL2 at GTC launch** (March 2026) — Reddit reports workarounds exist and NVIDIA has iterated since
- **GPU detection can be flaky** — nvidia-smi must work inside WSL2 before proceeding
- **Cgroup v2 errors** — current OpenShell releases handle this automatically (fixed in recent versions)
- **Port 18789 conflict** — NemoClaw gateway defaults to port 18789, same as Mac OpenClaw gateway. If both are on Tailscale, must configure different ports
- **Memory limit** — WSL2 defaults to using 50% of host RAM. For 128GB system, may want to cap via `.wslconfig`

---

## 2. Current Jarvis Config Inventory

### 2.1 Agent Architecture (from openclaw.json)

**8 agents configured:**

| Agent ID | Name | Model (Primary) | Fallbacks | Role |
|----------|------|-----------------|-----------|------|
| main | Jarvis | claude-opus-4-6 | grok-4.20, claude-sonnet-4-6 | Orchestrator |
| researcher | Researcher | claude-opus-4-6 | grok-4.20, claude-sonnet-4-6 | Research tasks |
| planner | Planner | claude-opus-4-6 | grok-4.20, claude-sonnet-4-6 | Plan authoring |
| coder | Coder | claude-opus-4-6 | claude-sonnet-4-6 | Code implementation |
| quality | Quality | grok-4.20 | claude-opus-4-6, claude-sonnet-4-6 | QA gate |
| monitor | Monitor | claude-sonnet-4-6 | grok-4.20 | System monitoring |
| auditor | External Auditor | grok-4.20 | claude-sonnet-4-6 | Security/compliance |
| conductor | Conductor | claude-sonnet-4-6 | grok-4.20 | Task orchestration |

**Agent defaults:**
- Workspace: `/Users/ericbrown/.openclaw/workspace` (Mac path — would change)
- Context pruning: cache-ttl, 1h
- Compaction: safeguard mode
- Timeout: 180s per agent
- Heartbeat: every 30m
- Max concurrent: 6 agents
- Subagent limits: max 8 concurrent, depth 3, 5 children/agent, 60min archive, 1200s timeout

### 2.2 Model Providers

| Provider | Base URL | Models | Notes |
|----------|----------|--------|-------|
| Anthropic | (default) | claude-opus-4-6, claude-sonnet-4-6 | API key auth |
| OpenAI | (default) | gpt-5.1-codex | API key auth |
| xAI | api.x.ai/v1 | grok-4, grok-4.20 | API key auth |
| ollama-local | http://100.81.21.114:11434/v1 | qwen3.5:35b-a3b | **Already on PowerSpec!** |
| ollama | http://100.81.21.114:11434 | glm-4.7-flash, qwen3.5:35b-a3b | **Already on PowerSpec!** |

**Key insight:** Ollama is already running on PowerSpec at port 11434. NemoClaw can route to this directly.

### 2.3 Channels

- **Telegram** — primary channel, bot token configured, streaming partial mode
- Exec approvals enabled (approver: 5387843769 = Eric)
- DM policy: pairing, group policy: allowlist

### 2.4 Gateway

- Port: 18789
- Mode: local, bind: LAN
- Auth: token-based with Tailscale allowed
- Allowed origins include both Mac (100.101.203.113) and PowerSpec (100.81.21.114) IPs
- Tailscale mode: off (but allowTailscale: true for auth)

### 2.5 Plugins

Active plugins: device-pair, memory-core, phone-control, talk-voice, telegram, voice-call, browser, anthropic, xai, openai, brave

### 2.6 Skills (Brave Search)

- API key configured in plugins.entries.brave
- Google Places API key in skills.entries.goplaces

### 2.7 TTS (ElevenLabs)

- Provider: elevenlabs
- API key configured in talk.providers.elevenlabs

---

## 3. Skills Portability Matrix

### 30 Skills Found in Workspace

| Skill | Category | Windows/NemoClaw | Mac-Only | Notes |
|-------|----------|:---:|:---:|-------|
| **afrexai-contract-analyzer** | Analysis | ✅ | | Pure analysis, no OS deps |
| **ai-legal-assistant** | Analysis | ✅ | | Pure analysis |
| **auditor** | Pipeline | ✅ | | Agent pipeline role |
| **autoClaw** | Pipeline | ✅ | | Self-evolving loop |
| **blogwatcher** | Monitoring | ✅ | | Web-based |
| **blucli** | Hardware | | ❌ | BluOS speakers — Mac LAN-specific |
| **cohesity-domain** | Knowledge | ✅ | | Pure knowledge |
| **competitive-intel** | Research | ✅ | | Web search-based |
| **earnings-analyzer** | Finance | ⚠️ | | Needs gog CLI (Google) — may need reconfiguring |
| **financial-report-gen** | Finance | ⚠️ | | Depends on gog, email delivery |
| **firecrawl** | Scraping | ✅ | | Already configured for PowerSpec |
| **gog** | Google | ⚠️ | | Google Workspace CLI — needs OAuth reconfig |
| **google-oauth-reauth** | Auth | | ❌ | Mac-specific OAuth flow |
| **librarian** | Pipeline | ✅ | | Knowledge manager |
| **linkedin-carousel** | Social | ✅ | | Content generation |
| **mc-snapshot** | Dashboard | ⚠️ | | Mission Control — needs URL reconfiguration |
| **monitor** | System | ⚠️ | | System sweep — Mac-specific paths need updating |
| **peekaboo** | macOS UI | | ❌ | macOS-only (AppleScript/Accessibility) |
| **project-dynamo** | Analysis | ✅ | | Pure analysis/knowledge |
| **ragflow-search** | Search | ✅ | | Points to PowerSpec already |
| **railway-deployment** | DevOps | ✅ | | Docker/Railway — portable |
| **remote-coder** | Compute | ⚠️ | | Routes to PowerSpec — circular if running ON PowerSpec |
| **salesforce-analytics** | CRM | ✅ | | API-based |
| **slack-teams-hub** | Messaging | ✅ | | API-based |
| **snowflake-sql** | Data | ✅ | | API-based |
| **tailscale-troubleshooting** | Network | | ❌ | Mac-specific (App Store version) |
| **tax-automation** | Finance | ⚠️ | | Depends on Google Sheets/Gmail |
| **workday-analytics** | HR | ✅ | | API-based |

### Summary

| Category | Count |
|----------|-------|
| ✅ Fully portable | 19 |
| ⚠️ Needs reconfiguration | 7 |
| ❌ Mac-only (won't migrate) | 4 |

---

## 4. Network Topology for PowerSpec NemoClaw

### Current Architecture

```
┌──────────────────────────────────────────────────┐
│  MacBook Pro (100.101.203.113)                   │
│  ├── OpenClaw Gateway :18789                     │
│  ├── Jarvis (main agent) — Telegram bot          │
│  ├── Mission Control Frontend :3000              │
│  ├── Mission Control Backend                     │
│  └── 11 LaunchAgent daemons                      │
│       (batteryguard, caffeinate, gateway          │
│        watchdog, heartbeat, librarian,            │
│        logrotation, obsidian sync, selfheal,      │
│        session monitor, tailscale monitor,         │
│        weekly security)                           │
└───────────────────┬──────────────────────────────┘
                    │ Tailscale (100.x.x.x)
┌───────────────────┴──────────────────────────────┐
│  PowerSpec PC (100.81.21.114)                    │
│  ├── Docker Desktop + WSL2                       │
│  ├── FinancialReportApp (:8000-8001, :3001)      │
│  ├── ContractAnalyzer (:5432, :6379, :9000-9001) │
│  ├── Ollama :11434 (qwen3.5, glm-4.7-flash)     │
│  └── SSH via Tailscale                           │
└──────────────────────────────────────────────────┘
```

### Proposed NemoClaw Architecture

```
┌──────────────────────────────────────────────────┐
│  MacBook Pro (100.101.203.113)                   │
│  ├── OpenClaw Gateway :18789 (EXISTING — keep)   │
│  ├── Jarvis main agent — Telegram bot            │
│  ├── Mission Control :3000                       │
│  └── LaunchAgent daemons (Mac-specific)          │
└───────────────────┬──────────────────────────────┘
                    │ Tailscale
┌───────────────────┴──────────────────────────────┐
│  PowerSpec PC (100.81.21.114)                    │
│  ├── WSL2 Ubuntu-22.04                           │
│  │   └── NemoClaw Sandbox                        │
│  │       ├── OpenShell Gateway :18790 (DIFF PORT)│
│  │       ├── OpenClaw instance (sandboxed)       │
│  │       ├── inference.local → routes to:        │
│  │       │   ├── Anthropic API (cloud)           │
│  │       │   ├── Ollama :11434 (local)           │
│  │       │   └── NVIDIA Endpoints (cloud)        │
│  │       └── Landlock + seccomp + netns          │
│  ├── Docker Desktop (existing containers)        │
│  │   ├── FinancialReportApp                      │
│  │   ├── ContractAnalyzer                        │
│  │   └── (NemoClaw uses Docker too)              │
│  ├── Ollama :11434 (shared)                      │
│  └── NVIDIA RTX 5080 (GPU passthrough to WSL2)  │
└──────────────────────────────────────────────────┘
```

### Key Network Decisions

1. **Port conflict:** Mac OpenClaw gateway = :18789, NemoClaw default = :18789. Must configure NemoClaw to use :18790 or another port
2. **Telegram bot:** Only ONE OpenClaw instance can own the Telegram bot token at a time. Options:
   - **Option A:** Mac keeps Telegram, PowerSpec NemoClaw uses TUI/CLI only (prototype mode)
   - **Option B:** Create a second Telegram bot for NemoClaw testing
   - **Option C:** Migrate Telegram entirely to NemoClaw (not recommended for prototype)
3. **Ollama sharing:** NemoClaw inside WSL2 can access host Ollama at `localhost:11434` (WSL2 shares localhost with Windows). Already tested/working path.
4. **Mission Control access:** NemoClaw sandbox can reach Mac MC at `http://100.101.203.113:3000` via Tailscale (already configured in gateway allowedOrigins)
5. **Inference routing:** NemoClaw's Privacy Router intercepts all inference traffic — the sandbox agent talks to `inference.local`, which the host routes to configured providers. API keys stay on the host (outside sandbox).

---

## 5. Credentials / API Keys Inventory

### Keys That Would Need Configuration on PowerSpec NemoClaw

| Credential | Current Location | NemoClaw Config Method | Notes |
|-----------|-----------------|----------------------|-------|
| **Anthropic API Key** | openclaw.json auth.profiles | `nemoclaw onboard` wizard (provider selection) | Host-side, not in sandbox |
| **OpenAI API Key** | openclaw.json auth.profiles | `nemoclaw onboard` or env var | Host-side |
| **xAI API Key** | openclaw.json auth.profiles | OpenAI-compatible endpoint config | Custom provider URL |
| **Telegram Bot Token** | openclaw.json channels.telegram | Manual config inside sandbox | ⚠️ Can only be active on ONE instance |
| **ElevenLabs API Key** | openclaw.json talk.providers | Manual config inside sandbox | TTS for voice |
| **Brave Search API Key** | openclaw.json plugins.entries.brave | Manual config inside sandbox | Web search |
| **Google Places API Key** | openclaw.json skills.entries.goplaces | Manual config inside sandbox | Place lookups |
| **NVIDIA API Key** | Not currently configured | Required for `nemoclaw onboard` | NEW — needed for NIM endpoints at build.nvidia.com |
| **Google OAuth (gog CLI)** | Mac-local OAuth tokens | Complex — needs OAuth flow on Windows | ⚠️ Most complex migration |
| **GitHub (gh CLI)** | PowerSpec already has gh authenticated as ericfbrown1-boop | Already present | ✅ |
| **Dropbox tokens** | workspace scripts | Environment variable | Portable |
| **1Password** | Mac-local tmux session | Would need separate setup on Windows | Complex |

### NemoClaw-Specific: NVIDIA API Key

NemoClaw requires an **NVIDIA API Key** from [build.nvidia.com](https://build.nvidia.com) for:
- Default inference routing to NVIDIA Endpoints (Nemotron models)
- NIM container management (experimental, if using local NIM)
- Model catalog validation

Eric will need to create/obtain this key before running `nemoclaw onboard`.

---

## 6. Cron Jobs & Scheduled Tasks

### OpenClaw Cron Jobs (18 active)

| Cron Job | Agent | Frequency | Mac-Dependent? | NemoClaw Migration |
|----------|-------|-----------|:-:|---|
| Monitor Sweep | monitor | every 3h | ⚠️ Partial | System paths need updating |
| Cron Delivery Self-Heal | main | every 30m | ❌ No | Portable |
| Auth Health Check | monitor | every 4h | ⚠️ Yes | Depends on gog CLI |
| Task Stall Respawner | monitor | every 2h | ❌ No | Portable |
| clawdbot-data-refresh | main | daily midnight | ❌ No | Portable |
| Daily OpenClaw Doctor | monitor | 5:00 AM | ⚠️ Partial | openclaw doctor paths |
| Daily Smoke Test | monitor | 5:30 AM | ⚠️ Partial | Needs test reconfiguration |
| Daily OpenClaw Auto-Update | main | 5:45 AM | ❌ No | Portable |
| Daily Tax Email Scan | main | 5:45 AM | ⚠️ Yes | Depends on gog/Gmail |
| Daily Security Scan | main | 5:50 AM | ⚠️ Yes | Mac-specific security scan |
| Stock Monitor | monitor | 6:00 AM | ❌ No | Portable (web search) |
| Daily 6 AM AI Productivity | main | 6:00 AM | ⚠️ Partial | Email delivery needs gog |
| Daily Subscription Monitor | main | 6:10 AM | ⚠️ Partial | Email-dependent |
| Weekly Competitor Analysis | researcher | Mon 7 AM | ❌ No | Portable |
| Weekly Claude Best Practices | auditor | Mon 7 AM | ❌ No | Portable |
| Anthropic Ecosystem Daily | monitor | 8:00 AM | ❌ No | Portable |
| Daily Vibe Coding Security | auditor | 8:00 AM | ❌ No | Portable |
| Weekly Background Infra | main | Mon 9 AM | ⚠️ Partial | Infrastructure-dependent |

### macOS LaunchAgent Daemons (11 active)

These are Mac-only and would NOT migrate to NemoClaw:

| Daemon | Purpose | NemoClaw Equivalent |
|--------|---------|-------------------|
| batteryguard | Battery monitoring | N/A (desktop PC) |
| caffeinate | Prevent sleep | N/A (always-on PC) |
| gatewaywatchdog | Gateway health | NemoClaw manages its own gateway |
| heartbeat | Periodic check-in | OpenClaw cron can replace |
| librarian.weekly | Knowledge indexing | OpenClaw cron can replace |
| logrotation | Log management | Linux logrotate |
| obsidian.sync | Obsidian vault sync | Needs reconfiguration |
| selfheal | Auto-recovery | NemoClaw has its own recovery |
| sessionmonitor | Session health | Part of NemoClaw stack |
| tailscale.monitor | Tailscale health | Windows Tailscale manages itself |
| weeklysecurity | Security audit | OpenClaw cron can replace |

---

## 7. What Already Runs on PowerSpec

### Docker Services (Running)

| Service | Ports | RAM Usage (est.) | Conflict Risk |
|---------|-------|-----------------|---------------|
| FinancialReportApp API | :8001 | ~512MB | None |
| FinancialReportApp Frontend | :3001 | ~256MB | None |
| FinancialReportApp Postgres | :5433 | ~256MB | None |
| FinancialReportApp Redis | :6380 | ~128MB | None |
| FinancialReportApp Celery | - | ~256MB | None |
| ContractAnalyzer API | :8000 | ~512MB | None |
| ContractAnalyzer Postgres | :5432 | ~256MB | None |
| ContractAnalyzer Redis | :6379 | ~128MB | None |
| ContractAnalyzer MinIO | :9000/:9001 | ~256MB | None |
| ContractAnalyzer Celery | - | ~256MB | None |
| **Ollama** | :11434 | ~4-8GB (model-dependent) | None — NemoClaw can share |

**Estimated total RAM usage:** ~7-11 GB out of 128 GB available. **NemoClaw has ample headroom.**

### Port Allocation Summary

| Port | Current Use | NemoClaw Impact |
|------|------------|-----------------|
| 3001 | FinancialReportApp Frontend | No conflict |
| 5432-5433 | Postgres instances | No conflict |
| 6379-6380 | Redis instances | No conflict |
| 8000-8001 | API servers | No conflict |
| 9000-9001 | MinIO | No conflict |
| 11434 | Ollama | **Shared** — NemoClaw can route here |
| **18789** | **RESERVED** | ⚠️ Must use different port — Mac gateway owns 18789 |

---

## 8. Mission Control Cross-Machine Access

### Current State
- MC frontend: MacBook localhost:3000
- MC backend: MacBook
- PowerSpec access: via `http://100.101.203.113:3000` (Tailscale IP)
- Gateway allowedOrigins already includes PowerSpec IP
- **Issue:** PowerSpec Chrome bookmark still points to `localhost` — needs updating to Tailscale IP

### NemoClaw Implications
- NemoClaw sandbox is network-isolated by default (netns)
- To reach Mac Mission Control, NemoClaw's network policy must allow egress to `100.101.203.113:3000`
- This requires either:
  - Adding MC URL to NemoClaw's network policy allowlist
  - Or running MC on PowerSpec as well (duplicate)
- **Recommendation:** Keep MC on Mac, add Tailscale IPs to NemoClaw network policy

---

## 9. Risks & Open Questions

### High Risk

1. **WSL2 Stability** — NemoClaw on WSL2 is "tested with limitations." Community reports GPU detection issues, cgroup errors, and `nemoclaw onboard` failures. The PowerSpec setup is MORE capable than most (RTX 5080, 128GB RAM, Docker Desktop already working), but WSL2 sandboxing edge cases are real.

2. **Telegram Bot Token Conflict** — Only one OpenClaw instance can own the bot token. Running NemoClaw with the same token will disconnect Mac Jarvis from Telegram. Prototype must use TUI/CLI or a separate bot.

3. **Google OAuth Migration** — gog CLI OAuth tokens are Mac-bound. Re-authenticating on Windows/WSL2 requires browser-based OAuth flow, which is complex inside WSL2. This blocks Gmail, Calendar, Sheets skills.

4. **NemoClaw is Alpha Software** — NVIDIA's own README says "not production-ready, interfaces/APIs may change without notice." This is a prototype/evaluation only.

### Medium Risk

5. **Docker Resource Contention** — NemoClaw uses Docker (k3s cluster inside). Existing Docker containers + NemoClaw + Ollama all competing for Docker Desktop resources. 128GB RAM helps, but Docker Desktop WSL2 memory allocation needs tuning.

6. **Network Policy Lockdown** — NemoClaw's sandbox applies strict egress policies. Any skill/tool that needs to reach an external API must be explicitly allowed. This will require iterative policy tuning.

7. **Fresh OpenClaw Instance** — NemoClaw creates a brand-new OpenClaw, not a clone. All workspace files, skills, memory, agents config must be manually imported or synced.

8. **Port 18789 Collision** — Both Mac OpenClaw and NemoClaw default to 18789. Must configure NemoClaw to use a different port.

### Low Risk

9. **Node.js Version** — PowerSpec has v24.14.1 (meets 22.16+ requirement) but it's on Windows. WSL2 Ubuntu will need its own Node.js — the installer handles this via nvm.

10. **GPU Passthrough** — RTX 5080 with CUDA 13.2 driver already installed on Windows. WSL2 GPU passthrough should work but needs nvidia-container-toolkit setup.

### Open Questions for Eric / Planner

1. **Scope of prototype:** Full Jarvis migration, or just test NemoClaw security features with a minimal OpenClaw setup?
2. **Telegram strategy:** Keep Mac as Telegram owner? Create second test bot? 
3. **Inference routing:** Use NVIDIA Endpoints (Nemotron models) via cloud, existing Anthropic API, local Ollama, or hybrid?
4. **NVIDIA API key:** Does Eric already have one from build.nvidia.com?
5. **Timeline:** How long until Ajax server arrives? Does NemoClaw need to be "production" on PowerSpec, or just evaluated?
6. **Coexistence:** Should PowerSpec NemoClaw be fully independent, or connected to Mac Jarvis as a compute node?
7. **Network policy baseline:** Start with NemoClaw's restrictive defaults and open incrementally, or start permissive for prototyping?

---

## 10. Recommended Prototype Approach (for Planner)

Based on research, the recommended path is:

1. **Eric downloads and installs NemoClaw** (Step 1 — he does this himself)
   - Install Ubuntu-22.04 WSL2 distro first
   - Enable systemd, configure Docker Desktop WSL integration
   - Set up NVIDIA GPU passthrough in WSL2
   - Run `curl -fsSL https://nvidia.com/nemoclaw.sh | bash`
   - Use Anthropic as inference provider (existing API key)

2. **Jarvis configures the sandbox** (Step 2 — post-install)
   - Import portable skills (19 of 30)
   - Configure inference routing (Anthropic + local Ollama hybrid)
   - Set gateway to non-conflicting port (:18790)
   - Add Tailscale IPs to network policy
   - Test with TUI/CLI first (no Telegram)

3. **Evaluate and iterate** (Step 3)
   - Test security sandbox behavior
   - Measure local inference quality (Nemotron vs Anthropic)
   - Test GPU-accelerated local inference
   - Document what works/breaks for Ajax server planning

---

*End of research report. This document feeds directly into the Planner agent for actionable plan creation.*
