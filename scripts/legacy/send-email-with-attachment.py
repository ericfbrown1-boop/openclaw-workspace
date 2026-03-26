#!/usr/bin/env python3
"""Send email with attachment via Gmail SMTP."""

import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

# Gmail SMTP configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
FROM_EMAIL = "ericfbrown1@gmail.com"
FROM_NAME = "Jarvis"
PASSWORD = "jplmfcfecipqwkgi"  # App password

def send_email_with_attachment(to_email, subject, body, attachment_path):
    """Send email with attachment."""
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add body
    msg.attach(MIMEText(body, 'plain'))
    
    # Add attachment
    attachment_file = Path(attachment_path)
    if not attachment_file.exists():
        print(f"Error: Attachment file not found: {attachment_path}")
        return False
    
    with open(attachment_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
    
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename= {attachment_file.name}'
    )
    msg.attach(part)
    
    # Send email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(FROM_EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: send-email-with-attachment.py <to_email> <subject> <body> <attachment_path>")
        sys.exit(1)
    
    to_email = sys.argv[1]
    subject = sys.argv[2]
    body = sys.argv[3]
    attachment_path = sys.argv[4]
    
    success = send_email_with_attachment(to_email, subject, body, attachment_path)
    sys.exit(0 if success else 1)
