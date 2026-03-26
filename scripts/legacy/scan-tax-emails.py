#!/usr/bin/env python3
"""Scan Gmail for tax-related emails from the past 7 days using targeted IMAP search."""

import imaplib
import email
from email.header import decode_header
import json
import re
from datetime import datetime, timedelta

EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"
IMAP_SERVER = "imap.gmail.com"

# Key tax search terms for IMAP OR queries
TAX_SEARCH_TERMS = [
    'tax', 'W-2', 'W2', '1099', '1098', 'K-1', 'IRS',
    'CPA', 'tax return', 'tax document', 'tax form',
    'dividend', 'capital gains', 'charitable donation',
    'brokerage statement', 'consolidated tax',
    'RSU', 'ESPP', 'stock option', 'equity compensation',
    'withholding', 'estimated payment', 'tax summary',
    'accountant', 'tax preparation',
]

def decode_mime_words(s):
    if s is None:
        return ""
    decoded_fragments = decode_header(s)
    return ''.join(
        str(fragment, encoding or 'utf-8') if isinstance(fragment, bytes) else str(fragment)
        for fragment, encoding in decoded_fragments
    )

def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                        break
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        except Exception:
            pass
    return re.sub(r'\s+', ' ', body).strip()[:300]

def main():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    # Use Gmail's All Mail with X-GM-RAW for better search
    mail.select('"[Gmail]/All Mail"', readonly=True)
    
    since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    
    all_ids = set()
    
    # Search for each tax keyword using Gmail's native search
    for term in TAX_SEARCH_TERMS:
        try:
            # Use X-GM-RAW for Gmail-specific search
            status, messages = mail.search(None, f'X-GM-RAW "subject:{term} after:2026/03/01"')
            if status == "OK" and messages[0]:
                for eid in messages[0].split():
                    all_ids.add(eid)
        except Exception:
            # Fallback to standard IMAP search
            try:
                status, messages = mail.search(None, f'(SINCE {since_date} SUBJECT "{term}")')
                if status == "OK" and messages[0]:
                    for eid in messages[0].split():
                        all_ids.add(eid)
            except Exception:
                pass
    
    print(f"Found {len(all_ids)} potential tax-related emails", file=__import__('sys').stderr)
    
    tax_emails = []
    seen_subjects = set()
    
    for eid in sorted(all_ids):
        try:
            status, msg_data = mail.fetch(eid, "(BODY.PEEK[HEADER] X-GM-MSGID)")
            if status != "OK":
                continue
            
            # Extract Gmail message ID
            gmail_msgid = None
            for item in msg_data:
                if isinstance(item, tuple) and b'X-GM-MSGID' in item[0]:
                    match = re.search(rb'X-GM-MSGID (\d+)', item[0])
                    if match:
                        gmail_msgid = match.group(1).decode()
            
            msg = email.message_from_bytes(msg_data[0][1])
            
            subject = decode_mime_words(msg.get("Subject", ""))
            from_addr = decode_mime_words(msg.get("From", ""))
            date_str = msg.get("Date", "")
            
            try:
                date_obj = email.utils.parsedate_to_datetime(date_str)
                # Filter to last 7 days
                cutoff = datetime.now(date_obj.tzinfo) - timedelta(days=7)
                if date_obj < cutoff:
                    continue
                date_formatted = date_obj.strftime("%Y-%m-%d")
            except Exception:
                date_formatted = date_str[:10]
            
            # Deduplicate by subject+sender
            dedup_key = f"{date_formatted}|{from_addr}|{subject}"
            if dedup_key in seen_subjects:
                continue
            seen_subjects.add(dedup_key)
            
            # Convert Gmail message ID to hex for URL
            gmail_hex = None
            if gmail_msgid:
                gmail_hex = hex(int(gmail_msgid))[2:]
            
            tax_emails.append({
                "date": date_formatted,
                "sender": from_addr.strip(),
                "subject": subject.strip(),
                "gmail_msgid": gmail_msgid,
                "gmail_hex": gmail_hex,
            })
        except Exception as e:
            print(f"Error: {e}", file=__import__('sys').stderr)
    
    # Sort by date
    tax_emails.sort(key=lambda x: x["date"])
    
    mail.close()
    mail.logout()
    
    print(json.dumps({"tax_emails": tax_emails, "total_found": len(tax_emails)}, indent=2))

if __name__ == "__main__":
    main()
