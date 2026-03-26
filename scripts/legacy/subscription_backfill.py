#!/usr/bin/env python3
"""
Subscription Tracker Backfill - Re-analyze all existing emails
Updates spreadsheet with enhanced vendor, category, and payment info
"""

import json
import re
import subprocess
import time

SHEET_ID = "1Ua45Dw38A32RMo2L6IBc6NoC-hyQXGs4rZb_7uymLzg"

def run_command(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def analyze_email_content(email_id):
    """Deep analysis of email body (same as daily monitor v2)"""
    result = run_command(f'gog gmail read {email_id} --plain')
    
    analysis = {
        'vendor': None,
        'amount': None,
        'description': None,
        'category': 'Unknown',
        'payment_method': None
    }
    
    # Check for credit card bill patterns first
    if re.search(r'(?:american express|amex)', result, re.IGNORECASE):
        analysis['vendor'] = 'American Express'
        analysis['category'] = 'Credit Card Bill'
        # Extract account ending
        card_match = re.search(r'(?:account ending|card ending in|ending):\s*(\d{4,5})', result, re.IGNORECASE)
        if card_match:
            analysis['payment_method'] = f'American Express (...{card_match.group(1)})'
        else:
            analysis['payment_method'] = 'American Express'
    
    elif re.search(r'(?:chase|jpmorgan)', result, re.IGNORECASE):
        analysis['vendor'] = 'Chase'
        analysis['category'] = 'Credit Card Bill'
        analysis['payment_method'] = 'Chase'
    
    elif re.search(r'(?:wells fargo|wellsfargo)', result, re.IGNORECASE):
        analysis['vendor'] = 'Wells Fargo'
        analysis['category'] = 'Credit Card Bill'
        analysis['payment_method'] = 'Wells Fargo'
    
    # Check for known subscription services
    elif 'anthropic' in result.lower():
        analysis['vendor'] = 'Anthropic'
        analysis['category'] = 'AI/LLM Services'
    
    elif 'parseur' in result.lower():
        analysis['vendor'] = 'Parseur'
        analysis['category'] = 'Software/SaaS'
    
    elif 'zoom' in result.lower():
        analysis['vendor'] = 'Zoom'
        analysis['category'] = 'Software/SaaS'
    
    elif 'tesla' in result.lower():
        analysis['vendor'] = 'Tesla'
        analysis['category'] = 'Vehicle Lease'
    
    elif 'apple' in result.lower() and any(word in result.lower() for word in ['receipt', 'purchase', 'app store']):
        analysis['vendor'] = 'Apple'
        analysis['category'] = 'Apple Services'
    
    elif 't-mobile' in result.lower() or 'tmobile' in result.lower():
        analysis['vendor'] = 'T-Mobile'
        analysis['category'] = 'Telecom'
    
    elif 'spectrum' in result.lower():
        analysis['vendor'] = 'Spectrum'
        analysis['category'] = 'Telecom'
    
    elif 'xai' in result.lower() or 'grok' in result.lower():
        analysis['vendor'] = 'xAI (Grok)'
        analysis['category'] = 'AI/LLM Services'
    
    # Amount extraction
    amount_patterns = [
        r'(?:Total|Amount Due|Payment|Balance|Charge|Price):\s*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'(?:Paid|Receipt for)\s+\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            analysis['amount'] = match.group(1).replace(',', '')
            break
    
    # Description from subject line
    subject_match = re.search(r'(?:Subject|Re):\s*(.+?)(?:\n|$)', result, re.IGNORECASE)
    if subject_match:
        analysis['description'] = subject_match.group(1).strip()[:100]
    
    # Category fallback detection
    if analysis['category'] == 'Unknown':
        if 'subscription' in result.lower() or 'monthly' in result.lower():
            analysis['category'] = 'Subscription'
        elif 'insurance' in result.lower() or 'policy' in result.lower():
            analysis['category'] = 'Insurance'
        elif any(word in result.lower() for word in ['utility', 'electric', 'gas', 'water', 'pge']):
            analysis['category'] = 'Utility'
        elif 'lease' in result.lower() or 'rent' in result.lower():
            analysis['category'] = 'Lease/Rent'
        elif 'autopay' in result.lower():
            analysis['category'] = 'AutoPay Bill'
    
    return analysis

def get_current_sheet_data():
    """Get all data from current sheet"""
    print("📊 Reading current spreadsheet data...")
    
    # Read just the data rows (skip header)
    result = run_command(f'gog sheets get "{SHEET_ID}" "Sheet1!A2:I100" --json')
    try:
        data = json.loads(result)
        rows = data.get('values', [])
        print(f"   Found {len(rows)} data rows")
        return rows
    except Exception as e:
        print(f"❌ Error reading sheet: {e}")
        return []

def extract_email_id_from_link(gmail_link):
    """Extract email ID from Gmail link"""
    match = re.search(r'#inbox/(\w+)', gmail_link)
    if match:
        return match.group(1)
    return None

def backfill_sheet():
    """Re-analyze all emails and update sheet"""
    print("🦞 Subscription Tracker Backfill")
    print("="*60)
    print()
    
    # Get current data (starts at row 2, no headers)
    rows = get_current_sheet_data()
    if len(rows) == 0:
        print("❌ No data to backfill")
        return
    
    print(f"\n🔍 Analyzing {len(rows)} existing emails...")
    print("   This will take a few minutes...\n")
    
    updated_rows = []
    processed = 0
    enhanced = 0
    
    for i, row in enumerate(rows):
        processed += 1
        
        # Pad row to ensure it has all columns
        while len(row) < 9:
            row.append('')
        
        # Extract email ID from Gmail link (column G, index 6)
        gmail_link = row[6] if len(row) > 6 else ''
        email_id = extract_email_id_from_link(gmail_link)
        
        if not email_id:
            print(f"   [{processed:3d}] Skipped: No Gmail link found")
            updated_rows.append(row)
            continue
        
        # Get original vendor name for comparison
        original_vendor = row[0] if len(row) > 0 else 'Unknown'
        
        # Analyze email
        print(f"   [{processed:3d}] Analyzing: {original_vendor[:40]}...")
        
        try:
            analysis = analyze_email_content(email_id)
            
            # Update row with enhanced data
            if analysis['vendor']:
                row[0] = analysis['vendor']  # Vendor
            if analysis['category'] and analysis['category'] != 'Unknown':
                row[1] = analysis['category']  # Category
            if analysis['amount']:
                row[2] = f"${analysis['amount']}"  # Amount
            # Keep original frequency (row[3])
            # Keep original date (row[4])
            # Keep original email count (row[5])
            # Keep Gmail link (row[6])
            if analysis['description']:
                row[7] = analysis['description']  # Description
            if analysis['payment_method']:
                row[8] = analysis['payment_method']  # Payment Method
            
            enhanced += 1
            
        except Exception as e:
            print(f"         ⚠️  Error analyzing email: {e}")
        
        updated_rows.append(row)
        
        # Rate limit to avoid API throttling
        if processed % 10 == 0:
            time.sleep(1)
    
    print(f"\n✅ Analysis complete: {enhanced}/{processed} rows enhanced\n")
    
    # Write updated data back to sheet (row by row to avoid shell escaping issues)
    print("📝 Writing updated data to spreadsheet...")
    print(f"   Updating {len(updated_rows)} rows...")
    
    success_count = 0
    fail_count = 0
    
    for i, row in enumerate(updated_rows):
        row_num = i + 2  # +2 because we start at row 2 (after header)
        range_notation = f"Sheet1!A{row_num}:I{row_num}"
        values_json = json.dumps([row])
        
        cmd = f'gog sheets update "{SHEET_ID}" "{range_notation}" --values-json \'{values_json}\''
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            success_count += 1
            if (i + 1) % 10 == 0:
                print(f"   Updated {i+1}/{len(updated_rows)} rows...")
        else:
            fail_count += 1
            if fail_count <= 3:  # Only show first few errors
                print(f"   ⚠️  Row {row_num} failed: {result.stderr[:100]}")
    
    print(f"\n✅ Spreadsheet update complete!")
    print(f"   Success: {success_count}/{len(updated_rows)} rows")
    if fail_count > 0:
        print(f"   Failed: {fail_count} rows")
    print(f"\n🔗 View updated sheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    
    print()
    print("="*60)
    print(f"Summary: {enhanced} emails enhanced with better details")
    print("="*60)

if __name__ == "__main__":
    backfill_sheet()
