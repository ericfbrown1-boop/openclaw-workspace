#!/usr/bin/env python3
"""Scan Gmail for tax-related emails from the past 7 days."""

import imaplib
import email
from email.header import decode_header
import re
import json
from datetime import datetime, timedelta

EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"
IMAP_SERVER = "imap.gmail.com"

TAX_KEYWORDS = [
    'tax', 'w-2', 'w2', '1099', '1098', 'k-1', 'k1',
    'irs', 'refund', 'deduction', 'withholding',
    'estimated tax', 'tax return', 'tax filing',
    'form 1040', 'schedule c', 'schedule e', 'schedule f',
    'capital gains', 'dividend', '1095', 'hsa',
    'charitable', 'donation receipt', 'property tax',
    'mortgage interest', 'tax statement', 'tax document',
    'turbotax', 'h&r block', 'cpa', 'accountant',
    'ein', 'ssn', 'federal tax', 'state tax',
    'franchise tax', 'ftb', 'california tax',
    'michigan tax', 'income tax', 'tax prep',
    'tax summary', 'annual statement', 'year-end',
    'yearend', 'form f', 'farm tax', 'agrivine',
    'tax bill', 'assessment', 'tax notice',
    'estimated payment', 'quarterly tax',
    'tax credit', 'amt', 'rsu', 'stock option',
    'equity compensation', 'vesting', 'cost basis',
    'schwab', 'fidelity', 'morgan stanley',  # brokerages sending tax docs
    'tax lot', 'realized gain', 'unrealized',
]

def decode_mime_words(s):
    if s is None:
        return ""
    decoded_fragments = decode_header(s)
    return ''.join(
        str(fragment, encoding or 'utf-8') if isinstance(fragment, bytes) else str(fragment)
        for fragment, encoding in decoded_fragments
    )

def is_tax_related(subject, from_addr, body_preview):
    """Check if email is tax-related based on keywords."""
    text = f"{subject} {from_addr} {body_preview}".lower()
    for kw in TAX_KEYWORDS:
        if kw in text:
            return True
    return False

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
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        except:
            pass
    return re.sub(r'\s+', ' ', body).strip()[:500]

def get_gmail_message_id(msg):
    """Extract the Gmail-compatible message ID from headers."""
    msg_id = msg.get("Message-ID", "")
    # Also get X-GM-MSGID if available (more reliable for Gmail links)
    return msg_id

def main():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX", readonly=True)  # readonly=True so we don't mark as read
        
        # Search for emails from past 7 days
        since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE {since_date})')
        
        if status != "OK" or not messages[0]:
            print(json.dumps({"tax_emails": [], "total_scanned": 0}))
            return
        
        email_ids = messages[0].split()
        tax_emails = []
        
        for eid in email_ids:
            try:
                # Use BODY.PEEK to avoid marking as read
                status, msg_data = mail.fetch(eid, "(BODY.PEEK[] X-GM-MSGID)")
                if status != "OK":
                    continue
                
                # Extract X-GM-MSGID from response
                gm_msgid = None
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        header_info = response_part[0].decode() if isinstance(response_part[0], bytes) else str(response_part[0])
                        # Try to extract X-GM-MSGID
                        gm_match = re.search(r'X-GM-MSGID (\d+)', header_info)
                        if gm_match:
                            gm_msgid = gm_match.group(1)
                        
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject = decode_mime_words(msg.get("Subject", ""))
                        from_addr = decode_mime_words(msg.get("From", ""))
                        date_str = msg.get("Date", "")
                        
                        try:
                            date_obj = email.utils.parsedate_to_datetime(date_str)
                            date_formatted = date_obj.strftime("%Y-%m-%d")
                        except:
                            date_formatted = date_str
                        
                        body_preview = get_email_body(msg)
                        
                        if is_tax_related(subject, from_addr, body_preview):
                            # Build Gmail link using X-GM-MSGID (hex format)
                            gmail_link = ""
                            if gm_msgid:
                                gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{hex(int(gm_msgid))[2:]}"
                            
                            # Clean sender - extract just name/email
                            sender_clean = from_addr
                            
                            tax_emails.append({
                                "date": date_formatted,
                                "sender": sender_clean,
                                "subject": subject,
                                "gmail_link": gmail_link,
                                "imap_id": eid.decode(),
                            })
                        break
            except Exception as e:
                continue
        
        result = {
            "tax_emails": tax_emails,
            "total_scanned": len(email_ids),
            "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "period": f"{since_date} to now"
        }
        print(json.dumps(result, indent=2))
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
