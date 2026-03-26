#!/usr/bin/env python3
"""
Send email with multiple attachments
Usage: send-email-multiple-attachments.py <to_email> <subject> <body> <attachment1> <attachment2> ...
"""

import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

if len(sys.argv) < 5:
    print("Usage: send-email-multiple-attachments.py <to_email> <subject> <body> <attachment1> [attachment2] [attachment3] ...")
    sys.exit(1)

to_email = sys.argv[1]
subject = sys.argv[2]
body = sys.argv[3]
attachments = sys.argv[4:]  # All remaining arguments are attachment paths

# Gmail SMTP settings
smtp_server = "smtp.gmail.com"
smtp_port = 587
from_email = "ericfbrown1@gmail.com"
password = "jplmfcfecipqwkgi"  # App password

# Create message
msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = to_email
msg['Subject'] = subject

# Add body
msg.attach(MIMEText(body, 'plain'))

# Add each attachment
for attachment_path in attachments:
    if not os.path.exists(attachment_path):
        print(f"Error: Attachment not found: {attachment_path}")
        sys.exit(1)
    
    filename = os.path.basename(attachment_path)
    
    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename= {filename}',
    )
    
    msg.attach(part)

# Send email
try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_email, password)
    server.send_message(msg)
    server.quit()
    print(f"Email sent successfully to {to_email} with {len(attachments)} attachment(s)")
except Exception as e:
    print(f"Error sending email: {e}")
    sys.exit(1)
