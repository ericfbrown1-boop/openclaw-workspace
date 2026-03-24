#!/usr/bin/env python3
"""Fetch email attachment by filename"""

import imaplib
import email
import sys
import os
from email.header import decode_header

# Gmail IMAP settings
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_ACCOUNT = "ericfbrown1@gmail.com"
EMAIL_PASSWORD = "jplmfcfecipqwkgi"  # App password

def search_and_download_attachment(search_filename, output_dir):
    """Search for email with specific attachment and download it"""
    
    # Connect to Gmail
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    
    # Select inbox
    mail.select("INBOX")
    
    # Search for recent emails (last 50)
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    
    # Get last 50 emails
    recent_ids = email_ids[-50:]
    
    found = False
    for email_id in reversed(recent_ids):
        # Fetch email
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Get subject
                subject = msg.get("Subject", "")
                if subject:
                    decoded_subject = decode_header(subject)[0]
                    if isinstance(decoded_subject[0], bytes):
                        subject = decoded_subject[0].decode(decoded_subject[1] or 'utf-8')
                    else:
                        subject = decoded_subject[0]
                
                # Check for attachments
                if msg.is_multipart():
                    for part in msg.walk():
                        content_disposition = part.get("Content-Disposition", "")
                        
                        if "attachment" in content_disposition:
                            filename = part.get_filename()
                            
                            if filename and search_filename.lower() in filename.lower():
                                print(f"✅ Found attachment: {filename}")
                                print(f"   Subject: {subject}")
                                print(f"   Email ID: {email_id.decode()}")
                                
                                # Download attachment
                                filepath = os.path.join(output_dir, filename)
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                
                                print(f"✅ Downloaded to: {filepath}")
                                found = True
                                mail.close()
                                mail.logout()
                                return filepath
    
    if not found:
        print(f"❌ No email found with attachment matching: {search_filename}")
        mail.close()
        mail.logout()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fetch-attachment.py <filename_to_search> <output_directory>")
        sys.exit(1)
    
    search_term = sys.argv[1]
    output_dir = sys.argv[2]
    
    os.makedirs(output_dir, exist_ok=True)
    
    result = search_and_download_attachment(search_term, output_dir)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
