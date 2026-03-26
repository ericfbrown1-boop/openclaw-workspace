# OpenClaw Coding Workflow — Complete Guide

**Author:** Claude Opus 4.6 for Eric Brown
**Date:** 2026-03-25
**Version:** 1.0

---

## Two Paths: Jarvis (Mac) vs Claude Code (PowerSpec)

```
                    ┌──────────────────────────────────┐
                    │       Eric Makes a Request        │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │   What kind of work is this?      │
                    └──────┬──────────────────┬────────┘
                           │                  │
              ┌────────────▼─────┐   ┌───────▼──────────────┐
              │  Multi-step      │   │  Direct coding task   │
              │  project, agent  │   │  on PowerSpec, urgent │
              │  orchestration,  │   │  fix, GPU workload,   │
              │  research, or    │   │  or simple one-off    │
              │  monitoring      │   │                       │
              └───────┬──────────┘   └────────┬─────────────┘
                      │                       │
              ┌───────▼──────────┐   ┌────────▼─────────────┐
              │  PATH 1: Jarvis  │   │  PATH 2: Claude Code │
              │  (MacBook Pro)   │   │  (PowerSpec PC)      │
              │  Multi-agent     │   │  Direct execution    │
              │  orchestration   │   │  SSH/local           │
              └──────────────────┘   └──────────────────────┘
```

---

## PATH 1: Jarvis on MacBook Pro (Multi-Agent Orchestration)

### When to Use Path 1
- New projects requiring planning + implementation + testing
- Research tasks (financial analysis, competitive intel)
- Tasks that need multiple agents (Planner → Coder → Tester → Quality)
- Monitoring, daily briefing, cron jobs
- Any task where you want the full pipeline (4-phase workflow)

### Session Bootstrap (Every Time)

```
Jarvis wakes up
    │
    ├── 1. Read SOUL.md (identity)
    ├── 2. Read USER.md (Eric's context)
    ├── 3. Read memory/YYYY-MM-DD.md (today + yesterday)
    ├── 4. Read MEMORY.md (if main session)
    ├── 5. Read DELEGATION.md (agent routing)
    ├── 6. Read PIPELINE.md (if code/build task)
    └── 7. Read POWERSPEC.md (if compute task)
```

### Task Complexity Gate (Before Spawning Agents)

```
Eric's request arrives
    │
    ▼
┌─────────────────────────────────────┐
│  "Could I do this in 2 min myself?" │
└───────┬─────────────────┬───────────┘
        │ YES             │ NO
        ▼                 ▼
┌──────────────┐  ┌────────────────────┐
│ SIMPLE       │  │ Check time estimate │
│ Jarvis does  │  └──┬─────────────┬───┘
│ it directly  │     │ 5-30 min    │ >30 min
│ No subagent  │     ▼             ▼
└──────────────┘  ┌─────────┐  ┌──────────┐
                  │MODERATE │  │ COMPLEX  │
                  │1 agent  │  │ Up to 3  │
                  │+ verify │  │ parallel │
                  └─────────┘  │ agents   │
                               └──────────┘
```

### The 4-Phase Pipeline (Mandatory for ALL Tasks)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PHASE 1: UNDERSTAND                              │
│                                                                      │
│  Planner reads existing codebase ("Explore First" rule)             │
│  Researcher gathers requirements if needed                          │
│  Output: PROJECT_CONTEXT.md                                         │
│  Gate: Context document exists                                      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                     PHASE 2: PLAN                                    │
│                                                                      │
│  Planner creates PLAN.md (architecture, tasks, risks)               │
│  GPT-5.4 Pro cross-review for edge cases (1M context)               │
│  Must include Compute Allocation table (MacBook vs PowerSpec)        │
│  Must include Repository Setup section                               │
│  Gate: PLAN.md approved by Jarvis                                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                     PHASE 3: IMPLEMENT                               │
│                                                                      │
│  Coder reads PLAN.md → writes code                                  │
│  CHECKPOINT.md at each major step                                    │
│  Verify at each checkpoint (tests, docker build, health check)       │
│  git add → git commit → git push before handoff                     │
│  Output: HANDOFF.md with commit SHA                                  │
│  Gate: Code pushed + tests pass locally                              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                     PHASE 4: VERIFY                                  │
│                                                                      │
│  ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌───────────┐       │
│  │ Tester  │───▶│ Quality │───▶│ External │───▶│ Conductor │       │
│  │         │    │         │    │ Auditor  │    │           │       │
│  │ Import  │    │ Security│    │ 6-step   │    │ Docker    │       │
│  │ verify  │    │ audit   │    │ QA gate  │    │ deploy    │       │
│  │ + tests │    │ + code  │    │ + sign   │    │ + smoke   │       │
│  │         │    │ review  │    │ off      │    │ test      │       │
│  └────┬────┘    └────┬────┘    └────┬─────┘    └─────┬─────┘       │
│       │FAIL          │CRITICAL      │                 │             │
│       │              │              │                 ▼             │
│       ▼              ▼              │          ┌───────────┐       │
│  Back to Coder  Back to Coder      │          │ 100% DONE │       │
│  (Phase 3)      (Phase 3)          │          │ SHA in     │       │
│                                     │          │ tasks.json │       │
│                                     ▼          └───────────┘       │
│                              ┌───────────┐                          │
│                              │ Librarian │                          │
│                              │ Post-audit│                          │
│                              │ review    │                          │
│                              └───────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Routing — Who Gets Activated When

