# PowerSpec PC Rebuild Guide — Complete Reference
> Created: 2026-04-01 | Last rebuilt: 2026-04-01 | Duration: ~2 hours

## Hardware Specifications

| Component | Spec |
|-----------|------|
| **System** | PowerSpec G484 (MicroCenter) |
| **Motherboard** | ASRock Z790-C (Intel Z790 chipset) |
| **CPU** | Intel Core i9-14900KF — 24 cores / 32 threads, 3.2 GHz, LGA 1700 |
| **RAM** | 128 GB DDR5 (4 DIMM slots: DDR5_A1, A2, B1, B2) |
| **GPU** | NVIDIA GeForce RTX 5080 16GB (Blackwell) |
| **Storage** | NVMe M.2 (4 slots: M2_1 Gen4, M2_2 Gen4, M2_3 SATA/Gen4, M2_4 Gen4) |
| **LAN** | Intel i219V (1 Gigabit Ethernet) |
| **WiFi** | 802.11ac module (Intel) |
| **BIOS** | AMI, UEFI mode |
| **OS** | Windows 11 Home 25H2 (Build 26200) |

## Phase 1: Fresh Windows Install — Getting Network Working

### ⚠️ CRITICAL: Windows 11 does NOT include drivers for ASRock Z790-C LAN or WiFi

**Option A: Load driver from old NVMe (fastest if old drive is accessible)**
1. Old drive shows up as D: or E: in File Explorer
2. Open **Device Manager** (right-click Start → Device Manager)
3. Find network adapter with ⚠️ yellow triangle
4. Right-click → **Update driver** → **Browse my computer for drivers**
5. Navigate to: `D:\Windows\System32\DriverStore\FileRepository\`
6. Key folders:
   - **`e1d.inf_amd64_*`** — Intel i219V Ethernet (LAN) driver
   - **`e2xw10x64.inf_amd64_*`** — Intel WiFi driver
7. Check **"Include subfolders"** → Click **Next**
8. Plug in Ethernet cable → should be online immediately

**Option B: iPhone USB tethering (no drivers needed)**
1. Plug iPhone into PC via USB cable
2. iPhone: Settings → Personal Hotspot → Allow Others to Join = ON
3. Windows auto-detects iPhone as network adapter
4. Once online → Windows Update installs all missing drivers

**Option C: Download on another device → USB transfer**
1. On another PC/Mac, download from: https://www.asrock.com/MB/Intel/Z790-C/Download.asp
2. Select Windows 11 64-bit, download:
   - **INF driver** (chipset — helps Windows see all devices)
   - **Intel LAN driver** (gets Ethernet working)
   - **WLAN driver** (WiFi)
3. Copy to USB stick → plug into PowerSpec → run INF first, then LAN, then WiFi

**Option D: Download Intel driver directly**
- Intel LAN: https://www.intel.com/content/www/us/en/download/18293/intel-network-adapter-driver-for-windows-10.html
- File: `PROWinx64.exe` (~120 MB)
- Note: Intel CDN blocks curl/wget — must download via browser

## Phase 2: Tailscale + SSH (Remote Access)

### Install Tailscale
1. Download from: https://tailscale.com/download/windows
2. Run installer, sign in with **ericfbrown1@gmail.com**
3. New device will get a new IP (e.g., 100.81.21.114) and hostname
4. Verify from MacBook: `tailscale ping <hostname>`

### Install OpenSSH Server
Open **PowerShell as Administrator** and run:
```powershell
# Install OpenSSH Server (takes 2-5 minutes)
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start and auto-enable
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

### Configure SSH Key Authentication
```powershell
# Create .ssh directory for user
mkdir "C:\Users\Eric Brown\.ssh" -Force

# Add MacBook's public key
Set-Content -Path "C:\Users\Eric Brown\.ssh\authorized_keys" -Value "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKPQafIy/j07bguFjwiHOxl+wvkagVeHMjkZSzERTxNz ericbrown@Mac"

# IMPORTANT: For admin users, also add to ProgramData
Set-Content -Path C:\ProgramData\ssh\administrators_authorized_keys -Value "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKPQafIy/j07bguFjwiHOxl+wvkagVeHMjkZSzERTxNz ericbrown@Mac"

# Fix permissions on admin key file
icacls C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant "Administrators:F" /grant "SYSTEM:F"

# Restart SSH
Restart-Service sshd
```

### Update MacBook SSH Config
Add to `~/.ssh/config`:
```
Host powerspecpc
    HostName 100.81.21.114
    User "Eric Brown"
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
```

**Note:** If Windows username has a space, always quote it in SSH commands:
```bash
ssh "Eric Brown@100.81.21.114" "hostname"
```

## Phase 3: Dev Environment (All via SSH from MacBook)

### Install Core Tools
```bash
# Git
ssh "Eric Brown@<IP>" "winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements"

# Python
ssh "Eric Brown@<IP>" "winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements"

# Node.js LTS
ssh "Eric Brown@<IP>" "winget install --id OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements"

# Docker Desktop
ssh "Eric Brown@<IP>" "winget install --id Docker.DockerDesktop -e --source winget --accept-package-agreements --accept-source-agreements"

# GitHub CLI
ssh "Eric Brown@<IP>" "winget install --id GitHub.cli -e --source winget --accept-package-agreements --accept-source-agreements"
```

### Configure Git
```bash
ssh "Eric Brown@<IP>" "git config --global user.name 'Eric Brown' && git config --global user.email 'ericfbrown1@gmail.com'"
```

### Authenticate GitHub CLI
```bash
# Get token from MacBook
TOKEN=$(gh auth token)
# Apply to PowerSpec
ssh "Eric Brown@<IP>" "echo '$TOKEN' | gh auth login --with-token"
```

