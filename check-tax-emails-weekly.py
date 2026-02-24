#!/usr/bin/env python3
"""Check unread tax-related emails from the past 7 days."""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"  # App password
IMAP_SERVER = "imap.gmail.com"

# Tax-related keywords
TAX_KEYWORDS = [
    "tax", "1099", "w-2", "w2", "irs", "1040", 
    "deduction", "tax return", "tax form", "tax document",
    "withholding", "estimated tax", "capital gains",
    "tax statement", "tax reporting", "taxable",
    "federal tax", "state tax", "tax year"
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

def get_message_id(msg):
    """Extract Gmail message ID from headers."""
    message_id = msg.get("Message-ID", "")
    # Try to extract the actual Gmail ID from the Message-ID header
    # Gmail message IDs are in the format <xxxxx.xxxxx@mail.gmail.com>
    if message_id:
        # Return just the hex ID part
        match = re.search(r'<(.+?)@', message_id)
        if match:
            return match.group(1).replace('.', '')
    return ""

def is_tax_related(subject, from_addr, body):
    """Check if email is tax-related."""
    combined = f"{subject} {from_addr} {body}".lower()
    return any(keyword.lower() in combined for keyword in TAX_KEYWORDS)

def main():
    """Check tax-related unread emails from past 7 days."""
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Calculate date 7 days ago
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        
        # Search for unread emails from the past 7 days
        search_criteria = f'(UNSEEN SINCE {seven_days_ago})'
        status, messages = mail.search(None, search_criteria)
        
        if status != "OK" or not messages[0]:
            print("No unread messages found in the past 7 days")
            mail.close()
            mail.logout()
            return
        
        email_ids = messages[0].split()
        total_unread = len(email_ids)
        
        print(f"Checking {total_unread} unread emails from the past 7 days...")
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
                except:
                    date_formatted = date_str
                
                # Get body preview for matching
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
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
                
                # Check if tax-related
                if is_tax_related(subject, from_addr, body):
                    # Get Gmail message ID
                    gmail_id = email_id.decode('utf-8')
                    
                    tax_emails.append({
                        'date': date_formatted,
                        'from': from_addr,
                        'subject': subject,
                        'gmail_id': gmail_id
                    })
                
            except Exception as e:
                print(f"Error processing email: {e}")
        
        # Print results in a structured format
        if tax_emails:
            print(f"\nFound {len(tax_emails)} tax-related emails:\n")
            print("=" * 80)
            for i, email_data in enumerate(tax_emails, 1):
                print(f"{i}.")
                print(f"Date: {email_data['date']}")
                print(f"From: {email_data['from']}")
                print(f"Subject: {email_data['subject']}")
                print(f"Gmail ID: {email_data['gmail_id']}")
                print("-" * 80)
        else:
            print("\nNo tax-related emails found in the past 7 days.")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