```
Eric's request
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                 JARVIS (Orchestrator)                  │
│                 Model: Opus 4.6                        │
│                                                        │
│  Reads DELEGATION.md trigger keywords                  │
│  Checks task complexity gate                           │
│  Fills DISPATCH_TEMPLATE.md                            │
│  Routes to appropriate agent ▼                         │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──┘
   │      │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
│Plan-││Rese-││Coder││Test-││Qual-││Audi-││Cond-││Moni-│
│ner  ││arch-││     ││er   ││ity  ││tor  ││uctor││tor  │
│     ││er   ││     ││     ││     ││     ││     ││     │
│Opus ││Son- ││Son- ││Son- ││Son- ││Son- ││Son- ││Son- │
│4.6  ││net  ││net  ││net  ││net  ││net  ││net  ││net  │
└─────┘└─────┘└─────┘└─────┘└─────┘└─────┘└─────┘└─────┘
```

### Agent Trigger Keywords

| Agent | Trigger Keywords / Conditions |
|-------|-------------------------------|
| **Planner** | "plan", "design", "architect", "new project", "build a", "start a", "create a system" |
| **Researcher** | Research NOT tied to project plans (financial analysis, market news, competitive intel) |
| **Coder** | Explicit coding task WITH existing PLAN.md |
| **Tester** | After Coder completes; before Quality audit |
| **Quality** | "error", "failed", "crash", "bug" (diagnosis); OR new code committed (security audit) |
| **External Auditor** | After Quality passes; final QA gate |
| **Conductor** | Docker build + deploy + smoke tests; marks 100% |
| **Monitor** | "check stocks", "system health", OR automated 5-min cron |
| **Librarian** | After External Auditor; post-deployment review |

### What Each Agent Reads, Produces, and Must Pass

| Agent | Reads Before Starting | Produces | Gate Before Handoff |
|-------|----------------------|----------|-------------------|
| **Planner** | Codebase structure, PIPELINE.md, POWERSPEC.md | PLAN.md + PROJECT_CONTEXT.md | Plan approved by Jarvis |
| **Researcher** | Research question, web sources | Findings committed to git | Sources cited, cross-checked |
| **Coder** | PLAN.md, 3+ existing project files | CHECKPOINT.md, HANDOFF.md, code pushed | Tests pass, docker builds, SHA recorded |
| **Tester** | HANDOFF.md, test suite | Test results | Min gate: health check, lint, 1 unit test |
| **Quality** | HANDOFF.md, code review | Security audit report | No critical issues; dashboard parity verified |
| **External Auditor** | Full project tree | Sign-off artifact in tasks.json | 6-step QA gate passed |
| **Conductor** | Deploy config, HANDOFF.md | Deployed app + smoke test | curl /health returns 200; SHA in tasks.json |
| **Monitor** | tasks.json, cron-state.json, auth state | Sweep report | All 11 checks ran; failures acted on |
| **Librarian** | incidents.jsonl, recent changes | Improvement proposals | Patterns >2 occurrences flagged |

---

## PATH 2: Claude Code on PowerSpec (Direct Execution)

### When to Use Path 2
- Direct coding on PowerSpec (GPU tasks, Docker builds, test suites)
- Urgent fixes that don't need full pipeline
- Interactive development (VS Code + Claude Code)
- One-off tasks on the remote machine
- Any task where agent overhead isn't worth it (<5 min, single concern)

### PowerSpec Direct Execution Flow

