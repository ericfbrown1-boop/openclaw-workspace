#!/usr/bin/env python3
import imaplib
import email
from email.header import decode_header
import os

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"
IMAP_SERVER = "imap.gmail.com"

def connect_and_download():
    """Connect to Gmail and download NARR memo"""
    print("Connecting to Gmail...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    print("✓ Connected\n")
    
    # Select INBOX
    mail.select("INBOX")
    print("Selected INBOX")
    
    # Search for NARR in subject
    status, msg_ids = mail.search(None, 'SUBJECT "NARR memo"')
    
    if status != 'OK' or not msg_ids[0]:
        print("❌ No NARR memo found")
        return None
    
    msg_id_list = msg_ids[0].split()
    print(f"Found {len(msg_id_list)} matching email(s)\n")
    
    # Get the most recent one
    msg_id = msg_id_list[-1]
    status, msg_data = mail.fetch(msg_id, '(RFC822)')
    
    # Parse email
    msg = email.message_from_bytes(msg_data[0][1])
    
    # Get subject
    subject = msg.get('Subject', '')
    print(f"Subject: {subject}")
    print(f"From: {msg.get('From', '')}")
    print(f"Date: {msg.get('Date', '')}\n")
    
    # Download attachments
    if msg.is_multipart():
        for part in msg.walk():
            filename = part.get_filename()
            
            if filename:
                # Decode filename
                decoded = decode_header(filename)
                if isinstance(decoded[0][0], bytes):
                    filename = decoded[0][0].decode(decoded[0][1] or 'utf-8')
                else:
                    filename = decoded[0][0]
                
                print(f"Downloading: {filename}")
                
                # Save file
                filepath = os.path.join(os.getcwd(), filename)
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                
                print(f"✓ Saved to: {filepath}")
                
                mail.logout()
                return filepath
    
    mail.logout()
    return None

if __name__ == "__main__":
    filepath = connect_and_download()
    if filepath:
        print(f"\n{'='*80}")
        print("SUCCESS!")
        print(f"{'='*80}")
    else:
        print("\n❌ Failed to download")
