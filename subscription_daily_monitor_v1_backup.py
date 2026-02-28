#!/usr/bin/env python3
"""
Daily Subscription Monitor - Check for new recurring charges
Runs daily via cron, updates Google Sheet, alerts on new subscriptions
"""

import json
import re
import subprocess
from datetime import datetime, timedelta

SHEET_ID_FILE = '/Users/ericbrown/.openclaw/workspace/.subscription_sheet_id'

def run_command(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def load_sheet_id():
    """Load the sheet ID from file"""
    try:
        with open(SHEET_ID_FILE, 'r') as f:
            return f.read().strip()
    except:
        return None

def extract_amount_from_email(email_id):
    """Read email and extract amount"""
    result = run_command(f'gog gmail read {email_id} --plain')
    
    patterns = [
        r'\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'(?:Total|Amount|Payment|Charge):\s*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            return match.group(1).replace(',', '')
    
    return ""

def extract_vendor(sender):
    """Extract vendor name from sender"""
    match = re.search(r'"([^"]+)"', sender)
    if match:
        vendor = match.group(1)
        vendor = re.sub(r',?\s+(Inc\.|LLC|Ltd\.|Corp\.|PBC|Pte\. Ltd\.)$', '', vendor, flags=re.IGNORECASE)
        return vendor.strip()
    
    match = re.search(r'<([^@]+)@([^>]+)>', sender)
    if match:
        domain = match.group(2)
        domain = domain.replace('.com', '').replace('noreply', '')
        return domain.split('.')[0].title()
    
    return sender.split('<')[0].strip()

def check_new_subscriptions():
    """Check for new subscription charges in last 24 hours"""
    print("🔍 Checking for new subscription charges (last 24 hours)...")
    
    # Search for recent receipts/invoices
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    
    search_queries = [
        f'after:{yesterday} subject:(receipt OR invoice OR payment OR subscription)',
        f'after:{yesterday} from:(stripe.com OR apple.com OR zoom.us OR tesla.com)',
    ]
    
    new_emails = {}
    
    for query in search_queries:
        result = run_command(f'gog gmail search "{query}" --max 50 --json')
        try:
            data = json.loads(result)
            if 'threads' in data:
                for thread in data['threads']:
                    email_id = thread['id']
                    if email_id not in new_emails:
                        new_emails[email_id] = thread
        except:
            continue
    
    if not new_emails:
        print("✅ No new subscription charges found")
        return []
    
    print(f"📧 Found {len(new_emails)} new emails, analyzing...")
    
    # Analyze new emails
    new_charges = []
    
    for email_id, email in new_emails.items():
        sender = email.get('from', '')
        subject = email.get('subject', '')
        date_str = email.get('date', '')
        
        vendor = extract_vendor(sender)
        amount = extract_amount_from_email(email_id)
        
        # Only track if it looks like a charge
        if amount or 'receipt' in subject.lower() or 'invoice' in subject.lower():
            new_charges.append({
                'vendor': vendor,
                'amount': amount,
                'date': date_str,
                'subject': subject,
                'email_id': email_id
            })
    
    return new_charges

def append_to_sheet(sheet_id, new_charges):
    """Append new charges to the Google Sheet"""
    if not new_charges:
        return True
    
    print(f"📝 Adding {len(new_charges)} new charges to sheet...")
    
    # Get current sheet data to find next row
    result = run_command(f'gog sheets get "{sheet_id}" "Sheet1!A:A" --json')
    try:
        data = json.loads(result)
        current_rows = len(data.get('values', []))
        next_row = current_rows + 1
    except:
        next_row = 2  # Fallback: assume headers in row 1
    
    # Append each charge
    for charge in new_charges:
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{charge['email_id']}"
        row = [
            charge['vendor'],
            'New',  # Category
            f"${charge['amount']}" if charge['amount'] else "N/A",
            'New - Needs Review',  # Frequency
            charge['date'][:10] if len(charge['date']) >= 10 else charge['date'],
            '1',  # Email count
            gmail_link
        ]
        
        range_notation = f"Sheet1!A{next_row}:G{next_row}"
        values_json = json.dumps([row])
        cmd = f'gog sheets update "{sheet_id}" "{range_notation}" --values-json \'{values_json}\''
        subprocess.run(cmd, shell=True, capture_output=True)
        next_row += 1
    
    print("✅ New charges added to sheet")
    return True

def format_alert_message(new_charges):
    """Format Telegram alert message"""
    if not new_charges:
        return None
    
    msg = f"🚨 **New Subscription Charges Detected** ({len(new_charges)})\n\n"
    
    for charge in new_charges:
        amount_str = f"${charge['amount']}" if charge['amount'] else "Amount TBD"
        msg += f"• **{charge['vendor']}** - {amount_str}\n"
        msg += f"  _Date: {charge['date'][:10]}_\n"
        msg += f"  Subject: {charge['subject'][:60]}...\n\n"
    
    msg += f"\n📊 View full tracking sheet:\nhttps://docs.google.com/spreadsheets/d/{load_sheet_id()}"
    
    return msg

def main():
    print("🦞 Subscription Daily Monitor\n")
    
    # Load sheet ID
    sheet_id = load_sheet_id()
    if not sheet_id:
        print("❌ No sheet ID found. Run subscription_scanner_full.py first.")
        return
    
    # Check for new charges
    new_charges = check_new_subscriptions()
    
    if new_charges:
        print(f"\n🔔 Found {len(new_charges)} new charges:")
        for charge in new_charges:
            amount_str = f"${charge['amount']}" if charge['amount'] else "N/A"
            print(f"   • {charge['vendor']:30} {amount_str:>10}")
        
        # Append to sheet
        success = append_to_sheet(sheet_id, new_charges)
        
        if success:
            # Generate alert message
            alert_msg = format_alert_message(new_charges)
            print(f"\n📢 Alert message:\n{alert_msg}")
            
            # Return alert for cron job to send via Telegram
            return alert_msg
    else:
        print("\n✅ No new subscription charges detected today")
        return None

if __name__ == "__main__":
    alert = main()
    if alert:
        # Output for cron job to capture
        print("\n" + "="*60)
        print("ALERT_MESSAGE:")
        print(alert)
