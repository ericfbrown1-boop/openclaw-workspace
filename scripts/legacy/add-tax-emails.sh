#!/bin/bash

# Add remaining key tax-related emails to the Google Sheet

# Email 2: Cody Heimerdinger - 2025 Tax Docs (first)
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-21, Sender: Cody Heimerdinger <cheimerdinger@keystone.cpa>, Description: 2025 Tax Docs, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67647, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: Cody Heimerdinger - 2025 Tax Docs (2/21)"

# Email 3: IRS - Vivian Lai (first)
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-20, Sender: Lai Vivian L <Vivian.L.Lai@irs.gov>, Description: RE: [EXT] Delay on my Appeals submission, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67639, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: IRS - Vivian Lai (2/20)"

# Email 4: IRS - Vivian Lai (second)
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-23, Sender: Lai Vivian L <Vivian.L.Lai@irs.gov>, Description: RE: [EXT] Delay on my Appeals submission, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67682, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: IRS - Vivian Lai (2/23)"

# Email 5: Eric - 2025 taxes Old mission foundation (first)
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-23, Sender: Eric Brown <ericfbrown1@gmail.com>, Description: 2025 taxes. Old mission foundation, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67697, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: Eric - 2025 taxes Old mission foundation (2/23) - first"

# Email 6: Eric - 2025 taxes Old mission foundation (duplicate)
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-23, Sender: Eric Brown <ericfbrown1@gmail.com>, Description: 2025 taxes. Old mission foundation, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67698, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: Eric - 2025 taxes Old mission foundation (2/23) - duplicate"

# Email 7: Cody Heimerdinger - RE: 2025 Tax Docs (second)
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-24, Sender: Cody Heimerdinger <cheimerdinger@keystone.cpa>, Description: RE: 2025 Tax Docs, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67717, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: Cody Heimerdinger - RE: 2025 Tax Docs (2/24)"

# Email 8: Cody Heimerdinger - RE: 2025 Tax Docs (third)
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-25, Sender: Cody Heimerdinger <cheimerdinger@keystone.cpa>, Description: RE: 2025 Tax Docs, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67722, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: Cody Heimerdinger - RE: 2025 Tax Docs (2/25)"

# Email 9: Noah Kolassa - rental on Old Mission Road (rental property - tax relevant)
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-20, Sender: Noah Kolassa <dteoutdoors@gmail.com>, Description: Re: From Eric Brown re rental on Old Mission Road, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67641, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: Noah Kolassa - rental property (2/20)"

# Email 10: Tesla lease billing statement
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-21, Sender: Tesla <noreply@tesla.com>, Description: Your Model S Lease Billing Statement is Available, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67655, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: Tesla - Lease Billing Statement (2/21)"

# Email 11: CCH tax software sign-in
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row with: Date Received: 2026-02-21, Sender: DoNotReply@cch.com, Description: Sign-in Verification, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67645, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json > /dev/null 2>&1

echo "Added: CCH Tax Software - Sign-in Verification (2/21)"

echo ""
echo "Done adding 11 key tax-related emails to the sheet."
