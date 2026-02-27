#!/usr/bin/env python3
"""
Full Subscription Scanner - Deep scan with email body analysis
Extracts amounts, categorizes vendors, and populates Google Sheet
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from collections import defaultdict

SHEET_ID = "1Ua45Dw38A32RMo2L6IBc6NoC-hyQXGs4rZb_7uymLzg"

def run_command(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def extract_amount_from_email(email_id):
    """Read full email and extract amount"""
    # Get email content
    result = run_command(f'gog gmail read {email_id} --plain')
    
    # Look for common amount patterns
    patterns = [
        r'\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',  # $XX.XX or $X,XXX.XX
        r'(?:Total|Amount|Payment|Charge|Price):\s*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'(?:USD|usd)\s+(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'(\d{1,3}(?:,\d{3})*\.\d{2})\s+(?:USD|usd)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            return match.group(1).replace(',', '')
    
    return ""

def categorize_subscription(vendor, subject):
    """Categorize the type of subscription"""
    vendor_lower = vendor.lower()
    subject_lower = subject.lower()
    
    categories = {
        'AI/LLM Services': ['anthropic', 'openai', 'claude', 'xai', 'grok'],
        'Software/SaaS': ['stripe', 'github', 'slack', 'zoom', 'adobe', 'microsoft', 'dropbox', 'parseur', 'xero'],
        'Streaming': ['netflix', 'spotify', 'apple music', 'youtube', 'hulu', 'disney'],
        'Cloud Services': ['aws', 'google cloud', 'azure', 'digitalocean'],
        'Phone/Telecom': ['t-mobile', 'verizon', 'at&t', 'spectrum'],
        'Utilities': ['pge', 'pg&e', 'water', 'electric', 'gas'],
        'Insurance': ['insurance', 'policy'],
        'Vehicle': ['tesla', 'lease', 'auto'],
        'Apple Services': ['apple.com', 'icloud', 'app store'],
        'Marine/Boat': ['helmut', 'marine'],
    }
    
    for category, keywords in categories.items():
        if any(kw in vendor_lower or kw in subject_lower for kw in keywords):
            return category
    
    return 'Other'

def extract_vendor(sender, subject):
    """Extract clean vendor name"""
    # Try to extract from quoted name
    match = re.search(r'"([^"]+)"', sender)
    if match:
        vendor = match.group(1)
        # Clean up "Inc.", "LLC", etc.
        vendor = re.sub(r',?\s+(Inc\.|LLC|Ltd\.|Corp\.|PBC|Pte\. Ltd\.)$', '', vendor, flags=re.IGNORECASE)
        return vendor.strip()
    
    # Extract from email domain
    match = re.search(r'<([^@]+)@([^>]+)>', sender)
    if match:
        domain = match.group(2)
        # Clean common patterns
        domain = domain.replace('.com', '').replace('noreply', '').replace('no-reply', '')
        domain = domain.replace('email.', '').replace('notify.', '')
        return domain.split('.')[0].title()
    
    return sender.split('<')[0].strip()

def scan_subscriptions():
    """Deep scan Gmail for recurring subscriptions"""
    print("🔍 Deep scanning Gmail for subscriptions (18 months)...")
    print("   This will take a few minutes...\n")
    
    # Comprehensive search queries
    search_queries = [
        # Specific vendors
        ('after:2024/08/27 from:stripe.com', 'Stripe payments'),
        ('after:2024/08/27 from:apple.com subject:receipt', 'Apple receipts'),
        ('after:2024/08/27 from:zoom.us', 'Zoom'),
        ('after:2024/08/27 from:tesla.com', 'Tesla'),
        ('after:2024/08/27 from:anthropic.com', 'Anthropic'),
        ('after:2024/08/27 from:x.ai', 'xAI'),
        ('after:2024/08/27 from:t-mobile.com subject:payment', 'T-Mobile'),
        ('after:2024/08/27 from:spectrum', 'Spectrum'),
        
        # Generic patterns
        ('after:2024/08/27 subject:"your receipt"', 'Receipts'),
        ('after:2024/08/27 subject:"your invoice"', 'Invoices'),
        ('after:2024/08/27 subject:"payment received"', 'Payments'),
        ('after:2024/08/27 subject:"subscription"', 'Subscriptions'),
        ('after:2024/08/27 subject:"monthly"', 'Monthly charges'),
        ('after:2024/08/27 subject:"billing statement"', 'Billing'),
    ]
    
    all_emails = {}
    
    for query, desc in search_queries:
        print(f"   📧 Searching: {desc}...")
        result = run_command(f'gog gmail search "{query}" --max 100 --json')
        try:
            data = json.loads(result)
            if 'threads' in data:
                for thread in data['threads']:
                    email_id = thread['id']
                    if email_id not in all_emails:
                        all_emails[email_id] = thread
        except json.JSONDecodeError:
            continue
    
    print(f"\n✅ Found {len(all_emails)} unique emails")
    print("📊 Analyzing patterns and extracting amounts...\n")
    
    # Group by vendor
    vendor_emails = defaultdict(list)
    processed = 0
    
    for email_id, email in all_emails.items():
        processed += 1
        if processed % 20 == 0:
            print(f"   Processing email {processed}/{len(all_emails)}...")
        
        sender = email.get('from', '')
        subject = email.get('subject', '')
        date_str = email.get('date', '')
        
        vendor = extract_vendor(sender, subject)
        
        # Extract amount from email body (sample first 50 for performance)
        amount = ""
        if processed <= 50:  # Deep scan first 50, others from subject
            amount = extract_amount_from_email(email_id)
        
        if not amount:
            # Try subject line
            match = re.search(r'\$(\d+\.?\d*)', subject)
            if match:
                amount = match.group(1)
        
        category = categorize_subscription(vendor, subject)
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        except:
            date = datetime.now()
        
        vendor_emails[vendor].append({
            'id': email_id,
            'date': date,
            'subject': subject,
            'amount': amount,
            'category': category,
            'sender': sender
        })
    
    print(f"\n✅ Processing complete")
    print("🔎 Identifying recurring patterns...\n")
    
    # Identify recurring subscriptions
    recurring_subscriptions = []
    
    for vendor, emails in vendor_emails.items():
        if len(emails) >= 2:  # At least 2 occurrences
            emails_sorted = sorted(emails, key=lambda x: x['date'], reverse=True)
            
            # Check frequency
            dates = [e['date'] for e in emails_sorted]
            is_monthly = False
            if len(dates) >= 2:
                days_diff = (dates[0] - dates[1]).days
                if 20 <= days_diff <= 40:  # ~monthly
                    is_monthly = True
            
            # Get most common amount
            amounts = [e['amount'] for e in emails_sorted if e['amount']]
            amount = amounts[0] if amounts else ""
            
            recurring_subscriptions.append({
                'vendor': vendor,
                'category': emails_sorted[0]['category'],
                'amount': amount,
                'frequency': 'Monthly' if is_monthly else 'Recurring',
                'last_date': emails_sorted[0]['date'].strftime('%Y-%m-%d'),
                'email_id': emails_sorted[0]['id'],
                'count': len(emails),
                'subject': emails_sorted[0]['subject']
            })
    
    # Sort by last date
    recurring_subscriptions.sort(key=lambda x: x['last_date'], reverse=True)
    
    print(f"✅ Identified {len(recurring_subscriptions)} recurring subscriptions\n")
    
    return recurring_subscriptions

def write_to_sheet(subscriptions):
    """Write all subscription data to Google Sheet"""
    print(f"📝 Writing {len(subscriptions)} subscriptions to Google Sheet...")
    
    # Prepare rows
    headers = ['Vendor', 'Category', 'Amount', 'Frequency', 'Last Charge Date', 'Email Count', 'Gmail Link']
    rows = [headers]
    
    for sub in subscriptions:
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{sub['email_id']}"
        rows.append([
            sub['vendor'],
            sub['category'],
            f"${sub['amount']}" if sub['amount'] else "N/A",
            sub['frequency'],
            sub['last_date'],
            str(sub['count']),
            gmail_link
        ])
    
    # Write using values-json
    values_json = json.dumps(rows)
    end_row = len(rows)
    range_notation = f"Sheet1!A1:G{end_row}"
    
    cmd = f'gog sheets update "{SHEET_ID}" "{range_notation}" --values-json \'{values_json}\''
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Data written successfully")
        return True
    else:
        print(f"❌ Failed to write: {result.stderr}")
        return False

def main():
    print("🦞 Subscription Scanner - Full Deep Scan\n")
    print("="*60)
    
    # Scan
    subscriptions = scan_subscriptions()
    
    if not subscriptions:
        print("❌ No subscriptions found")
        return
    
    # Show summary
    print("📊 SUMMARY:")
    print("="*60)
    for sub in subscriptions[:15]:
        amount_str = f"${sub['amount']:>8}" if sub['amount'] else "     N/A"
        print(f"   {sub['vendor']:30} {amount_str}  {sub['frequency']:10} ({sub['count']} emails)")
    
    if len(subscriptions) > 15:
        print(f"   ... and {len(subscriptions) - 15} more")
    
    # Calculate totals
    monthly_subs = [s for s in subscriptions if s['frequency'] == 'Monthly' and s['amount']]
    if monthly_subs:
        monthly_total = sum(float(s['amount']) for s in monthly_subs)
        print(f"\n💰 Estimated Monthly Total: ${monthly_total:,.2f}")
        print(f"   (Based on {len(monthly_subs)} confirmed monthly subscriptions)")
    
    print("\n" + "="*60)
    
    # Write to sheet
    success = write_to_sheet(subscriptions)
    
    if success:
        print(f"\n🔗 View your sheet:")
        print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        
        # Save sheet ID for daily monitoring
        with open('/Users/ericbrown/.openclaw/workspace/.subscription_sheet_id', 'w') as f:
            f.write(SHEET_ID)
        print(f"\n✅ Sheet ID saved for daily monitoring")

if __name__ == "__main__":
    main()
