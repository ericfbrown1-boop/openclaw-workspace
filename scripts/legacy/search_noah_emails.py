#!/usr/bin/env python3
"""Search for emails from Noah Kolassa about the lease."""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"  # App password
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
    """Extract full email body text."""
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
    return body

def main():
    """Search for emails from Noah about the property."""
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Search for emails mentioning Noah, Kolassa, 3469, or "Old Mission"
        search_terms = [
            'FROM "Noah"',
            'FROM "Kolassa"',
            'SUBJECT "Noah"',
            'SUBJECT "Kolassa"',
            'SUBJECT "3469"',
            'SUBJECT "Old Mission"',
            'BODY "Noah Kolassa"',
            'BODY "3469"'
        ]
        
        all_email_ids = set()
        
        for term in search_terms:
            try:
                status, messages = mail.search(None, term)
                if status == "OK" and messages[0]:
                    email_ids = messages[0].split()
                    all_email_ids.update(email_ids)
            except Exception:
                pass
        
        if not all_email_ids:
            print("No emails found matching search criteria")
            return
        
        print(f"Found {len(all_email_ids)} emails matching search criteria")
        print("=" * 80)
        
        emails_data = []
        
        for email_id in all_email_ids:
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
                    date_obj = date_tuple
                except Exception:
                    date_formatted = date_str
                    date_obj = None
                
                # Get full body
                body = get_email_body(msg)
                
                emails_data.append({
                    'id': email_id.decode(),
                    'subject': subject,
                    'from': from_addr,
                    'date': date_formatted,
                    'date_obj': date_obj,
                    'body': body
                })
                
            except Exception as e:
                print(f"Error processing email: {e}")
        
        # Sort by date (most recent first)
        emails_data.sort(key=lambda x: x['date_obj'] if x['date_obj'] else datetime.min, reverse=True)
        
        # Print results
        print(f"\nFound {len(emails_data)} emails:\n")
        
        for i, email_data in enumerate(emails_data, 1):
            print(f"{i}. [{email_data['date']}]")
            print(f"   From: {email_data['from']}")
            print(f"   Subject: {email_data['subject']}")
            print(f"   Body:")
            print(f"   {email_data['body'][:2000]}")
            print()
            print("=" * 80)
            print()
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
