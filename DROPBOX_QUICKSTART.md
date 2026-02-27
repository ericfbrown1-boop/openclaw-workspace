# 🚀 Dropbox OAuth Quick Start (5 Minutes)

## TL;DR
Never manually refresh Dropbox tokens again. This system auto-renews them forever.

## Setup (One-Time)

### 1. Create Dropbox App (2 min)
Go to: https://www.dropbox.com/developers/apps
- Click "Create app"
- Choose: **Scoped access** + **Full Dropbox**
- Name it: "Jarvis Dropbox CLI" (or whatever)
- Click "Create app"

### 2. Configure App (2 min)
On the app settings page:

**OAuth 2 section:**
- Add redirect URI: `http://localhost:8765/callback`

**Permissions tab:**
- Enable all these (use search box):
  - `files.metadata.write`
  - `files.metadata.read`
  - `files.content.write`
  - `files.content.read`
- Click **Submit** at bottom

**App key & secret:**
- Copy the **App key** (visible on Settings tab)
- Copy the **App secret** (click "Show" to reveal)

### 3. Run Setup Commands (1 min)

```bash
cd ~/.openclaw/workspace

# Install requirements if needed
pip3 install requests

# Store credentials (replace with your actual values)
python3 dropbox-auth.py setup <YOUR_APP_KEY> <YOUR_APP_SECRET>

# Authorize (opens browser)
python3 dropbox-auth.py authorize
```

The browser will open, ask you to authorize the app, then redirect back with "Authorization successful!"

## ✅ Done!

Your `dropbox-cli.py` now auto-refreshes tokens. Nothing else to do.

## Test It

```bash
# Check status
python3 dropbox-auth.py status

# Use Dropbox CLI normally
python3 dropbox-cli.py list /
```

## What Changed?

**Before:** Token expires every 4 hours → manual renewal required  
**After:** Refresh token never expires → automatic renewal forever

## Files

- `dropbox-auth.py` - OAuth automation script ✅ Created
- `dropbox-cli.py` - Updated with auto-refresh ✅ Updated  
- `.dropbox_auth.json` - Secure token storage (auto-created, gitignored)

## Help

Detailed docs: `DROPBOX_AUTH_SETUP.md`

Problems? Run: `python3 dropbox-auth.py status`
