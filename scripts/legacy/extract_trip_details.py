#!/usr/bin/env python3
"""Extract specific trip-related emails with full details."""

import imaplib
import email
from email.header import decode_header
import re
import json

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"
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

def get_email_body(msg):
    """Extract email body text (both plain and HTML)."""
    body_plain = ""
    body_html = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    if content_type == "text/plain":
                        body_plain = payload.decode('utf-8', errors='ignore')
                    elif content_type == "text/html":
                        body_html = payload.decode('utf-8', errors='ignore')
            except Exception:
                pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                if msg.get_content_type() == "text/plain":
                    body_plain = payload.decode('utf-8', errors='ignore')
                else:
                    body_html = payload.decode('utf-8', errors='ignore')
        except Exception:
            pass
    
    return body_plain if body_plain else body_html

def main():
    """Extract trip details from specific emails."""
    try:
        print("Connecting to Gmail...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Search for specific emails
        searches = [
            '(SINCE 01-Sep-2025 BEFORE 01-Nov-2025 FROM "United Airlines")',
            '(SINCE 01-Sep-2025 BEFORE 01-Nov-2025 SUBJECT "booking confirmation")',
            '(SINCE 01-Sep-2025 BEFORE 01-Nov-2025 SUBJECT "itinerary")',
            '(SINCE 01-Sep-2025 BEFORE 01-Nov-2025 SUBJECT "rental car")',
            '(SINCE 01-Sep-2025 BEFORE 01-Nov-2025 SUBJECT "hotel")',
            '(SINCE 01-Sep-2025 BEFORE 01-Nov-2025 BODY "Traverse City")',
            '(SINCE 01-Sep-2025 BEFORE 01-Nov-2025 BODY "TVC")',
        ]
        
        all_email_ids = set()
        
        for search_query in searches:
            print(f"Searching: {search_query}")
            status, messages = mail.search(None, search_query)
            if status == "OK" and messages[0]:
                email_ids = messages[0].split()
                all_email_ids.update(email_ids)
                print(f"  Found {len(email_ids)} emails")
        
        print(f"\nTotal unique emails found: {len(all_email_ids)}")
        print("="*80)
        
        trip_emails = []
        
        for email_id in all_email_ids:
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = decode_mime_words(msg.get("Subject", ""))
                from_addr = decode_mime_words(msg.get("From", ""))
                date_str = msg.get("Date", "")
                
                try:
                    date_tuple = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = date_tuple.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_formatted = date_str
                
                body = get_email_body(msg)
                
                # Check if relevant to trip
                search_text = f"{subject} {from_addr} {body}".lower()
                is_relevant = any(keyword in search_text for keyword in [
                    'traverse city', 'tvc', 'united airlines', 'rental car',
                    'hotel', 'lodging', 'cherry capital', 'michigan'
                ])
                
                if is_relevant:
                    email_data = {
                        'date': date_formatted,
                        'from': from_addr,
                        'subject': subject,
                        'body': body
                    }
                    trip_emails.append(email_data)
                    
                    print(f"\n{'='*80}")
                    print(f"Date: {date_formatted}")
                    print(f"From: {from_addr}")
                    print(f"Subject: {subject}")
                    print(f"Body length: {len(body)} chars")
                    print(f"Body preview (first 1000 chars):\n{body[:1000]}")
                    
            except Exception as e:
                print(f"Error processing email: {e}")
        
        # Save to JSON
        output_file = "/Users/ericbrown/.openclaw/workspace/trip_details.json"
        with open(output_file, 'w') as f:
            json.dump(trip_emails, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"\nTotal relevant emails found: {len(trip_emails)}")
        print(f"Results saved to: {output_file}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
