# Dropbox OAuth 2.0 Auto-Refresh Setup Guide

## 🎯 What This Does
- Eliminates manual Dropbox token renewal every 4 hours
- Uses OAuth 2.0 with refresh tokens for automatic renewal
- Seamlessly integrates with existing `dropbox-cli.py`
- Stores credentials securely with proper file permissions

## 📋 Prerequisites
1. Dropbox account
2. Python 3 with `requests` library

## 🚀 First-Time Setup (One-Time)

### Step 1: Create a Dropbox App
1. Go to https://www.dropbox.com/developers/apps
2. Click "Create app"
3. Choose:
   - **API**: Scoped access
   - **Access type**: Full Dropbox
   - **Name**: Something like "Jarvis Dropbox CLI"
4. Click "Create app"
5. On the app settings page:
   - Copy the **App key** (starts with something like `abc123...`)
   - Copy the **App secret** (click "Show" to reveal it)
   - Under **OAuth 2** section, add redirect URI: `http://localhost:8765/callback`
   - Under **Permissions** tab, enable:
     - files.metadata.write
     - files.metadata.read
     - files.content.write
     - files.content.read
   - Click "Submit" at bottom of Permissions page

### Step 2: Install Python Requirements
```bash
pip3 install requests
```

### Step 3: Configure the Auth System
```bash
cd ~/.openclaw/workspace

# Store your app credentials
python3 dropbox-auth.py setup <YOUR_APP_KEY> <YOUR_APP_SECRET>
```

### Step 4: Authorize (One-Time Browser Flow)
```bash
python3 dropbox-auth.py authorize
```

This will:
1. Open your browser
2. Ask you to authorize the app
3. Redirect back to localhost
4. Automatically exchange the code for tokens
5. Store both access token (4 hours) and refresh token (forever)
6. Update `dropbox-cli.py` with the new token

## ✅ Daily Use

**You don't need to do anything!**

The system automatically:
- Checks token expiry before each `dropbox-cli.py` call
- Refreshes the token if it's expired or expiring soon (<5 min)
- Updates `dropbox-cli.py` with the new token

Just use `dropbox-cli.py` normally:
```bash
python3 dropbox-cli.py list /
python3 dropbox-cli.py download "/path/to/file.pdf" output.pdf
```

## 🔧 Manual Commands

Check authentication status:
```bash
python3 dropbox-auth.py status
```

Manually refresh the access token:
```bash
python3 dropbox-auth.py refresh
```

Get a valid token (auto-refresh if needed):
```bash
python3 dropbox-auth.py token
```

## 🔐 Security

- App credentials and tokens stored in `~/.openclaw/workspace/.dropbox_auth.json`
- File permissions automatically set to `0600` (owner read/write only)
- Refresh token never expires (unless revoked by user)
- Access tokens are short-lived (4 hours) and auto-renewed

## 🐛 Troubleshooting

**"Token expired" errors:**
```bash
python3 dropbox-auth.py refresh
```

**Lost refresh token:**
```bash
python3 dropbox-auth.py authorize
```
(Re-run the browser auth flow)

**Check what's configured:**
```bash
python3 dropbox-auth.py status
```

**Token not updating in dropbox-cli.py:**
- Make sure the script path is correct in `dropbox-auth.py`
- Check that `ACCESS_TOKEN = "..."` pattern exists in `dropbox-cli.py`

## 📊 How It Works

```
┌─────────────────┐
│ dropbox-cli.py  │
│ (your commands) │
└────────┬────────┘
         │
         ↓ Checks token expiry
┌────────────────────────┐
│ .dropbox_auth.json     │
│ - access_token         │
│ - refresh_token        │
│ - token_expiry         │
└────────┬───────────────┘
         │
         ↓ If expired (<5 min left)
┌────────────────────────┐
│ dropbox-auth.py        │
│ refresh command        │
└────────┬───────────────┘
         │
         ↓ POST to Dropbox API
┌────────────────────────┐
│ Dropbox OAuth2 API     │
│ /oauth2/token          │
└────────┬───────────────┘
         │
         ↓ Returns new access_token
┌────────────────────────┐
│ Update .dropbox_auth   │
│ Update dropbox-cli.py  │
└────────────────────────┘
```

## 🎉 Benefits Over Manual Tokens

| Manual Tokens | OAuth Auto-Refresh |
|---------------|-------------------|
| Expire every 4 hours | Auto-renew seamlessly |
| Must regenerate manually | Never expires (refresh token) |
| Copy/paste into code | Automatic updates |
| Security risk if hardcoded | Secure storage with proper permissions |

## 📝 Files Created

- `~/.openclaw/workspace/dropbox-auth.py` - Auth automation script
- `~/.openclaw/workspace/.dropbox_auth.json` - Token storage (gitignored)
- `~/.openclaw/workspace/dropbox-cli.py` - Updated with auto-refresh integration

## 🔄 Migration from Old System

Your old hardcoded token is kept as a fallback in `dropbox-cli.py`. If the auth system fails for any reason, it will automatically fall back to the old token.

Once you've confirmed the new system works, you can remove the fallback token from `dropbox-cli.py` if desired.
