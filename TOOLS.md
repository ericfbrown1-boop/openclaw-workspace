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


## Dropbox (Primary: Native MCP)
- **MCP Server:** https://mcp.dropbox.com/mcp (native Dropbox Connector)
- **Priority:** ALWAYS use native Dropbox MCP first — it supports full read/write/share
- **Capabilities:** list_folder, get_file_metadata, create_file, create_folder, create_shared_link, get_file_content
- **Account:** Eric personal Dropbox (ericfbrown1@gmail.com)
- **Reports folder:** /Jarvis/reports/ (create if missing)
- **Fallback:** Only use Zapier MCP Dropbox if native MCP fails or is unavailable (see Zapier MCP section below)
- **Tested:** 2026-04-09 — native MCP confirmed working, Zapier MCP erroring

## Zapier MCP (20 tools via mcporter)
- **Config:** `~/.openclaw/workspace/config/mcporter.json`
- **Gmail:** send_email, find_email, create_draft, create_draft_reply, get_attachment_by_filename
- **Google Sheets:** lookup_rows, find_worksheet, create_row, create_multiple_rows, create_spreadsheet, create_worksheet, create_column, conditional_formatting
- **Dropbox (FALLBACK ONLY):** find_file, find_folder, find_file_content_search, create_shared_link — use only if native Dropbox MCP unavailable
- **All params must be strings** — use `--args '{...}'` for JSON
- **Dropbox account:** Eric's personal (not Jarvis's)
- **Gmail backup:** Use `mcporter call zapier.gmail_send_email` when gog CLI fails

## Windows Remote Coder PC (powerspecpc)
- **Tailscale IP:** 100.81.21.114
- **Hostname:** powerspecpc (was remote-coder-main before Apr 2026 rebuild)
- **System Model:** MicroElectronics G484 (PowerSpec brand from MicroCenter)
- **OS:** Windows 11 Home 25H2 (Build 26200)

### Motherboard: ASRock Z790-C (detailed spec from ASRock, updated 2026-04-05)
- **Chipset:** Intel Z790
- **BIOS:** 128Mb AMI UEFI, Version 19.01.MC01 (dated 2025-12-04)
- **Form Factor:** ATX (12.0" x 9.6" / 30.5 cm x 24.4 cm)
- **CPU Socket:** LGA1700 — supports 14th, 13th & 12th Gen Intel Core
  - Intel Hybrid Technology, Turbo Boost Max 3.0, TVB, ABT supported
- **Power Design:** 14+1+1 phase, 50A Dr.MOS for VCore+GT
  - 1x 24-pin ATX, 2x 8-pin 12V (Hi-Density)
- **Memory:** 4x DDR5 DIMM slots, dual-channel, max 256 GB
  - 1DPC 1R: up to 6800+ MHz (OC), 4800 MHz native
  - 1DPC 2R: up to 6000+ MHz (OC), 4400 MHz native
  - Supports Intel XMP 3.0
- **PCIe Slots:**
  - PCIE1: PCIe 5.0 x16 (from CPU) — **GPU slot**
  - PCIE4: PCIe 4.0 x16 (chipset, wired x4)
  - PCIE5: PCIe 3.0 x16 (chipset, wired x1)
  - PCIE2, PCIE3: PCIe 3.0 x1
  - M.2 Key-E: for WiFi/BT module (type 2230)
- **M.2 Storage Slots:**
  - M2_1 (CPU): PCIe Gen4x4, type 2260/2280
  - M2_2 (Chipset): PCIe Gen4x4, type 2242/2260/2280
  - M2_3 (Chipset): PCIe Gen4x4 or SATA3, type 2260/2280
  - M2_4 (Chipset): PCIe Gen4x4, type 2260/2280
- **SATA:** 4x SATA3 6.0 Gb/s
- **RAID:** SATA: 0/1/5/10; M.2 NVMe: 0/1/5 (Intel VMD supported)
- **USB Ports:**
  - Rear: 1x USB 3.2 Gen2x2 Type-C (20 Gb/s), 1x USB 3.2 Gen2 Type-A (10 Gb/s), 5x USB 3.2 Gen1 Type-A, 1x USB 2.0
  - Front headers: 1x USB 3.2 Gen1 Type-C, 2x USB 3.2 Gen1 headers (4 ports), 1x USB 2.0 header (2 ports)
