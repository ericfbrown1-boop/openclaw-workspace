#!/usr/bin/env python3
"""
Simple Google Sheets creator using gspread
Easier OAuth flow than full Google API
"""

import json
import os
import sys

# Check if gspread is installed
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Installing required library...")
    os.system("pip3 install --quiet gspread google-auth")
    print("\n✓ Installed gspread")
    print("Please run this script again.")
    sys.exit(0)

def create_sheet_with_oauth():
    """Create sheet using OAuth (browser-based auth)"""
    print("=" * 80)
    print("GOOGLE SHEETS CREATION - OAUTH METHOD")
    print("=" * 80)
    print("\nThis will open a browser for you to authorize access.")
    print("Sign in with: ericfbrown1@gmail.com")
    input("\nPress Enter to continue...")
    
    try:
        # Use OAuth2 flow
        gc = gspread.oauth(
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.file'
            ]
        )
        
        print("\n✓ Authenticated successfully!")
        return gc
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return None

def create_and_populate_sheet(gc, json_file="tax_emails_2025.json"):
    """Create spreadsheet and populate it"""
    
    # Load data
    print(f"\nLoading data from {json_file}...")
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data)} items")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None
    
    # Create spreadsheet
    print("\nCreating Google Sheet...")
    try:
        sheet = gc.create("Income Tax Tracking Items")
        worksheet = sheet.get_worksheet(0)
        worksheet.update_title("2025 Tax Items")
        
        print(f"✓ Created spreadsheet")
        print(f"  URL: {sheet.url}")
        
    except Exception as e:
        print(f"❌ Error creating sheet: {e}")
        return None
    
    # Prepare data
    headers = [
        "Date Received",
        "Sender",  
        "Description of Email Communication",
        "Type of Tax Income or Expense Item",
        "Link to Original Gmail",
        "Comments/Questions"
    ]
    
    rows = [headers]
    
    for item in data:
        desc = item.get('description', item.get('subject', ''))[:200]
        desc = ' '.join(desc.split())
        
        row = [
            item.get('date_received', ''),
            item.get('sender', ''),
            desc,
            item.get('tax_type', 'Other'),
            item.get('gmail_link', ''),
            item.get('comments', '')
        ]
        rows.append(row)
    
    # Write data
    print(f"\nWriting {len(rows)} rows to spreadsheet...")
    try:
        worksheet.update('A1', rows)
        print(f"✓ Data written successfully")
    except Exception as e:
        print(f"❌ Error writing data: {e}")
        return None
    
    # Format header row
    print("\nFormatting header row...")
    try:
        worksheet.format('A1:F1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8},
            'textFormat': {
                'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                'fontSize': 11,
                'bold': True
            },
            'horizontalAlignment': 'CENTER'
        })
        
        # Freeze header row
        worksheet.freeze(rows=1)
        
        print("✓ Formatted headers")
    except Exception as e:
        print(f"⚠ Warning: Could not format: {e}")
    
    # Share with user
    print(f"\nSharing with ericfbrown1@gmail.com...")
    try:
        sheet.share('ericfbrown1@gmail.com', perm_type='user', role='writer')
        print("✓ Shared successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not auto-share: {e}")
        print(f"  Please manually share: {sheet.url}")
    
    return sheet

def main():
    print("\n" + "=" * 80)
    print("SIMPLE GOOGLE SHEETS TAX TRACKING SETUP")
    print("=" * 80)
    print()
    
    # Authenticate
    gc = create_sheet_with_oauth()
    if not gc:
        print("\n❌ Setup failed")
        print("\nFallback option:")
        print("  1. Use the CSV file: Income_Tax_Tracking_Items.csv")
        print("  2. Manually import to Google Sheets")
        print("  3. See TAX_SHEET_SETUP_REPORT.md for instructions")
        return
    
    # Create and populate
    sheet = create_and_populate_sheet(gc)
    
    if sheet:
        print("\n" + "=" * 80)
        print("✅ SUCCESS! TAX TRACKING SHEET IS READY")
        print("=" * 80)
        print(f"\n📊 Spreadsheet URL:")
        print(f"   {sheet.url}")
        print(f"\n✉️  Shared with: ericfbrown1@gmail.com")
        print(f"\n📈 Total items: {len(open('tax_emails_2025.json').read().split('date_received')) - 1}")
        print("\n💡 Next steps:")
        print("  1. Review items and delete any false positives")
        print("  2. Add manually found items")
        print("  3. See TAX_SHEET_SETUP_REPORT.md for missing items checklist")
        print("\n" + "=" * 80)
    else:
        print("\n❌ Failed to create sheet")
        print("\nUse manual import method instead (see report)")

if __name__ == "__main__":
    main()
