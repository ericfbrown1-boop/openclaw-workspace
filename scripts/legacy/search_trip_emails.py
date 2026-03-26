#!/usr/bin/env python3
"""Search Gmail for trip-related emails and extract expense information."""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
import json

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
    
    # Prefer plain text, fall back to HTML
    return body_plain if body_plain else body_html

def extract_amounts(text):
    """Extract dollar amounts from text."""
    # Match patterns like $123.45, $1,234.56, USD 123.45, etc.
    patterns = [
        r'\$\s*[\d,]+\.?\d*',
        r'USD\s*[\d,]+\.?\d*',
        r'Total[:\s]+\$?\s*[\d,]+\.?\d*',
        r'Amount[:\s]+\$?\s*[\d,]+\.?\d*',
    ]
    
    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amounts.extend(matches)
    
    return amounts

def main():
    """Search for trip-related emails in Sept-Oct 2025."""
    try:
        # Connect to Gmail
        print("Connecting to Gmail...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Search for emails in Sept-Oct 2025 timeframe
        # IMAP date format: DD-MMM-YYYY
        # Search for emails from Sept 1 to Oct 31, 2025
        search_criteria = '(SINCE 01-Sep-2025 BEFORE 01-Nov-2025)'
        
        print(f"Searching for emails from Sept 1 - Oct 31, 2025...")
        status, messages = mail.search(None, search_criteria)
        
        if status != "OK":
            print("No messages found")
            return
        
        email_ids = messages[0].split()
        total_emails = len(email_ids)
        
        print(f"Found {total_emails} emails in date range")
        print("=" * 80)
        
        # Keywords to search for
        keywords = [
            'TVC', 'Traverse City', 'traverse city',
            'flight confirmation', 'flight', 'airline',
            'reservation', 'booking', 'itinerary',
            'United', 'Delta', 'American Airlines',
            'SFO', 'San Francisco',
            'hotel', 'lodging', 'accommodation',
            'rental car', 'car rental', 'hertz', 'enterprise', 'avis', 'budget'
        ]
        
        relevant_emails = []
        
        for i, email_id in enumerate(email_ids, 1):
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
                except Exception:
                    date_formatted = date_str
                
                # Get full body
                body = get_email_body(msg)
                
                # Check if any keywords match
                search_text = f"{subject} {from_addr} {body}".lower()
                matching_keywords = [kw for kw in keywords if kw.lower() in search_text]
                
                if matching_keywords:
                    # Extract dollar amounts
                    amounts = extract_amounts(body)
                    
                    email_data = {
                        'id': email_id.decode(),
                        'subject': subject,
                        'from': from_addr,
                        'date': date_formatted,
                        'matching_keywords': matching_keywords,
                        'amounts': amounts,
                        'body': body[:2000]  # First 2000 chars
                    }
                    
                    relevant_emails.append(email_data)
                    
                    print(f"\n{'='*80}")
                    print(f"Email {len(relevant_emails)}: [{date_formatted}]")
                    print(f"From: {from_addr}")
                    print(f"Subject: {subject}")
                    print(f"Matching keywords: {', '.join(matching_keywords)}")
                    if amounts:
                        print(f"Amounts found: {', '.join(amounts[:5])}")
                    print(f"Body preview: {body[:500]}...")
                
            except Exception as e:
                print(f"Error processing email {i}: {e}")
        
        print(f"\n{'='*80}")
        print(f"\nTotal relevant emails found: {len(relevant_emails)}")
        
        # Save results to JSON file
        output_file = "/Users/ericbrown/.openclaw/workspace/trip_emails_data.json"
        with open(output_file, 'w') as f:
            json.dump(relevant_emails, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
