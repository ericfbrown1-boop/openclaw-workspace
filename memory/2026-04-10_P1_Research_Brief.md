# P1 Research Brief — Email Phantom Attachments & PPT Durable Write
**Date:** April 10, 2026  
**Researcher:** Jarvis (web research — Grok 4.20 subagent model not permitted for spawned agents)  
**Sources:** gogcli GitHub, Gmail API docs, Stack Overflow, Python fsync docs, python-pptx issues

---

## Issue 1: gog --attach Phantom Success

### Root Cause

**Two compounding failures, neither in the Gmail API itself:**

**Failure 1 — gog CLI does not pre-validate attachment path before constructing MIME message.**  
The gog CLI builds the multipart MIME message by reading the file at the `--attach` path. If the file doesn't exist, the CLI either silently omits the attachment part from the MIME message OR raises an exception that is caught and swallowed internally — then sends the email body-only. The Gmail API never sees a missing file; it receives a valid (but attachment-free) base64URL-encoded MIME message and returns a 200 + message_id.

**Failure 2 — Gmail API has no attachment validation.**  
Per Google's official docs (`developers.google.com/workspace/gmail/api/guides/sending`), `messages.send` accepts a pre-encoded RFC 2822 MIME message as a base64URL string. The API does **zero content inspection** — it sends whatever MIME it receives. If the gog CLI constructs a message without an attachment part, the API sends it without one, returns 200, and reports a valid message_id. There is no "attachment missing" error possible at the API layer.

### gog CLI Bug Status

