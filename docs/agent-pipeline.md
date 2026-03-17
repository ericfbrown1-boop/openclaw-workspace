# Jarvis Agent Pipeline — How All 8 Agents Work Together

## Research Workflow

```mermaid
flowchart TD
    Eric["👤 Eric\n(Request via Telegram/Web)"]

    subgraph Orchestrator["🤖 Jarvis — Orchestrator (Opus 4.6)"]
        J_route{{"Route Request"}}
    end

    subgraph Research["Research Path"]
        R["🔬 Oracle — Researcher\n(Sonnet 4.6)\nWeb search, financial analysis,\ncompetitive intel, fact-checking"]
    end

    Eric -->|"Research request"| J_route
    J_route -->|"Standalone research\n(not a new project)"| R
    R -->|"Findings & analysis"| J_route
    J_route -->|"Formatted report"| Eric

    style Eric fill:#4a90d9,color:#fff,stroke:#2d6cb4
    style J_route fill:#ff6b35,color:#fff,stroke:#cc5529
    style R fill:#7b68ee,color:#fff,stroke:#5a4bc7
```

## Code Pipeline (New Project, End-to-End)

```mermaid
flowchart TD
    Eric["👤 Eric\n(Request via Telegram/Web)"]

    subgraph Orchestrator["🤖 Jarvis — Orchestrator (Opus 4.6)"]
        J_route{{"Classify & Route"}}
        J_merge["Merge reviews\nProduce final PLAN.md"]
        J_relay["Relay audit prompt\nto Eric"]
        J_done["✅ Ship It"]
    end

    subgraph Planning["Phase 1: Architecture"]
        P["📐 Architect — Planner\n(GPT 5.4)\nSystem design, tech stack,\nPLAN.md + PROJECT_CONTEXT.md"]
        GPT["🧠 GPT 5.4 Cross-Review\nSpeed + fresh perspective\non Planner output"]
        COND_PRE["🚂 Conductor Preflight\n(Sonnet 4.6)\nVerify Docker, Railway,\nenv vars ready"]
    end

    subgraph Implementation["Phase 2: Build"]
        C["⚙️ Scotty — Coder\n(Sonnet 4.6)\nReads PLAN.md → writes code\nCHECKPOINT.md at each phase\nHANDOFF.md on completion"]
    end

    subgraph Testing["Phase 3: Test"]
        T["🧪 Tester\n(via Quality/Coder)\nImport verification\n+ test suite execution"]
    end

    subgraph QualityGate["Phase 4: Quality Gate"]
        Q_SEC["🔍 Inspector — Quality\n(Sonnet 4.6)\nPart B: Security Audit\nSecrets, deps, Tailscale checks"]
        Q_CODE["🔍 Inspector — Quality\n(Sonnet 4.6)\nPart C: Code Quality Review\nBest practices, patterns"]
    end

    subgraph Audit["Phase 5: External Review"]
        A["🛡️ External Auditor\n(Sonnet 4.6)\nPackages code via repomix\nOffers Grok review option"]
    end

    subgraph Deploy["Phase 6: Deploy"]
        COND["🚂 Conductor\n(Sonnet 4.6)\nDocker build → Railway deploy\n→ smoke tests"]
    end

    subgraph PostDeploy["Phase 7: Learn"]
        LIB["📚 Librarian\n(via Jarvis)\nPost-audit review\nSuggests agent improvements"]
    end

    subgraph Background["Always Running"]
        M["📡 Sentinel — Monitor\n(Sonnet 4.6)\nStock alerts, price watches,\nsystem health, cron jobs"]
    end

    %% Main flow
    Eric -->|"New project request"| J_route
    J_route -->|"Plan it"| P

    P -->|"Draft PLAN.md"| GPT
    P -->|"Check infra"| COND_PRE
    GPT -->|"Review notes"| J_merge
    COND_PRE -->|"Env ready ✅"| J_merge

    J_merge -->|"Final PLAN.md"| C
    C -->|"HANDOFF.md"| T

    T -->|"❌ FAIL"| C
    T -->|"✅ PASS"| Q_SEC
    T -->|"✅ PASS"| Q_CODE

    Q_SEC -->|"🔴 CRITICAL"| C
    Q_SEC -->|"✅ CLEAN"| A
    Q_CODE -->|"✅ CLEAN"| A

    A -->|"Prompt: Grok review?"| J_relay
    J_relay -->|"Eric decides"| Eric
    Eric -->|"Yes/No"| A

    A -->|"Done"| COND
    COND -->|"Deployed ✅"| LIB
    LIB -->|"Improvement suggestions"| J_done
    J_done -->|"Report"| Eric

    %% Monitor runs independently
    Eric -.->|"Check stocks,\nprice alerts"| M
    M -.->|"Alerts &\nnotifications"| Eric

    %% Error routing
    Eric -->|"Bug / error report"| J_route
    J_route -->|"Diagnose first\n(never straight to Coder)"| Q_SEC

    %% Research routing
    J_route -->|"Research request\n(not a project)"| R2["🔬 Oracle — Researcher\n(Sonnet 4.6)"]
    R2 -->|"Findings"| Eric

    %% Styling
    style Eric fill:#4a90d9,color:#fff,stroke:#2d6cb4
    style J_route fill:#ff6b35,color:#fff,stroke:#cc5529
    style J_merge fill:#ff6b35,color:#fff,stroke:#cc5529
    style J_relay fill:#ff6b35,color:#fff,stroke:#cc5529
    style J_done fill:#2ecc71,color:#fff,stroke:#27ae60
    style P fill:#9b59b6,color:#fff,stroke:#7d3c98
    style GPT fill:#f39c12,color:#fff,stroke:#d68910
    style COND_PRE fill:#1abc9c,color:#fff,stroke:#16a085
    style C fill:#e74c3c,color:#fff,stroke:#c0392b
    style T fill:#3498db,color:#fff,stroke:#2980b9
    style Q_SEC fill:#e67e22,color:#fff,stroke:#ca6f1e
    style Q_CODE fill:#e67e22,color:#fff,stroke:#ca6f1e
    style A fill:#95a5a6,color:#fff,stroke:#7f8c8d
    style COND fill:#1abc9c,color:#fff,stroke:#16a085
    style LIB fill:#8e44ad,color:#fff,stroke:#6c3483
    style M fill:#2c3e50,color:#fff,stroke:#1a252f
    style R2 fill:#7b68ee,color:#fff,stroke:#5a4bc7
```

