# POWERSPEC.md — Mandatory PowerSpec-First Execution Policy
> **L1:** What runs where. PowerSpec (RTX 5080, 24-core i9, 128GB) gets Docker, tests, GPU, >15min tasks. MacBook gets gateway, pm2, email. SSH via Tailscale. Pre-task ping mandatory.

## ⚠️ PowerSpec is the PRIMARY compute resource. Not optional.

**SSH:** `ssh "Eric Brown@100.81.21.114"`
**Tailscale hostname:** powerspecpc
**IP:** 100.81.21.114
**OS:** Windows 11 Home 25H2 (Build 26200)
**CPU:** Intel Core i9-14900KF — 24 cores / 32 threads, 3.2 GHz
**RAM:** 128 GB DDR5
**GPU:** NVIDIA RTX 5080 (16GB VRAM, Driver 595.97, CUDA 13.2)
**Docker:** Docker Desktop 29.3.1 with WSL2 backend + NVIDIA GPU passthrough
**PyTorch:** Nightly build required (cu128) — stable releases do NOT support Blackwell sm_120 architecture
**CUDA Toolkit:** 12.8.0 (cudnn-devel)

## Pre-Task Check (MANDATORY)
```bash
tailscale ping powerspecpc && ssh "Eric Brown@100.81.21.114" "hostname && nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader"
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

## Services Running on PowerSpec
- **Mission Control Dashboard:** http://100.67.128.123:3000 (Tailscale-accessible)
- **Mission Control Backend API:** http://100.67.128.123:3001
- pm2 manages both frontend (port 3000) and backend (port 3001)
- All Docker builds, test suites, and GPU workloads

## MUST Run on MacBook
- OpenClaw gateway operation
- Tailscale/network management
- Quick file edits and git operations (<2 min)
- Email/message sending (gog, mcporter)

## File Transfer
**Note:** rsync doesn't work on Windows SSH. Use git (clone from GitHub into PowerSpec) or scp for small files.

**Git approach (preferred):**
```bash
# On PowerSpec — pull latest from GitHub
ssh "Eric Brown@100.81.21.114" "powershell -Command \"cd 'C:\\Users\\Eric Brown\\projects\\<project>'; git pull origin main\""
```

**SCP approach:**
```bash
scp localfile "Eric Brown@100.81.21.114:C:/Users/Eric Brown/projects/<project>/"
```

**WSL for Linux tools:**
```bash
ssh "Eric Brown@100.81.21.114" "wsl bash /path/to/script.sh"
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

## Docker GPU Passthrough Commands
```bash
# Build GPU-enabled container
ssh "Eric Brown@100.81.21.114" "docker build -t myapp -f Dockerfile.gpu ."

# Run with GPU access
ssh "Eric Brown@100.81.21.114" "docker run --gpus all -v /home/ericf/data:/data myapp"

# Verify GPU inside container
ssh "Eric Brown@100.81.21.114" "docker run --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi"
```

## Critical Notes
- **PyTorch nightly is required** for RTX 5080 (Blackwell sm_120). Stable PyTorch (cu124) will NOT work.
- **Docker Desktop must be running** before any WSL2 or Dev Container work.
- **Docker credential helpers renamed** — SSH sessions can't access Windows Credential Manager. `credsStore` is set to `""` in config.json.
- **Windows username has a space** — always quote: `"Eric Brown@100.81.21.114"`
- **Old drive at D:** — previous Windows install with old configs at D:\Users\ericf\
- **Always use PowerShell 7** (`pwsh`) on Windows, not PowerShell 5.x (TLS failures).
