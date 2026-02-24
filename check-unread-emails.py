#!/usr/bin/env python3
"""Check oldest unread emails in Gmail."""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"  # App password
IMAP_SERVER = "imap.gmail.com"

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
    # Remove excessive whitespace
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
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        except:
            pass
    return clean_text(body)[:500]  # First 500 chars

def main():
    """Check oldest 100 unread emails."""
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        if status != "OK":
            print("No unread messages found")
            return
        
        email_ids = messages[0].split()
        total_unread = len(email_ids)
        
        print(f"Total unread emails: {total_unread}")
        print("=" * 80)
        
        # Get oldest 100 (or all if less than 100)
        oldest_ids = email_ids[:min(100, total_unread)]
        
        emails_data = []
        
        for i, email_id in enumerate(oldest_ids, 1):
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                
                # Parse email
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Extract headers
                subject = decode_mime_words(msg.get("Subject", ""))
                from_addr = decode_mime_words(msg.get("From", ""))
                date_str = msg.get("Date", "")
                
                # Parse date
                try:
                    date_tuple = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = date_tuple.strftime("%Y-%m-%d %H:%M")
                except:
                    date_formatted = date_str
                
                # Get body preview
                body_preview = get_email_body(msg)
                
                emails_data.append({
                    'num': i,
                    'subject': subject,
                    'from': from_addr,
                    'date': date_formatted,
                    'body': body_preview
                })
                
            except Exception as e:
                print(f"Error processing email {i}: {e}")
        
        # Print results
        print(f"\nOldest {len(emails_data)} unread emails:\n")
        
        for email_data in emails_data:
            print(f"{email_data['num']}. [{email_data['date']}]")
            print(f"   From: {email_data['from']}")
            print(f"   Subject: {email_data['subject']}")
            if email_data['body']:
                print(f"   Preview: {email_data['body'][:200]}...")
            print()
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
