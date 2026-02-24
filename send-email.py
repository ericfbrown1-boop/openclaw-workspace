#!/usr/bin/env python3
"""
Simple email sender script for Jarvis
Usage: python3 send-email.py "Subject" "Body"
"""
import smtplib
import sys
from email.message import EmailMessage

def send_email(subject, body):
    msg = EmailMessage()
    msg['From'] = 'ericfbrown1@gmail.com'
    msg['To'] = 'ericfbrown1@gmail.com'
    msg['Subject'] = subject
    
    # Add signature
    full_body = body + "\n\n---\nFrom Jarvis - AI Assistant to Eric Brown"
    msg.set_content(full_body)
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login('ericfbrown1@gmail.com', 'sxugqgnxpfgvxcik')
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: send-email.py <subject> <body>")
        sys.exit(1)
    
    success = send_email(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
