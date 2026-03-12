# Jarvis Full Restore Procedure
## From Dropbox Backup

**Last backup:** March 9, 2026
**Backup location:** Dropbox `/Jarvis Backups/2026-03-09/jarvis_full_backup_20260309.tar.gz`
**Size:** 20MB

---

## When Would You Need This?

- MacBook Pro is replaced or wiped
- OpenClaw installation gets corrupted
- Starting fresh on a new machine
- Recovering from a catastrophic failure

---

## Prerequisites

Before restoring, you need these installed on the Mac:

1. **Homebrew** (package manager)
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Node.js**
   ```
   brew install node
   ```

3. **OpenClaw**
   ```
   npm install -g openclaw
   ```

4. **Python 3**
   ```
   brew install python3
   ```

5. **Other tools**
   ```
   brew install tesseract poppler bfg gh tailscale
   pip3 install anthropic openai-whisper
   ```

---

## Step-by-Step Restore

### Step 1: Download the Backup

Option A — From Dropbox web:
1. Go to dropbox.com and sign in
2. Navigate to `/Jarvis Backups/2026-03-09/`
3. Download `jarvis_full_backup_20260309.tar.gz`
4. Move it to your home folder: `mv ~/Downloads/jarvis_full_backup_20260309.tar.gz ~/`

Option B — If Dropbox CLI is available:
```bash
python3 dropbox-cli.py download "/Jarvis Backups/2026-03-09/jarvis_full_backup_20260309.tar.gz" ~/jarvis_full_backup_20260309.tar.gz
```

### Step 2: Extract the Backup

```bash
cd ~
tar xzf jarvis_full_backup_20260309.tar.gz
cd jarvis_backup_20260309
ls -la
```

You should see:
```
openclaw.json
workspace-core.tar.gz
workspace-auditor.tar.gz
workspace-coder.tar.gz
workspace-monitor.tar.gz
workspace-planner.tar.gz
workspace-quality.tar.gz
workspace-researcher.tar.gz
ProjectRemoteCoder.tar.gz
ContractAnalyzer.tar.gz
gogcli-credentials.json
LaunchAgents/
```

### Step 3: Restore OpenClaw Config

```bash
# Create OpenClaw directory if it doesn't exist
mkdir -p ~/.openclaw

# Restore main config
cp openclaw.json ~/.openclaw/openclaw.json
```

### Step 4: Restore Main Workspace

```bash
# Create workspace directory
mkdir -p ~/.openclaw/workspace

# Extract core files (AGENTS.md, SOUL.md, USER.md, MEMORY.md, plans/, memory/, scripts/, etc.)
cd ~/.openclaw/workspace
tar xzf ~/jarvis_backup_20260309/workspace-core.tar.gz
```

### Step 5: Restore Agent Workspaces

```bash
# Extract each agent workspace
cd ~/.openclaw

tar xzf ~/jarvis_backup_20260309/workspace-auditor.tar.gz
tar xzf ~/jarvis_backup_20260309/workspace-coder.tar.gz
tar xzf ~/jarvis_backup_20260309/workspace-monitor.tar.gz
tar xzf ~/jarvis_backup_20260309/workspace-planner.tar.gz
tar xzf ~/jarvis_backup_20260309/workspace-quality.tar.gz
tar xzf ~/jarvis_backup_20260309/workspace-researcher.tar.gz
```

### Step 6: Restore Projects

```bash
# ProjectRemoteCoder
cd ~/.openclaw/workspace
tar xzf ~/jarvis_backup_20260309/ProjectRemoteCoder.tar.gz

# ContractAnalyzer
cd ~
tar xzf ~/jarvis_backup_20260309/ContractAnalyzer.tar.gz
```

### Step 7: Restore Google OAuth Credentials

```bash
# Create gog CLI config directory
mkdir -p ~/Library/Application\ Support/gogcli

# Restore credentials file
cp ~/jarvis_backup_20260309/gogcli-credentials.json \
   ~/Library/Application\ Support/gogcli/credentials.json

# Re-authenticate (credentials file only has client_id/secret — you need to re-auth)
gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent
# Browser will open — sign in and click Allow
```

