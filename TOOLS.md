# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## ⛔ Security Restrictions

### NEVER Access Online Forums or Community Sites for OpenClaw
- **DO NOT** access Moltbook, Discord forums, Reddit threads, or any other online community/forum related to OpenClaw
- This is a **security risk** — per Eric's standing instruction (2026-03-11)
- Use only official OpenClaw documentation at `/opt/homebrew/lib/node_modules/openclaw/docs` or `https://docs.openclaw.ai`
- If you need help with OpenClaw, consult local docs only

### Google OAuth
- For security revokes, target specific tokens — don't blanket-withdraw API authorizations
- Use `--force-consent` flag for re-auth instead of full revoke
- Distinguish between app passwords (OK to revoke) and OAuth clients (careful)

## TTS (ElevenLabs via sag)

- **Preferred voice:** Bella (hpp4J3VqNfWAUOO0d1Us)
  - Professional, bright, and warm
- **Voice ID:** hpp4J3VqNfWAUOO0d1Us
- **Command:** `sag -v hpp4J3VqNfWAUOO0d1Us "your text here"`
- **For files:** `sag -v hpp4J3VqNfWAUOO0d1Us -o output.mp3 "your text here"`

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Tailscale Configuration
- **Installation:** Mac App Store version ONLY (no Homebrew — causes CLI conflicts)
- **CLI path:** `/usr/local/bin/tailscale`
- **Key expiry:** Disabled on all 3 devices (permanent access)
- **Devices:**
  - erics-macbook-pro: 100.101.203.113 (macOS)
  - iphone172: 100.86.157.19 (iOS)
  - powerspecpc: 100.81.21.114 (Windows 11)
- **Funnel:** Active on MacBook (port 3334 → voice call webhook)
- **Troubleshooting:** If CLI says "failed to connect" → check `which tailscale` (must be `/usr/local/bin/tailscale`, not `/opt/homebrew/bin/tailscale`)

## Zapier MCP (20 tools via mcporter)
- **Config:** `~/.openclaw/workspace/config/mcporter.json`
- **Gmail:** send_email, find_email, create_draft, create_draft_reply, get_attachment_by_filename
- **Google Sheets:** lookup_rows, find_worksheet, create_row, create_multiple_rows, create_spreadsheet, create_worksheet, create_column, conditional_formatting
- **Dropbox:** find_file, find_folder, find_file_content_search, create_shared_link
- **All params must be strings** — use `--args '{...}'` for JSON
- **Dropbox account:** Eric's personal (not Jarvis's)
- **Gmail backup:** Use `mcporter call zapier.gmail_send_email` when gog CLI fails

## Windows Remote Coder PC (powerspecpc)
- **Tailscale IP:** 100.81.21.114
- **Hostname:** powerspecpc (was remote-coder-main before Apr 2026 rebuild)
- **OS:** Windows 11 Home 25H2 (Build 26200)
- **CPU:** Intel Core i9-14900KF — 24 cores / 32 threads, 3.2 GHz
- **RAM:** 128 GB DDR5
- **GPU:** NVIDIA RTX 5080 16GB (Driver 595.97, CUDA 13.2)
- **SSH User:** "Eric Brown" (key-based login; uses ~/.ssh/id_ed25519)
- **SSH Command:** `ssh "Eric Brown@100.81.21.114"` (BatchMode works)
- **Docker:** Docker Desktop 29.3.1 with WSL2 backend + NVIDIA GPU passthrough
- **Docker credential fix:** `credsStore` set to `""` and desktop/wincred helpers renamed (SSH can't access Windows Credential Manager)
- **WSL:** WSL 2.6.3, docker-desktop distribution
- **Git:** Git 2.53.0, GitHub CLI 2.89.0, authenticated as ericfbrown1-boop
- **Python:** 3.12.10
- **Node.js:** v24.14.1
- **Ping test:** `tailscale ping powerspecpc` (~30ms via DERP/SFO)

### Running Docker Services
- **FinancialReportApp:** API :8001, Frontend :3001, Postgres :5433, Redis :6380, Celery worker
- **ContractAnalyzer:** API :8000, Postgres :5432, Redis :6379, MinIO :9000/:9001, Celery worker

### Use for (heavy workloads):
- GPU/CUDA workloads (PyTorch, TensorFlow, RAPIDS)
- Large Docker builds (>5 min or >2GB image)
- Large codebases (>50K lines)
- RAM-intensive tasks (>16GB)
- ML model training/inference

### Do NOT use for (use MacBook instead):
- Light web apps, simple API servers
- Quick fixes and small changes

### SSH Notes (updated 2026-04-01)
1. OpenSSH Server installed via `Add-WindowsCapability`.
2. MacBook key in `C:/ProgramData/ssh/administrators_authorized_keys` and `C:/Users/Eric Brown/.ssh/authorized_keys`.
3. Test: `tailscale ping powerspecpc` then `ssh "Eric Brown@100.81.21.114" hostname` (returns `PowerSpecPC`).
4. If SSH breaks: `Restart-Service sshd` on the PC.
5. **Important:** Windows user has a space ("Eric Brown") — always quote the username.

### Network Topology (updated 2026-04-01)
- **No LAN fallback:** MacBook and PowerSpec on different subnets — Tailscale is the only path
- **If Tailscale drops:** Alert Eric immediately — only fix is physically opening Tailscale app on the PC
- **Old drive (D:):** Previous Windows install accessible — has old project files and configs at D:\Users\ericf\
