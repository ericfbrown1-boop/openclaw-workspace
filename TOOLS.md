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
  - remote-coder-main: 100.67.128.123 (Windows 11)
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

## Windows Remote Coder PC (remote-coder-main)
- **Tailscale IP:** 100.67.128.123
- **Hostname:** remote-coder-main / efbpowerspec
- **OS:** Windows 11 25H2
- **CPU:** 32 vCPUs
- **RAM:** 128 GB
- **GPU:** NVIDIA RTX 5080 Blackwell (CUDA 13.1)
- **SSH User:** ericf (⚠️ PENDING — password auth not yet working; fix sshd_config first)
- **SSH Command:** `ssh ericf@100.67.128.123` (once working)
- **Docker:** Docker Desktop with NVIDIA Container Toolkit (GPU passthrough via WSL2)
- **Git:** Configured with Eric's GitHub credentials
- **Tailscale key expiry:** Disabled (permanent access)
- **Ping test:** `tailscale ping remote-coder-main` (28ms via DERP/SFO)

### Use for (heavy workloads):
- GPU/CUDA workloads (PyTorch, TensorFlow, RAPIDS)
- Large Docker builds (>5 min or >2GB image)
- Large codebases (>50K lines)
- RAM-intensive tasks (>16GB)
- ML model training/inference

### Do NOT use for (use MacBook instead):
- Light web apps, simple API servers
- Quick fixes and small changes
- Any work until SSH is confirmed working

### SSH Fix Pending (sshd_config):
Need to edit `C:\ProgramData\ssh\sshd_config` on Windows:
1. Set `PasswordAuthentication yes` (uncomment)
2. Comment out last two lines: `#Match Group administrators` and `# AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys`
3. Run `Restart-Service sshd` in Admin PowerShell

### Once SSH working — set up key-based auth:
```bash
ssh-keygen -t ed25519 -C "jarvis@openclaw" -f ~/.ssh/remote_coder_key
ssh-copy-id -i ~/.ssh/remote_coder_key.pub ericf@100.67.128.123
# Then add to ~/.ssh/config:
# Host remote-coder-main
#   HostName 100.67.128.123
#   User ericf
#   IdentityFile ~/.ssh/remote_coder_key
```
