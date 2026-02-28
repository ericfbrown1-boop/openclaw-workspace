#!/usr/bin/env python3
"""
Daily Subscription Monitor v2 - Enhanced with email body analysis
Reads full email content to better identify vendors and payment types
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

def analyze_email_content(email_id):
    """Deep analysis of email body to extract vendor, amount, and payment details"""
    result = run_command(f'gog gmail read {email_id} --plain')
    
    analysis = {
        'vendor': None,
        'amount': None,
        'description': None,
        'category': 'Unknown',
        'payment_method': None
    }
    
    # Vendor patterns - prioritize these over sender name
    # Check for credit card bill patterns first
    if re.search(r'(?:american express|amex)', result, re.IGNORECASE):
        analysis['vendor'] = 'American Express'
        analysis['category'] = 'Credit Card Bill'
    elif re.search(r'autopay.*?payment', result, re.IGNORECASE):
        # AutoPay usually means credit card or utility bill
        analysis['category'] = 'AutoPay Bill'
    
    # If vendor not found yet, try other patterns
    if not analysis['vendor']:
        vendor_patterns = [
            r'(?:Payment to|Paid to|Charge from|Payment for)\s+([A-Z][A-Za-z\s&]+?)(?:\s+for|\s+on|\s*\$)',
            r'Your\s+([A-Z][A-Za-z\s]+?)\s+(?:bill|statement|invoice)',
            r'(?:Invoice|Receipt)\s+from\s+([A-Z][A-Za-z\s&]+)',
            r'Thank you for your payment to\s+([A-Z][A-Za-z\s&]+)',
        ]
        
        for pattern in vendor_patterns:
            match = re.search(pattern, result, re.IGNORECASE)
            if match and len(match.groups()) > 0:
                analysis['vendor'] = match.group(1).strip()
                break
    
    # Amount patterns - look for most explicit amounts first
    amount_patterns = [
        r'(?:Total|Amount Due|Payment|Balance|Charge):\s*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'AutoPay.*?\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            analysis['amount'] = match.group(1).replace(',', '')
            break
    
    # Payment method detection
    if 'american express' in result.lower() or 'amex' in result.lower():
        analysis['payment_method'] = 'American Express'
        # Extract last 4 digits if available
        card_match = re.search(r'(?:card ending in|account ending in|\*{4})(\d{4})', result, re.IGNORECASE)
        if card_match:
            analysis['payment_method'] += f' (...{card_match.group(1)})'
    elif 'visa' in result.lower():
        analysis['payment_method'] = 'Visa'
    elif 'mastercard' in result.lower():
        analysis['payment_method'] = 'MasterCard'
    
    # Description extraction
    desc_patterns = [
        r'(?:Subject|Re|RE):\s*(.+?)(?:\n|$)',
        r'(?:Invoice|Statement|Bill) for\s+(.+?)(?:\n|$)',
        r'AutoPay\s+(.+?)(?:\n|$)',
    ]
    
    for pattern in desc_patterns:
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            analysis['description'] = match.group(1).strip()[:100]  # Limit length
            break
    
    # Category detection
    if analysis['category'] == 'Unknown':
        if any(word in result.lower() for word in ['subscription', 'monthly', 'recurring']):
            analysis['category'] = 'Subscription'
        elif any(word in result.lower() for word in ['insurance', 'policy']):
            analysis['category'] = 'Insurance'
        elif any(word in result.lower() for word in ['utility', 'electric', 'gas', 'water']):
            analysis['category'] = 'Utility'
        elif any(word in result.lower() for word in ['lease', 'rent']):
            analysis['category'] = 'Lease/Rent'
        elif any(word in result.lower() for word in ['phone', 'mobile', 'wireless', 'internet']):
            analysis['category'] = 'Telecom'
    
    return analysis

def extract_vendor_from_sender(sender):
    """Fallback vendor extraction from sender if email analysis fails"""
    # Check for known vendors in sender name or domain
    if 'american express' in sender.lower() or 'americanexpress' in sender.lower():
        return 'American Express'
    if 'chase' in sender.lower():
        return 'Chase'
    if 'wellsfargo' in sender.lower() or 'wells fargo' in sender.lower():
        return 'Wells Fargo'
    if 'bank of america' in sender.lower() or 'bankofamerica' in sender.lower():
        return 'Bank of America'
    if 'citi' in sender.lower() and 'bank' in sender.lower():
        return 'Citibank'
    
    # Extract from quoted name
    match = re.search(r'"([^"]+)"', sender)
    if match:
        vendor = match.group(1)
        vendor = re.sub(r',?\s+(Inc\.|LLC|Ltd\.|Corp\.|PBC|Pte\. Ltd\.)$', '', vendor, flags=re.IGNORECASE)
        return vendor.strip()
    
    # Extract from domain
    match = re.search(r'<([^@]+)@([^>]+)>', sender)
    if match:
        domain = match.group(2)
        # Don't use 'welcome' or 'noreply' as vendor names
        domain = domain.replace('.com', '').replace('noreply', '').replace('notify', '').replace('welcome.', '')
        cleaned = domain.split('.')[0].title()
        if cleaned.lower() in ['welcome', 'noreply', 'donotreply', 'no-reply']:
            # Try second part of domain
            parts = domain.split('.')
            if len(parts) > 1:
                return parts[1].title()
        return cleaned
    
    return sender.split('<')[0].strip()

def check_new_subscriptions():
    """Check for new subscription charges in last 24 hours"""
    print("🦞 Subscription Monitor v2 - Enhanced Email Analysis")
    print("🔍 Checking for new charges (last 24 hours)...\n")
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    
    search_queries = [
        f'after:{yesterday} subject:(receipt OR invoice OR payment OR subscription OR statement OR autopay)',
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
        print("✅ No new charges found")
        return []
    
    print(f"📧 Found {len(new_emails)} emails, analyzing content...\n")
    
    new_charges = []
    
    for email_id, email in new_emails.items():
        sender = email.get('from', '')
        subject = email.get('subject', '')
        date_str = email.get('date', '')
        
        # Deep analysis of email content
        print(f"   Analyzing: {subject[:60]}...")
        analysis = analyze_email_content(email_id)
        
        # Fallback to sender if vendor not found in body
        if not analysis['vendor']:
            analysis['vendor'] = extract_vendor_from_sender(sender)
        
        # Skip if no amount found
        if not analysis['amount']:
            continue
        
        # Use subject as description if not found
        if not analysis['description']:
            analysis['description'] = subject[:100]
        
        new_charges.append({
            'vendor': analysis['vendor'],
            'amount': analysis['amount'],
            'category': analysis['category'],
            'description': analysis['description'],
            'payment_method': analysis['payment_method'] or 'N/A',
            'date': date_str,
            'subject': subject,
            'email_id': email_id
        })
    
    return new_charges

def append_to_sheet(sheet_id, new_charges):
    """Append new charges to the Google Sheet with enhanced details"""
    if not new_charges:
        return True
    
    print(f"\n📝 Adding {len(new_charges)} charges to sheet...\n")
    
    # Get current sheet data to find next row
    result = run_command(f'gog sheets get "{sheet_id}" "Sheet1!A:A" --json')
    try:
        data = json.loads(result)
        current_rows = len(data.get('values', []))
        next_row = current_rows + 1
    except:
        next_row = 2
    
    # Append each charge
    for charge in new_charges:
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{charge['email_id']}"
        
        # Enhanced row with more columns
        row = [
            charge['vendor'],
            charge['category'],
            f"${charge['amount']}" if charge['amount'] else "N/A",
            'Needs Review',  # Frequency
            charge['date'][:10] if len(charge['date']) >= 10 else charge['date'],
            '1',  # Email count
            gmail_link,
            charge['description'],  # New: Description column
            charge['payment_method']  # New: Payment method column
        ]
        
        print(f"   • {charge['vendor']:30} ${charge['amount']:>10} ({charge['category']})")
        
        range_notation = f"Sheet1!A{next_row}:I{next_row}"  # Extended to column I
        values_json = json.dumps([row])
        cmd = f'gog sheets update "{sheet_id}" "{range_notation}" --values-json \'{values_json}\''
        subprocess.run(cmd, shell=True, capture_output=True)
        next_row += 1
    
    print("\n✅ All charges added to sheet")
    return True

def format_alert_message(new_charges):
    """Format Telegram alert message with enhanced details"""
    if not new_charges:
        return None
    
    msg = f"🚨 **New Charges Detected** ({len(new_charges)})\n\n"
    
    for charge in new_charges:
        amount_str = f"${charge['amount']}" if charge['amount'] else "Amount TBD"
        msg += f"• **{charge['vendor']}** - {amount_str}\n"
        msg += f"  Category: {charge['category']}\n"
        if charge['payment_method'] != 'N/A':
            msg += f"  Payment: {charge['payment_method']}\n"
        msg += f"  Date: {charge['date'][:10]}\n"
        msg += f"  _{charge['description'][:80]}..._\n\n"
    
    msg += f"\n📊 View tracking sheet:\nhttps://docs.google.com/spreadsheets/d/{load_sheet_id()}"
    
    return msg

def main():
    print("="*60 + "\n")
    
    sheet_id = load_sheet_id()
    if not sheet_id:
        print("❌ No sheet ID found. Run subscription_scanner_full.py first.")
        return
    
    new_charges = check_new_subscriptions()
    
    if new_charges:
        print(f"\n🔔 Found {len(new_charges)} new charges\n")
        
        # Show summary
        for charge in new_charges:
            amount_str = f"${charge['amount']}" if charge['amount'] else "N/A"
            print(f"   {charge['vendor']:30} {amount_str:>12}  [{charge['category']}]")
        
        # Append to sheet
        success = append_to_sheet(sheet_id, new_charges)
        
        if success:
            alert_msg = format_alert_message(new_charges)
            if alert_msg:
                print("\n" + "="*60)
                print("ALERT_MESSAGE:")
                print(alert_msg)
                return alert_msg
    else:
        print("\n✅ No new charges detected today")
        return None

if __name__ == "__main__":
    main()
