---

## ⚠️ KEY FINDING (2026-03-26): 7-Day Token Expiry Root Cause

**Root cause:** Google Cloud OAuth consent screen was in "Testing" mode. Google policy: Testing + External user type = refresh tokens expire after exactly 7 days.

**Permanent fix applied:** Changed to "In Production" at https://console.cloud.google.com/auth/audience (project: EFB Calendar Clawdbot, ID 672907822296). Then re-issued token via `gog auth add --force-consent`.

**Result:** Tokens now NEVER expire (only if unused 6 months or password change).

**For any new Google Cloud project:** ALWAYS set Publishing Status to "In Production" immediately. Do NOT leave in "Testing" mode or tokens will expire weekly.

---

name: google-oauth-reauth
description: >
  Diagnose and fix Google OAuth token expiration for the gog CLI. Use this skill
  when Gmail, Calendar, Drive, Contacts, Sheets, or Docs stop working with
  "invalid_grant", "Token has been expired or revoked", or any gog CLI auth error.
  Also use when Zapier MCP Gmail works but gog CLI doesn't — indicates OAuth-specific
  issue. Covers diagnosis, keychain cleanup, re-auth, verification, and prevention.
---

# Google OAuth Re-Authentication Skill

## When to Use This Skill
- gog CLI returns `"invalid_grant"` or `"Token has been expired or revoked"`
- Gmail, Calendar, Drive, or Sheets API calls fail but worked previously
- Zapier MCP Gmail works fine but gog CLI doesn't (confirms it's OAuth, not Google-wide)
- `gog auth list` shows a token but API calls still fail
- After a Google password change or security event

---

## Step 0: Diagnose — Is It Actually OAuth?

Run these in order to confirm:

```bash
# 1. Check if token exists
gog auth list

# 2. Test Gmail
gog gmail search "newer_than:1d" --max 1 --account ericfbrown1@gmail.com

# 3. Test Calendar
gog calendar list --account ericfbrown1@gmail.com
```

**If you see `invalid_grant` or `expired or revoked`** → OAuth token is dead. Continue to Step 1.

**If you see `connection refused` or `timeout`** → Not OAuth. Check network/gateway.

**If Zapier MCP Gmail works but gog doesn't** → Confirmed OAuth-only issue.

---

## Step 1: Delete Stale Keychain Entry

The old token must be removed from macOS Keychain before re-auth will work:

```bash
security delete-generic-password -s "gogcli" -a "token:default:ericfbrown1@gmail.com"
```

**Expected output:** Entry deleted (or "item not found" if already gone — that's fine).

**Why this is required:** gog CLI reads the cached token from Keychain. If the cached token is expired, gog will keep using it instead of refreshing. Deleting forces a fresh auth flow.

---

## Step 2: Re-Authenticate (Requires Browser)

⚠️ **This step requires Eric to be at the MacBook** — it opens a browser for Google sign-in.

```bash
gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent
```

**What happens:**
1. Browser opens to Google sign-in page
2. Sign in as **ericfbrown1@gmail.com**
3. Click **"Allow"** on the permissions screen (all 6 services)
4. Browser shows success message
5. Token saved to macOS Keychain automatically

**`--force-consent` is critical** — without it, Google may reuse the old (broken) authorization.

---

## Step 3: Verify All 6 Services

Run each one to confirm:

```bash
# Gmail
gog gmail search "newer_than:1d" --max 3 --account ericfbrown1@gmail.com

# Calendar
gog calendar list --account ericfbrown1@gmail.com

# Drive
gog drive ls --account ericfbrown1@gmail.com

# Contacts
gog contacts list --max 3 --account ericfbrown1@gmail.com

# Sheets (test with known spreadsheet)
gog auth list
```

**All should return data without errors.** If any fail, repeat Steps 1-2.

---

## Step 4: Verify Token Details

```bash
# Check token issue date
gog auth list

# Check keychain entry
security find-generic-password -s "gogcli" -a "token:default:ericfbrown1@gmail.com" 2>&1 | grep -i "cdat\|mdat"
```

The `cdat` (creation date) should be today's date.

---

## Token Expiration Rules

The OAuth token uses a **refresh token** that does NOT expire under normal conditions. It will only expire if:

| Trigger | Likelihood | Prevention |
|---------|------------|------------|
| Manual revoke at myaccount.google.com/permissions | Low | Don't revoke unless intentional |
| Google password change | Medium | Re-auth immediately after password change |
| Google detects suspicious activity | Low | Use from consistent IP/location |
| Token unused for 6+ months | Very low | Daily briefing uses it every day |
| Another `--force-consent` auth | Medium | Only run when actually needed |
| Google project OAuth client reset | Very low | Don't modify the Google Cloud project |

**Best prevention:** The daily briefing cron uses Gmail and Calendar every day at 6 AM, keeping the token active.

---

## Backup Path: Zapier MCP

If OAuth is broken and Eric is not available to re-auth in a browser, use Zapier MCP as a backup for Gmail and Sheets:

```bash
# Send email
mcporter call zapier.gmail_send_email --args '{"instructions":"Send email","to":["recipient@email.com"],"subject":"Subject","body":"Body text"}'

# Search email
mcporter call zapier.gmail_find_email --args '{"instructions":"Find recent emails","query":"newer_than:1d"}'

# Read Google Sheets
mcporter call zapier.google_sheets_lookup_spreadsheet_row --args '{"instructions":"Look up data","output_hint":"columns needed"}'
```

**Zapier MCP does NOT cover:** Calendar, Drive, Contacts, Docs. These require gog CLI OAuth.

---

## Troubleshooting

### "security: SecKeychainSearchCopyNext: The specified item could not be found"
Token was already deleted or never existed. Skip Step 1, go to Step 2.

### Browser doesn't open during auth
Run from a Terminal window with GUI access (not SSH). If using tmux, try a fresh terminal.

### Auth succeeds but API still fails
1. Wait 30 seconds (token propagation)
2. Try `gog auth list` — verify the timestamp updated
3. If timestamp is old, the auth didn't actually save. Delete keychain entry and retry.

### Multiple Google accounts interfering
Make sure you sign in as **ericfbrown1@gmail.com** specifically, not a work or secondary account. Google may default to the last-used account in the browser.

---

## Quick Reference (Copy-Paste Fix)

```bash
# Full fix in 3 commands:
security delete-generic-password -s "gogcli" -a "token:default:ericfbrown1@gmail.com"
gog auth add ericfbrown1@gmail.com --services gmail,calendar,drive,contacts,docs,sheets --force-consent
gog gmail search "newer_than:1d" --max 3 --account ericfbrown1@gmail.com && gog calendar list --account ericfbrown1@gmail.com && echo "✅ All working!"
```
