#!/usr/bin/env python3
"""Check for tax-related emails from the past 7 days."""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta
import json

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"  # App password
IMAP_SERVER = "imap.gmail.com"

# Tax-related keywords to search for
TAX_KEYWORDS = [
    'tax', 'irs', 'w-2', 'w2', '1099', 'k-1', 'k1', 
    'income', 'deduction', 'cpa', 'accountant', 'turbotax',
    'filing', 'refund', 'withholding', 'estimated tax',
    'schedule c', 'schedule d', 'schedule e', 'form 1040',
    'tax return', 'tax document', 'tax form'
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
    combined_text = f"{subject} {from_addr} {body_preview}".lower()
    return any(keyword in combined_text for keyword in TAX_KEYWORDS)

def get_message_id(msg):
    """Extract Gmail message ID."""
    message_id = msg.get("Message-ID", "")
    # Try to extract the Gmail message ID if available
    return message_id

def main():
    """Check for tax-related emails from the past 7 days."""
    try:
        # Calculate date 7 days ago
        seven_days_ago = datetime.now() - timedelta(days=7)
        date_string = seven_days_ago.strftime("%d-%b-%Y")
        
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Search for emails from the past 7 days (both read and unread)
        status, messages = mail.search(None, f'(SINCE {date_string})')
        if status != "OK":
            print("No messages found")
            return
        
        email_ids = messages[0].split()
        total_emails = len(email_ids)
        
        print(f"Checking {total_emails} emails from the past 7 days for tax-related content...")
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
                    date_formatted = date_tuple.strftime("%Y-%m-%d %H:%M")
                except:
                    date_formatted = date_str
                
                # Get body preview for keyword matching
                body_preview = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body_preview = payload.decode('utf-8', errors='ignore')[:1000]
                                    break
                            except:
                                pass
                else:
                    try:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body_preview = payload.decode('utf-8', errors='ignore')[:1000]
                    except:
                        pass
                
                # Check if tax-related
                if is_tax_related(subject, from_addr, body_preview):
                    # Extract Gmail message ID from Message-ID header
                    gmail_id = email_id.decode('utf-8')
                    
                    tax_emails.append({
                        'date': date_formatted,
                        'from': from_addr,
                        'subject': subject,
                        'message_id': message_id,
                        'gmail_id': gmail_id
                    })
                
            except Exception as e:
                print(f"Error processing email: {e}")
        
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
