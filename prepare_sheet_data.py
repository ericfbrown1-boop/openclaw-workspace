#!/usr/bin/env python3
import csv
import json

# Read the CSV file
with open('/Users/ericbrown/.openclaw/workspace/Income_Tax_Tracking_Items.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = []
    
    # First, add the header row with our desired column names
    headers = ["Date Received", "Sender", "Description", "Tax Type", "Gmail Link", "Comments"]
    rows.append(headers)
    
    # Then add all data rows
    for row in reader:
        formatted_row = [
            row['Date Received'],
            row['Sender'],
            row['Description of Email Communication'],
            row['Type of Tax Income or Expense Item'],
            row['Link to Original Gmail'],
            row['Comments/Questions']
        ]
        rows.append(formatted_row)

# Write to JSON file for the API call
output = {
    "spreadsheet_id": "1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4",
    "rows": rows
}

with open('/Users/ericbrown/.openclaw/workspace/sheet_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Prepared {len(rows)} rows (including header) for import")
