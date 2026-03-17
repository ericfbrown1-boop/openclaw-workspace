---
name: tailscale-troubleshooting
description: >
  Diagnose and fix Tailscale connectivity issues on macOS. Use this skill when
  tailscale status fails, CLI can't connect to service, Homebrew/App Store
  conflicts occur, Funnel stops working for voice calls, devices disconnect,
  or key expiry causes access loss. Covers the Mac App Store version specifically
  (not Homebrew). Also covers Funnel setup for webhook exposure and multi-device
  tailnet management.
---

# Tailscale Troubleshooting Skill

## Architecture on This Mac

- **Installation:** Mac App Store version (NOT Homebrew)
- **CLI path:** `/usr/local/bin/tailscale` (provided by the App Store app)
- **System extension:** `io.tailscale.ipn.macsys.network-extension.systemextension`
- **App process:** `/Applications/Tailscale.app/Contents/MacOS/Tailscale`
- **No tailscaled daemon** — the App Store version uses a macOS system extension instead

### Tailnet Devices (all with key expiry disabled)

| Device | IP | OS |
|--------|----|----|
| erics-macbook-pro | 100.101.203.113 | macOS |
| iphone172 | 100.86.157.19 | iOS |
| remote-coder-main | 100.67.128.123 | Windows 11 |

---

## Step 0: Triage — What's the Symptom?

| Symptom | Jump to |
|---------|---------|
| `failed to connect to local Tailscale service` | Section 1 |
| CLI works but no peers / can't reach other devices | Section 2 |
| Funnel not working / voice calls broken | Section 3 |
| Device disappeared from tailnet | Section 4 |
| Key expired / needs re-authentication | Section 5 |
| Homebrew conflict detected | Section 6 |

---

## Section 1: "Failed to connect to local Tailscale service"

This is the most common issue. The CLI can't talk to the running Tailscale app.

### Diagnosis

```bash
# Check which tailscale binary is being used
which tailscale

# Check if the app is running
pgrep -l Tailscale
pgrep -l "io.tailscale"

# Check if system extension is loaded
ps aux | grep "tailscale" | grep -v grep
```

### Most Likely Cause: Homebrew/App Store Conflict

If `which tailscale` returns `/opt/homebrew/bin/tailscale`:

**The Homebrew CLI cannot talk to the App Store app.** They use different IPC mechanisms:
- Homebrew version expects `tailscaled` (a daemon)
- App Store version uses a macOS system extension (no daemon)

### Fix

```bash
# Remove Homebrew tailscale
brew uninstall tailscale

# Verify correct CLI
which tailscale
# Should return: /usr/local/bin/tailscale

# Test
tailscale status
```

### If App Store Tailscale Isn't Running

```bash
# Open the app
open /Applications/Tailscale.app

# Wait 10 seconds, then test
sleep 10
tailscale status
```

If the app opens but CLI still can't connect, check:
1. Is the system extension allowed? (System Settings → Privacy & Security → Network Extensions)
2. Try toggling Tailscale off/on in the menu bar

---

## Section 2: CLI Works But No Connectivity

```bash
# Check state
tailscale status --json | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'State: {d.get(\"BackendState\")}')
print(f'Online: {d.get(\"Self\",{}).get(\"Online\")}')
for k,v in d.get('Peer',{}).items():
    print(f'  {v.get(\"HostName\")}: Online={v.get(\"Online\")} LastSeen={v.get(\"LastSeen\",\"?\")[:19]}')
"
```

### Causes
1. **Not logged in** — check menu bar, click "Log in"
2. **Network firewall blocking** — Tailscale needs UDP 41641 outbound
3. **VPN conflict** — some corporate VPNs block Tailscale. Disconnect VPN and test
4. **DNS issues** — `tailscale ping <device-name>` to test direct connectivity

---

## Section 3: Funnel Not Working (Voice Calls Broken)

Tailscale Funnel exposes a local port to the internet via Tailscale's infrastructure. Required for the voice call webhook.

### Check Status

