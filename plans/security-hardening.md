# Security Hardening Tracker

**Source:** references/OpenClaw_System_Audit_2026-03-06.docx
**Audit Date:** 2026-03-06
**Last Reviewed:** 2026-03-25

## CRITICAL Findings

### 1. Open Telegram Group Policy
- **Risk:** ANY Telegram group can interact with all agents. Prompt injection from untrusted groups.
- **Fix:** Set `groupPolicy` to `"allowlist"` in openclaw.json with explicit trusted group IDs.
- **Status:** [ ] UNVERIFIED — Check current openclaw.json on Mac

### 2. All Agents Unsandboxed with Full Filesystem Access
- **Risk:** Any agent can read/write entire filesystem, not just workspace.
- **Fix:** Set `fs.workspaceOnly: true` for all non-main agents. Enable sandbox mode.
- **Status:** [ ] UNVERIFIED — Check agent configs on Mac

### 3. Plaintext API Keys in openclaw.json
- **Risk:** 10 plaintext secrets (Telegram bot token, ElevenLabs, Brave Search, Google Places, gateway auth). Included in Dropbox backup tarballs (unencrypted).
- **Fix:** Migrate to 1Password with `op` CLI injection. Remove from openclaw.json.
- **Status:** [ ] UNVERIFIED — Check if secrets migrated to 1Password

## WARNING Findings

### 4. gpt-4o-mini Below Recommended Tier
- **Risk:** Model too weak for agents with tool access. May produce incorrect tool calls.
- **Fix:** Remove gpt-4o-mini from fallback chains. Minimum tier: Sonnet 4.6.
- **Status:** [ ] UNVERIFIED

### 5. denyCommands Schema Mismatch
- **Risk:** denyCommands entries don't match OpenClaw schema — no protection applied.
- **Fix:** Review and fix denyCommands format per OpenClaw docs.
- **Status:** [ ] UNVERIFIED

### 6. macOS Application Firewall Disabled
- **Risk:** Stealth mode OFF, firewall OFF. Network services exposed.
- **Fix:** Enable firewall: System Settings → Network → Firewall → ON. Enable stealth mode.
- **Status:** [ ] UNVERIFIED

### 7. Tailscale Version Mismatch
- **Risk:** Client 1.94.1 vs server 1.95.161. Minor risk of protocol issues.
- **Fix:** Update Tailscale: `brew upgrade tailscale` or update via App Store.
- **Status:** [ ] UNVERIFIED — May be resolved by now

## HOUSEKEEPING

- [ ] Delete BOOTSTRAP.md (one-time use, no longer needed)
- [ ] Consolidate orphaned Python venvs (230 MB recoverable)
- [ ] Trash backup tarballs after verification (700 MB recoverable)
- [ ] Fix 2 failing cron jobs: Daily Tax Email Scan, Clawdbot Data Refresh
- [ ] Consolidate workspace scripts into organized directories
- [ ] Enable heartbeat on Monitor agent

## How to Verify

Run on Mac:
```bash
# Check Telegram groupPolicy
python3 -c "import json; cfg=json.load(open('$HOME/.openclaw/openclaw.json')); print('groupPolicy:', cfg.get('channels',{}).get('telegram',{}).get('groupPolicy','NOT SET'))"

# Check agent sandbox settings
python3 -c "import json; cfg=json.load(open('$HOME/.openclaw/openclaw.json')); [print(a.get('id','?'), 'sandbox:', a.get('sandbox','NOT SET'), 'fsWorkspaceOnly:', a.get('fs',{}).get('workspaceOnly','NOT SET')) for a in cfg.get('agents',{}).get('list',[])]"

# Check for plaintext secrets
grep -c "token\|key\|secret" ~/.openclaw/openclaw.json

# Check macOS firewall
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```
