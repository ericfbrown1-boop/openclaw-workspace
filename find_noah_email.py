#!/usr/bin/env python3
"""Find email from Noah Kolassa."""

import imaplib
import email
from email.header import decode_header
import re

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"
IMAP_SERVER = "imap.gmail.com"

def decode_mime_words(s):
    if s is None:
        return ""
    decoded_fragments = decode_header(s)
    return ''.join(
        str(fragment, encoding or 'utf-8') if isinstance(fragment, bytes) else str(fragment)
        for fragment, encoding in decoded_fragments
    )

def get_email_body(msg):
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
    return body

def main():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("INBOX")
        
        # Simple search for emails from Noah
        print("Searching for emails from Noah...")
        status, messages = mail.search(None, 'FROM "Noah"')
        
        if status != "OK" or not messages[0]:
            print("No emails found from Noah")
            mail.close()
            mail.logout()
            return
        
        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} emails from Noah\n")
        print("=" * 80)
        
        # Process most recent 10 emails
        recent_ids = email_ids[-10:] if len(email_ids) > 10 else email_ids
        recent_ids.reverse()  # Most recent first
        
        for i, email_id in enumerate(recent_ids, 1):
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
                except:
                    date_formatted = date_str
                
                body = get_email_body(msg)
                
                print(f"\n{i}. Email from Noah")
                print(f"   Date: {date_formatted}")
                print(f"   From: {from_addr}")
                print(f"   Subject: {subject}")
                print(f"\n   Body:\n{body}")
                print("\n" + "=" * 80)
                
            except Exception as e:
                print(f"Error processing email: {e}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
