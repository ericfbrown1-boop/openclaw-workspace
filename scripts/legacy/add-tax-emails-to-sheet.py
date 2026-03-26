#!/usr/bin/env python3
"""Add filtered tax emails to Google Sheet using gspread."""

import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Spreadsheet ID
SPREADSHEET_ID = "1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"

# Load filtered tax emails
with open('/Users/ericbrown/.openclaw/workspace/tax-emails-filtered.json', 'r') as f:
    tax_emails = json.load(f)

print(f"Found {len(tax_emails)} tax-related emails to add")
print("=" * 80)

# For now, just print what we would add
# (We'll need to get OAuth credentials to actually write to the sheet)
for email in tax_emails:
    gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{email['gmail_id']}"
    print(f"Date: {email['date']}")
    print(f"Sender: {email['sender']}")
    print(f"Subject: {email['subject']}")
    print(f"Link: {gmail_link}")
    print()

print(f"\nTotal: {len(tax_emails)} tax-related emails ready to add to sheet")
