# PowerSpec App Restoration Guide
> Scanned: 2026-04-02 | Source: D: (old NVMe drive)

## COMPLETE APP INVENTORY (from old drive scan)

### ✅ Already Reinstalled (from last night's rebuild)
| App | Version | Status |
|-----|---------|--------|
| Git | 2.53.0 | ✅ Installed |
| Python 3.12 | 3.12.10 | ✅ Installed |
| Node.js LTS | 24.14.1 | ✅ Installed |
| Docker Desktop | 4.67.0 | ✅ Installed |
| GitHub CLI | 2.89.0 | ✅ Installed |
| Tailscale | 1.96.3 | ✅ Installed |
| Google Chrome | 146.x | ✅ Installed |
| NVIDIA Drivers | 595.97 | ✅ Installed |
| WSL2 + Ubuntu | 2.6.3 | ✅ Installed |
| Ollama | 0.19.0 | ✅ Installed |
| Claude Desktop | 1.2.234.0 | ✅ Installed |
| OneDrive | latest | ✅ Installed |
| PowerShell 7 | 7.x | ✅ Installed |

---

## 📥 APPS TO REINSTALL — Grouped by Priority

### 🔴 Priority 1: Security (Install First)
| App | Download Link | Notes |
|-----|--------------|-------|
| **ESET Security** | https://www.eset.com/us/home/internet-security/download/ | Was installed, license needed |
| **ESET VPN** | Bundled with ESET Security | |

### 🔴 Priority 2: Productivity
| App | Download Link | Notes |
|-----|--------------|-------|
| **Microsoft Office 365** | https://portal.office.com → Install Office | Sign in with your Microsoft account |
| **Microsoft Teams** | Already installed (winget) | May need sign-in |
| **Google Drive** | https://dl.google.com/drive-file-stream/GoogleDriveSetup.exe | Was in C:\PowerSpec Applications\ |
| **Dropbox** | https://www.dropbox.com/install | Was installed |
| **Microsoft OneDrive** | Already installed | Just sign in |

### 🟡 Priority 3: Hardware / Peripheral
| App | Download Link | Notes |
|-----|--------------|-------|
| **Logitech G HUB** | https://www.logitechg.com/en-us/innovation/g-hub.html | For Logitech peripherals |
| **Realtek Audio** | Already reinstalled via Windows | Check Device Manager |
| **Intel Driver & Support** | https://www.intel.com/content/www/us/en/support/detect.html | Auto-detects Intel drivers |
| **ASRock RGB LED** | https://www.asrock.com/MB/Intel/Z790-C/Download.asp → Utility | ASRRGBLED.lnk was on old drive |
| **NVIDIA App** | https://www.nvidia.com/en-us/software/nvidia-app/ | Already installed (11.0.6.383) |
| **NVIDIA Nsight Compute** | https://developer.nvidia.com/nsight-compute | For GPU profiling |
| **NVIDIA Nsight Systems** | https://developer.nvidia.com/nsight-systems | For system profiling |

### 🟡 Priority 4: Scanning / Printing
| App | Download Link | Notes |
|-----|--------------|-------|
| **ScanSnap Home** | https://www.pfu.ricoh.com/global/scanners/scansnap/dl/ | PFU/Ricoh scanner software |
| **ABBYY FineReader for ScanSnap** | Bundled with ScanSnap Home | Installs automatically |
| **Brother iPrint&Scan** | https://support.brother.com/g/s/id/htmldoc/iprint/win/ | |
| **Brother Utilities** | https://support.brother.com → find your model | |
| **ControlCenter4** | Bundled with Brother drivers | |

### 🟡 Priority 5: Development Tools
| App | Download Link | Notes |
|-----|--------------|-------|
| **Python 3.14** | https://www.python.org/downloads/release/python-3140/ | Was at D:\Python314 |
| **Visual Studio 2022** | https://visualstudio.microsoft.com/downloads/ | Community edition free |
| **Tesseract OCR** | https://github.com/UB-Mannheim/tesseract/releases | v5.5 installer |
| **CUDA Toolkit** | https://developer.nvidia.com/cuda-downloads | For GPU compute |
| **NVIDIA GPU Computing Toolkit** | Bundled with CUDA | |
| **HWiNFO64** | https://www.hwinfo.com/download/ | Hardware monitoring |
| **CPU-Z (CPUID)** | https://www.cpuid.com/softwares/cpu-z.html | CPU info tool |

### 🟢 Priority 6: Gaming & Entertainment
| App | Download Link | Notes |
|-----|--------------|-------|
| **Steam** | https://store.steampowered.com/about/ | |
| **World of Warships** | Via Steam OR https://worldofwarships.com/download/ | **Data still at D:\Games\World_of_Warships** — point installer there to avoid re-downloading! |
| **Sonos** | https://www.sonos.com/en-us/controller-app | |

### 🟢 Priority 7: Audio / Creative
| App | Download Link | Notes |
|-----|--------------|-------|
| **Creative App** | https://creative.com/creative-app | Sound Blaster related |
| **Brave Browser** | https://brave.com/download/ | Was in C:\PowerSpec Applications\ |

### ⚪ Already Built Into Windows (no reinstall needed)
- Microsoft Edge, Notepad, Calculator, Paint, Snipping Tool, Sticky Notes, Windows Terminal, Xbox app, Phone Link, Clipchamp

