#!/usr/bin/env python3
"""
send_file_email.py — Durable file attachment emailer for Jarvis

Enforces the mandatory 3-step delivery protocol:
  1. Pre-flight: file exists + non-zero size
  2. Send via gog gmail (with fallback to Gmail API direct)
  3. Post-confirm: verify email landed in Gmail

Usage:
  python3 send_file_email.py \
    --file /Users/ericbrown/Documents/report.pptx \
    --to ericfbrown1@gmail.com \
    --subject "My Report" \
    --body "Please find attached."

  # Multiple recipients:
  python3 send_file_email.py \
    --file /path/to/file.docx \
    --to ericfbrown1@gmail.com \
    --cc Eric.brown@cohesity.com \
    --subject "Report" \
    --body "Body text here"
"""

import argparse
import os
import subprocess
import sys
import time


# ── Constants ────────────────────────────────────────────────────────────────

EMAIL_FOOTER = "\n\nSent by Jarvis - AI assistant to Eric Brown"
DEFAULT_CC = "ericfbrown1@gmail.com"
MIN_FILE_SIZE = 1  # bytes — zero-byte files are always invalid
CONFIRM_WAIT_SECS = 12
CONFIRM_SEARCH_WINDOW = "10m"


# ── Step 1: Pre-flight ───────────────────────────────────────────────────────

def preflight(filepath: str) -> int:
    """Validate file exists and is non-zero. Returns file size in bytes."""
    filepath = os.path.expanduser(filepath)

    if not os.path.exists(filepath):
        print(f"❌ ABORT: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(filepath):
        print(f"❌ ABORT: Path is not a file: {filepath}", file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(filepath)
    if size < MIN_FILE_SIZE:
        print(f"❌ ABORT: File is zero bytes: {filepath}", file=sys.stderr)
        sys.exit(1)

    # Mirror ls -la output for confirmation
    result = subprocess.run(
        ["ls", "-lah", filepath],
        capture_output=True, text=True
    )
    print(f"✅ Pre-flight passed:\n   {result.stdout.strip()}")
    return size


# ── Step 2: Send via gog ─────────────────────────────────────────────────────

def send_via_gog(filepath: str, to: str, cc: str, subject: str, body: str) -> str:
    """Send email with attachment via gog CLI. Returns message_id."""
    full_body = body + EMAIL_FOOTER

    cmd = [
        "gog", "gmail", "send",
        "--to", to,
        "--subject", subject,
        "--body", full_body,
        "--attach", os.path.expanduser(filepath),
    ]
    if cc:
        cmd += ["--cc", cc]

    print(f"\n📤 Sending via gog: {os.path.basename(filepath)} → {to}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ gog send failed (exit {result.returncode}):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        print("\n⚡ Attempting fallback via Gmail API direct...", file=sys.stderr)
        return send_via_gmail_api(filepath, to, cc, subject, body)

    msg_id = ""
    for line in result.stdout.splitlines():
        if "message_id" in line:
            msg_id = line.split()[-1].strip()
            break

    if not msg_id:
        print(f"⚠️  gog returned no message_id. stdout:\n{result.stdout}", file=sys.stderr)
    else:
        print(f"✅ Sent — message_id: {msg_id}")

    return msg_id


# ── Step 2 Fallback: Gmail API via Python ────────────────────────────────────

def send_via_gmail_api(filepath: str, to: str, cc: str, subject: str, body: str) -> str:
    """
    Fallback: send via Python smtplib using Gmail SMTP.
    Requires GMAIL_APP_PASSWORD env var or falls back to Zapier MCP.
    Explicitly reads file bytes — missing file raises immediately.
    """
    # Explicitly read file — will raise FileNotFoundError if missing
    filepath = os.path.expanduser(filepath)
    try:
        with open(filepath, "rb") as f:
            file_bytes = f.read()
    except FileNotFoundError:
        print(f"❌ FALLBACK ABORT: File truly missing at {filepath}", file=sys.stderr)
        sys.exit(1)

    if len(file_bytes) == 0:
        print(f"❌ FALLBACK ABORT: File is zero bytes at {filepath}", file=sys.stderr)
        sys.exit(1)

    import smtplib
    import ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders
    import mimetypes

    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    sender = "ericfbrown1@gmail.com"

    if not app_password:
        print("⚠️  GMAIL_APP_PASSWORD not set — cannot use SMTP fallback.", file=sys.stderr)
        print("   Set env var GMAIL_APP_PASSWORD with a Gmail App Password.", file=sys.stderr)
        print("   Falling back to Zapier MCP for notification (no attachment).", file=sys.stderr)
        _notify_zapier_no_attachment(to, subject, body, filepath)
        return ""

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc

    msg.attach(MIMEText(body + EMAIL_FOOTER, "plain"))

    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type is None:
        mime_type = "application/octet-stream"
    main_type, sub_type = mime_type.split("/", 1)

    part = MIMEBase(main_type, sub_type)
    part.set_payload(file_bytes)
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{os.path.basename(filepath)}"'
    )
    msg.attach(part)

    recipients = [to] + ([cc] if cc else [])
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, app_password)
            server.sendmail(sender, recipients, msg.as_string())
        print(f"✅ Sent via Gmail SMTP fallback → {to}")
        return "smtp-fallback"
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP auth failed — check GMAIL_APP_PASSWORD", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ SMTP send failed: {e}", file=sys.stderr)
        sys.exit(1)


