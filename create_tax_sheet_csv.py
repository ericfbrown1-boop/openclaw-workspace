#!/usr/bin/env python3
"""
Convert tax email results to CSV for Google Sheets import
"""

import json
import csv
from datetime import datetime

def create_csv_from_json(json_file, csv_file):
    """Convert JSON results to CSV"""
    
    # Load JSON data
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in: {json_file}")
        return False
    
    if not data:
        print("❌ No data found in JSON file")
        return False
    
    print(f"Processing {len(data)} items...")
    
    # CSV headers
    headers = [
        "Date Received",
        "Sender",
        "Description of Email Communication",
        "Type of Tax Income or Expense Item",
        "Link to Original Gmail",
        "Comments/Questions"
    ]
    
    # Write CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for item in data:
            # Clean up description - remove extra whitespace
            description = item.get('description', item.get('subject', ''))[:200]
            description = ' '.join(description.split())
            
            row = [
                item.get('date_received', ''),
                item.get('sender', ''),
                description,
                item.get('tax_type', 'Other'),
                item.get('gmail_link', ''),
                item.get('comments', '')
            ]
            writer.writerow(row)
    
    print(f"✓ Created CSV: {csv_file}")
    return True

def main():
    print("=" * 80)
    print("CREATING CSV FOR GOOGLE SHEETS")
    print("=" * 80)
    print()
    
    json_file = "tax_emails_2025.json"
    csv_file = "Income_Tax_Tracking_Items.csv"
    
    if create_csv_from_json(json_file, csv_file):
        print(f"\n✓ SUCCESS!")
        print(f"\nYou can now:")
        print(f"  1. Create a new Google Sheet named 'Income Tax Tracking Items'")
        print(f"  2. File > Import > Upload > {csv_file}")
        print(f"  3. Share with: ericfbrown1@gmail.com")
        print()
    else:
        print("\n❌ Failed to create CSV")

if __name__ == "__main__":
    main()
