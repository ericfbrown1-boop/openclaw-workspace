# POWERSPEC.md — Mandatory PowerSpec-First Execution Policy

## ⚠️ PowerSpec is the PRIMARY compute resource. Not optional.

**SSH:** `ssh ericf@100.67.128.123`
**Tailscale hostname:** remote-coder-main
**IP:** 100.67.128.123
**OS:** Windows 11 25H2 (WSL2 + Docker available)
**CPU:** 32 vCPUs | **RAM:** 128 GB | **GPU:** NVIDIA RTX 5080 (16GB VRAM, CUDA 13.1)
**Docker:** Docker Desktop with NVIDIA Container Toolkit

## Pre-Task Check (MANDATORY)
```bash
tailscale ping remote-coder-main && ssh ericf@100.67.128.123 "hostname && nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader"
```
If unreachable: 3 retries (30s apart) → alert Eric → fall back to MacBook ONLY with Eric's acknowledgment → log in `memory/incidents.jsonl`.

## MUST Run on PowerSpec
- ANY Docker build or image creation
- ANY test suite execution
- ANY Next.js production build
- ANY research/data processing >5 min
- ANY AI/ML/GPU workload
- ANY codebase >10K lines
- ANY task estimated >15 minutes

## MUST Run on MacBook
- pm2 process management (local services)
- Mission Control UI serving (localhost:3000/3001)
- OpenClaw gateway operation
- Tailscale/network management
- Quick file edits and git operations (<2 min)
- Email/message sending (gog, mcporter)

## File Transfer
**Note:** rsync doesn't work on Windows SSH. Use git (clone from GitHub into PowerSpec) or scp for small files.

**Git approach (preferred):**
```bash
# On PowerSpec — pull latest from GitHub
ssh ericf@100.67.128.123 "powershell -Command \"git -C C:\\Users\\ericf\\projects\\<project> pull origin main\""
```

**WSL for Linux tools:**
```bash
ssh ericf@100.67.128.123 "powershell -Command \"wsl bash /path/to/script.sh\""
```

## Planner Rule
Every PLAN.md MUST include a "Compute Allocation" table:
```markdown
| Task | Host | Reason |
|------|------|--------|
| Docker build | PowerSpec | Heavy compute |
| pm2 setup | MacBook | Local service |
```
Plans without this table are INCOMPLETE — send back for revision.

## Researcher Rule
ALL data scraping, financial processing, document generation → PowerSpec. Sync outputs back via git push before handoff.

## Coder Rule
ALL builds + Docker work → PowerSpec. Record which host ran each command in HANDOFF.md.

## Monitor Rule
Check PowerSpec utilization every 5 minutes. GPU util <5% while tasks queued → alert Conductor. Offline while tasks queued → alert Eric.