def _notify_zapier_no_attachment(to, subject, body, filepath):
    """Last-resort: send notification without attachment via Zapier MCP."""
    notification = (
        f"{body}\n\n"
        f"⚠️  NOTE: Attachment could not be sent automatically.\n"
        f"File is available locally at: {filepath}\n"
        f"{EMAIL_FOOTER}"
    )
    result = subprocess.run([
        "mcporter", "call", "zapier.gmail_send_email",
        "--args", f'{{"to":"{to}","subject":"[ATTACHMENT FAILED] {subject}","body":"{notification}"}}'
    ], capture_output=True, text=True)
    if result.returncode == 0:
        print("⚠️  Sent no-attachment notification via Zapier MCP")
    else:
        print(f"❌ All send methods failed. File at: {filepath}", file=sys.stderr)


# ── Step 3: Post-confirm ─────────────────────────────────────────────────────

def confirm_receipt(subject: str, msg_id: str) -> bool:
    """Wait briefly then search Gmail to confirm email landed."""
    if not msg_id or msg_id == "smtp-fallback":
        # For SMTP sends we can still search by subject
        pass

    print(f"\n⏳ Waiting {CONFIRM_WAIT_SECS}s before confirmation search...")
    time.sleep(CONFIRM_WAIT_SECS)

    # Search by subject in recent window
    # Escape quotes in subject for search query
    safe_subject = subject.replace('"', "").split()[0]  # use first word for reliability
    search_query = f'subject:{safe_subject} newer_than:{CONFIRM_SEARCH_WINDOW}'

    result = subprocess.run(
        ["gog", "gmail", "search", search_query, "--max", "1"],
        capture_output=True, text=True
    )

    if result.returncode == 0 and result.stdout.strip():
        lines = [line for line in result.stdout.strip().splitlines() if line and not line.startswith("#")]
        if lines:
            print("✅ Confirmed: Email found in Gmail inbox")
            print(f"   {lines[-1][:120]}")
            return True

    print(f"⚠️  Could not auto-confirm — check Gmail manually for: '{subject}'")
    print("   (This may be a search timing issue, not a delivery failure)")
    return False


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Send a file attachment via email with pre-flight validation and post-confirm."
    )
    parser.add_argument("--file", required=True, help="Path to file to attach")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--cc", default=DEFAULT_CC, help=f"CC address (default: {DEFAULT_CC})")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body text")
    parser.add_argument("--no-confirm", action="store_true", help="Skip post-send confirmation")
    args = parser.parse_args()

    print("=" * 60)
    print("📎 Jarvis File Delivery — 3-Step Protocol")
    print("=" * 60)

    # Step 1
    print("\n── Step 1: Pre-flight ──────────────────────────────────────")
    size = preflight(args.file)
    print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")

    # Step 2
    print("\n── Step 2: Send ────────────────────────────────────────────")
    msg_id = send_via_gog(args.file, args.to, args.cc, args.subject, args.body)

    # Step 3
    if not args.no_confirm:
        print("\n── Step 3: Confirm ─────────────────────────────────────────")
        confirmed = confirm_receipt(args.subject, msg_id)
    else:
        confirmed = None

    print("\n" + "=" * 60)
    if msg_id:
        print("✅ DELIVERY COMPLETE")
        print(f"   File:       {os.path.basename(args.file)}")
        print(f"   To:         {args.to}")
        print(f"   Message ID: {msg_id}")
        print(f"   Confirmed:  {'Yes' if confirmed else 'Not verified (check manually)'}")
    else:
        print("⚠️  DELIVERY UNCERTAIN — check Gmail manually")
    print("=" * 60)


if __name__ == "__main__":
    main()
