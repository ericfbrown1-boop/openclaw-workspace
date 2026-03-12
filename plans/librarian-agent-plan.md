# Librarian Agent — Self-Learning Loop for OpenClaw
## Comprehensive Architecture & Implementation Plan

**Version:** 1.0  
**Date:** 2026-03-10  
**Author:** Jarvis (Research Subagent)  
**Status:** Ready for Eric's Review

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Agent Configuration](#2-agent-configuration)
3. [Web Interface Design](#3-web-interface-design)
4. [Post-Audit Analysis Engine](#4-post-audit-analysis-engine)
5. [Approval Workflow](#5-approval-workflow)
6. [Self-Learning Loop Design](#6-self-learning-loop-design)
7. [Implementation Phases](#7-implementation-phases)
8. [Technical Requirements](#8-technical-requirements)

---

## 1. Architecture Overview

### 1.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OPENCLAW AGENT ECOSYSTEM                      │
│                                                                       │
│  ┌─────────┐   commissions   ┌──────────┐   specs   ┌──────────┐   │
│  │  Jarvis  │ ─────────────► │ Planner  │ ─────────► │  Coder   │   │
│  │  (main)  │                └──────────┘            └──────────┘   │
│  └────┬─────┘                                              │         │
│       │                                              code complete   │
│       │ orchestrates                                       ▼         │
│       │                                        ┌────────────────┐   │
│       │                                        │ Quality Agent  │   │
│       │                                        │  (Inspector)   │   │
│       │                                        └───────┬────────┘   │
│       │                                         passed │            │
│       │                                                ▼            │
│       │                                     ┌──────────────────┐   │
│       │                                     │ External Auditor │   │
│       │                                     └────────┬─────────┘   │
│       │                                     push to  │             │
│       │                                     GitHub   ▼             │
│       │                                   ┌──────────────────┐     │
│       └──────────────────────────────────►│   LIBRARIAN 📚   │     │
│                                           │  (New Agent)     │     │
│                                           └────────┬─────────┘     │
│                                                    │               │
│                    ┌───────────────────────────────┘               │
│                    ▼                                                │
│           ┌─────────────────┐    reviews    ┌──────────────┐       │
│           │  GitHub Repos   │ ◄─────────────│  Analysis    │       │
│           │  (git history,  │               │  Engine      │       │
│           │   commits, PRs) │               └──────┬───────┘       │
│           └─────────────────┘                      │               │
│                                                     │ proposes      │
│                                                     ▼               │
│                                           ┌──────────────────┐     │
│                                           │  Change Proposals │     │
│                                           │  (diffs/patches)  │     │
│                                           └────────┬──────────┘     │
│                                                    │               │
└────────────────────────────────────────────────────┼───────────────┘
                                                     │
                    ┌────────────────────────────────┘
                    ▼
          ┌──────────────────────────────────────────────┐
          │         ERIC'S REVIEW & APPROVAL             │
          │  ┌─────────────────┐  ┌────────────────────┐ │
          │  │  Web Dashboard  │  │  Telegram Bot      │ │
          │  │  (Librarian UI) │  │  (approve/reject)  │ │
          │  └────────┬────────┘  └──────────┬─────────┘ │
          │           └──────────┬───────────┘           │
          │                      ▼                        │
          │            ✅ Approved / ❌ Rejected          │
          └──────────────────────────────────────────────┘
                                 │
                    ┌────────────┘ apply approved changes
                    ▼
          ┌──────────────────────────────────────────────┐
          │         UPDATED AGENT CONFIGURATIONS         │
          │  AGENTS.md  │  SOUL.md  │  TOOLS.md  │ etc   │
          │   (Jarvis, Coder, Quality, Planner...)        │
          └──────────────────────────────────────────────┘
```

### 1.2 The Recursive Self-Learning Loop

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
         ┌──────────────────┐                            │
         │  1. BUILD PROJECT │                            │
         │  Planner→Coder→  │                            │
         │  Quality→Auditor │                            │
         └────────┬─────────┘                            │
                  │                                       │
                  ▼                                       │
         ┌──────────────────┐                            │
         │  2. PUSH TO GH   │                            │
         │  git push origin │                            │
         │  main            │                            │
         └────────┬─────────┘                            │
                  │ triggers                              │
                  ▼                                       │
         ┌──────────────────┐                            │
         │  3. LIBRARIAN    │                            │
         │  AUDIT           │                            │
         │  Analyzes what   │                            │
         │  happened        │                            │
         └────────┬─────────┘                            │
                  │                                       │
                  ▼                                       │
         ┌──────────────────┐                            │
         │  4. PROPOSE      │                            │
         │  CHANGES         │                            │
         │  Diffs for each  │                            │
         │  agent's .md     │                            │
         └────────┬─────────┘                            │
                  │                                       │
                  ▼                                       │
         ┌──────────────────┐                            │
         │  5. ERIC REVIEWS │                            │
         │  Approve/reject  │                            │
         │  each change     │                            │
         └────────┬─────────┘                            │
                  │ approved changes                      │
                  ▼                                       │
         ┌──────────────────┐                            │
         │  6. APPLY        │                            │
         │  Update agent    │─────────────────────────── ┘
         │  .md files       │    loop restarts
         └──────────────────┘    next project is better
```

### 1.3 Data Flow

```
GitHub Push Event
       │
       ▼
git log --oneline -p                    ← commit history
git log --pretty=format: --name-status  ← files changed
~/.openclaw/workspace/memory/           ← session memory files
~/.openclaw/agents/*/sessions/*.jsonl   ← session transcripts
~/.openclaw/workspace/plans/*.md        ← project plans
       │
       ▼
Librarian Analysis Engine
  ├── Timeline reconstruction
  ├── Agent involvement mapping
  ├── Challenge/error detection
  ├── Success/failure classification
  └── Pattern extraction
       │
       ▼
Improvement Suggestion Generator
  ├── AGENTS.md diff per agent
  ├── SOUL.md suggestions
  ├── TOOLS.md notes
  └── New skills to add
       │
       ▼
Approval Workflow (Web UI + Telegram)
       │
       ▼
Approved changes → applied to workspace files
```

---

## 2. Agent Configuration

### 2.1 openclaw.json Entry

Add to `agents.list` in `~/.openclaw/openclaw.json`:

```json
{
  "id": "librarian",
  "name": "Librarian",
  "workspace": "/Users/ericbrown/.openclaw/workspace-librarian",
  "model": {
    "primary": "anthropic/claude-opus-4-6",
    "fallbacks": [
      "xai/grok-4",
      "anthropic/claude-sonnet-4-6"
    ]
  },
  "tools": {
    "allow": [
      "read",
      "write",
      "exec",
      "web_search",
      "web_fetch",
      "sessions_send",
      "sessions_spawn"
    ],
    "deny": [
      "cron",
      "gateway",
      "browser",
      "screenshot"
    ],
    "fs": {
      "workspaceOnly": false
    }
  }
}
```

**Notes:**
- `workspaceOnly: false` — Librarian needs to read all agent workspaces and project directories.
- `write` allowed — Librarian writes audit reports and proposes file changes (but only after Eric's approval).
- No `cron` — Librarian is triggered by Jarvis post-push, not by its own schedule.
- No `browser` — Librarian is headless; the web UI is a separate process.

### 2.2 Trigger Mechanism (How Librarian Gets Invoked)

**Option A — Post-Push via Jarvis (recommended for Phase 1-3):**

Add a git post-push hook to each project repo that notifies Jarvis, who then dispatches Librarian:

```bash
# ~/.openclaw/workspace/scripts/git-post-push-hook.sh
#!/bin/bash
REPO_PATH=$(pwd)
REPO_NAME=$(basename $REPO_PATH)
BRANCH=$(git branch --show-current)

# Notify Jarvis via sessions_send (requires openclaw CLI)
openclaw sessions send --agent main \
  "📚 Git push detected: $REPO_NAME ($BRANCH). Please dispatch Librarian for post-audit."
```

Install hook across all projects:
```bash
for repo in /Users/ericbrown/ContractAnalyzer /Users/ericbrown/ProjectScraper; do
  cp ~/.openclaw/workspace/scripts/git-post-push-hook.sh $repo/.git/hooks/post-push
  chmod +x $repo/.git/hooks/post-push
done
```

**Option B — GitHub Webhook (Phase 3):**
- Configure GitHub repo webhooks to POST to a local endpoint (using `ngrok` or `smee.io` as relay)
- Endpoint triggers Librarian via OpenClaw sessions_spawn
- More reliable than local git hooks

**Option C — Manual Dispatch (Phase 1):**
- Eric or Jarvis says: "Librarian, audit ContractAnalyzer"
- Librarian runs analysis on demand

### 2.3 Proposed IDENTITY.md

```markdown
# IDENTITY.md — Librarian

- **Name:** Librarian
- **Creature:** AI knowledge curator and system historian
- **Vibe:** Methodical, insightful, precise — the agent who makes every
  project smarter than the last
- **Emoji:** 📚
- **Role:** Post-audit analyst, institutional memory keeper, and
  recursive improvement engine for the OpenClaw agent fleet
```

### 2.4 Proposed AGENTS.md for Librarian Workspace

```markdown
# AGENTS.md — Librarian

You are Librarian 📚 — the institutional memory of Eric's OpenClaw
agent fleet. Every project that gets pushed to GitHub is a lesson.
Your job is to extract those lessons and make every agent smarter.

---

## Core Purpose

1. **Reconstruct** what happened during a project (timeline, agents,
   challenges, successes)
2. **Identify** patterns — what worked, what didn't, where agents
   got confused or succeeded
3. **Propose** concrete changes to agent AGENTS.md files as diffs
4. **Never apply** changes without Eric's explicit approval
5. **Track** the history of all proposed and approved changes

---

## Trigger: You Are Dispatched By Jarvis

When Jarvis dispatches you, you receive:
- `project_path` — local path to the project
- `repo_url` — GitHub repo URL
- `session_ids` — (optional) relevant OpenClaw session IDs

---

## Workflow

### Phase 1: History Reconstruction

```bash
cd <project_path>

# Get full commit log with stats
git log --oneline --stat --since="30 days ago" > /tmp/lib_git_log.txt

# Get all commits with diffs
git log --all -p --since="30 days ago" > /tmp/lib_git_diff.txt

# Get branch history
git log --all --oneline --graph --decorate > /tmp/lib_graph.txt

# Get PR/issues from GitHub
gh pr list --repo <repo> --state all --json number,title,body,comments,reviews
gh issue list --repo <repo> --state all --json number,title,body,comments
```

Read memory files for project timeline:
```bash
ls ~/.openclaw/workspace/memory/ | sort
grep -l "<project_name>" ~/.openclaw/workspace/memory/*.md
```

Read relevant session transcripts:
```bash
ls ~/.openclaw/agents/*/sessions/*.jsonl
```

### Phase 2: Agent Involvement Analysis

For each session file found:
- Identify which agents were involved (Planner, Coder, Quality, Auditor)
- Note handoff points (when Jarvis dispatched a sub-agent)
- Track task completion vs. errors
- Note re-dispatches (same task sent twice = problem)
- Identify tool usage patterns

### Phase 3: Challenge Detection

Flag as challenges:
- Any commit message containing: "fix", "hotfix", "revert", "retry", "again"
- Sessions where error keywords appear: "failed", "exception", "crash"
- Multiple commits to the same file in quick succession
- Quality Agent findings (secrets found, warnings, failures)
- Tasks that required human intervention

### Phase 4: Generate Improvement Proposals

For each identified challenge or pattern:
1. Determine WHICH agent was involved
2. Identify WHAT configuration change would prevent recurrence
3. Generate a unified diff of the proposed AGENTS.md change
4. Assign a confidence level: HIGH / MEDIUM / LOW
5. Explain the reasoning

### Phase 5: Write Audit Report

Save to: `<workspace>/librarian/audits/<project>-<YYYY-MM-DD>.md`
Format: see Audit Report Template below

### Phase 6: Notify Jarvis

sessions_send to Jarvis with:
- Audit complete notification
- Number of proposals generated
- Path to audit report
- Telegram-friendly summary of key findings

---

## Audit Report Template

```
# Post-Audit Report: <Project Name>
**Date:** <date>
**Repo:** <url>
**Commits Analyzed:** <count>
**Period:** <start> → <end>

## Executive Summary
<2-3 sentences on what was built and the overall quality>

## Project Timeline
| Date | Event | Agent | Outcome |
|------|-------|-------|---------|

## Key Challenges Encountered
### Challenge 1: <title>
- **What happened:** ...
- **Evidence:** commit <sha> / session <id>
- **Impact:** delayed project by ~X hours / required rework
- **Root cause:** ...

## Agent Performance
| Agent | Tasks | Success | Re-dispatched | Notes |
|-------|-------|---------|---------------|-------|

## Proposed Improvements
(see separate change proposal files)

## Learnings Accumulated
- ...

## Approval Status
- [ ] Change Proposal 1 — pending
- [x] Change Proposal 2 — approved 2026-03-10
- [ ] Change Proposal 3 — rejected
```

---

## Rules

- **NEVER apply changes without Eric's explicit approval**
- Read ALL agent workspaces (cross-workspace reads are allowed)
- Be specific in proposals — vague suggestions are useless
- Always explain WHY a change is proposed, not just WHAT
- Track all proposals in `librarian/proposals/` with status
- Never modify production AGENTS.md files directly — only write
  to `librarian/proposals/<agent>-<change-id>.patch`
- If in doubt, propose less — fewer high-confidence changes beat
  many low-quality ones
```

---

## 3. Web Interface Design

### 3.1 Technology Stack Recommendation

**Recommendation: Streamlit (Python) for Phase 2, with optional upgrade path to Next.js**

**Reasoning:**
| Criterion | Streamlit | Next.js |
|-----------|-----------|---------|
| Time to build | Hours | Days-weeks |
| Python integration | Native | Requires API layer |
| File system access | Direct via Python | Requires server |
| Git/gh CLI integration | `subprocess` calls | Requires backend |
| Eric's use case | Internal tool | Internal tool |
| Hosting | `localhost:8501` | `localhost:3000` |
| Learning curve | Minimal | Significant |
| Polished UI | Adequate | Excellent |

**Decision:** Streamlit is the right choice here. This is an internal tool for one user. Streamlit lets you build a working dashboard in a few hours vs. days. If Eric wants a more polished UI later, the backend logic (Python scripts) can be reused with a Next.js frontend.

**Stack:**
- **Web framework:** Streamlit 1.x (Python)
- **Git integration:** `gitpython` + `subprocess` (`git`, `gh` CLI)
- **Diff rendering:** `diff-highlight`, rendered in Streamlit `st.code()`
- **Data storage:** SQLite (lightweight, no server needed) for proposals/approvals
- **Authentication:** None needed (localhost only)
- **Telegram integration:** `python-telegram-bot` for approval notifications

### 3.2 Screen Designs

---

#### Screen A: Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Librarian Dashboard                    [Refresh] [⚙️ Settings] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  RECENT ACTIVITY                         AGENT FLEET STATUS │
│  ─────────────                           ──────────────────  │
│  📦 ContractAnalyzer                     Jarvis    ✅ Active  │
│     Audited 2026-03-09 · 3 proposals     Researcher ✅ Active │
│     2 approved · 1 pending               Planner   ✅ Active  │
│                                          Coder     ✅ Active  │
│  📦 ProjectScraper                       Quality   ✅ Active  │
│     Audited 2026-03-05 · 1 proposal      Auditor   ✅ Active  │
│     1 approved                           Librarian 🆕 New    │
│                                                              │
│  PENDING APPROVALS                      LEARNING METRICS    │
│  ─────────────────                      ─────────────────── │
│  🔵 3 proposals awaiting review         4 projects audited  │
│  [Review Now →]                         12 changes approved  │
│                                         3 changes rejected  │
│                                         ~23% reduction in   │
│                                         re-dispatches       │
│                                                              │
│  RECENT LEARNINGS                                           │
│  ────────────────                                           │
│  • Coder benefits from PLAN.md path being explicit         │
│  • Quality Agent should scan test files too                 │
│  • Planner should research APIs before spec'ing them        │
└─────────────────────────────────────────────────────────────┘
```

---

#### Screen B: File Browser

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 File Browser          [🔍 Search files...]  [Filter ▼]   │
├──────────────────────────┬──────────────────────────────────┤
│ WORKSPACE TREE           │  FILE VIEWER                     │
│ ─────────────            │  ─────────────────               │
│ 📁 ~/.openclaw/workspace │  AGENTS.md                       │
│  ├── 📄 AGENTS.md    ←   │  Last modified: 2026-03-09       │
│  ├── 📄 SOUL.md          │  Size: 4.2 KB                    │
│  ├── 📄 MEMORY.md        │  ──────────────────────────────  │
│  ├── 📁 memory/          │  # AGENTS.md - Your Workspace    │
│  │   ├── 2026-03-10.md   │  ...                             │
│  │   └── 2026-03-09.md   │  [View Raw] [Edit] [History]     │
│  ├── 📁 plans/           │                                  │
│  │   └── ...             │  AGENT WORKSPACES                │
│  └── 📁 projects/        │  ─────────────────               │
│                          │  [workspace-quality →]           │
│ AGENT WORKSPACES         │  [workspace-coder →]             │
│ ──────────────────       │  [workspace-planner →]           │
│ 📁 workspace-quality     │  [workspace-researcher →]        │
│ 📁 workspace-coder       │  [workspace-librarian →]         │
│ 📁 workspace-planner     │                                  │
│ 📁 workspace-researcher  │                                  │
│ 📁 workspace-librarian   │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

---

#### Screen C: Chat History

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Chat History          [🔍 Search sessions...]            │
├─────────────────────────────────────────────────────────────┤
│  FILTER: [All Agents ▼]  [Date Range ▼]  [Project ▼]       │
├─────────────────────────────────────────────────────────────┤
│  SESSION: main-telegram-2026-03-09T14:23                     │
│  Agent: Jarvis | Channel: Telegram | Duration: 47 min        │
│  Tags: ContractAnalyzer, Coder, GitHub push                  │
│  ───────────────────────────────────────────────────────    │
│  Eric: "Build the ContractAnalyzer Docker backend"          │
│  Jarvis: [dispatched Planner → Coder → Quality → Auditor]   │
│  [View Full Session →]                                       │
│                                                              │
│  SESSION: quality-subagent-2026-03-09T16:11                  │
│  Agent: Quality | Parent: main | Duration: 8 min             │
│  Tags: security-audit, ContractAnalyzer, CLEAN               │
│  [View Full Session →]                                       │
│                                                              │
│  SESSION: coder-subagent-2026-03-09T15:30                    │
│  Agent: Coder | Parent: main | Duration: 31 min              │
│  Tags: ContractAnalyzer, Docker, FastAPI                     │
│  [View Full Session →]                                       │
└─────────────────────────────────────────────────────────────┘
```

---

#### Screen D: Project View

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Project: ContractAnalyzer                                 │
│ github.com/ericfbrown1-boop/ContractAnalyzer [View on GH →] │
├─────────────────────────────────────────────────────────────┤
│  TIMELINE                                                    │
│  ────────                                                    │
│  Mar 09 14:23  Eric requests Docker backend                  │
│  Mar 09 14:25  Jarvis dispatches Planner                     │
│  Mar 09 14:47  Planner creates PLAN.md                       │
│  Mar 09 15:00  Jarvis dispatches Coder                       │
│  Mar 09 15:31  Coder: initial Dockerfile + FastAPI app       │
│  Mar 09 15:52  ⚠️  Coder re-dispatched (import error)       │
│  Mar 09 16:10  Coder: fixed import, tests pass               │
│  Mar 09 16:11  Quality Agent: security audit → CLEAN         │
│  Mar 09 16:20  External Auditor: packaged, ready             │
│  Mar 09 16:25  Eric: pushed to GitHub                        │
│                                                              │
│  COMMIT HISTORY          AGENTS INVOLVED                    │
│  ──────────────          ──────────────                     │
│  a3f21bc Add Dockerfile  Planner     ✅ 1 dispatch           │
│  b9d4e12 Fix imports     Coder       ⚠️  2 dispatches        │
│  c1a8f93 Add tests       Quality     ✅ 1 dispatch (CLEAN)   │
│  d2b7g84 Initial commit  Auditor     ✅ 1 dispatch           │
│                                                              │
│  AUDIT REPORT            [View Audit →] [View Proposals →]  │
│  3 proposals generated · 2 approved · 1 pending             │
└─────────────────────────────────────────────────────────────┘
```

---

#### Screen E: Audit Reports

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Audit Report: ContractAnalyzer (2026-03-09)               │
├─────────────────────────────────────────────────────────────┤
│  Executive Summary                                          │
│  Built Docker-based contract OCR system using FastAPI and   │
│  LlamaIndex. Good overall execution; one re-dispatch of     │
│  Coder due to a missing import suggests Coder's AGENTS.md  │
│  should encourage import verification before task complete. │
│                                                              │
│  Key Challenges                                             │
│  ───────────────                                            │
│  ⚠️  Coder re-dispatched after import error (commit b9d4e12) │
│     Evidence: memory/2026-03-09.md mentions "import retry"  │
│     Impact: ~20 min delay                                   │
│                                                              │
│  Agent Performance                                          │
│  ─────────────────                                          │
│  Planner   ✅ Delivered complete PLAN.md in 22 min          │
│  Coder     ⚠️  Required 2 dispatches; import not verified   │
│  Quality   ✅ Clean audit, no secrets found                  │
│  Auditor   ✅ Packaged cleanly                              │
│                                                              │
│  Learnings                                                   │
│  ─────────                                                   │
│  1. Coder should run import checks before marking complete  │
│  2. Planner's Docker spec should include python env details │
│                                                              │
│  [View Proposals →]                                         │
└─────────────────────────────────────────────────────────────┘
```

---

#### Screen F: Change Proposals (Core Screen)

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Change Proposals                    [3 pending] [Filter ▼]│
├─────────────────────────────────────────────────────────────┤
│  PROPOSAL #001 — Coder AGENTS.md                            │
│  Source: ContractAnalyzer audit · Confidence: HIGH          │
│  ─────────────────────────────────────────────────────────  │
│  Reasoning: Coder was re-dispatched due to a Python import   │
│  error that would have been caught by running the code before│
│  marking the task complete.                                  │
│                                                              │
│  DIFF:                                                       │
│  ───────────────────────────────────────────────────────    │
│  --- a/workspace-coder/AGENTS.md                            │
│  +++ b/workspace-coder/AGENTS.md                            │
│  @@ -45,6 +45,12 @@                                         │
│   ## Completion Checklist                                   │
│   - [ ] All files written                                   │
│   - [ ] Tests pass                                          │
│  +- [ ] **Verify imports run cleanly:**                     │
│  +  ```bash                                                  │
│  +  python3 -c "import <main_module>" 2>&1                  │
│  +  ```                                                      │
│  +  If import fails, fix before reporting complete.         │
│   - [ ] No syntax errors                                    │
│  ─────────────────────────────────────────────────────────  │
│  [✅ Approve] [❌ Reject] [💬 Comment] [⏸️ Defer]           │
│                                                              │
│  PROPOSAL #002 — Planner AGENTS.md       [Confidence: MED]  │
│  [Expand ▼]                                                  │
│                                                              │
│  PROPOSAL #003 — Quality AGENTS.md       [Confidence: HIGH]  │
│  [Expand ▼]                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 How It Connects to OpenClaw Data

```python
# Data sources the Streamlit app reads:

# 1. Session transcripts (JSONL)
SESSIONS_BASE = "~/.openclaw/agents/{agent_id}/sessions/"

# 2. Agent workspaces (AGENTS.md, SOUL.md etc.)
WORKSPACES = {
    "main": "~/.openclaw/workspace/",
    "coder": "~/.openclaw/workspace-coder/",
    "quality": "~/.openclaw/workspace-quality/",
    "planner": "~/.openclaw/workspace-planner/",
    "researcher": "~/.openclaw/workspace-researcher/",
    "auditor": "~/.openclaw/workspace-auditor/",
    "librarian": "~/.openclaw/workspace-librarian/",
}

# 3. Librarian's own storage
LIBRARIAN_DB = "~/.openclaw/workspace-librarian/librarian.db"
AUDITS_DIR = "~/.openclaw/workspace-librarian/audits/"
PROPOSALS_DIR = "~/.openclaw/workspace-librarian/proposals/"

# 4. Memory files
MEMORY_DIR = "~/.openclaw/workspace/memory/"

# 5. GitHub (via gh CLI)
# gh repo list, gh pr list, gh issue list — subprocess calls
```

---

## 4. Post-Audit Analysis Engine

### 4.1 Reconstructing Project History

The analysis engine combines three data streams:

**Stream 1 — Git History:**
```bash
# Commits with timing and changed files
git log --all --pretty=format:"%H|%ai|%s|%an" --name-status

# Full diffs for pattern matching
git log --all -p --since="<project_start>"

# Identify "fix" commits (signal of problems)
git log --all --grep="fix\|revert\|hotfix\|retry\|again" --oneline
```

**Stream 2 — OpenClaw Memory Files:**
```python
# Read daily memory files for project references
for md_file in sorted(glob("~/.openclaw/workspace/memory/*.md")):
    content = open(md_file).read()
    if project_name.lower() in content.lower():
        # Extract mentions, timestamps, agent dispatches
        parse_memory_file(content)
```

**Stream 3 — Session Transcripts:**
```python
# JSONL files contain full message history
import json

def parse_session(session_path):
    messages = []
    with open(session_path) as f:
        for line in f:
            msg = json.loads(line)
            messages.append({
                "role": msg.get("role"),
                "content": msg.get("content"),
                "timestamp": msg.get("timestamp"),
                "tool_calls": msg.get("tool_calls", [])
            })
    return messages
```

### 4.2 Metrics & Patterns to Analyze

| Metric | How to Measure | Signal |
|--------|---------------|--------|
| Time to completion | First commit → final push (git log timestamps) | >2x expected = problems |
| Re-dispatch count | Count Jarvis sessions_spawn calls for same task | >1 = agent struggled |
| Error frequency | grep for error keywords in sessions | High = needs better guidance |
| Agent handoffs | Count sessions_send calls in transcripts | Many = coordination overhead |
| Fix commit ratio | Commits containing "fix" / total commits | >30% = unstable development |
| Security issues | Quality Agent critical/warning counts | Any critical = process gap |
| Plan adherence | Does final code match Planner's PLAN.md spec? | Deviations = spec quality issue |
| Tool usage efficiency | Most-used tools per agent | Mismatches = wrong tools allowed |

### 4.3 Identifying "Key Challenges" Programmatically

**Algorithm:**

```python
def identify_challenges(project_path, sessions):
    challenges = []
    
    # Pattern 1: Re-dispatched agents
    dispatch_counts = count_agent_dispatches(sessions)
    for agent, count in dispatch_counts.items():
        if count > 1:
            challenges.append({
                "type": "re_dispatch",
                "agent": agent,
                "count": count,
                "severity": "MEDIUM" if count == 2 else "HIGH"
            })
    
    # Pattern 2: Fix commits
    fix_commits = git_log_grep(project_path, 
                               r"fix|revert|hotfix|retry|again|wrong")
    if len(fix_commits) > 0:
        challenges.append({
            "type": "fix_commits",
            "commits": fix_commits,
            "severity": "MEDIUM"
        })
    
    # Pattern 3: Long sessions (> 30 min for typical task)
    long_sessions = [s for s in sessions if s.duration_minutes > 30]
    for session in long_sessions:
        challenges.append({
            "type": "long_session",
            "session_id": session.id,
            "agent": session.agent,
            "duration": session.duration_minutes,
            "severity": "LOW"
        })
    
    # Pattern 4: Quality findings
    quality_findings = extract_quality_findings(sessions)
    for finding in quality_findings:
        if finding.severity in ["CRITICAL", "WARNING"]:
            challenges.append({
                "type": "security_finding",
                "finding": finding,
                "severity": "HIGH" if "CRITICAL" in finding.severity else "MEDIUM"
            })
    
    return sorted(challenges, key=lambda x: severity_rank[x["severity"]])
```

### 4.4 Generating AGENTS.md Improvement Suggestions

The key principle: **translate challenge patterns into specific instructions.**

| Challenge Pattern | Improvement Strategy |
|-------------------|---------------------|
| Coder re-dispatched for import error | Add import verification step to completion checklist |
| Planner spec missing tech details | Add "research dependencies first" rule |
| Quality found secrets in code | Add pre-commit hook instruction to Coder |
| Long planning session (>1 hour) | Add timeboxing guidance to Planner |
| Agent asked clarifying questions | Add "assume standard defaults if unclear" rule |
| Agent produced wrong file format | Add explicit format examples |
| Security audit found IP addresses | Add IP scrubbing to Coder's pre-commit checklist |

**Prompt template for LLM-generated suggestions:**

```python
SUGGESTION_PROMPT = """
You are analyzing a software development project to improve AI agent configurations.

PROJECT: {project_name}
CHALLENGE: {challenge_description}
EVIDENCE: {evidence}
AFFECTED_AGENT: {agent_name}
CURRENT AGENTS.MD SECTION:
{current_section}

Based on this challenge, propose a specific, concrete change to the agent's AGENTS.md that would prevent this problem in future projects.

Requirements:
- Be specific (add a checklist item, rule, or example — not vague advice)
- Keep the change minimal (one targeted improvement)
- Explain WHY this helps
- Output as a unified diff

Output format:
CONFIDENCE: HIGH/MEDIUM/LOW
REASONING: <one sentence>
DIFF:
<unified diff>
"""
```

### 4.5 Audit Report Template (Detailed)

```markdown
# Post-Audit Report: {project_name}

**Audit ID:** AUDIT-{YYYY-MM-DD}-{project_slug}
**Audited by:** Librarian 📚
**Date:** {date}
**Repo:** {repo_url}
**Commits analyzed:** {commit_count}
**Period:** {start_date} → {end_date}
**Sessions analyzed:** {session_count}

---

## Executive Summary

{2-3 sentence summary of project, quality, and key findings}

**Overall assessment:** ✅ Smooth / ⚠️ Some friction / 🔴 Significant issues

---

## Project Timeline

| Timestamp | Event | Agent | Outcome | Notes |
|-----------|-------|-------|---------|-------|
| {ts} | Task requested | Jarvis | ✅ | "{task summary}" |
| {ts} | Planner dispatched | Planner | ✅ | Plan created in {N} min |
| {ts} | Coder dispatched (attempt 1) | Coder | ⚠️ | Import error |
| {ts} | Coder re-dispatched | Coder | ✅ | Fixed, tests pass |

---

## Commit History

| SHA | Message | Files Changed | Assessment |
|-----|---------|--------------|------------|
| {sha} | {msg} | {files} | ✅ Feature |
| {sha} | fix: {msg} | {files} | ⚠️ Rework |

**Fix commit ratio:** {fix_count}/{total} ({pct}%) 
{> 25%: ⚠️ Elevated rework | < 25%: ✅ Healthy}

---

## Key Challenges

### Challenge 1: {title}
- **Type:** re_dispatch / fix_commit / security_finding / long_session
- **Severity:** HIGH / MEDIUM / LOW
- **What happened:** {description}
- **Evidence:** {commit SHA or session reference}
- **Estimated impact:** {time lost or risk level}
- **Root cause:** {analysis}

---

## Agent Performance Summary

| Agent | Dispatches | Success | Re-dispatches | Avg Duration | Assessment |
|-------|-----------|---------|--------------|-------------|------------|
| Planner | 1 | ✅ | 0 | 22 min | Excellent |
| Coder | 2 | ✅ | 1 | 31 min | Needs checklist |
| Quality | 1 | ✅ | 0 | 8 min | Excellent |
| Auditor | 1 | ✅ | 0 | 3 min | Excellent |

---

## Proposed Improvements

{N} change proposals generated. See `librarian/proposals/` for diffs.

| ID | Agent | File | Confidence | Status |
|----|-------|------|-----------|--------|
| P001 | Coder | AGENTS.md | HIGH | Pending |
| P002 | Planner | AGENTS.md | MEDIUM | Pending |

---

## Learnings Accumulated

1. {learning 1}
2. {learning 2}

---

## Metadata

- Librarian version: {version}
- Analysis model: Claude Opus 4.6
- Generated: {timestamp}
```

---

## 5. Approval Workflow

### 5.1 How Changes Are Proposed (Diff Format)

Each proposal is saved as a patch file in `workspace-librarian/proposals/`:

```
workspace-librarian/
└── proposals/
    ├── P001-coder-agents-import-check.patch
    ├── P001-coder-agents-import-check.meta.json
    ├── P002-planner-agents-docker-spec.patch
    └── P002-planner-agents-docker-spec.meta.json
```

**Patch file format (standard unified diff):**
```diff
--- a/workspace-coder/AGENTS.md
+++ b/workspace-coder/AGENTS.md
@@ -45,6 +45,12 @@
 ## Completion Checklist
 - [ ] All files written
 - [ ] Tests pass
+- [ ] **Verify imports run cleanly:**
+  ```bash
+  python3 -c "import <main_module>" 2>&1
+  ```
+  If import fails, fix before reporting complete.
 - [ ] No syntax errors
```

**Metadata file format:**
```json
{
  "id": "P001",
  "created": "2026-03-09T16:45:00Z",
  "source_audit": "AUDIT-2026-03-09-contract-analyzer",
  "source_project": "ContractAnalyzer",
  "target_agent": "coder",
  "target_file": "workspace-coder/AGENTS.md",
  "confidence": "HIGH",
  "reasoning": "Coder was re-dispatched due to import error caught during QA. A verification step in the completion checklist would have caught this.",
  "status": "PENDING",
  "reviewed_at": null,
  "reviewed_by": "Eric",
  "decision": null,
  "decision_notes": null,
  "applied_at": null,
  "rollback_sha": null
}
```

### 5.2 How Eric Reviews

**Primary: Web UI (Librarian Dashboard → Change Proposals screen)**
- Visual diff with syntax highlighting
- Approve / Reject / Comment / Defer buttons per proposal
- See full context (which project triggered it, confidence, reasoning)

**Secondary: Telegram**
When proposals are ready, Librarian notifies Jarvis, who forwards to Eric:

```
📚 Librarian: ContractAnalyzer audit complete.

3 improvement proposals generated:
• P001: Coder AGENTS.md — import verification [HIGH confidence]
• P002: Planner AGENTS.md — Docker spec detail [MEDIUM confidence]
• P003: Quality AGENTS.md — test file scanning [HIGH confidence]

Review at: http://localhost:8501 (Librarian Dashboard)
Or reply with: approve P001, reject P002, etc.
```

Jarvis handles Telegram-based approval commands:
- "approve P001" → Jarvis tells Librarian to apply P001
- "reject P002" → Librarian marks P002 rejected
- "approve all" → Eric approves all pending proposals (use carefully)
- "show P001 diff" → Jarvis sends the diff text in Telegram

### 5.3 How Approved Changes Are Applied

```python
def apply_proposal(proposal_id):
    meta = load_proposal_meta(proposal_id)
    patch_file = f"proposals/{proposal_id}.patch"
    target_file = meta["target_file"]
    
    # 1. Record pre-change SHA for rollback
    pre_sha = sha256_of_file(target_file)
    meta["rollback_sha"] = pre_sha
    
    # 2. Apply the patch
    result = subprocess.run(
        ["patch", "-p1", "--input", patch_file, target_file],
        capture_output=True
    )
    
    if result.returncode != 0:
        raise Exception(f"Patch failed: {result.stderr}")
    
    # 3. Update metadata
    meta["status"] = "APPLIED"
    meta["applied_at"] = datetime.utcnow().isoformat()
    save_proposal_meta(proposal_id, meta)
    
    # 4. Log to audit trail
    append_audit_trail({
        "action": "PROPOSAL_APPLIED",
        "proposal_id": proposal_id,
        "target_file": target_file,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # 5. Notify Jarvis
    notify_jarvis(f"✅ Proposal {proposal_id} applied to {target_file}")
```

### 5.4 Rollback Mechanism

```python
def rollback_proposal(proposal_id):
    meta = load_proposal_meta(proposal_id)
    
    if meta["status"] != "APPLIED":
        raise Exception("Proposal not applied — nothing to roll back")
    
    # Reverse-apply the patch
    result = subprocess.run(
        ["patch", "-p1", "--reverse", "--input", 
         f"proposals/{proposal_id}.patch"],
        capture_output=True
    )
    
    meta["status"] = "ROLLED_BACK"
    meta["rolled_back_at"] = datetime.utcnow().isoformat()
    save_proposal_meta(proposal_id, meta)
    
    append_audit_trail({
        "action": "PROPOSAL_ROLLED_BACK",
        "proposal_id": proposal_id,
        "timestamp": datetime.utcnow().isoformat()
    })
```

### 5.5 Audit Trail

All approval events are logged to an append-only SQLite database and to a plain text log:

```
workspace-librarian/
├── librarian.db          ← SQLite (proposals, audits, approvals)
└── audit-trail.log       ← Human-readable append-only log

Example audit-trail.log:
2026-03-09T16:45:00Z PROPOSAL_CREATED P001 coder AGENTS.md HIGH
2026-03-09T17:02:00Z PROPOSAL_REVIEWED P001 Eric APPROVED
2026-03-09T17:02:01Z PROPOSAL_APPLIED  P001 workspace-coder/AGENTS.md
2026-03-10T09:15:00Z PROPOSAL_CREATED P002 planner AGENTS.md MEDIUM
2026-03-10T09:30:00Z PROPOSAL_REVIEWED P002 Eric REJECTED "Too vague"
```

---

## 6. Self-Learning Loop Design

### 6.1 How Learnings Accumulate Over Time

```
Project 1 → Audit → 3 proposals (2 approved, 1 rejected)
                          │
                          ▼
                   workspace-coder/AGENTS.md (updated)
                          │
Project 2 → Audit → fewer issues in Coder, 1 new proposal
                          │
                          ▼
                   workspace-planner/AGENTS.md (updated)
                          │
Project 3 → Audit → agents now more aligned with Eric's patterns
                          │
                          ▼
              Metrics show: 40% reduction in re-dispatches
```

**Librarian maintains a `LEARNINGS.md` in its workspace:**

```markdown
# LEARNINGS.md — Accumulated Wisdom

## Coder Agent Patterns
- **Import verification** (applied P001, 2026-03-09): Always check
  imports before marking Python tasks complete
- **Dockerfile ENV vars** (applied P007, 2026-03-15): Include
  ENV directives in Dockerfile spec

## Planner Agent Patterns
- **API research first** (applied P003, 2026-03-11): Research
  third-party API availability before speccing it

## Quality Agent Patterns
- **Test file scanning** (applied P002, 2026-03-10): Include
  test/ directory in security scan

## Rejected Proposals (and Why)
- P004 (rejected): Too prescriptive about commit message format
  — Eric: "I don't care about commit messages"
- P006 (rejected): Suggested restricting Planner's tool set
  — Eric: "Planner needs flexibility"
```

### 6.2 Preventing Drift/Degradation

**Risk:** Accumulated changes could make agents over-specified, rigid, or conflicting.

**Safeguards:**

1. **Confidence thresholds:** Only auto-present HIGH confidence proposals. MEDIUM/LOW need an extra review step.

2. **Change frequency limits:** No agent's AGENTS.md should receive more than 3 approved changes per month without a human review of the full file.

3. **Conflict detection:** Before applying a proposal, check if it contradicts recently approved changes.

4. **Periodic AGENTS.md review:** Monthly, Librarian generates a "health check" report on each agent's AGENTS.md — checking for contradictions, over-length, and deprecated instructions.

5. **Rejection learning:** When Eric rejects a proposal with a reason, that reason is saved. Future similar proposals are flagged: "Warning: similar to previously rejected P004 — Eric rejected due to: '{reason}'"

### 6.3 Feedback Mechanisms

| Signal | Source | How Used |
|--------|--------|---------|
| Proposal approved | Eric | Positive signal — this type of improvement works |
| Proposal rejected + reason | Eric | Negative signal — don't suggest this category again |
| Re-dispatch count decreasing | git/session metrics | Macro confirmation learning is working |
| Eric adds custom notes to AGENTS.md | File watcher | Eric's manual edits are ground truth — preserve them |
| Eric says "Librarian, this worked well" | Telegram | Capture as positive feedback |
| Eric says "that change made things worse" | Telegram | Immediately offer rollback |

### 6.4 Metrics to Track Improvement

Librarian maintains a `metrics.json` file updated after each audit:

```json
{
  "projects_audited": 4,
  "proposals_generated": 12,
  "proposals_approved": 9,
  "proposals_rejected": 3,
  "approval_rate": 0.75,
  "avg_re_dispatches_per_project": {
    "all_time": 1.8,
    "last_3": 0.9,
    "trend": "improving"
  },
  "avg_time_to_complete_hours": {
    "all_time": 2.3,
    "last_3": 1.7,
    "trend": "improving"
  },
  "fix_commit_ratio": {
    "all_time": 0.28,
    "last_3": 0.18,
    "trend": "improving"
  },
  "quality_findings_per_project": {
    "all_time": 0.5,
    "last_3": 0.25,
    "trend": "improving"
  }
}
```

### 6.5 Safety Guardrails

| Guardrail | Implementation |
|-----------|---------------|
| Eric always approves | No change is ever applied without explicit approval |
| No auto-approval | Even HIGH confidence proposals require human sign-off |
| Rollback available | Every applied change can be reversed in one command |
| Audit trail immutable | append-only log; Librarian cannot delete it |
| Scope limited | Librarian only writes to its own workspace + proposals dir |
| No production changes | Librarian writes patches; patch tool applies them |
| Dry-run mode | `librarian audit --dry-run` shows proposals without saving |

---

## 7. Implementation Phases

### Phase 1: Basic Agent + CLI Audit Reports
**Timeframe:** 1-2 days  
**Effort:** 4-6 hours of coding + configuration

**Deliverables:**
- [ ] Add Librarian to `openclaw.json`
- [ ] Create `workspace-librarian/` with AGENTS.md, IDENTITY.md
- [ ] Write `librarian-audit.sh` CLI script that:
  - Takes a project path as argument
  - Runs git log analysis
  - Reads memory files
  - Calls Claude API with analysis prompt
  - Outputs Markdown audit report
- [ ] Create `workspace-librarian/audits/` and `proposals/` dirs
- [ ] Test manually: run audit on ContractAnalyzer

**Cost estimate:** ~$2-5 in API calls per audit

---

### Phase 2: Web UI for File Browsing and Project Views
**Timeframe:** 3-5 days  
**Effort:** 12-20 hours of coding

**Deliverables:**
- [ ] Install Streamlit: `pip install streamlit gitpython`
- [ ] Build app with 4 screens: Dashboard, File Browser, Project View, Audit Reports
- [ ] Wire up git log parsing and memory file reading
- [ ] Create `workspace-librarian/app/librarian_app.py`
- [ ] Create launch script: `openclaw workspace/scripts/start-librarian-ui.sh`
- [ ] Test: browse ContractAnalyzer and ProjectScraper project views

**Cost estimate:** $0 (local Streamlit, no additional API calls)  
**How to start:** `streamlit run ~/.openclaw/workspace-librarian/app/librarian_app.py`

---

### Phase 3: Automated Post-Audit on GitHub Push
**Timeframe:** 1-2 days  
**Effort:** 3-5 hours

**Deliverables:**
- [ ] Write `git-post-push-hook.sh` (sends message to Jarvis)
- [ ] Update Jarvis's AGENTS.md to include "dispatch Librarian after GitHub push" rule
- [ ] Install hook in ContractAnalyzer and ProjectScraper
- [ ] Test: push a commit, verify Jarvis auto-dispatches Librarian

**Alternative (more robust):**
- [ ] Set up `smee.io` as GitHub webhook relay
- [ ] Write webhook listener script that triggers Librarian
- [ ] Configure GitHub repo webhooks

---

### Phase 4: Change Proposal and Approval Workflow
**Timeframe:** 3-5 days  
**Effort:** 12-20 hours

**Deliverables:**
- [ ] SQLite database schema for proposals + audit trail
- [ ] Proposal generation engine (LLM-powered diff generation)
- [ ] Patch file writer and applier
- [ ] Web UI screen: Change Proposals with approve/reject buttons
- [ ] Telegram approval flow (Jarvis relay)
- [ ] Rollback mechanism
- [ ] Test: generate proposals for ContractAnalyzer, approve one, verify AGENTS.md updated

**Cost estimate:** ~$3-8 per project audit (LLM calls for proposal generation)

---

### Phase 5: Metrics Dashboard and Learning Analytics
**Timeframe:** 2-3 days  
**Effort:** 8-12 hours

**Deliverables:**
- [ ] Metrics collection and storage in `metrics.json`
- [ ] Dashboard screen: trend charts (Streamlit `st.line_chart`)
- [ ] Rejection learning (save rejection reasons, flag similar future proposals)
- [ ] `LEARNINGS.md` auto-generation and maintenance
- [ ] Monthly AGENTS.md health check report
- [ ] End-to-end test: 3 full project cycles, verify metrics improving

**Cost estimate:** $0 (metrics are aggregated from existing data)

---

### Phase Summary

| Phase | Days | Dev Hours | API Cost/Audit | Milestone |
|-------|------|-----------|---------------|-----------|
| 1 | 1-2 | 4-6h | ~$2-5 | First CLI audit report |
| 2 | 3-5 | 12-20h | $0 | Working web UI |
| 3 | 1-2 | 3-5h | $0 | Auto-triggered audits |
| 4 | 3-5 | 12-20h | ~$3-8 | Approve/reject workflow |
| 5 | 2-3 | 8-12h | $0 | Metrics + learning loop |
| **Total** | **10-17 days** | **39-63h** | **~$5-13/audit** | Full system |

---

## 8. Technical Requirements

### 8.1 Dependencies & Tools

**New Python packages:**
```bash
pip install streamlit>=1.31.0    # Web UI
pip install gitpython>=3.1.41    # Git repo parsing
pip install sqlite3              # Built into Python 3
pip install anthropic>=0.25.0   # LLM calls (already installed)
pip install python-dotenv        # Env var management
pip install watchdog             # Optional: file system watcher
pip install rich                 # CLI output formatting
```

**System tools (already available):**
- `git` — version control
- `gh` — GitHub CLI (for PR/issue data)
- `patch` — applying diff files
- `diff` — generating diffs

**New files to create:**
```
~/.openclaw/workspace-librarian/
├── AGENTS.md           ← Librarian's instructions
├── IDENTITY.md         ← Name and persona
├── SOUL.md             ← Personality (optional)
├── librarian.db        ← SQLite database
├── LEARNINGS.md        ← Accumulated wisdom
├── audit-trail.log     ← Append-only change log
├── metrics.json        ← Learning metrics
├── audits/             ← Audit reports per project
│   └── AUDIT-*.md
├── proposals/          ← Change proposals
│   ├── P001.patch
│   ├── P001.meta.json
│   └── ...
├── app/
│   ├── librarian_app.py      ← Streamlit main app
│   ├── pages/
│   │   ├── 01_dashboard.py
│   │   ├── 02_file_browser.py
│   │   ├── 03_chat_history.py
│   │   ├── 04_project_view.py
│   │   ├── 05_audit_reports.py
│   │   └── 06_proposals.py
│   └── lib/
│       ├── git_analysis.py    ← Git log parsing
│       ├── session_parser.py  ← JSONL session parsing
│       ├── proposal_engine.py ← LLM diff generation
│       └── db.py              ← SQLite helpers
└── scripts/
    ├── librarian-audit.sh     ← CLI audit runner
    └── git-post-push-hook.sh  ← Git hook
```

### 8.2 Storage Requirements

| Data | Estimated Size |
|------|---------------|
| Audit reports (per project) | 10-50 KB each |
| Patch files (per proposal) | 1-5 KB each |
| Session transcript JSONL files | 100KB - 2MB per session |
| SQLite database | <1 MB after 100 audits |
| audit-trail.log | ~5 KB per 100 events |
| **Total for 1 year** | **~50-200 MB** |

No significant storage concern. All data fits comfortably on the MacBook Pro.

### 8.3 API Integrations

**Anthropic API (existing):**
- Used by Librarian agent for: history reconstruction, challenge identification, proposal generation
- Estimated cost: $3-8 per full project audit (1-2 Claude Opus calls)
- Uses existing auth profile `anthropic:default`

**GitHub API (via `gh` CLI, existing auth):**
```bash
# Existing gh auth — verify with:
gh auth status

# APIs used by Librarian:
gh api repos/{owner}/{repo}/commits       # Commit list
gh api repos/{owner}/{repo}/pulls         # PRs
gh api repos/{owner}/{repo}/issues        # Issues
gh pr list --json number,title,body       # PR details
gh issue list --json number,title,body    # Issue details
```

**OpenClaw sessions_send (existing):**
- Librarian sends audit completion notifications to Jarvis
- Jarvis relays proposals to Eric via Telegram

**No new API keys needed.** All integrations use existing credentials.

### 8.4 Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Librarian reads all workspaces | Only runs locally; no external data exfiltration |
| Patch files could corrupt AGENTS.md | Verify patch applies cleanly before executing; rollback always available |
| Session transcripts contain sensitive data | Librarian reads locally only; never uploads sessions anywhere |
| GitHub credentials in gh CLI | Existing auth; Librarian never handles tokens directly |
| Web UI exposed on localhost | Streamlit binds to `127.0.0.1:8501` by default; not accessible externally |
| Proposal injection attacks | Librarian generates proposals; only `patch` binary applies them; Eric reviews before apply |
| LLM prompt injection via code | Analysis engine sanitizes commit messages before including in prompts |
| Audit trail tampering | Append-only log; use `chattr +a audit-trail.log` to make it OS-level append-only |

**Key principle:** Librarian never has the authority to modify production files directly. It writes to `proposals/` only. The `patch` command, triggered by an explicit approval action, makes the actual change. Eric's approval is the mandatory gate.

---

## Appendix A: Jarvis AGENTS.md Addition

Add this section to the main `AGENTS.md` (after the External Auditor pipeline entry):

```markdown
### → Librarian Agent (agentId: librarian)
Trigger: AFTER External Auditor completes AND code is pushed to GitHub.
This is the FINAL + ONGOING step — it triggers the learning loop.

**When to dispatch:**
- After any project is pushed to GitHub
- When Eric says "audit [project name]"
- When Eric says "show me proposals" or "any learnings?"

Action: spawn librarian with project path and repo URL. Librarian will:
1. Reconstruct project history from git + memory files + sessions
2. Identify challenges and patterns
3. Generate change proposals (diffs) for affected agents
4. Notify Jarvis with audit summary
5. Jarvis forwards summary to Eric via Telegram
6. Eric reviews proposals at http://localhost:8501 or via Telegram commands

**Approval commands Eric can use:**
- "approve P001" → Jarvis tells Librarian to apply the patch
- "reject P002 too prescriptive" → Librarian marks rejected with reason
- "show proposals" → Jarvis lists all pending proposals
- "show P001 diff" → Jarvis sends the patch text

## 🔄 Updated Complete Code Pipeline

Eric request → Planner (if new project) → Coder (implementation)
  → Quality Agent (security audit)
    → If CRITICAL: Jarvis runs BFG, loop back to Quality
    → If CLEAN: proceed
  → External Auditor (asks Eric about Grok review)
    → If YES: repomix packages code → Eric uploads to Grok
    → If NO: done
  → **Librarian (post-audit, learning loop)**
    → Analyzes project history
    → Generates improvement proposals
    → Eric approves/rejects
    → Agents get smarter for next project ♻️
  → Code shipped + agents improved ✅
```

---

## Appendix B: Quick Start Checklist (Phase 1)

```bash
# 1. Create Librarian workspace
mkdir -p ~/.openclaw/workspace-librarian/{audits,proposals,app/pages,app/lib,scripts}

# 2. Add to openclaw.json (use openclaw agents add or edit manually)
# (see agent config in Section 2.1)

# 3. Create AGENTS.md and IDENTITY.md
# (see content in Section 2.3 and 2.4)

# 4. Test dispatch from Jarvis:
# "Librarian, audit ContractAnalyzer"

# 5. Verify audit report saved to:
ls ~/.openclaw/workspace-librarian/audits/

# 6. Run Phase 1 audit manually:
# cd /Users/ericbrown/ContractAnalyzer
# ~/.openclaw/workspace-librarian/scripts/librarian-audit.sh .

# 7. Restart gateway to pick up new agent:
openclaw gateway restart
```

---

*End of Librarian Agent Plan v1.0*  
*Generated by Jarvis Research Subagent — 2026-03-10*  
*Save location: `/Users/ericbrown/.openclaw/workspace/plans/librarian-agent-plan.md`*
