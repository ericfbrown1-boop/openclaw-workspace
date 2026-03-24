# Remote Coder Skill — PowerSpec-First Execution

## Purpose
PowerSpec (remote-coder-main) is the PRIMARY compute resource for all non-trivial work.
The MacBook is reserved for local services (pm2, OpenClaw gateway, Mission Control UI).

**This is not optional. Every agent must check this skill before executing any task.**

## Connection
- **SSH:** `ssh ericf@100.67.128.123`
- **Tailscale hostname:** remote-coder-main
- **Tailscale IP:** 100.67.128.123
- **OS:** Windows 11 25H2 (WSL2 available)
- **CPU:** 32 vCPUs
- **RAM:** 128 GB
- **GPU:** NVIDIA RTX 5080 (16GB VRAM, CUDA 13.1)
- **Docker:** Docker Desktop with NVIDIA Container Toolkit

## Pre-Task Check (MANDATORY)
Before ANY task execution, run:
```bash
tailscale ping remote-coder-main && ssh ericf@100.67.128.123 "hostname && nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader"
```
If unreachable: 3 retries (30s apart) → alert Eric → fall back to MacBook only with Eric's acknowledgment.

## Routing Rules

### MUST run on PowerSpec
- Docker builds (any size)
- Docker image creation
- Test suite execution (Jest, Cypress, pytest, etc.)
- Next.js production builds
- Data processing / scraping >5 minutes
- AI/ML workloads (training, inference, embeddings)
- Research data collection (ProjectScraper, API calls)
- Any task estimated >15 minutes
- Any codebase >10K lines

### MUST run on MacBook
- pm2 process management
- Mission Control UI serving (localhost:3000/3001)
- OpenClaw gateway operation
- Tailscale/network management
- Email/message sending (gog, mcporter)
- Quick git operations (<2 minutes)

## How to Run Tasks on PowerSpec

### One-liner execution
```bash
ssh ericf@100.67.128.123 "cd /path/to/project && <command>"
```

### Interactive session
```bash
ssh ericf@100.67.128.123
cd /path/to/project
<commands>
```

### Sync code TO PowerSpec
```bash
rsync -avz --exclude node_modules --exclude .next /local/project/ ericf@100.67.128.123:/home/ericf/projects/project-name/
```

### Sync results FROM PowerSpec
```bash
rsync -avz ericf@100.67.128.123:/home/ericf/projects/project-name/output/ /local/project/output/
```

### Docker on PowerSpec
```bash
ssh ericf@100.67.128.123 "cd /path/to/project && docker build -t myapp . && docker run --rm -p 8000:8000 myapp"
```

### GPU workloads on PowerSpec
```bash
ssh ericf@100.67.128.123 "cd /path/to/project && docker run --gpus all -v /home/ericf/data:/data myapp"
```

## For Planner Agent
Every PLAN.md must include a "Compute Allocation" table:
```markdown
## Compute Allocation
| Task | Host | Reason |
|------|------|--------|
| Docker build | PowerSpec | Heavy compute |
| pm2 setup | MacBook | Local service |
| Test suite | PowerSpec | 32 cores available |
| Deploy config | MacBook | Local gateway |
```
Plans without this table are INCOMPLETE.

## For Researcher Agent
- ALL data scraping → PowerSpec
- ALL financial data processing → PowerSpec
- ALL document generation (Word/PDF) → PowerSpec
- Sync outputs back via rsync before handoff

## For Coder Agent
- ALL builds → PowerSpec
- ALL Docker work → PowerSpec
- Git commit/push can happen from either machine
- Record which host ran each command in HANDOFF.md

## For Monitor Agent
- Check PowerSpec utilization every 5 minutes
- If GPU util <5% while tasks are queued → alert Conductor
- If PowerSpec offline while tasks are queued → alert Eric

## Escalation
- PowerSpec offline >5 min with active queue → CRITICAL → Telegram alert to Eric
- PowerSpec idle while tasks stalled → Conductor must offload immediately
- Any MacBook fallback must be logged in `memory/incidents.jsonl`
