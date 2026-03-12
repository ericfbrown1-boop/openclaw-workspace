#!/bin/bash
mcporter call zapier.google_sheets_create_spreadsheet_row \
  'instructions:"Add a new row to the Income Tax Tracking Items spreadsheet with the following data: Date Received: 2026-02-21, Sender: Christy Moore <cmoore@keystone.cpa>, Description: Brown - IRS Deliverable, Type of Tax Item: (empty), Link to Original Gmail: https://mail.google.com/mail/u/0/#inbox/67646, Comments/Questions: (empty), Not Tax Related: (empty)"' \
  'output_hint:"confirmation of row added"' \
  'spreadsheet:"1PwSUPWBT-IJ4rIyJ8TlEPqsq8D2XiO8unStzX0sy-e4"' \
  --output json
