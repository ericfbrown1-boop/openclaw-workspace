#!/usr/bin/env python3
"""Check for tax-related emails from the past 7 days with proper Gmail IDs."""

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
    'tax', 'irs', 'w-2', 'w2', '1099', 'k-1', 'k1', 
    'income', 'deduction', 'cpa', 'accountant', 'turbotax',
    'filing', 'refund', 'withholding', 'estimated tax',
    'schedule c', 'schedule d', 'schedule e', 'form 1040',
    'tax return', 'tax document', 'tax form', 'keystone'
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

def get_gmail_id_from_imap(mail, email_id):
    """Get Gmail's X-GM-MSGID which can be used in Gmail URLs."""
    try:
        status, data = mail.fetch(email_id, '(X-GM-MSGID)')
        if status == 'OK':
            # Parse the response to extract X-GM-MSGID
            response = data[0].decode('utf-8') if isinstance(data[0], bytes) else str(data[0])
            match = re.search(r'X-GM-MSGID (\d+)', response)
            if match:
                # Convert decimal to hex for Gmail URL
                gmail_id_decimal = match.group(1)
                gmail_id_hex = format(int(gmail_id_decimal), 'x')
                return gmail_id_hex
    except Exception as e:
        print(f"Error getting Gmail ID: {e}")
    return None

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
                
                # Parse date
                try:
                    date_tuple = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = date_tuple.strftime("%Y-%m-%d")
                    date_time = date_tuple.strftime("%Y-%m-%d %H:%M")
                except:
                    date_formatted = date_str
                    date_time = date_str
                
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
                    # Get Gmail message ID for URL
                    gmail_id = get_gmail_id_from_imap(mail, email_id)
                    gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{gmail_id}" if gmail_id else ""
                    
                    # Clean up sender name/email
                    sender_match = re.search(r'<(.+?)>', from_addr)
                    if sender_match:
                        sender_email = sender_match.group(1)
                        sender_name = from_addr.split('<')[0].strip().strip('"')
                    else:
                        sender_email = from_addr
                        sender_name = from_addr
                    
                    tax_emails.append({
                        'date_received': date_formatted,
                        'date_time': date_time,
                        'sender_name': sender_name,
                        'sender_email': sender_email,
                        'sender_full': from_addr,
                        'subject': subject,
                        'gmail_url': gmail_url,
                        'gmail_id': gmail_id
                    })
                
            except Exception as e:
                print(f"Error processing email: {e}")
        
        # Sort by date
        tax_emails.sort(key=lambda x: x['date_time'])
        
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
