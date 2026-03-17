#!/usr/bin/env python3
"""Scan Gmail for tax-related emails from the past 7 days."""

import imaplib
import email
from email.header import decode_header
import re
import json
from datetime import datetime, timedelta

EMAIL_ADDR = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"
IMAP_SERVER = "imap.gmail.com"

TAX_KEYWORDS = [
    'tax', 'w-2', 'w2', '1099', '1098', 'k-1', 'k1',
    'irs', 'federal tax', 'state tax', 'estimated tax',
    'tax return', 'tax refund', 'tax payment', 'tax document',
    'tax form', 'tax statement', 'tax filing', 'tax preparation',
    'cpa', 'accountant', 'turbotax', 'h&r block',
    'capital gains', 'dividend', 'interest income',
    'charitable', 'donation receipt', 'deduction',
    'property tax', 'mortgage interest', 'schedule',
    'withholding', 'exemption', 'adjusted gross',
    'amt', 'alternative minimum', 'tax credit',
    'rsu', 'stock option', 'vesting', 'equity compensation',
    'form 8949', 'schedule d', 'schedule c', 'schedule e', 'schedule f',
    'form f', 'farm income', 'rental income',
    'fidelity', 'schwab', 'vanguard', 'morgan stanley',
    'brokerage statement', 'year-end statement',
    'tax-ready', 'consolidated 1099',
    'annual tax', 'tax summary', 'tax information',
    'intuit', 'tax season', 'tax deadline',
    'estimated payment', 'quarterly tax',
    'franchise tax', 'ftb',
]

def decode_mime_words(s):
    if s is None:
        return ""
    decoded_fragments = decode_header(s)
    return ''.join(
        str(fragment, encoding or 'utf-8') if isinstance(fragment, bytes) else str(fragment)
        for fragment, encoding in decoded_fragments
    )

def is_tax_related(subject, from_addr, body=""):
    text = f"{subject} {from_addr} {body}".lower()
    return any(kw in text for kw in TAX_KEYWORDS)

def main():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDR, PASSWORD)
    mail.select("INBOX", readonly=True)
    
    # Search for emails from the past 7 days
    since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    status, messages = mail.search(None, f'(SINCE {since_date})')
    
    if status != "OK":
        print(json.dumps({"tax_emails": [], "error": "Search failed"}))
        return
    
    email_ids = messages[0].split()
    results = []
    
    for email_id in email_ids:
        try:
            status, msg_data = mail.fetch(email_id, "(RFC822 X-GM-MSGID)")
            if status != "OK":
                continue
            
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_mime_words(msg.get("Subject", ""))
            from_addr = decode_mime_words(msg.get("From", ""))
            date_str = msg.get("Date", "")
            message_id = msg.get("Message-ID", "")
            
            # Get Gmail message ID from X-GM-MSGID
            gm_msgid = ""
            for part in msg_data:
                if isinstance(part, tuple) and b'X-GM-MSGID' in part[0]:
                    match = re.search(rb'X-GM-MSGID (\d+)', part[0])
                    if match:
                        gm_msgid = hex(int(match.group(1)))[2:]
            
            # Get body preview
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode('utf-8', errors='ignore')[:500]
                                break
                        except:
                            pass
            else:
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')[:500]
                except:
                    pass
            
            if is_tax_related(subject, from_addr, body):
                try:
                    date_parsed = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = date_parsed.strftime("%Y-%m-%d")
                except:
                    date_formatted = date_str
                
                # Extract just the sender name/email
                sender = from_addr
                if '<' in from_addr:
                    sender_name = from_addr.split('<')[0].strip().strip('"')
                    sender_email = from_addr.split('<')[1].split('>')[0]
                    sender = sender_name if sender_name else sender_email
                
                # Use email UID for Gmail link
                results.append({
                    "date": date_formatted,
                    "sender": sender,
                    "subject": subject,
                    "message_id": message_id,
                    "gm_msgid": gm_msgid,
                    "email_id": email_id.decode()
                })
        except Exception as e:
            continue
    
    mail.close()
    mail.logout()
    
    print(json.dumps({"tax_emails": results, "total_scanned": len(email_ids)}, indent=2))

if __name__ == "__main__":
    main()
