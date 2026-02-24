# Update Dropbox Access

## Overview
The `update-dropbox-access.py` script automates the generation of new Dropbox access tokens using your app credentials.

## Prerequisites
1. Dropbox app credentials (App Key + App Secret)
2. Find these at: https://www.dropbox.com/developers/apps

## Usage

### Method 1: With Refresh Token (Fastest)
If you have a refresh token saved:

```bash
python3 ~/.openclaw/workspace/update-dropbox-access.py
# Enter app key and secret
# Enter your refresh token when prompted
# ✅ New access token generated instantly!
```

### Method 2: Full OAuth Flow (First Time)
If you don't have a refresh token:

```bash
python3 ~/.openclaw/workspace/update-dropbox-access.py
# Enter app key and secret
# Skip the refresh token (press Enter)
# Browser opens with authorization URL
# Click "Allow"
# Copy the authorization code from the URL
# Paste it into the script
# ✅ New access token + refresh token generated!
```

### Method 3: Command Line (Quick)
```bash
python3 ~/.openclaw/workspace/update-dropbox-access.py YOUR_APP_KEY YOUR_APP_SECRET
```

## Output Files
After running, tokens are saved to:
- `/tmp/dropbox_new_token.txt` - New access token (share with Jarvis)
- `/tmp/dropbox_refresh_token.txt` - Refresh token (save for future use!)
- `/tmp/dropbox_tokens.json` - Full response

## How to Update Jarvis's Access

### Option 1: Update dropbox-cli.py directly
```bash
# Edit the TOKEN variable
nano ~/.openclaw/workspace/dropbox-cli.py
# Replace old token with new token from /tmp/dropbox_new_token.txt
```

### Option 2: Tell Jarvis the new token
Just send the token in chat:
```
Here's my new Dropbox token: sl.u.ABC123...XYZ
```

## Refresh Token Benefits
- **Save the refresh token!** It never expires (unless revoked)
- Use it to generate new access tokens instantly
- No need to re-authorize in browser
- Much faster than full OAuth flow

## Security Notes
- Keep your app secret and refresh token private
- Access tokens expire (typically after a few hours)
- Refresh tokens are long-lived (use them to get new access tokens)
- Store refresh token securely (not in code)

## Troubleshooting

### "Invalid authorization code"
- The code expired (they're short-lived, ~10 minutes)
- Try again and paste the code faster

### "Invalid app key/secret"
- Check your credentials at https://www.dropbox.com/developers/apps
- Make sure you're using the correct app

### "Redirect URI mismatch"
- The script uses `http://localhost` as redirect
- Make sure your app settings allow this redirect URI

## Example Session

```
$ python3 update-dropbox-access.py
============================================================
DROPBOX OAUTH TOKEN GENERATOR
============================================================

Enter your Dropbox app credentials:
(Find these at https://www.dropbox.com/developers/apps)

App Key: abc123xyz
App Secret: secret456

============================================================
OPTION 1: Use existing refresh token (if you have one)
============================================================

Refresh token (or press Enter to skip): 

============================================================
OPTION 2: Generate new token via OAuth flow
============================================================

📋 STEP 1: Authorize the app
------------------------------------------------------------

Authorization URL:
https://www.dropbox.com/oauth2/authorize?client_id=abc123xyz...

1. Click the URL above (or copy/paste into browser)
2. Click 'Allow' to authorize the app
3. Copy the authorization code from the URL

🌐 Opening browser automatically...

📋 STEP 2: Enter authorization code
------------------------------------------------------------

Authorization code: ABC123DEF456

🔄 Exchanging authorization code for access token...

============================================================
✅ SUCCESS! NEW TOKENS GENERATED
============================================================

🔑 Access Token:
sl.u.NEWTOKEN123...

🔄 Refresh Token (save this!):
REFRESH789...

💾 Tokens saved:
   Access token: /tmp/dropbox_new_token.txt
   Refresh token: /tmp/dropbox_refresh_token.txt
   Full response: /tmp/dropbox_tokens.json

============================================================
🎉 DONE! Share the access token with Jarvis.
============================================================
```
