#!/usr/bin/env python3
"""Check for tax-related emails from the past 24 hours in Gmail."""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta
import json

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"  # App password
IMAP_SERVER = "imap.gmail.com"

# Tax-related keywords to search for
TAX_KEYWORDS = [
    "tax", "irs", "1099", "w-2", "w2", "1040", "k-1", "k1",
    "form", "federal return", "state return", "estimated tax",
    "tax form", "tax document", "tax return", "withholding",
    "deduction", "capital gain", "dividend", "interest income",
    "property tax", "accountant", "cpa", "turbotax", "h&r block"
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

def clean_text(text):
    """Clean up email text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_email_body(msg):
    """Extract email body text."""
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
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        except Exception:
            pass
    return clean_text(body)

def is_tax_related(subject, from_addr, body):
    """Check if email is tax-related based on keywords."""
    combined_text = f"{subject} {from_addr} {body}".lower()
    return any(keyword.lower() in combined_text for keyword in TAX_KEYWORDS)

def get_message_id(msg):
    """Extract the Gmail message ID for constructing links."""
    message_id = msg.get("Message-ID", "")
    # Gmail uses a hex version of the message-id
    return message_id

def main():
    """Check for tax-related emails from the past 24 hours."""
    try:
        # Calculate date 1 day ago
        seven_days_ago = datetime.now() - timedelta(days=1)
        date_filter = seven_days_ago.strftime("%d-%b-%Y")
        
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Search for emails from the past 24 hours
        status, messages = mail.search(None, f'(SINCE {date_filter})')
        if status != "OK":
            print("No messages found from the past 24 hours")
            return
        
        email_ids = messages[0].split()
        total_recent = len(email_ids)
        
        print(f"Total emails from past 24 hours: {total_recent}")
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
                message_id = msg.get("Message-ID", "")
                
                # Parse date
                try:
                    date_tuple = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = date_tuple.strftime("%Y-%m-%d")
                except Exception:
                    date_formatted = date_str
                
                # Get body
                body = get_email_body(msg)
                
                # Check if tax-related
                if is_tax_related(subject, from_addr, body):
                    # Extract Gmail message ID (the numeric part after the last /)
                    # We'll use the IMAP UID which we can convert to Gmail ID
                    gmail_id = email_id.decode() if isinstance(email_id, bytes) else email_id
                    
                    tax_emails.append({
                        'date': date_formatted,
                        'sender': from_addr,
                        'subject': subject,
                        'gmail_id': gmail_id,
                        'message_id': message_id
                    })
                
            except Exception as e:
                print(f"Error processing email: {e}")
        
        # Print results as JSON for easy parsing
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
