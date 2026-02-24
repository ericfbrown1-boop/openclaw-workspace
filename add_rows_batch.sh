#!/bin/bash

SHEET_ID="1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"

# First, let's add the header row
echo "Adding header row..."
mcporter call zapier.google_sheets_create_spreadsheet_row \
  --args '{"instructions": "Add header row to spreadsheet '$SHEET_ID' with columns: Date Received, Sender, Description, Tax Type, Gmail Link, Comments", "spreadsheet": "'$SHEET_ID'"}'

echo "Header row added. Now importing data rows..."

# Now let's try importing all rows using the CSV we created
python3 << 'EOF'
import csv
import json
import subprocess

# Read CSV data
with open('/Users/ericbrown/.openclaw/workspace/Income_Tax_Tracking_Items.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Process in batches of 10
batch_size = 10
total_batches = (len(rows) + batch_size - 1) // batch_size

for batch_num in range(total_batches):
    start_idx = batch_num * batch_size
    end_idx = min(start_idx + batch_size, len(rows))
    batch_rows = rows[start_idx:end_idx]
    
    print(f"Processing batch {batch_num + 1}/{total_batches} (rows {start_idx + 1}-{end_idx})...")
    
    # Create instructions for this batch
    rows_data = []
    for row in batch_rows:
        row_str = f"Date Received: {row['Date Received']}, Sender: {row['Sender'][:50]}..., Description: {row['Description of Email Communication'][:50]}..., Tax Type: {row['Type of Tax Income or Expense Item']}, Gmail Link: {row['Link to Original Gmail']}, Comments: {row['Comments/Questions']}"
        rows_data.append(row_str)
    
    instructions = f"Add {len(batch_rows)} rows to spreadsheet 1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4: " + " | ".join(rows_data)
    
    # Execute the command
    cmd = [
        'mcporter', 'call', 'zapier.google_sheets_create_multiple_spreadsheet_rows',
        '--args', json.dumps({"instructions": instructions, "spreadsheet": "1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"})
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"  ✓ Batch {batch_num + 1} completed")
        else:
            print(f"  ✗ Batch {batch_num + 1} failed: {result.stderr}")
    except Exception as e:
        print(f"  ✗ Batch {batch_num + 1} error: {e}")
    
    # Small delay between batches
    import time
    time.sleep(2)

print("Import complete!")
EOF
