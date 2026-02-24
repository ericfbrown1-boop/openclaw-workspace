#!/usr/bin/env python3
"""Email the farm trip tax documentation."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Gmail credentials
EMAIL = "ericfbrown1@gmail.com"
PASSWORD = "sxugqgnxpfgvxcik"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email_with_attachment():
    """Send email with Word document attachment."""
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    msg['Subject'] = "Farm Trip Documentation - Sept/Oct 2025 for Tax Return"
    
    # Email body
    body = """
Dear Eric,

Please find attached the farm business travel documentation for your trip to Traverse City in October 2025.

TRIP SUMMARY:
- Dates: October 22-26, 2025
- Purpose: End-of-season farm review at 6644 Peninsula Drive, Traverse City, MI
- Transportation: United Airlines (Confirmation MH14S3)
- Total Documented Expense: $670.94

This document is formatted for IRS Schedule F (Form 1040) supporting documentation.

Flight Details:
- Route: San Francisco (SFO) → Chicago (ORD) → Traverse City (TVC) and return
- Cost: $670.94

The trip was made to review end-of-season farming operations, including assessment of the cherry harvest, equipment needs, and property management activities.

Best regards,
OpenClaw Assistant
    """.strip()
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach Word document
    filename = "Farm_Trip_Sept_Oct_2025_Tax_Documentation.docx"
    filepath = "/Users/ericbrown/.openclaw/workspace/" + filename
    
    try:
        with open(filepath, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}',
        )
        
        msg.attach(part)
        
        # Send email
        print("Connecting to Gmail SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        print("Logging in...")
        server.login(EMAIL, PASSWORD)
        
        print("Sending email...")
        text = msg.as_string()
        server.sendmail(EMAIL, EMAIL, text)
        server.quit()
        
        print(f"\n✓ Email sent successfully to {EMAIL}")
        print(f"✓ Attachment: {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_email_with_attachment()
