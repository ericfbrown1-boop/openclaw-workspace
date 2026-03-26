#!/usr/bin/env python3
"""Find tax-related emails from the past 24 hours."""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import json

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"  # App password
IMAP_SERVER = "imap.gmail.com"

# Tax-related keywords
TAX_KEYWORDS = [
    'tax', 'irs', '1099', 'w-2', 'w2', '1040', 'cpa', 'accountant',
    'deduction', 'withholding', 'refund', 'schedule', 'k-1', 'k1',
    'estimated tax', 'quarterly', 'filing', 'return', 'form', 
    'revenue', 'assessment', 'property tax', 'income tax', 'capital gain'
]

def decode_mime_words(s):
    """Decode MIME encoded-words in header."""
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
    return any(keyword.lower() in text for keyword in TAX_KEYWORDS)

def main():
    """Find tax-related emails from past 24 hours."""
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Calculate date 1 day ago
        seven_days_ago = datetime.now() - timedelta(days=1)
        date_str = seven_days_ago.strftime("%d-%b-%Y")
        
        # Search for emails from past 24 hours
        status, messages = mail.search(None, f'(SINCE {date_str})')
        if status != "OK":
            print("No messages found")
            return
        
        email_ids = messages[0].split()
        total_emails = len(email_ids)
        
        print(f"Total emails from past 24 hours: {total_emails}")
        print("=" * 80)
        
        tax_emails = []
        
        for email_id in email_ids:
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                
                # Parse email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract headers
                subject = decode_mime_words(msg.get("Subject", ""))
                from_addr = decode_mime_words(msg.get("From", ""))
                date_str = msg.get("Date", "")
                message_id = msg.get("Message-ID", "").strip('<>')
                
                # Parse date
                try:
                    date_tuple = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = date_tuple.strftime("%Y-%m-%d")
                except Exception:
                    date_formatted = ""
                
                # Get body preview for keyword matching
                body_preview = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body_preview = payload.decode('utf-8', errors='ignore')[:500]
                                    break
                            except Exception:
                                pass
                else:
                    try:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body_preview = payload.decode('utf-8', errors='ignore')[:500]
                    except Exception:
                        pass
                
                # Check if tax-related
                if is_tax_related(subject, from_addr, body_preview):
                    tax_emails.append({
                        'date': date_formatted,
                        'sender': from_addr,
                        'subject': subject,
                        'message_id': message_id
                    })
                
            except Exception as e:
                print(f"Error processing email {email_id}: {e}")
        
        # Print results as JSON
        print(f"\nFound {len(tax_emails)} tax-related emails:\n")
        print(json.dumps(tax_emails, indent=2))
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
