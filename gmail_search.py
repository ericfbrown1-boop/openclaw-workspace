#!/usr/bin/env python3
import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "jplmfcfecipqwkgi"
IMAP_SERVER = "imap.gmail.com"

def connect_gmail():
    """Connect to Gmail via IMAP"""
    print(f"Connecting to {IMAP_SERVER}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    print("✓ Connected successfully")
    return mail

def search_sent_folder(mail):
    """Search for emails in Sent folder from today with NARR attachment"""
    # Gmail uses [Gmail]/Sent Mail for sent items
    print("\nSearching Gmail folders...")
    status, folders = mail.list()
    
    # Try different possible sent folder names
    sent_folders = ['[Gmail]/Sent Mail', 'Sent', 'SENT', '[Gmail]/Sent']
    
    for folder in sent_folders:
        try:
            status, messages = mail.select(f'"{folder}"')
            if status == 'OK':
                print(f"✓ Found sent folder: {folder}")
                
                # Search for emails from today
                today = datetime.now().strftime("%d-%b-%Y")
                print(f"Searching for emails from: {today}")
                
                # Search for emails from today
                status, msg_ids = mail.search(None, f'SINCE {today}')
                
                if status == 'OK':
                    msg_id_list = msg_ids[0].split()
                    print(f"Found {len(msg_id_list)} email(s) from today")
                    return mail, msg_id_list, folder
        except Exception as e:
            print(f"Could not access {folder}: {e}")
            continue
    
    return mail, [], None

def download_attachment(mail, msg_ids):
    """Download attachment from emails"""
    print("\nSearching for NARR Memo attachment...")
    
    for msg_id in reversed(msg_ids):  # Start with most recent
        status, msg_data = mail.fetch(msg_id, '(RFC822)')
        
        if status != 'OK':
            continue
            
        # Parse email
        msg = email.message_from_bytes(msg_data[0][1])
        
        # Get subject
        subject = msg.get('Subject', '')
        if subject:
            subject_decoded = decode_header(subject)[0]
            if isinstance(subject_decoded[0], bytes):
                subject = subject_decoded[0].decode()
            else:
                subject = subject_decoded[0]
        
        print(f"\nChecking email: {subject}")
        
        # Check for attachments
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                filename = part.get_filename()
                
                if filename:
                    # Decode filename if needed
                    decoded = decode_header(filename)
                    if isinstance(decoded[0][0], bytes):
                        filename = decoded[0][0].decode(decoded[0][1] or 'utf-8')
                    else:
                        filename = decoded[0][0]
                    
                    print(f"  Found attachment: {filename}")
                    
                    # Check if this is the NARR Memo
                    if 'NARR' in filename and 'Memo' in filename:
                        print(f"\n✓ Found NARR Memo: {filename}")
                        
                        # Download the attachment
                        filepath = os.path.join(os.getcwd(), filename)
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        
                        print(f"✓ Downloaded to: {filepath}")
                        return filepath, subject
    
    return None, None

def main():
    try:
        # Connect to Gmail
        mail = connect_gmail()
        
        # Search sent folder
        mail, msg_ids, folder = search_sent_folder(mail)
        
        if not msg_ids:
            print("\n❌ No emails found from today in Sent folder")
            mail.logout()
            return
        
        # Download attachment
        filepath, subject = download_attachment(mail, msg_ids)
        
        if filepath:
            print(f"\n✓ SUCCESS: Downloaded NARR Memo")
            print(f"File: {filepath}")
            print(f"Original email subject: {subject}")
        else:
            print("\n❌ Could not find NARR Memo attachment")
        
        # Logout
        mail.logout()
        print("\n✓ Disconnected from Gmail")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
