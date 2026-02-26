#!/usr/bin/env python3
"""Scan Gmail for tax-related emails from the past 7 days."""

import imaplib
import email
from email.header import decode_header
import re
import json
from datetime import datetime, timedelta, timezone

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"  # App password
IMAP_SERVER = "imap.gmail.com"

# Tax-related keywords
TAX_KEYWORDS = [
    'tax', '1099', 'w-2', 'w2', '1040', 'irs', 'k-1', 'k1',
    'deduct', 'depreciat', 'schedule', 'refund', 'withhold',
    'capital gain', 'dividend', 'interest income', 'estate tax',
    'property tax', 'income tax', 'tax return', 'tax document',
    'tax form', 'tax statement', 'brokerage', 'schwab', 'fidelity',
    'vanguard', 'turbotax', 'h&r block', 'cpa', 'accountant',
    'fiscal', 'agi', 'adjusted gross', 'charitable contribution',
    'donation receipt', 'mortgage interest', 'charitable deduction',
    '1098', '1095', 'ssn', 'ein', 'employer identification',
    'quarterly', 'estimated tax', 'extension', 'audit', 'amend',
    'state tax', 'federal tax', 'tax credit', 'child tax',
    'wash sale', 'cost basis', 'unrealized', 'realized gain',
    'roth', '401k', 'ira distribution', 'rmd', 'required minimum',
    'farm', 'vineyard', 'agrivine', 'rental income', 'rental property',
    'depreciation', 'section 179', 'bonus depreciation',
]

def decode_mime_words(s):
    """Decode MIME encoded-words in header."""
    if s is None:
        return ""
    decoded_fragments = decode_header(s)
    result = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            result.append(fragment.decode(encoding or 'utf-8', errors='replace'))
        else:
            result.append(str(fragment))
    return ''.join(result)

def is_tax_related(subject, from_addr, body_preview=""):
    """Check if email is likely tax-related."""
    text = f"{subject} {from_addr} {body_preview}".lower()
    for kw in TAX_KEYWORDS:
        if kw in text:
            return True, kw
    return False, None

def get_email_body(msg):
    """Extract email body text (first 500 chars)."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
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

def main():
    """Scan last 7 days of email for tax-related messages."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        results = []
        
        # Search both INBOX and ALL mail (including read emails)
        # Use SINCE date for last 7 days
        since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        
        for folder in ["INBOX", "[Gmail]/All Mail"]:
            try:
                status, _ = mail.select(folder, readonly=True)
                if status != "OK":
                    continue
                
                # Search ALL emails (read + unread) in last 7 days
                search_criteria = f'SINCE {since_date}'
                status, messages = mail.search(None, search_criteria)
                if status != "OK":
                    continue
                
                email_ids = messages[0].split()
                print(f"Folder '{folder}': {len(email_ids)} emails in last 7 days", flush=True)
                
                seen_ids = set()
                
                for email_id in email_ids:
                    try:
                        # Fetch headers only first (faster)
                        status, msg_data = mail.fetch(email_id, "(BODY[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)] UID)")
                        if status != "OK":
                            continue
                        
                        raw = msg_data[0][1] if isinstance(msg_data[0], tuple) else b""
                        msg = email.message_from_bytes(raw)
                        
                        subject = decode_mime_words(msg.get("Subject", ""))
                        from_addr = decode_mime_words(msg.get("From", ""))
                        date_str = msg.get("Date", "")
                        message_id = msg.get("Message-ID", "").strip().strip("<>")
                        
                        # Skip already processed
                        if message_id and message_id in seen_ids:
                            continue
                        if message_id:
                            seen_ids.add(message_id)
                        
                        # Parse date
                        try:
                            date_tuple = email.utils.parsedate_to_datetime(date_str)
                            # Normalize to PT-ish (just use as-is, show local date)
                            date_formatted = date_tuple.strftime("%Y-%m-%d")
                            date_display = date_tuple.strftime("%m/%d/%Y")
                        except:
                            date_formatted = date_str
                            date_display = date_str
                        
                        # Quick tax check on subject + from
                        tax_hit, keyword = is_tax_related(subject, from_addr)
                        
                        if tax_hit:
                            # Get UID for Gmail link
                            status2, uid_data = mail.fetch(email_id, "(UID)")
                            uid = ""
                            if status2 == "OK" and uid_data:
                                uid_match = re.search(r'UID (\d+)', str(uid_data[0]))
                                if uid_match:
                                    uid = uid_match.group(1)
                            
                            results.append({
                                "date_received": date_display,
                                "date_sort": date_formatted,
                                "sender": from_addr,
                                "subject": subject,
                                "message_id": message_id,
                                "uid": uid,
                                "keyword_matched": keyword,
                                "gmail_link": f"https://mail.google.com/mail/u/0/#search/rfc822msgid:{message_id}" if message_id else ""
                            })
                            
                    except Exception as e:
                        pass
                        
            except Exception as e:
                print(f"Error with folder {folder}: {e}")
        
        mail.close()
        mail.logout()
        
        # Deduplicate by message_id
        seen = set()
        deduped = []
        for r in results:
            key = r["message_id"] or f"{r['date_sort']}|{r['sender']}|{r['subject']}"
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        
        # Sort by date
        deduped.sort(key=lambda x: x["date_sort"])
        
        print(f"\nTotal tax-related emails found: {len(deduped)}")
        print("=" * 80)
        
        for i, e in enumerate(deduped, 1):
            print(f"\n{i}. Date: {e['date_received']}")
            print(f"   From: {e['sender']}")
            print(f"   Subject: {e['subject']}")
            print(f"   Keyword: {e['keyword_matched']}")
            print(f"   Message-ID: {e['message_id']}")
            print(f"   Gmail Link: {e['gmail_link']}")
        
        # Write JSON for further processing
        with open("/tmp/tax_emails.json", "w") as f:
            json.dump(deduped, f, indent=2)
        
        print(f"\nResults saved to /tmp/tax_emails.json")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