```bash
tailscale serve status
tailscale funnel status
```

### Expected Configuration

```
# serve: port 3334 exposed locally
# funnel: port 3334 exposed to internet
https://erics-macbook-pro.tail1e87b8.ts.net:443 → http://127.0.0.1:3334
```

### Fix: Re-enable Funnel

```bash
tailscale serve --bg 3334
tailscale funnel --bg 3334
```

### Verify

```bash
tailscale funnel status
# Should show port 3334 as active

# Test from external
curl -s https://erics-macbook-pro.tail1e87b8.ts.net/voice/webhook
```

### If Funnel Won't Enable
1. Check that Funnel is enabled in Tailscale admin console (admin.tailscale.com → DNS → Funnel)
2. HTTPS must be enabled: `tailscale cert erics-macbook-pro.tail1e87b8.ts.net`
3. The device must have a stable hostname in the tailnet

---

## Section 4: Device Disappeared from Tailnet

```bash
tailscale status
```

If a device (e.g., remote-coder-main) doesn't appear:

1. **Device is offline** — turn it on / check its internet connection
2. **Key expired** — if key expiry was re-enabled, the device needs to re-authenticate
3. **Removed from admin console** — check admin.tailscale.com → Machines

### Re-add a Device
On the device itself, run Tailscale and log in. It will rejoin the tailnet automatically.

---

## Section 5: Key Expiry Issues

All 3 devices currently have **key expiry disabled** (set March 17, 2026). If expiry gets re-enabled:

### Symptoms
- Device drops off tailnet
- `tailscale status` shows device as "expired"
- Can't reach the device via Tailscale IP

### Fix (in Tailscale Admin Console)
1. Go to https://login.tailscale.com/admin/machines
2. Find the device
3. Click "..." menu → "Disable key expiry"
4. The device reconnects automatically within ~60 seconds

### Prevention
- **Never re-enable key expiry** on these 3 devices unless intentionally rotating access
- The daily smoke test checks for Tailscale connectivity and will alert if devices go offline

---

## Section 6: Homebrew Conflict — Detection and Removal

### Detection

```bash
which tailscale
# BAD: /opt/homebrew/bin/tailscale
# GOOD: /usr/local/bin/tailscale

brew list tailscale 2>/dev/null && echo "⚠️ Homebrew tailscale installed — CONFLICT" || echo "✅ No Homebrew conflict"
```

### Why It Conflicts
- Mac App Store Tailscale uses a **system extension** for networking
- Homebrew Tailscale uses a **userspace daemon** (`tailscaled`)
- The Homebrew CLI talks to `tailscaled` via a Unix socket
- The App Store app doesn't create that socket → CLI fails

### Removal

```bash
brew uninstall tailscale
```

### After Removal
- CLI at `/usr/local/bin/tailscale` (from App Store) takes over
- The App Store app's "CLI integration" feature provides this binary
- Enable it: Tailscale menu bar → Settings → CLI integration → "Show me how"

### Prevention
- **Never run `brew install tailscale`** on this Mac
- If any script or tool tries to install it, block it
- The daily smoke test checks for this conflict and flags it as HIGH priority

---

## Quick Reference

```bash
# Full diagnostic
tailscale status
tailscale status --json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'State: {d[\"BackendState\"]} Online: {d[\"Self\"][\"Online\"]}')"

# Fix CLI conflict
brew uninstall tailscale

# Re-enable Funnel
tailscale serve --bg 3334 && tailscale funnel --bg 3334

# Open app if not running
open /Applications/Tailscale.app

# Check which CLI
which tailscale  # Must be /usr/local/bin/tailscale
```

---

## Integration with Other Skills

- **Voice Call skill** depends on Tailscale Funnel (port 3334)
- **Remote Coder** (remote-coder-main) is only reachable via Tailscale at 100.67.128.123
- **Daily Smoke Test** checks Tailscale status, CLI path, Funnel, and peer connectivity every morning
- **Self-Heal Watchdog** monitors Tailscale and logs alerts if connectivity drops