```
Eric opens Claude Code on PowerSpec
    │
    ├── Claude reads CLAUDE.md (quick start, rules, auth)
    │
    ▼
┌─────────────────────────────────────────────┐
│           Direct Execution                   │
│                                              │
│  Eric gives instruction                      │
│       │                                      │
│       ▼                                      │
│  Claude Code executes directly:              │
│  - Reads/writes files                        │
│  - Runs commands (docker, pytest, npm)       │
│  - Uses GPU (docker run --gpus all)          │
│  - Commits and pushes to GitHub              │
│                                              │
│  Pre-commit hooks run automatically:         │
│  - JSON/YAML validation                      │
│  - Secret detection                          │
│  - Python lint (ruff)                        │
│  - Shell lint (shellcheck)                   │
│                                              │
│  On push → GitHub Actions CI runs:           │
│  - Secret scan                               │
│  - AGENTS.md size check (<5KB)               │
│  - Skill file validation                     │
│  - Python + shell lint                       │
└─────────────────────────────────────────────┘
```

### PowerSpec Compute Routing

```
Task arrives
    │
    ▼
┌────────────────────────────────────────────────────┐
│              Where does this run?                    │
└───────┬────────────────────────────┬───────────────┘
        │                            │
        ▼                            ▼
┌───────────────────┐    ┌───────────────────────────┐
│  MacBook Pro      │    │  PowerSpec (remote-coder)  │
│                   │    │                            │
│  - pm2 services   │    │  - Docker builds           │
│  - Mission Ctrl   │    │  - Test suites             │
│  - OpenClaw GW    │    │  - Next.js prod builds     │
│  - Tailscale      │    │  - AI/ML/GPU tasks         │
│  - Quick git ops  │    │  - Research >5 min         │
│  - Email (gog)    │    │  - Codebases >10K lines    │
│  - <2 min tasks   │    │  - Tasks >15 min           │
└───────────────────┘    └───────────────────────────┘
```

---

## How Skills and Agents Work Together

```
┌─────────────────────────────────────────────────────────────┐
│                     SKILLS (Knowledge)                        │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ railway- │ │ earnings-│ │ salesforce│ │ google-  │       │
│  │ deploy   │ │ analyzer │ │ analytics│ │ oauth    │  ...  │
│  │ 26KB     │ │ 5KB      │ │ 12KB     │ │ 6KB      │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │             │            │             │              │
│       └──────┬──────┴────────────┴─────┬───────┘              │
│              │   Skills are READ by    │                      │
│              │   agents when needed    │                      │
│              ▼                         ▼                      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────▼───────────────┐
              │                               │
┌─────────────▼──────────────┐  ┌─────────────▼──────────────┐
│      AGENTS (Actors)        │  │     AGENTS (Actors)         │
│                             │  │                             │
│  Coder reads:               │  │  Monitor reads:             │
│  - railway-deployment       │  │  - monitor SKILL.md         │
│  - remote-coder             │  │  - google-oauth-reauth      │
│  when deploying to Railway  │  │  - competitive-intel         │
│  on PowerSpec               │  │  every 5-min sweep          │
└─────────────────────────────┘  └─────────────────────────────┘
```

### Skill Activation: How Jarvis Picks the Right Skill

```
Eric: "Analyze Rubrik's latest earnings"
    │
    ▼
Jarvis reads DELEGATION.md
    │
    ├── Matches: financial analysis → Researcher agent
    │
    ▼
Researcher agent activated
    │
    ├── Reads earnings-analyzer/SKILL.md (SEC EDGAR workflow)
    ├── Reads competitive-intel/SKILL.md (stock data)
    ├── Reads financial-report-gen/SKILL.md (Word doc output)
    │
    ▼
Executes workflow from skill files
    │
    ├── Pull 10-Q from EDGAR
    ├── Get stock price from yfinance
    ├── Calculate multiples
    ├── Generate Word doc
    ├── Email via gog gmail send
    │
    ▼
Done → tasks.json updated → Monitor verifies
```

---

## How the Two Paths Sync

```
┌───────────────┐                        ┌────────────────┐
│  MacBook Pro  │                        │  PowerSpec PC  │
│  (Jarvis)     │                        │  (Claude Code) │
│               │                        │                │
│  Agent writes │    ┌──────────────┐    │  Claude writes │
│  code         │───▶│   GitHub     │◀───│  code          │
│               │    │  (shared     │    │                │
│  git push     │    │   repos)     │    │  git push      │
│               │    └──────────────┘    │                │
│               │                        │                │
│  Agent reads  │    ┌──────────────┐    │  Claude reads  │
│  tasks.json   │───▶│ Mission Ctrl │    │  CLAUDE.md     │
│               │    │ (Mac:3001)   │    │                │
│               │    └──────────────┘    │                │
│               │                        │                │
│  SSH to       │    ┌──────────────┐    │  Direct        │
│  PowerSpec    │───▶│  Tailscale   │◀───│  execution     │
│  for heavy    │    │  (VPN mesh)  │    │  on local      │
│  compute      │    └──────────────┘    │  hardware      │
└───────────────┘                        └────────────────┘
```