### Step 8: Restore LaunchAgents (Watchdogs & Self-Heal)

```bash
# Copy all LaunchAgent plists
cp ~/jarvis_backup_20260309/LaunchAgents/*.plist ~/Library/LaunchAgents/

# Load them
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.openclaw.gateway.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.selfheal.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.gatewaywatchdog.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.logrotation.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.tailscale.monitor.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.weeklysecurity.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.sessionmonitor.plist
```

### Step 9: Start OpenClaw Gateway

```bash
openclaw gateway install
openclaw gateway start
```

### Step 10: Verify Everything Works

```bash
# Check gateway
openclaw gateway status

# Check doctor
openclaw doctor

# Test Gmail
gog gmail search "newer_than:1d" --max 3 --account ericfbrown1@gmail.com

# Check all agents are configured
cat ~/.openclaw/openclaw.json | python3 -c "
import sys, json
config = json.load(sys.stdin)
for a in config['agents']['list']:
    print(f\"  {a['id']}: {a['name']}\")
"
```

Expected output:
```
  main: Jarvis
  researcher: Researcher
  planner: Planner
  coder: Coder
  quality: Quality
  monitor: Monitor
  auditor: External Auditor
```

### Step 11: Restore Cron Jobs

Cron jobs are NOT included in file backups — they're managed by OpenClaw internally. You'll need to recreate them. Ask Jarvis to set them up again, or reference the cron list:

- Daily doctor --fix at 5:00 AM PT
- Daily auto-update at 5:45 AM PT
- Daily tax email scan at 5:45 AM PT
- Daily security scan at 5:50 AM PT
- Stock monitor at 6:00 AM PT
- Daily AI briefing at 6:00 AM PT
- Subscription monitor at 6:10 AM PT
- MicroCenter prices at 8:00 AM PT
- Weekly competitor analysis Mon 7:00 AM PT
- Weekly background info Mon 9:00 AM PT
- Clawdbot data refresh at midnight

### Step 12: Re-configure API Keys

These are NOT stored in the backup (for security):

1. **Anthropic API Key** — Set in `~/.openclaw/openclaw.json` under `providers.anthropic.apiKey`
2. **Dropbox Token** — Update in `~/.openclaw/workspace/dropbox-cli.py`
3. **GitHub** — Run `gh auth login` to re-authenticate
4. **Tailscale** — Open the Tailscale app and sign in with ericfbrown1@gmail.com

Reference: Check the "Tokens" Google Doc for current API keys.

### Step 13: macOS Settings

- System Settings → Privacy & Security → Full Disk Access → Enable for Terminal and node
- System Settings → General → Sharing → Remote Login (SSH) → ON
- System Settings → General → Sharing → Screen Sharing → ON
- Energy settings:
  ```
  sudo pmset -c displaysleep 0
  sudo pmset -c networkoversleep 1
  ```

---

## Quick Restore (If OpenClaw is Already Installed)

If you just need to restore Jarvis's memory and config (not a full rebuild):

```bash
# Download and extract
cd ~
# (download from Dropbox first)
tar xzf jarvis_full_backup_20260309.tar.gz

# Restore config + workspaces
cp jarvis_backup_20260309/openclaw.json ~/.openclaw/
cd ~/.openclaw/workspace && tar xzf ~/jarvis_backup_20260309/workspace-core.tar.gz
cd ~/.openclaw && tar xzf ~/jarvis_backup_20260309/workspace-quality.tar.gz
cd ~/.openclaw && tar xzf ~/jarvis_backup_20260309/workspace-auditor.tar.gz

# Restart gateway
openclaw gateway restart
```

---

## Backup Schedule

Backups are saved to Dropbox `/Jarvis Backups/YYYY-MM-DD/` on demand.
Ask Jarvis: "backup your config" to create a new one anytime.

---

## Support

If something goes wrong during restore, ask Jarvis via Telegram — even a fresh Jarvis instance can read SOUL.md, USER.md, and MEMORY.md to understand who you are and pick up where things left off.

---

*Prepared by Jarvis for Eric Brown — March 9, 2026*
