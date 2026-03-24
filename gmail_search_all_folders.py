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
    print("✓ Connected successfully\n")
    return mail

def search_all_folders(mail):
    """Search all folders for NARR-related content"""
    
    # Get list of all folders
    status, folders = mail.list()
    
    print("Available folders:")
    folder_list = []
    for f in folders:
        # Decode folder name
        parts = f.decode().split(' "/" ')
        if len(parts) >= 2:
            folder_name = parts[1].strip('"')
            folder_list.append(folder_name)
            print(f"  - {folder_name}")
    
    print(f"\n{'='*80}")
    print("SEARCHING FOR NARR IN ALL FOLDERS:")
    print(f"{'='*80}\n")
    
    # Search for emails from past 30 days
    since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
    today = datetime.now().strftime("%d-%b-%Y")
    
    narr_emails = []
    
    for folder_name in folder_list:
        try:
            status, messages = mail.select(f'"{folder_name}"', readonly=True)
            if status != 'OK':
                continue
            
            # Try searching for NARR in subject or body
            search_criteria = [
                f'(SINCE {since_date} SUBJECT "NARR")',
                f'(SINCE {since_date} BODY "NARR")',
                f'(ON {today})'  # All emails from today
            ]
            
            for criteria in search_criteria:
                try:
                    status, msg_ids = mail.search(None, criteria)
                    if status == 'OK' and msg_ids[0]:
                        msg_id_list = msg_ids[0].split()
                        
                        for msg_id in msg_id_list:
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
                                    subject = subject_decoded[0].decode(errors='ignore')
                                else:
                                    subject = subject_decoded[0]
                            
                            # Get date
                            date_str = msg.get('Date', '')
                            
                            # Get from
                            from_str = msg.get('From', '')
                            
                            # Check for NARR in subject or attachments
                            has_narr = False
                            attachments_list = []
                            
                            if 'NARR' in subject.upper():
                                has_narr = True
                            
                            # Check for attachments
                            if msg.is_multipart():
                                for part in msg.walk():
                                    filename = part.get_filename()
                                    
                                    if filename:
                                        # Decode filename if needed
                                        decoded = decode_header(filename)
                                        if isinstance(decoded[0][0], bytes):
                                            filename = decoded[0][0].decode(decoded[0][1] or 'utf-8', errors='ignore')
                                        else:
                                            filename = decoded[0][0]
                                        
                                        attachments_list.append(filename)
                                        
                                        if 'NARR' in filename.upper():
                                            has_narr = True
                            
                            if has_narr:
                                email_info = {
                                    'folder': folder_name,
                                    'subject': subject,
                                    'date': date_str,
                                    'from': from_str,
                                    'attachments': attachments_list,
                                    'msg_id': msg_id,
                                    'msg': msg
                                }
                                
                                # Check if not already in list
                                if not any(e['subject'] == subject and e['date'] == date_str for e in narr_emails):
                                    narr_emails.append(email_info)
                                    print(f"✓ Found NARR email in [{folder_name}]")
                                    print(f"  Subject: {subject}")
                                    print(f"  Date: {date_str}")
                                    print(f"  From: {from_str}")
                                    if attachments_list:
                                        for att in attachments_list:
                                            print(f"  📎 {att}")
                                    print()
                
                except Exception as e:
                    pass  # Skip search errors
                    
        except Exception as e:
            pass  # Skip folder access errors
    
    return narr_emails

def download_attachment(email_info, attachment_name=None):
    """Download attachment from email"""
    msg = email_info['msg']
    
    if msg.is_multipart():
        for part in msg.walk():
            filename = part.get_filename()
            
            if filename:
                # Decode filename if needed
                decoded = decode_header(filename)
                if isinstance(decoded[0][0], bytes):
                    filename = decoded[0][0].decode(decoded[0][1] or 'utf-8', errors='ignore')
                else:
                    filename = decoded[0][0]
                
                # If specific attachment requested, check for match
                if attachment_name and attachment_name.lower() not in filename.lower():
                    continue
                
                # Download
                filepath = os.path.join(os.getcwd(), filename)
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                
                print(f"✓ Downloaded: {filename}")
                print(f"  Path: {filepath}")
                return filepath
    
    return None

def main():
    try:
        # Connect to Gmail
        mail = connect_gmail()
        
        # Search all folders
        narr_emails = search_all_folders(mail)
        
        if not narr_emails:
            print("\n❌ No NARR-related emails found in any folder")
            mail.logout()
            return
        
        print(f"\n{'='*80}")
        print(f"FOUND {len(narr_emails)} NARR-RELATED EMAIL(S)")
        print(f"{'='*80}\n")
        
        # Download attachments from most recent
        for email_info in narr_emails[:3]:  # Download from first 3
            print(f"\nProcessing: {email_info['subject']}")
            if email_info['attachments']:
                for att_name in email_info['attachments']:
                    if 'NARR' in att_name.upper() or 'MEMO' in att_name.upper() or '.doc' in att_name.lower():
                        filepath = download_attachment(email_info, att_name)
                        if filepath:
                            print(f"\n{'='*80}")
                            print(f"✓ SUCCESS: Downloaded NARR document")
                            print(f"File: {filepath}")
                            print(f"From email: {email_info['subject']}")
                            print(f"Folder: {email_info['folder']}")
                            print(f"Date: {email_info['date']}")
                            print(f"{'='*80}")
                            break
        
        # Logout
        mail.logout()
        print("\n✓ Disconnected from Gmail")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