---

## Authentication & Fallback Flow

```
Before ANY credential-dependent work:
    │
    ├── Check memory/auth-fallback-state.json
    │
    ▼
┌───────────────────────────────────┐
│  gog gmail search "newer_than:1h" │
│  gh auth status                   │
└──────┬────────────────┬───────────┘
       │ PASS           │ FAIL
       ▼                ▼
  ┌─────────┐    ┌──────────────────────────┐
  │ Proceed │    │ Circuit breaker activates │
  │ normally│    │                           │
  └─────────┘    │ 1. Set auth_healthy=false │
                 │    in cron-state.json     │
                 │ 2. Switch to Zapier MCP   │
                 │    for email              │
                 │ 3. Alert Eric via Telegram│
                 │ 4. Pause all auth-        │
                 │    dependent crons        │
                 │ 5. Log to incidents.jsonl │
                 └──────────────────────────┘
```

---

## Model Tiering & Cost Flow

```
┌─────────────────────────────────────────────────────┐
│            Check memory/api-usage-state.json          │
└───────┬──────────────────┬──────────────────┬───────┘
        │ <75%             │ 75-90%           │ >90%
        ▼                  ▼                  ▼
  ┌───────────┐    ┌──────────────┐    ┌──────────────┐
  │  NORMAL   │    │  DOWNGRADE   │    │  PAUSE       │
  │           │    │              │    │              │
  │ Jarvis:   │    │ Jarvis:      │    │ Only critical│
  │  Opus 4.6 │    │  Opus 4.6   │    │ fixes on     │
  │ Planner:  │    │ Everything   │    │ Sonnet 4.6   │
  │  Opus 4.6 │    │ else:        │    │              │
  │ Workers:  │    │  Sonnet 4.6  │    │ Alert Eric   │
  │  Sonnet   │    │              │    │              │
  └───────────┘    └──────────────┘    └──────────────┘
```

---

## Skill vs Agent: The Difference

| | **Agent** | **Skill** |
|---|-----------|-----------|
| **What is it** | A subprocess spawned by Jarvis | A knowledge file (SKILL.md) |
| **Has its own session** | Yes (isolated context) | No (read by agents) |
| **Uses a model** | Yes (Opus or Sonnet) | No (just documentation) |
| **Can execute commands** | Yes | No (agents execute based on skill content) |
| **Can be triggered by cron** | Yes (Monitor, daily briefing) | No |
| **Count** | 9 agents | 20 skills |
| **Example** | Coder agent writes code | railway-deployment skill tells Coder HOW to deploy |

**Think of it this way:** Agents are the workers. Skills are the instruction manuals they read.

---

## Complete Request Lifecycle Example

```
Eric: "Build me a stock dashboard with real-time Rubrik and Commvault prices"
    │
    ▼
JARVIS checks DELEGATION.md
    │ Keywords: "build" → new project → needs Planner
    │ Complexity: >30min → COMPLEX → multi-agent
    │
    ▼
PHASE 1: UNDERSTAND
    │ Planner reads existing codebase
    │ Researcher checks yfinance API capabilities
    │ Output: PROJECT_CONTEXT.md
    │
    ▼
PHASE 2: PLAN
    │ Planner creates PLAN.md:
    │   - React frontend + Node.js backend
    │   - yfinance for stock data
    │   - Railway deployment
    │   - Compute: Docker build on PowerSpec, UI on MacBook
    │ GPT-5.4 cross-reviews for edge cases
    │ Jarvis approves plan
    │
    ▼
PHASE 3: IMPLEMENT
    │ Coder reads PLAN.md
    │   Reads: railway-deployment SKILL, competitive-intel SKILL
    │   SSHs to PowerSpec for Docker build
    │   Writes CHECKPOINT.md at each phase
    │   Runs tests after each change
    │   git push → HANDOFF.md
    │
    ▼
PHASE 4: VERIFY
    │ Tester: imports work, lint clean, health endpoint responds
    │   │ PASS
    │   ▼
    │ Quality: security audit, no hardcoded keys, dashboard parity
    │   │ PASS
    │   ▼
    │ External Auditor: 6-step QA gate, click every link, sign off
    │   │ PASS
    │   ▼
    │ Conductor: Railway deploy, curl /health 200, SHA in tasks.json
    │   │ PASS
    │   ▼
    │ Librarian: reviews incident log, suggests improvements
    │
    ▼
✅ DONE — tasks.json: status="completed", progress=100
```
