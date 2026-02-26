#!/usr/bin/env python3
"""Scan Gmail for tax-related emails from the past 7 days."""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta, timezone
import json

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"  # App password
IMAP_SERVER = "imap.gmail.com"

# Tax-related keywords to search for
TAX_KEYWORDS = [
    "tax", "taxes", "1099", "W-2", "W2", "1040", "IRS", "TurboTax",
    "H&R Block", "deduction", "refund", "withholding", "K-1", "K1",
    "Schedule", "capital gain", "dividend", "interest income", "charitable",
    "charitable contribution", "mortgage interest", "property tax",
    "estimated tax", "tax return", "tax document", "tax form",
    "tax statement", "annual statement", "year-end statement",
    "1098", "1095", "SSA-1099", "brokerage", "consolidated 1099",
    "tax season", "taxable", "Fidelity", "Schwab", "Vanguard",
    "Bernstein", "county tax", "state tax", "federal tax"
]

def decode_mime_words(s):
    """Decode MIME encoded-words in header."""
    if s is None:
        return ""
    try:
        decoded_fragments = decode_header(s)
        result = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                result.append(fragment.decode(encoding or 'utf-8', errors='ignore'))
            else:
                result.append(str(fragment))
        return ''.join(result)
    except:
        return str(s) if s else ""

def is_tax_related(subject, from_addr, body_preview=""):
    """Check if email is tax-related based on keywords."""
    text_to_check = f"{subject} {from_addr} {body_preview}".lower()
    for keyword in TAX_KEYWORDS:
        if keyword.lower() in text_to_check:
            return True
    return False

def get_message_id(msg):
    """Extract the Gmail message ID from email headers."""
    msg_id = msg.get("Message-ID", "")
    return msg_id.strip("<>") if msg_id else ""

def main():
    """Scan emails from past 7 days for tax-related content."""
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Calculate date range (past 7 days)
        since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        
        print(f"Searching for emails since: {since_date}")
        print("=" * 80)
        
        # Search for all emails from the past 7 days (both read and unread)
        status, messages = mail.search(None, f'SINCE {since_date}')
        if status != "OK":
            print("No messages found")
            return
        
        email_ids = messages[0].split()
        print(f"Total emails in past 7 days: {len(email_ids)}")
        
        tax_emails = []
        
        for email_id in email_ids:
            try:
                # Fetch email headers only first for efficiency
                status, msg_data = mail.fetch(email_id, "(RFC822.HEADER UID)")
                if status != "OK":
                    continue
                
                raw_header = None
                uid = None
                for part in msg_data:
                    if isinstance(part, tuple):
                        # Try to extract UID from the response info
                        info_str = part[0].decode('utf-8', errors='ignore') if isinstance(part[0], bytes) else str(part[0])
                        uid_match = re.search(r'UID (\d+)', info_str)
                        if uid_match:
                            uid = uid_match.group(1)
                        raw_header = part[1]
                
                if not raw_header:
                    continue
                
                msg = email.message_from_bytes(raw_header)
                
                subject = decode_mime_words(msg.get("Subject", ""))
                from_addr = decode_mime_words(msg.get("From", ""))
                date_str = msg.get("Date", "")
                message_id_header = msg.get("Message-ID", "")
                
                # Parse date
                try:
                    date_obj = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = date_obj.strftime("%Y-%m-%d")
                    date_display = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    date_formatted = date_str
                    date_display = date_str
                
                # Check if tax-related
                if is_tax_related(subject, from_addr):
                    # Get the IMAP sequence number as string for linking
                    imap_id = email_id.decode('utf-8') if isinstance(email_id, bytes) else str(email_id)
                    
                    tax_emails.append({
                        'imap_id': imap_id,
                        'uid': uid or imap_id,
                        'subject': subject,
                        'from': from_addr,
                        'date': date_display,
                        'date_short': date_formatted,
                        'message_id': message_id_header.strip('<>') if message_id_header else '',
                    })
                    print(f"TAX EMAIL FOUND:")
                    print(f"  Date: {date_display}")
                    print(f"  From: {from_addr}")
                    print(f"  Subject: {subject}")
                    print(f"  IMAP ID: {imap_id}")
                    print()
            
            except Exception as e:
                print(f"Error processing email {email_id}: {e}")
        
        print("=" * 80)
        print(f"Total tax-related emails found: {len(tax_emails)}")
        
        # Now get UIDs for proper Gmail links
        # Fetch UIDs for all found tax emails
        uid_map = {}
        if tax_emails:
            imap_ids_str = ','.join(e['imap_id'] for e in tax_emails)
            status, uid_data = mail.fetch(imap_ids_str, "(UID)")
            if status == "OK":
                for item in uid_data:
                    if isinstance(item, tuple):
                        info = item[0].decode('utf-8', errors='ignore') if isinstance(item[0], bytes) else str(item[0])
                        # Parse: "123 (UID 456789)"
                        seq_match = re.match(r'^(\d+)', info)
                        uid_match = re.search(r'UID (\d+)', info)
                        if seq_match and uid_match:
                            uid_map[seq_match.group(1)] = uid_match.group(1)
        
        # Update UIDs in tax_emails
        for e in tax_emails:
            if e['imap_id'] in uid_map:
                e['uid'] = uid_map[e['imap_id']]
        
        # Output as JSON for easy parsing
        print("\nJSON_OUTPUT_START")
        print(json.dumps(tax_emails, indent=2))
        print("JSON_OUTPUT_END")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