## Agent Roster Summary

| # | Agent | Identity | Model | Role |
|---|-------|----------|-------|------|
| 1 | **Jarvis** (main) | 🤖 Jarvis | Opus 4.6 | Orchestrator — routes all requests, merges reviews, relays to Eric |
| 2 | **Researcher** | 🔬 Oracle | Sonnet 4.6 | Web research, financial analysis, competitive intel |
| 3 | **Planner** | 📐 Architect | GPT 5.4 | System architecture, PLAN.md creation, tech stack decisions |
| 4 | **Coder** | ⚙️ Scotty | Sonnet 4.6 | Implementation — reads PLAN.md, writes code, checkpoints |
| 5 | **Quality** | 🔍 Inspector | Sonnet 4.6 | Security audits, code quality, error diagnosis |
| 6 | **Auditor** | 🛡️ External Auditor | Sonnet 4.6 | Final review gate, repomix packaging, Grok review option |
| 7 | **Conductor** | 🚂 Conductor | Sonnet 4.6 | Infrastructure — Docker builds, Railway deploys, smoke tests |
| 8 | **Monitor** | 📡 Sentinel | Sonnet 4.6 | Background — stock alerts, price watches, system health |

## Key Rules

- **Errors always go to Quality first** — never straight to Coder
- **New projects always go to Planner first** — never straight to Coder
- **Every code task gets a Security Audit** (Quality Part B) before shipping
- **Planner output gets dual-model review** (GPT 5.4 cross-review)
- **Jarvis orchestrates everything** — Eric only needs to make the request and approve the Grok review prompt