- **LAN:** Intel I219V Gigabit (10/100/1000)
- **WiFi:** 802.11ac module (dual-band 2.4/5 GHz, up to 433 Mbps) + Bluetooth
- **Audio:** Realtek ALC897 (7.1 CH HD Audio)
- **Rear Panel:** 2x antenna, PS/2, HDMI, USB ports (above), RJ-45, HD audio jacks (line in/front speaker/mic)
- **Connectors:** Thunderbolt 4 AIC header (5-pin), 1x RGB LED, 3x ARGB, 6x fan headers (CPU + 5 chassis), eDP, SPI TPM
- **Driver downloads:** https://www.asrock.com/MB/Intel/Z790-C/Download.asp

### CPU: Intel Core i9-14900KF
- 24 cores / 32 threads, 3.2 GHz base
- L2 Cache: 32 MB, L3 Cache: 36 MB
- Family 6 Model 183 Stepping 1, Processor ID: 0xB0671
- No integrated GPU (KF variant) — discrete GPU required

### GPU: NVIDIA GeForce RTX 5080 16GB
- Driver: 32.0.15.9597 (dated 2026-03-17), CUDA 13.2
- Current resolution: 1920x1200 @ 59Hz (max 75Hz)
- PCI bus 1, device 0, function 0
- Device ID: PCI\VEN_10DE&DEV_2C02&SUBSYS_89D71043&REV_A1\4&341CA995&0&0008
- In PCIE1 slot (PCIe 5.0 x16)

### RAM: 128 GB DDR5
- 94.81 GB available at last scan
- Virtual memory: 144.89 GB total, page file: C:\pagefile.sys (17 GB)

### Storage
- **C: (Boot)** Samsung SSD 990 NVMe, 1863 GB, 1608 GB free
  - Serial: 0025_385A_51A2_CE22, Firmware: 2B2QKXG7
  - Device: SCSI\DISK&VEN_NVME&PROD_SAMSUNG_SSD_990\5&BF4CBCD&0&000000
- **D: (Old boot)** SK Hynix SHPP41-2000GM NVMe, 1863 GB, 1321 GB free
  - Serial: ACE4_2E00_5584_22D1_2EE4_AC00_0000_0001, Firmware: 51061A20
  - Device: SCSI\DISK&VEN_NVME&PROD_SHPP41-2000GM\5&1B178F10&0&000000

### Audio
- Realtek ALC897: RTKVHD64.sys v6.0.9844.1
  - Device: HDAUDIO\FUNC_01&VEN_10EC&DEV_0897&SUBSYS_18493897&REV_1004\4&18FC4C1C&0&0001
- NVIDIA HD Audio: nvhda64v.sys v1.4.5.7
- NVIDIA Virtual Audio: nvvad64v.sys v4.65.0.12

### Network
- **Intel i219V Ethernet:** Driver v12.19.2.60, MAC 9C:6B:00:C8:68:BB, service e1dexpress
  - Device: PCI\VEN_8086&DEV_0DC8&SUBSYS_0DC81849&REV_11\3&11583659&0&FE
- **MediaTek WiFi (802.11ac):** Driver v3.4.0.1123, MAC F4:28:9D:3F:AB:6D, service mtkwlex
  - Device: PCI\VEN_14C3&DEV_0616&SUBSYS_061614C3&REV_00\4&1BD763EC&0&00E0
- **Bluetooth:** MAC F4:28:9D:3F:AB:6E, service BthPan
- **WireGuard/Tailscale:** wintun v0.14.0.0
  - Device: SWD\WINTUN\{37217669-42DA-4657-A55B-0D995D328250}

### Software & Remote Access
- **SSH User:** "Eric Brown" (key-based login; uses ~/.ssh/id_ed25519)
- **SSH Command:** `ssh "Eric Brown@100.81.21.114"` (BatchMode works)
- **Docker:** Docker Desktop 29.3.1 with WSL2 backend + NVIDIA GPU passthrough
- **Docker credential fix:** `credsStore` set to `""` and desktop/wincred helpers renamed
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

## Dell U5226KW 6K Monitor
- Model: Dell UltraSharp U5226KW — 52" curved, 6K (6144x2560), 120Hz, 21:9
- Connection: DisplayPort 1.4 with DSC from RTX 5080 (UGREEN DP 2.1 cable ordered)
- **CRITICAL:** Previous connection attempt crashed Windows — use cold-plug procedure only
- Cold-plug: Shut down PC → connect cable → turn on monitor → wait 5s → power on PC
- Start at 60Hz, then increase to 120Hz once stable
- Inputs available: 2x HDMI 2.1, 2x DisplayPort 1.4, 1x Thunderbolt 4, 3x USB-C upstream
- Built-in: KVM switch, 2.5GbE Ethernet, USB hub, 2x9W speakers
