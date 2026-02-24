#!/usr/bin/env python3
import csv
import json

# Read the CSV file
with open('/Users/ericbrown/.openclaw/workspace/Income_Tax_Tracking_Items.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    # Prepare rows for Google Sheets
    rows_data = []
    
    # Add header row
    rows_data.append({
        "Date Received": "Date Received",
        "Sender": "Sender", 
        "Description": "Description",
        "Tax Type": "Tax Type",
        "Gmail Link": "Gmail Link",
        "Comments": "Comments"
    })
    
    # Add all data rows
    for row in reader:
        rows_data.append({
            "Date Received": row['Date Received'],
            "Sender": row['Sender'],
            "Description": row['Description of Email Communication'],
            "Tax Type": row['Type of Tax Income or Expense Item'],
            "Gmail Link": row['Link to Original Gmail'],
            "Comments": row['Comments/Questions']
        })

print(f"Total rows to add: {len(rows_data)}")

# Create JSON payload as an object with "rows" key
payload = {
    "spreadsheet_id": "1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4",
    "rows": rows_data
}

# Write to file
with open('/Users/ericbrown/.openclaw/workspace/api_payload.json', 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("Payload saved to api_payload.json")