---

## 📁 FILES IN C:\PowerSpec Applications\

Downloads running in background. After waking the PC, check:
```powershell
dir "C:\PowerSpec Applications"
```

Files being downloaded:
- `Brave_Browser_Setup.exe`
- `ESET_Security_Setup.exe`
- `Sonos_Setup.exe`
- `Logitech_GHUB_Setup.exe`
- `HWiNFO64_Setup.exe`
- `CPU-Z_Setup.exe`
- `Intel_DSA_Setup.exe`
- `Python314_Setup.exe`
- `Tesseract_OCR_Setup.exe`
- `PowerShell7_Setup.msi`
- `Steam_Setup.exe`
- `Dropbox_Setup.exe`
- `GoogleDrive_Setup.exe`
- `_Office365_README.txt` (instructions)
- `_VisualStudio2022_README.txt` (instructions)
- `_CUDA_Toolkit_README.txt` (instructions)
- `_WorldOfWarships_README.txt` (instructions)

---

## 🔁 STEP-BY-STEP REINSTALL PROCEDURE

### Step 1: Security First
1. Open `C:\PowerSpec Applications\ESET_Security_Setup.exe`
2. Sign in with your ESET license → full protection restored

### Step 2: Microsoft Office
1. Go to https://portal.office.com in Chrome
2. Sign in with your Microsoft 365 account
3. Click Install Office → Office 365 apps
4. Run the installer — it downloads and installs Word, Excel, PowerPoint, OneNote

### Step 3: Cloud Storage
1. Run `Dropbox_Setup.exe` → sign in
2. Run `GoogleDrive_Setup.exe` → sign in with ericfbrown1@gmail.com
3. OneDrive already installed — sign in via Start menu

### Step 4: Logitech & Hardware Peripherals
1. Run `Logitech_GHUB_Setup.exe` → your device profiles sync from cloud
2. Run `Intel_DSA_Setup.exe` → auto-detects and installs Intel drivers
3. Download ASRock RGBLED from https://www.asrock.com/MB/Intel/Z790-C/Download.asp

### Step 5: Scanning
1. Run `ScanSnap_Home` installer → connects to your scanner
2. ABBYY FineReader installs automatically as part of ScanSnap Home
3. Install Brother drivers for your printer model

### Step 6: Development
1. Run `Python314_Setup.exe` → install to C:\Python314 (matches old path)
2. Download Visual Studio 2022 from link above → select workloads you need
3. Run `Tesseract_OCR_Setup.exe`
4. Download CUDA Toolkit for your driver version (595.97 → CUDA 12.8)

### Step 7: Gaming
1. Run `Steam_Setup.exe` → sign in → your library syncs from cloud
2. **World of Warships:** In Steam, right-click game → Properties → Local Files → "Move Install Folder" → point to `D:\Games\World_of_Warships` (saves re-downloading ~50GB!)

### Step 8: Browsers
1. Run `Brave_Browser_Setup.exe` → sign in to sync bookmarks/extensions

---

## 🧠 ENVIRONMENT CLONE RECOMMENDATIONS

Beyond apps, here are key settings to restore to fully clone your old environment:

### 1. Disable Sleep Mode (CRITICAL — prevented reconnection tonight)
```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 0
```

### 2. Restore Python pip packages
```powershell
# Check what was installed on old drive
D:\Python314\Scripts\pip.exe list > "C:\PowerSpec Applications\_python314_packages.txt"
# After installing Python 3.14, restore with:
# pip install -r packages.txt
```

### 3. Restore pnpm / npm global packages
```powershell
# Check old npm globals
Get-Content D:\Users\ericf\AppData\Local\npm-cache\*.json | head -50
```

### 4. Windows Environment Variables
```powershell
# Export from old registry
reg export "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "C:\PowerSpec Applications\_env_vars.reg"
reg export "HKCU\Environment" "C:\PowerSpec Applications\_user_env_vars.reg"
```

### 5. NVIDIA Settings
- Open NVIDIA App → restore color profiles and display settings
- Re-enable GPU scaling, set preferred refresh rate

### 6. Tailscale Key Expiry
- Go to https://login.tailscale.com/admin/machines → find `powerspecpc` → Disable key expiry

### 7. Browser Profiles / Extensions
- Brave: Sign in to Brave Sync → restores bookmarks, extensions, passwords
- Chrome: Sign in to Google account → restores everything

### 8. SSH Keys (for Git/GitHub)
```powershell
# Check if old SSH keys exist on old drive
dir D:\Users\ericf\.ssh\
# If found, copy to new location:
# Copy-Item D:\Users\ericf\.ssh\* "C:\Users\Eric Brown\.ssh\"
```

---

## 💾 WORLD OF WARSHIPS — SAVE 50GB+ OF DOWNLOADING

Your game data is intact at `D:\Games\World_of_Warships`!

**To use it without re-downloading:**
1. Download WoWS launcher from https://worldofwarships.com/download/
2. When it asks for install location, choose `D:\Games\World_of_Warships`
3. It will detect existing files and only update what changed
4. Saves potentially 50GB+ of downloads

---

*Guide created: 2026-04-02 | Based on scan of D: (old NVMe)*
