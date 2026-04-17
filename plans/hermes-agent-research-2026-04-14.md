# Hermes Agent — Research Report & Implementation Plan

**Date:** 2026-04-14  
**Prepared by:** Jarvis Researcher Agent  
**For:** Eric Brown, CFO & COO, Cohesity  

---

## Executive Summary

Hermes Agent is an open-source (MIT), self-improving AI agent framework built by **Nous Research** — the same lab behind the Hermes model family and the Atropos RL framework. It is the most prominent direct competitor to OpenClaw, differentiated by its **built-in learning loop**: the agent autonomously creates reusable "skills" from complex tasks, refines them during use, and maintains persistent memory plus a user model across sessions. It supports 15+ messaging platforms, 47 built-in tools, 18+ LLM providers, 6 terminal backends, and an MCP integration layer. It includes a one-command migration path from OpenClaw (`hermes claw migrate`). **Recommendation: Conditional Go** — worth evaluating as a complementary agent on the PowerSpec PC or a sandboxed MacBook venv, but not as an OpenClaw replacement given Eric's deeply invested Jarvis/OpenClaw ecosystem.

---

## What Is Hermes Agent

**Hermes Agent** (https://github.com/NousResearch/hermes-agent) is a self-hosted, model-agnostic personal AI agent released by Nous Research. As of April 2026, it has ~8,700 GitHub stars, 142 contributors, and 2,293+ commits. The latest release is **v0.8.0 (v2026.4.8)**.

### Key Identity
- **Not** a chatbot wrapper or IDE copilot — it's a long-running autonomous agent
- **Not** a hosted SaaS — fully self-hosted, you own all data
- **MIT licensed** — no restrictions on commercial or personal use
- Python-based (~10,700 lines in the core agent loop alone)
- Ranked **#2 daily global rank** on OpenRouter by token volume (1.86T total tokens as of March 2026)

### Sources
- Official site: https://hermes-agent.nousresearch.com
- GitHub: https://github.com/NousResearch/hermes-agent
- Docs: https://hermes-agent.nousresearch.com/docs/
- Skills Hub: https://agentskills.io (open standard, portable skills)

---

## Architecture & How It Works

### System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Entry Points                        │
│  CLI (cli.py)   Gateway (gateway/run.py)   ACP      │
│  Batch Runner   API Server   Python Library          │
└──────────┬──────────────┬──────────────┬────────────┘
           │              │              │
           ▼              ▼              ▼
┌─────────────────────────────────────────────────────┐
│              AIAgent (run_agent.py)                   │
│                                                       │
│  Prompt Builder → Provider Resolution → Tool Dispatch │
│  Compression    → 3 API Modes        → Tool Registry  │
│  & Caching      → (chat_completions,   (47 tools,     │
│                    codex_responses,      19 toolsets)   │
│                    anthropic_messages)                  │
└──────────┬──────────────┬──────────────┬────────────┘
           │              │              │
           ▼              ▼              ▼
┌──────────────────┐  ┌──────────────────────────────┐
│ Session Storage   │  │ Tool Backends                 │
│ (SQLite + FTS5)   │  │ Terminal (6): local, Docker,  │
│                   │  │   SSH, Daytona, Modal,        │
│                   │  │   Singularity                 │
│                   │  │ Browser (5 backends)          │
│                   │  │ Web (4 backends)              │
│                   │  │ MCP (dynamic)                 │
└──────────────────┘  └──────────────────────────────┘
```

### The Learning Loop (Key Differentiator)

1. **Task Execution** — Decomposes goals, selects tools, executes (similar to any agent)
2. **Outcome Evaluation** — Evaluates success/failure, reads implicit + explicit feedback
3. **Skill Creation** — After complex tasks (5+ tool calls), autonomously creates a skill document (structured markdown with procedures, pitfalls, verification steps)
4. **Skill Refinement** — Skills evolve during use; if a better approach outperforms the stored one, the skill is updated
5. **Skill Retrieval** — On new tasks, searches skill library for applicable patterns; loads them instead of solving from scratch

### Memory System

| Component | Size Limit | Purpose |
|-----------|-----------|---------|
| `MEMORY.md` | 2,200 chars | Environment facts, conventions, lessons |
| `USER.md` | 1,375 chars | User preferences, communication style |
| FTS5 session search | Unlimited | On-demand recall from all past sessions |
| Honcho user modeling | Dynamic | Dialectic model of who you are |

### Skills System (Progressive Disclosure)

- **Level 0**: Agent sees list of skill names + descriptions (~3,000 tokens)
- **Level 1**: Agent loads full skill content when needed
- **Level 2**: Agent loads specific reference files within a skill
- Compatible with **agentskills.io** open standard (same as OpenClaw!)

### Gateway (Messaging)

18 platform adapters in a single gateway process:
Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost, Email, SMS, DingTalk, Feishu, WeCom, BlueBubbles, QQBot, Home Assistant, Webhook, API Server

### Supported Providers (18+)

Nous Portal, OpenRouter (200+ models), OpenAI, Anthropic, xAI/Grok, Xiaomi MiMo, z.ai/GLM, Kimi/Moonshot, MiniMax, Alibaba Cloud, Hugging Face, Ollama, vLLM, SGLang, and any OpenAI-compatible endpoint.

---

## Key Capabilities

| Capability | Description | Tool Count |
|-----------|-------------|------------|
| **Self-improving skills** | Autonomous creation, refinement, and retrieval of reusable task patterns | N/A (meta) |
| **Persistent memory** | Cross-session MEMORY.md, USER.md, FTS5 search, Honcho user modeling | 3 tools |
| **Terminal execution** | 6 backends: local, Docker, SSH, Daytona, Modal, Singularity | 5 tools |
| **Web tools** | Search, extract, browse, screenshot, vision | 10+ tools |
| **File operations** | read, write, patch, search_files | 4 tools |
| **Browser automation** | 10 browser tools across 5 backends | 10 tools |
| **Code execution** | Sandboxed execute_code tool | 1 tool |
| **Subagent delegation** | Spawn isolated subagents for parallel workstreams | 1 tool |
| **MCP integration** | Connect any MCP server via config | Dynamic |
| **Cron scheduling** | Natural-language scheduled tasks delivered to any platform | 2 tools |
| **Voice mode** | Real-time voice in CLI, Telegram, Discord VC | 3 tools |
| **ACP integration** | IDE-native agent via stdio/JSON-RPC (VS Code, Zed, JetBrains) | N/A |
| **Research/RL** | Batch trajectories, Atropos RL environments, trajectory compression | N/A |
| **OpenClaw migration** | One-command import of settings, memories, skills, API keys | N/A |

**Total: 47 registered tools across 19 toolsets**

---

## Pros of Integration with Jarvis/OpenClaw

### 1. Self-Improving Skills (High Value for Eric)
Eric's daily workflows are highly repetitive — 6AM briefings, competitive intel, earnings analysis. Hermes's learning loop would compound value over time on these recurring tasks. After a month of daily briefings, Hermes would have a refined skill that knows exactly what Eric wants.

### 2. Model Agnosticism
Like OpenClaw, Hermes works with any model. Eric could continue using Claude Opus 4.6, Grok 4.20, or run local models on the PowerSpec RTX 5080. Switching is a single command (`hermes model`).

### 3. OpenClaw Migration Path
`hermes claw migrate` imports: SOUL.md, MEMORY.md, USER.md, skills, command allowlists, messaging configs, API keys, and TTS assets. This significantly reduces switching cost.

### 4. Complementary Strengths
- OpenClaw excels at **ecosystem breadth** (29 skills, 11 agents, deep customization)
- Hermes excels at **skill evolution** (tasks get better over time)
- Running both is technically possible (same Telegram bot can't serve both, but separate interfaces can)

### 5. MCP Compatibility
Both support MCP, so tools and servers are portable between them.

### 6. agentskills.io Compatibility
Both use the same open skill standard, so skills are portable.

### 7. Serverless Deployment Options
Daytona/Modal backends mean Hermes can run on serverless infra that costs nearly nothing when idle — interesting for low-cost auxiliary deployment.

### 8. Local/Offline Capability
With Hermes 4 + Ollama on the PowerSpec PC (RTX 5080, 128GB RAM), Eric could run a fully offline autonomous agent at $0/month — useful for sensitive financial analysis.

---

## Cons & Risks

### 1. Redundancy with OpenClaw (Critical)
Eric already has a deeply customized Jarvis/OpenClaw setup: 11 agents, 29 skills, daily cron jobs, monitoring, AutoClaw self-healing. Hermes would duplicate much of this. Running two agent platforms creates maintenance overhead and split-brain risk.

### 2. Python-Only Stack
Hermes is Python-based (Python 3.11). OpenClaw is Node.js. Running both means maintaining two ecosystems on the MacBook. Dependencies, updates, and troubleshooting double.

### 3. Less Mature Ecosystem
OpenClaw has Eric's custom skills (competitive-intel, earnings-analyzer, monitor, project-dynamo, salesforce-analytics, etc.). Hermes has no equivalent out of the box. Those would need to be rebuilt or ported.

### 4. No Native Multi-Agent Orchestration at OpenClaw's Level
Hermes supports subagents but doesn't match OpenClaw's 11-agent pipeline (researcher → planner → coder → quality → auditor → conductor). Hermes's multi-agent is simpler — task delegation, not role-based orchestration.

### 5. Learning Loop Limitations
- Skills are markdown documents, not code — they guide the LLM but don't guarantee consistent execution
- Skill quality depends on the underlying model's capability
- The learning loop can crystallize bad patterns if early tasks go poorly
- Memory is small (3,575 chars total) — less than OpenClaw's SOUL.md + MEMORY.md customization

### 6. Gateway Port Conflict
Both OpenClaw (port 18789) and Hermes run gateways. If both connect to the same Telegram bot, they'll conflict. You'd need separate bot tokens.

### 7. No Windows Native Support
PowerSpec PC (Windows 11) requires WSL2 to run Hermes. This adds a layer of complexity for heavy compute tasks.

### 8. Young Project
v0.8.0 as of April 2026 — still pre-1.0. Breaking changes are possible. OpenClaw is more battle-tested in Eric's specific configuration.

---

## Comparison vs Current Stack

| Dimension | OpenClaw/Jarvis (Current) | Hermes Agent | Winner |
|-----------|--------------------------|--------------|--------|
| **Agent orchestration** | 11 role-based agents | Subagent delegation | OpenClaw |
| **Custom skills** | 29 (deep enterprise) | 0 (would need porting) | OpenClaw |
| **Self-improving skills** | No | Yes (built-in loop) | Hermes |
| **Persistent memory** | SOUL.md + MEMORY.md | MEMORY.md + USER.md + FTS5 + Honcho | Hermes |
| **Messaging platforms** | Telegram + others | 15+ from single gateway | Hermes |
| **Model support** | Claude, Grok, xAI | 18+ providers, 200+ models | Hermes (broader) |
| **Terminal backends** | Local + SSH | 6 (local, Docker, SSH, Daytona, Modal, Singularity) | Hermes |
| **MCP support** | Yes | Yes | Tie |
| **Skills standard** | agentskills.io | agentskills.io | Tie |
| **Daily briefings** | Custom cron + monitor | Built-in cron + NL scheduling | Tie |
| **Enterprise workflows** | Deep (FinancialReportApp, ContractAnalyzer, etc.) | Would need building | OpenClaw |
| **Maturity** | Production-grade for Eric | v0.8.0 pre-1.0 | OpenClaw |
| **Offline capability** | Requires API keys | Can run fully local with Ollama | Hermes |
| **IDE integration** | ACP (Codex, Claude Code) | ACP (VS Code, Zed, JetBrains) | Tie |
| **Setup complexity** | Moderate (already done) | Moderate (from scratch) | OpenClaw (sunk cost) |

---

## Implementation Plan

### Phase 0: Prerequisites (Day 1)

1. **Decide deployment target**: PowerSpec PC (recommended for evaluation) or MacBook Pro
2. **If PowerSpec**: Ensure WSL2 is installed and configured
3. **If MacBook**: Ensure Python 3.11 is available (`brew install python@3.11` or via uv)
4. **Allocate a separate Telegram bot token** for Hermes (do NOT share Jarvis's bot)
5. **Budget**: Plan for OpenRouter API costs (~$1-3/M input tokens, ~$3-9/M output tokens depending on model)

### Phase 1: Installation & Setup (Day 1-2)

```bash
# On PowerSpec (WSL2) or MacBook:
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc  # or ~/.zshrc

# Configure model (use OpenRouter for flexibility)
hermes model
# Select: OpenRouter → claude-opus-4-6 (or grok-4.20)

# Run doctor check
hermes doctor

# Start interactive session
hermes
```

### Phase 2: OpenClaw Integration (Day 2-3)

**Option A — Migration (if evaluating as replacement)**
```bash
hermes claw migrate --dry-run  # Preview what would import
hermes claw migrate --preset user-data  # Import without secrets first
```

**Option B — Parallel Run (recommended)**
- Keep OpenClaw/Jarvis as primary
- Run Hermes on a separate machine (PowerSpec) or in a separate terminal
- Give Hermes a different Telegram bot token
- Test head-to-head on the same tasks

### Phase 3: Jarvis Skill/Agent Config (Day 3-5)

Port 2-3 key skills to Hermes for comparison:

1. **Daily Briefing** — Set up via Hermes cron:
   > "Every weekday at 6am PT, check competitive news for Rubrik, Commvault, and Veeam, summarize key developments, and send to Telegram"

2. **Competitive Intel** — Create an initial skill, let Hermes refine it:
   ```
   mkdir -p ~/.hermes/skills/competitive-intel/
   # Copy/adapt the OpenClaw competitive-intel SKILL.md
   ```

3. **Earnings Analysis** — Test with a one-off:
   > "Pull the latest 10-Q for Rubrik and calculate YoY ARR growth, margins, and valuation multiples"

### Phase 4: Testing & Validation (Week 2)

| Test | Success Criteria |
|------|-----------------|
| Daily briefing accuracy | Matches or exceeds Jarvis output quality |
| Skill creation | After 5 briefings, Hermes auto-creates a reusable skill |
| Skill improvement | By day 10, briefings are faster/more relevant |
| Memory persistence | Agent remembers Eric's preferences across sessions |
| Cross-platform | Send task on Telegram, check status on CLI |
| MCP connectivity | Connect GitHub MCP server, verify tool access |
| PowerSpec compute | Run local Hermes 4 model via Ollama for offline analysis |

### Phase 5: Production Rollout (Week 3-4, if validated)

**Recommended: Complementary deployment, not replacement**

1. Keep Jarvis/OpenClaw as primary agent (all 29 skills, 11 agents intact)
2. Deploy Hermes on PowerSpec as a **specialist agent** for:
   - Tasks that benefit from learning loops (recurring analysis)
   - Local/offline financial analysis (Hermes 4 + Ollama + RTX 5080)
   - Experimental MCP server connections
3. Create a Jarvis skill that can **delegate to Hermes** via SSH for specific tasks
4. Monitor for 2 weeks before expanding scope

---

## Cost Analysis

### Software Cost
| Item | Cost |
|------|------|
| Hermes Agent license | **$0** (MIT) |
| Installation | **$0** |
| Skills Hub | **$0** |

### API/Model Costs (monthly estimates for Eric's usage patterns)

| Provider/Model | Input Cost | Output Cost | Est. Monthly* |
|---------------|-----------|-------------|---------------|
| OpenRouter → Claude Opus 4.6 | $15/M tokens | $75/M tokens | $50-150 |
| OpenRouter → Hermes 4 405B | $1/M tokens | $3/M tokens | $5-15 |
| OpenRouter → Hermes 3 405B (free) | $0 | $0 | $0 |
| Ollama → Hermes 4 (local on PowerSpec) | $0 | $0 | $0 (+ electricity) |
| Nous Portal (subscription) | Flat rate | Flat rate | ~$20-50 |

*Based on ~5-10 agent sessions/day with moderate tool use

### Infrastructure Costs
| Item | Cost |
|------|------|
| PowerSpec PC (already owned) | $0 incremental |
| MacBook Pro (already owned) | $0 incremental |
| Daytona/Modal serverless (optional) | $0-10/month (hibernates when idle) |
| Separate Telegram bot | $0 |

**Total incremental cost: $0-150/month** depending on model choice and usage volume.

---

## Recommendation: Conditional Go ✅

### Verdict: **Deploy as Complementary Agent, Not Replacement**

**Rationale:**
1. Eric's Jarvis/OpenClaw setup is deeply customized (29 skills, 11 agents, daily production workflows). Replacing it would be high-risk with uncertain payoff.
2. Hermes's learning loop is genuinely novel — it addresses a real gap in OpenClaw (skills don't self-improve).
3. The PowerSpec PC is underutilized for agent work — running Hermes there gives a zero-conflict evaluation.
4. The `agentskills.io` standard means skills are portable between the two systems.
5. If Hermes proves valuable, a gradual migration path exists (`hermes claw migrate`).

### Suggested Approach
1. **Week 1**: Install Hermes on PowerSpec via WSL2, test daily briefings
2. **Week 2**: Port 2-3 skills, evaluate learning loop effectiveness
3. **Week 3-4**: If positive, deploy as persistent specialist agent for recurring analysis
4. **Month 2+**: Evaluate whether to expand scope or stay complementary

### Do NOT Do
- Replace Jarvis/OpenClaw — the switching cost is too high for uncertain benefit
- Run both on the same MacBook with the same Telegram bot — conflict guaranteed
- Migrate in production without 2 weeks of parallel testing

---

## Open Questions for Eric

1. **Primary interest driver?** Is this about the learning loop specifically, or general curiosity about the OpenClaw alternative ecosystem?

2. **PowerSpec availability?** Is the PowerSpec PC available for running a persistent Hermes gateway, or is it committed to other workloads (Docker builds, test suites)?

3. **Local model interest?** Would a fully offline agent (Hermes 4 + Ollama on RTX 5080) be valuable for sensitive financial analysis that shouldn't hit cloud APIs?

4. **Skill portability test?** Want me to try porting the `competitive-intel` SKILL.md to Hermes format as a proof-of-concept?

5. **Timeline?** Is this exploratory research or do you want to start Phase 0-1 this week?

6. **HermesClaw bridge?** There's a community project (https://github.com/AaronWong1999/hermesclaw) that bridges Hermes and OpenClaw on the same messaging account. Worth investigating if you want both agents accessible from the same Telegram chat.

---

*Report generated 2026-04-14 by Jarvis Researcher Agent. All data sourced from official Hermes Agent documentation, GitHub repository, and independent reviews published between March-April 2026.*
