#!/usr/bin/env python3
"""
Write subscription data to existing Google Sheet
"""

import json
import subprocess
import sys

def write_to_sheet(sheet_id, rows):
    """Write data to Google Sheet using values-json"""
    print(f"📝 Writing {len(rows)} rows to sheet {sheet_id}...")
    
    # Prepare JSON 2D array
    values_json = json.dumps(rows)
    
    # Determine range based on number of rows
    end_row = len(rows)
    range_notation = f"Sheet1!A1:G{end_row}"
    
    # Write to temp file to avoid shell escaping issues
    with open('/tmp/sheet_values.json', 'w') as f:
        f.write(values_json)
    
    # Use gog sheets update with --values-json
    cmd = f'gog sheets update "{sheet_id}" "{range_notation}" --values-json \'{values_json}\''
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Data written successfully")
        print(result.stdout)
        return True
    else:
        print("❌ Failed to write data")
        print(result.stderr)
        return False

if __name__ == "__main__":
    # Test data
    sheet_id = "1Ua45Dw38A32RMo2L6IBc6NoC-hyQXGs4rZb_7uymLzg"
    
    rows = [
        ["Vendor", "Category", "Amount", "Frequency", "Last Charge Date", "Email Count", "Gmail Link"],
        ["Parseur Pte Ltd", "Software/SaaS", "$49.00", "Monthly", "2026-02-24", "1", "https://mail.google.com/mail/u/0/#inbox/19c905cfac41bb23"],
        ["Zoom", "Software/SaaS", "TBD", "Monthly", "2026-02-23", "5", "https://mail.google.com/mail/u/0/#inbox/19c8a89915668ab4"],
        ["Tesla", "Vehicle", "TBD", "Monthly", "2026-02-21", "3", "https://mail.google.com/mail/u/0/#inbox/19c8139e155be973"],
    ]
    
    write_to_sheet(sheet_id, rows)
