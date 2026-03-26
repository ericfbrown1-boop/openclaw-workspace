#!/usr/bin/env python3
import csv
import json
import subprocess
import time

# Read the CSV file
with open('/Users/ericbrown/.openclaw/workspace/Income_Tax_Tracking_Items.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows to import: {len(rows) + 1} (including header)")

# Prepare header row
header = ["Date Received", "Sender", "Description", "Tax Type", "Gmail Link", "Comments"]

# Prepare all rows including header
all_rows = [header]
for row in rows:
    all_rows.append([
        row['Date Received'],
        row['Sender'],
        row['Description of Email Communication'],
        row['Type of Tax Income or Expense Item'],
        row['Link to Original Gmail'],
        row['Comments/Questions']
    ])

# Create a more structured payload for batch import
# Prepare as CSV format for import
csv_content = []
for row_data in all_rows:
    # Escape quotes and commas properly
    escaped_row = []
    for cell in row_data:
        if cell:
            # Escape quotes by doubling them
            cell = cell.replace('"', '""')
            # Wrap in quotes if contains comma, quote, or newline
            if ',' in cell or '"' in cell or '\n' in cell:
                cell = f'"{cell}"'
        escaped_row.append(cell)
    csv_content.append(','.join(escaped_row))

csv_string = '\n'.join(csv_content)

# Write to file
with open('/Users/ericbrown/.openclaw/workspace/import_data.csv', 'w', encoding='utf-8') as f:
    f.write(csv_string)

print(f"Created CSV file with {len(all_rows)} rows")
print("CSV preview (first 3 rows):")
for i, row in enumerate(csv_content[:3]):
    print(f"Row {i+1}: {row[:100]}...")
