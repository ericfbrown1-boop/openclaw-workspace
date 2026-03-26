#!/usr/bin/env python3
"""
Subscription Tracker - Analyze emails for recurring charges
Creates and maintains a Google Sheet tracking monthly subscriptions
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from collections import defaultdict

def run_command(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def extract_amount(subject, body_preview=""):
    """Extract dollar amount from email subject or body"""
    text = f"{subject} {body_preview}"
    # Match $XX.XX or $X,XXX.XX patterns
    match = re.search(r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
    if match:
        return match.group(1).replace(',', '')
    return ""

def categorize_subscription(sender, subject):
    """Categorize the type of subscription"""
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    
    # Mapping common patterns to categories
    categories = {
        'Software/SaaS': ['stripe', 'github', 'slack', 'zoom', 'adobe', 'microsoft', 'dropbox', 'parseur'],
        'Streaming': ['netflix', 'spotify', 'apple music', 'youtube', 'hulu', 'disney'],
        'Cloud Services': ['aws', 'google cloud', 'azure', 'digitalocean'],
        'Phone/Internet': ['t-mobile', 'verizon', 'at&t', 'comcast', 'xfinity'],
        'Utilities': ['pge', 'pg&e', 'water', 'electric', 'gas'],
        'Insurance': ['insurance', 'policy'],
        'Finance': ['bank', 'credit card', 'loan', 'mortgage'],
        'Apple Services': ['apple.com', 'icloud', 'app store'],
    }
    
    for category, keywords in categories.items():
        if any(kw in sender_lower or kw in subject_lower for kw in keywords):
            return category
    
    return 'Other'

def extract_vendor(sender, subject):
    """Extract clean vendor name"""
    # Try to extract from sender
    match = re.search(r'"([^"]+)"', sender)
    if match:
        return match.group(1)
    
    # Extract email domain
    match = re.search(r'<([^@]+)@([^>]+)>', sender)
    if match:
        domain = match.group(2)
        # Clean up common patterns
        domain = domain.replace('stripe.com', '').replace('noreply', '').strip('.')
        if 'stripe' in sender.lower() and 'acct_' in sender:
            # Extract vendor from Stripe emails
            if '"' in sender:
                return re.search(r'"([^"]+)"', sender).group(1)
        return domain.split('.')[0].title()
    
    return sender.split('<')[0].strip()

def analyze_subscriptions():
    """Analyze Gmail for recurring subscriptions"""
    print("🔍 Scanning Gmail for recurring subscriptions...")
    
    # Load search results
    _subscriptions = []
    
    # Search for common subscription patterns
    search_queries = [
        'after:2024/08/27 from:(stripe.com)',
        'after:2024/08/27 from:(apple.com) subject:receipt',
        'after:2024/08/27 from:(zoom.us)',
        'after:2024/08/27 from:(tesla.com) subject:billing',
        'after:2024/08/27 subject:"your receipt" OR subject:"your invoice"',
        'after:2024/08/27 subject:"payment received" OR subject:"subscription"',
    ]
    
    all_emails = {}
    
    for query in search_queries:
        print(f"   Searching: {query[:50]}...")
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
    
    print(f"✅ Found {len(all_emails)} unique emails")
    
    # Group by vendor to identify recurring patterns
    vendor_emails = defaultdict(list)
    
    for email_id, email in all_emails.items():
        sender = email.get('from', '')
        subject = email.get('subject', '')
        date_str = email.get('date', '')
        
        vendor = extract_vendor(sender, subject)
        amount = extract_amount(subject)
        category = categorize_subscription(sender, subject)
        
        # Parse date
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        except Exception:
            date = datetime.now()
        
        vendor_emails[vendor].append({
            'id': email_id,
            'date': date,
            'subject': subject,
            'amount': amount,
            'category': category,
            'sender': sender
        })
    
    # Identify recurring subscriptions (vendors with 2+ emails)
    print(f"\n📊 Analyzing patterns...")
    recurring_subscriptions = []
    
    for vendor, emails in vendor_emails.items():
        if len(emails) >= 2:
            # Sort by date
            emails_sorted = sorted(emails, key=lambda x: x['date'], reverse=True)
            
            # Check for monthly pattern (emails ~30 days apart)
            dates = [e['date'] for e in emails_sorted]
            is_monthly = False
            if len(dates) >= 2:
                days_diff = (dates[0] - dates[1]).days
                if 25 <= days_diff <= 35:  # ~monthly
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
                'count': len(emails)
            })
    
    # Sort by last date
    recurring_subscriptions.sort(key=lambda x: x['last_date'], reverse=True)
    
    print(f"✅ Identified {len(recurring_subscriptions)} recurring subscriptions\n")
    
    return recurring_subscriptions

def create_google_sheet(subscriptions):
    """Create Google Sheet with subscription data"""
    print("📄 Creating Google Sheet...")
    
    # Create new sheet
    result = run_command('gog sheets create "Recurring Subscriptions Tracker" --json')
    try:
        sheet_data = json.loads(result)
        sheet_id = sheet_data.get('spreadsheetId')
        sheet_url = sheet_data.get('spreadsheetUrl')
    except Exception as e:
        print(f"❌ Failed to create sheet: {e}")
        return None
    
    print(f"✅ Created sheet: {sheet_id}")
    
    # Prepare data rows
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
    
    # Write to sheet
    print("📝 Writing data to sheet...")
    
    # Write all rows at once using update command
    # Need to escape values for shell
    import csv
    import io
    
    # Convert rows to CSV format for easier handling
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerows(rows)
    csv_content = csv_buffer.getvalue()
    
    # Write to temp file
    with open('/tmp/subscriptions_data.txt', 'w') as f:
        f.write(csv_content)
    
    # Use gog sheets append to add rows one by one (more reliable)
    for row_idx, row in enumerate(rows):
        range_notation = f"Sheet1!A{row_idx+1}:G{row_idx+1}"
        # Build command with proper escaping
        values_str = ' '.join([f'"{val}"' for val in row])
        cmd = f'gog sheets update "{sheet_id}" "{range_notation}" {values_str}'
        result = run_command(cmd)
        if row_idx == 0:
            print(f"   Writing headers...")
        elif row_idx % 5 == 0:
            print(f"   Writing row {row_idx}/{len(rows)}...")
    
    print(f"✅ Data written to sheet ({len(rows)} rows)")
    print(f"\n🔗 Sheet URL: {sheet_url}")
    
    return sheet_id

if __name__ == "__main__":
    print("🦞 Subscription Tracker - Starting Analysis\n")
    
    subscriptions = analyze_subscriptions()
    
    if subscriptions:
        print("\n📊 Summary:")
        for sub in subscriptions[:10]:  # Show top 10
            print(f"   • {sub['vendor']:25} ${sub['amount']:>8} - {sub['frequency']:10} (Last: {sub['last_date']})")
        
        if len(subscriptions) > 10:
            print(f"   ... and {len(subscriptions) - 10} more")
        
        # Calculate total monthly cost
        monthly_total = sum(float(s['amount']) for s in subscriptions if s['amount'] and s['frequency'] == 'Monthly')
        print(f"\n💰 Estimated Monthly Total: ${monthly_total:,.2f}")
        
        print("\n" + "="*60)
        
        # Auto-create if running non-interactively or if --auto flag
        auto_create = '--auto' in sys.argv or not sys.stdin.isatty()
        
        if not auto_create:
            response = input("Create Google Sheet with this data? (y/n): ")
            auto_create = response.lower() == 'y'
        
        if auto_create:
            print("Creating Google Sheet...")
            sheet_id = create_google_sheet(subscriptions)
            if sheet_id:
                # Save sheet ID for daily monitoring
                with open('/Users/ericbrown/.openclaw/workspace/.subscription_tracker_sheet_id', 'w') as f:
                    f.write(sheet_id)
                print(f"\n✅ Sheet ID saved for daily monitoring")
    else:
        print("❌ No recurring subscriptions found")
