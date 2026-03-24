#!/usr/bin/env python3
import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime, timedelta

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

def search_sent_folder_week(mail):
    """Search for emails in Sent folder from past 7 days"""
    print("\nSearching Gmail folders...")
    
    # Try different possible sent folder names
    sent_folders = ['[Gmail]/Sent Mail', 'Sent', 'SENT', '[Gmail]/Sent']
    
    for folder in sent_folders:
        try:
            status, messages = mail.select(f'"{folder}"')
            if status == 'OK':
                print(f"✓ Found sent folder: {folder}")
                
                # Search for emails from past 7 days
                week_ago = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
                print(f"Searching for emails since: {week_ago}")
                
                # Search for emails from past week
                status, msg_ids = mail.search(None, f'SINCE {week_ago}')
                
                if status == 'OK':
                    msg_id_list = msg_ids[0].split()
                    print(f"Found {len(msg_id_list)} email(s) from past week")
                    return mail, msg_id_list, folder
        except Exception as e:
            print(f"Could not access {folder}: {e}")
            continue
    
    return mail, [], None

def search_narr_attachments(mail, msg_ids):
    """Search specifically for NARR-related attachments"""
    print("\n" + "="*80)
    print("SEARCHING FOR NARR-RELATED ATTACHMENTS:")
    print("="*80)
    
    narr_emails = []
    
    for idx, msg_id in enumerate(reversed(msg_ids), 1):
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
        
        # Get date
        date_str = msg.get('Date', '')
        
        # Check subject for NARR
        if 'NARR' in subject.upper():
            print(f"\n✓ Found NARR in subject!")
            print(f"   Subject: {subject}")
            print(f"   Date: {date_str}")
            
            # Check for attachments
            if msg.is_multipart():
                for part in msg.walk():
                    filename = part.get_filename()
                    
                    if filename:
                        # Decode filename if needed
                        decoded = decode_header(filename)
                        if isinstance(decoded[0][0], bytes):
                            filename = decoded[0][0].decode(decoded[0][1] or 'utf-8')
                        else:
                            filename = decoded[0][0]
                        
                        print(f"   📎 Attachment: {filename}")
                        narr_emails.append({
                            'subject': subject,
                            'date': date_str,
                            'filename': filename,
                            'part': part
                        })
        
        # Check attachments for NARR
        if msg.is_multipart():
            for part in msg.walk():
                filename = part.get_filename()
                
                if filename:
                    # Decode filename if needed
                    decoded = decode_header(filename)
                    if isinstance(decoded[0][0], bytes):
                        filename = decoded[0][0].decode(decoded[0][1] or 'utf-8')
                    else:
                        filename = decoded[0][0]
                    
                    if 'NARR' in filename.upper():
                        print(f"\n✓ Found NARR in attachment filename!")
                        print(f"   Subject: {subject}")
                        print(f"   Date: {date_str}")
                        print(f"   📎 Attachment: {filename}")
                        narr_emails.append({
                            'subject': subject,
                            'date': date_str,
                            'filename': filename,
                            'part': part
                        })
    
    return narr_emails

def download_narr_attachment(attachments):
    """Download the most recent NARR attachment"""
    if not attachments:
        return None, None
    
    # Take the first one (most recent)
    att = attachments[0]
    
    print(f"\n{'='*80}")
    print(f"DOWNLOADING MOST RECENT NARR DOCUMENT:")
    print(f"{'='*80}")
    print(f"Subject: {att['subject']}")
    print(f"Date: {att['date']}")
    print(f"Filename: {att['filename']}")
    
    # Download the attachment
    filepath = os.path.join(os.getcwd(), att['filename'])
    with open(filepath, 'wb') as f:
        f.write(att['part'].get_payload(decode=True))
    
    print(f"✓ Downloaded to: {filepath}")
    return filepath, att['subject']

def main():
    try:
        # Connect to Gmail
        mail = connect_gmail()
        
        # Search sent folder for past week
        mail, msg_ids, folder = search_sent_folder_week(mail)
        
        if not msg_ids:
            print("\n❌ No emails found from past week in Sent folder")
            mail.logout()
            return
        
        # Search for NARR attachments
        narr_attachments = search_narr_attachments(mail, msg_ids)
        
        if not narr_attachments:
            print("\n❌ No NARR-related emails or attachments found in past week")
            mail.logout()
            return
        
        # Download the most recent NARR attachment
        filepath, subject = download_narr_attachment(narr_attachments)
        
        if filepath:
            print(f"\n{'='*80}")
            print(f"✓ SUCCESS!")
            print(f"{'='*80}")
        
        # Logout
        mail.logout()
        print("\n✓ Disconnected from Gmail")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