- **No open issue found** specifically for `--attach` silent file-not-found on gogcli GitHub  
- Issue #474 (Mar 24, 2026) is a PR adding `forward` command with attachment support — not the same bug  
- Issue #206 covers a different silent failure (empty token write on headless Keychain) — same "silent failure" pattern in the codebase  
- **Status: Likely unfiled bug.** The silent failure pattern is consistent with the auth bug (#206), suggesting gog has a systemic issue with not surfacing file/path errors  
- **Recommendation: File a bug** at github.com/steipete/gogcli with the specific reproduction case

### Permanent Fix

**No upstream fix exists yet.** Must enforce a pre-send validation protocol in Jarvis workflows.

There is no `--dry-run` or `--verify` flag in gog. The only reliable approach is external validation before calling gog.

### Recommended Mandatory 3-Step Validation Protocol

Enforce this shell pattern for ALL file attachment sends:

```bash
# Step 1: Pre-flight — file must exist and be non-zero
FILE="/Users/ericbrown/Documents/filename.pptx"
if [ ! -f "$FILE" ] || [ ! -s "$FILE" ]; then
  echo "❌ ABORT: File missing or empty at $FILE"
  exit 1
fi

# Step 2: Send
MSG_ID=$(gog gmail send \
  --to "ericfbrown1@gmail.com" \
  --cc "Eric.brown@cohesity.com" \
  --subject "Subject" \
  --body "Body text. Sent by Jarvis - AI assistant to Eric Brown" \
  --attach "$FILE" | grep message_id | awk '{print $2}')

echo "Sent: $MSG_ID"

# Step 3: Post-confirm (wait 10s then verify)
sleep 10
gog gmail search "subject:Subject newer_than:5m" --max 1
```

For Python scripts generating and sending files, use this pattern:

```python
import os, subprocess, time

def send_file_with_validation(filepath, subject, body):
    # Pre-flight
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Attachment missing: {filepath}")
    size = os.path.getsize(filepath)
    if size == 0:
        raise ValueError(f"Attachment is zero bytes: {filepath}")
    print(f"✅ Pre-flight: {filepath} ({size:,} bytes)")

    # Send
    result = subprocess.run([
        "gog", "gmail", "send",
        "--to", "ericfbrown1@gmail.com",
        "--cc", "Eric.brown@cohesity.com",
        "--subject", subject,
        "--body", body,
        "--attach", filepath
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"gog send failed: {result.stderr}")

    msg_id = [l for l in result.stdout.split('\n') if 'message_id' in l]
    print(f"✅ Sent: {msg_id[0] if msg_id else 'unknown'}")

    # Post-confirm
    time.sleep(10)
    confirm = subprocess.run([
        "gog", "gmail", "search",
        f"subject:{subject} newer_than:5m", "--max", "1"
    ], capture_output=True, text=True)
    if confirm.returncode == 0 and confirm.stdout.strip():
        print("✅ Confirmed: Email found in Gmail")
    else:
        print("⚠️  WARNING: Could not confirm email in Gmail — check manually")
```

### Alternative Tools

| Tool | Attachment Validation | Notes |
|------|----------------------|-------|
| `gog gmail send --attach` | ❌ None | Current tool, phantom success bug |
| Zapier MCP `gmail_send_email` | ❓ Unknown | Available as fallback; handles base64 encoded attachments via API; likely safer but untested for file-not-found |
| `himalaya` (IMAP/SMTP) | ✅ Reads file directly | Validates at SMTP layer — file must be readable or send fails with clear error. Recommended as verification alternative |
| Python `smtplib` + `email.mime` | ✅ Explicit read | `open(filepath, 'rb').read()` fails loudly if file missing. Most robust option for scripted sends |

**Recommendation:** For any scripted/automated file send, switch to Python `smtplib` + Gmail SMTP or the Gmail API directly — both require explicitly reading the file bytes, so missing files raise exceptions before the send. Reserve gog for interactive/simple sends with the 3-step protocol enforced.

---

## Issue 2: PPTX Durable Write Protocol

### Root Cause

**Two compounding failures:**

**Failure 1 — Files written to ephemeral paths.**  
Python scripts writing to `/tmp/` or paths that only exist during a session are subject to macOS temp file cleanup:
- macOS `/tmp` is a symlink to `/private/tmp`
- Files are cleaned by `periodic daily` (runs nightly via launchd) using `110.clean-tmps` — deletes files not accessed in `$daily_clean_tmps_days` days (default: 3 days on macOS)
- However, the more likely cause is OpenClaw session isolation: when a session ends, any files written by scripts running in that session context may not persist if the working directory was session-scoped or if the script wrote to a relative path
- Writing to `~/Documents/` is durable (APFS, persists across reboots and session ends)

**Failure 2 — python-pptx `save()` is synchronous but NOT guaranteed durable without fsync.**  
`prs.save(filepath)` in python-pptx internally calls Python's `zipfile.ZipFile` to write the OOXML package. This writes to the OS kernel buffer — not directly to disk. On a normal session close, the OS flushes buffers. But:
- If the process crashes after `save()` returns but before the OS flushes → partial file
- If the filesystem is network-mounted or has write caching → data may be in cache, not on disk
- For local APFS (macOS native filesystem): `save()` is effectively durable in practice unless the machine loses power mid-write
- **The real risk is not `save()` durability but path selection** — writing to the wrong path (temp, relative, session-scoped)

### python-pptx save() Durability Analysis

```python
# python-pptx internally does this:
prs.save(filepath)
# → calls PackageWriter.write(pkg_file)
# → opens ZipFile(pkg_file, 'w', ZIP_DEFLATED)
# → writes all XML parts into the zip
# → ZipFile.__exit__() closes and flushes
# → Python file handle closed automatically
```

**Verdict:** `prs.save(filepath)` to a local APFS path is durable enough for our use case. No fsync needed for normal operations. The risk is not `save()` itself — it's the PATH being wrong (temp/ephemeral).

For maximum safety (e.g., critical deliverables), add post-save verification:

```python
import os
prs.save(filepath)
assert os.path.exists(filepath), f"Save failed: {filepath} not found"
assert os.path.getsize(filepath) > 10000, f"File suspiciously small: {os.path.getsize(filepath)} bytes"
```

### macOS Temp File Behavior

| Path | Persistence | Risk |
|------|-------------|------|
| `/tmp/` or `/private/tmp/` | Cleaned nightly (3-day access rule) | HIGH — use for scratch only |
| `/var/tmp/` | Not cleared on reboot, cleaned less often | MEDIUM |
| `~/Documents/` | Permanent until deleted | ✅ SAFE — use this |
| `~/.openclaw/workspace/` | Permanent, git-tracked | ✅ SAFE for workspace files |
| Relative paths (`./file.pptx`) | Depends on cwd at runtime | HIGH — cwd may be unexpected |

### Recommended Atomic Write + Verify Protocol

```python
import os
import shutil
import hashlib
from pptx import Presentation

def save_pptx_durable(prs: Presentation, final_path: str) -> str:
    """
    Save a python-pptx Presentation durably with atomic write + verification.
    Returns the SHA256 hash of the saved file.
    
    Always writes to ~/Documents/ — never /tmp/ or relative paths.
    """
    # Ensure final_path is absolute and under ~/Documents/
    final_path = os.path.expanduser(final_path)
    if not final_path.startswith(os.path.expanduser("~/Documents/")):
        raise ValueError(f"Refusing to save outside ~/Documents/: {final_path}")
    
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    
    # Write to temp path in same directory (same filesystem = atomic rename)
    tmp_path = final_path + ".tmp"
    
    try:
        prs.save(tmp_path)
        
        # Verify temp file
        if not os.path.exists(tmp_path):
            raise RuntimeError(f"save() returned but file not found: {tmp_path}")
        size = os.path.getsize(tmp_path)
        if size < 5000:  # Valid PPTX is always >5KB
            raise RuntimeError(f"PPTX suspiciously small ({size} bytes) — likely corrupt")
        
        # Atomic move to final path
        shutil.move(tmp_path, final_path)
        
        # Compute hash for integrity tracking
        sha256 = hashlib.sha256(open(final_path, 'rb').read()).hexdigest()
        
        print(f"✅ Saved: {final_path} ({size:,} bytes, sha256={sha256[:16]}...)")
        return sha256
        
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
```

### Recommended Dropbox Backup Protocol

```python
import subprocess

def backup_to_dropbox(local_path: str, dropbox_filename: str = None) -> bool:
    """
    Upload a file to Dropbox /Jarvis Reports/ as backup.
    Returns True on success, False on failure (non-blocking).
    """
    if dropbox_filename is None:
        dropbox_filename = os.path.basename(local_path)
    
    dropbox_path = f"/Jarvis Reports/{dropbox_filename}"
    
    result = subprocess.run([
        "python3",
        "/Users/ericbrown/.openclaw/workspace/dropbox-cli.py",
        "upload",
        local_path,
        dropbox_path
    ], capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        print(f"✅ Dropbox backup: {dropbox_path}")
        return True
    else:
        print(f"⚠️  Dropbox backup failed: {result.stderr} — proceeding anyway")
        return False  # Non-blocking: don't prevent email send if Dropbox fails
```

### Complete Durable PPT Delivery Workflow

```python
def deliver_pptx(prs, filename, subject, body):
    """Full durable delivery: generate → verify → backup → send → confirm."""
    
    final_path = os.path.expanduser(f"~/Documents/{filename}")
    
    # 1. Save durably with atomic write + verification
    sha256 = save_pptx_durable(prs, final_path)
    
    # 2. Backup to Dropbox (non-blocking)
    backup_to_dropbox(final_path)
    
    # 3. Send email with pre-flight validation
    send_file_with_validation(final_path, subject, body)
    
    print(f"✅ Delivery complete: {filename} (sha256={sha256[:16]}...)")
    return sha256
```

### Standing Rule for AGENTS.md

> **File Delivery Protocol (Standing Rule — 2026-04-10):**  
> All generated files (PPTX, DOCX, PDF) must be saved to `~/Documents/<filename>` using an atomic write (write to `.tmp`, verify size > 5KB, rename to final). Before any email send: assert file exists and size > 0. After send: confirm via `gog gmail search`. Back up to Dropbox `/Jarvis Reports/` as a separate non-blocking step before sending. Never write deliverables to `/tmp/`, relative paths, or session-scoped directories.

---

## Summary & Recommendations

### Top 5 Findings

1. **gog `--attach` phantom success is a gog CLI bug, not a Gmail API bug.** The API receives a valid attachment-free MIME message and legitimately returns 200. Fix is external pre-validation — gog will not detect missing files on its own. File a bug at steipete/gogcli.

2. **python-pptx `save()` IS durable on local APFS** — the risk is path selection, not the write itself. Files written to `~/Documents/` survive session ends. Files written to `/tmp/` survive 3 days on macOS but are unreliable for session-end scenarios.

3. **The permanent fix for both issues is the same pattern:** validate → write durably → backup → send → confirm. This needs to be enforced as a standing protocol in AGENTS.md, not left to per-session judgment.

4. **Python `smtplib` or direct Gmail API is safer than gog for automated attachment sends** because both require explicitly reading file bytes before transmission — missing files raise clear exceptions before any API call is made.

5. **Atomic write pattern (write .tmp → verify → rename) is the correct Python approach** for durable file writes. This is the industry standard (used by databases, log systems, package managers). `shutil.move()` on the same filesystem is an atomic rename on POSIX/macOS — the file either exists completely or not at all.

### Immediate Actions

| Priority | Action |
|----------|--------|
| 🔴 P1 | Add File Delivery Protocol to AGENTS.md as a standing rule |
| 🔴 P1 | Update all PPTX/DOCX generation scripts to use `~/Documents/` as output path |
| 🔴 P1 | Enforce 3-step validation (pre-check → send → confirm) on all gog attachment sends |
| 🟡 P2 | File bug at github.com/steipete/gogcli for `--attach` silent file-not-found |
| 🟡 P2 | Create reusable `deliver_pptx()` Python function in workspace scripts |
| 🟡 P2 | Evaluate switching automated file sends to Python smtplib + Gmail SMTP |

---

*Research by Jarvis — April 10, 2026*  
*Sources: gogcli GitHub, Gmail API docs (developers.google.com), Stack Overflow, python-pptx GitHub, Python fsync docs*