### Enable WSL2
```bash
# Enable features (needs admin — run from PowerShell on PC or use dism via SSH)
ssh "Eric Brown@<IP>" "dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart"
ssh "Eric Brown@<IP>" "dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart"

# Install Ubuntu
ssh "Eric Brown@<IP>" "winget install --id Canonical.Ubuntu.2204 -e --source winget --accept-package-agreements --accept-source-agreements"

# REBOOT REQUIRED for WSL2 features to activate
ssh "Eric Brown@<IP>" "powershell -Command Restart-Computer -Force"

# After reboot, Eric must log in for Tailscale to reconnect
# Then: wsl --install (may need to run on the PC directly)
```

### Fix Docker Credential Helper for SSH
Docker Desktop's credential helper can't access Windows Credential Manager from SSH sessions.

```bash
# Rename the helpers
ssh "Eric Brown@<IP>" "powershell -Command \"Rename-Item 'C:\Program Files\Docker\Docker\resources\bin\docker-credential-desktop.exe' 'docker-credential-desktop.exe.bak'\""
ssh "Eric Brown@<IP>" "powershell -Command \"Rename-Item 'C:\Program Files\Docker\Docker\resources\bin\docker-credential-wincred.exe' 'docker-credential-wincred.exe.bak'\""

# Set credsStore to empty in config
# SCP a clean config or edit via PowerShell:
# {"auths":{},"credsStore":"","currentContext":"desktop-linux"}
```

### Verify GPU in Docker
```bash
ssh "Eric Brown@<IP>" "docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi"
# Should show: RTX 5080, CUDA 13.2, 16GB VRAM
```

## Phase 4: Restore Applications

### Clone Repos
```bash
ssh "Eric Brown@<IP>" "mkdir projects && cd projects && gh repo clone ericfbrown1-boop/FinancialReportApp && gh repo clone ericfbrown1-boop/ContractAnalyzer && gh repo clone ericfbrown1-boop/ceregent && gh repo clone ericfbrown1-boop/JarvisMissionControl"
```

### Restore .env Files
- Check old drive at `D:\Users\ericf\<project>\.env` for API keys
- Key secrets needed: ANTHROPIC_API_KEY, auth credentials, database passwords
- Use `scp` to transfer .env files from MacBook if needed

### Copy App-Specific Files from Old Drive
```bash
# Example: gog CLI binary and credentials for FinancialReportApp
ssh "Eric Brown@<IP>" "powershell -Command \"Copy-Item 'D:\Users\ericf\projects\FinancialReportApp\api\gog' 'C:\Users\Eric Brown\projects\FinancialReportApp\api\gog'\""
ssh "Eric Brown@<IP>" "powershell -Command \"Copy-Item 'D:\Users\ericf\projects\FinancialReportApp\api\gog-*' 'C:\Users\Eric Brown\projects\FinancialReportApp\api\'\""
```

### Start Docker Containers
```bash
# FinancialReportApp (ports: API 8001, Frontend 3001, Postgres 5433, Redis 6380)
ssh "Eric Brown@<IP>" "cd projects/FinancialReportApp && docker compose up -d"

# ContractAnalyzer (ports: API 8000, Postgres 5432, Redis 6379, MinIO 9000/9001)
ssh "Eric Brown@<IP>" "cd projects/ContractAnalyzer && docker compose up -d"
```

## Phase 5: Post-Setup

### Restore Tailscale Watchdog
```bash
# Copy from old drive
ssh "Eric Brown@<IP>" "powershell -Command \"Copy-Item 'D:\Users\ericf\TailscaleSelfHeal\*' 'C:\Users\Eric Brown\TailscaleSelfHeal\' -Recurse\""

# Register scheduled task
ssh "Eric Brown@<IP>" "schtasks /create /tn TailscaleWatchdog /tr \"powershell.exe -ExecutionPolicy Bypass -File 'C:\Users\Eric Brown\TailscaleSelfHeal\tailscale-watchdog.ps1'\" /sc minute /mo 1 /ru SYSTEM /rl HIGHEST /f"
```

### Disable Tailscale Key Expiry
- Go to https://login.tailscale.com/admin/machines
- Find the new device → three dots menu → Disable key expiry

### Update Jarvis Config Files
- `TOOLS.md` — new Tailscale IP, hostname, SSH user
- `POWERSPEC.md` — new SSH command, hostname, CUDA version
- `~/.ssh/config` — new Host block
- `MEMORY.md` — document the rebuild

## Lessons Learned

1. **Always keep the old NVMe accessible** — DriverStore has all needed drivers, .env files have API keys
2. **Windows 11 fresh install has NO network drivers** for ASRock Z790-C — plan for offline driver loading
3. **Docker credential helpers don't work over SSH** — must rename them and set credsStore to ""
4. **WSL2 requires a reboot** after enabling features — Tailscale won't auto-reconnect until user logs in
5. **Windows usernames with spaces** cause SSH quoting issues — always quote the username
6. **winget is the fastest way to install** everything from SSH — no need for manual downloads
7. **iPhone USB tethering** is the fastest zero-download path to internet on a bare Windows install

## Port Map (When All Services Running)

| Port | Service | App |
|------|---------|-----|
| 3001 | Frontend (nginx) | FinancialReportApp |
| 5432 | PostgreSQL + pgvector | ContractAnalyzer |
| 5433 | PostgreSQL | FinancialReportApp |
| 6379 | Redis | ContractAnalyzer |
| 6380 | Redis | FinancialReportApp |
| 8000 | FastAPI | ContractAnalyzer |
| 8001 | FastAPI | FinancialReportApp |
| 9000 | MinIO API | ContractAnalyzer |
| 9001 | MinIO Console | ContractAnalyzer |
