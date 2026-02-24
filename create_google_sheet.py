#!/usr/bin/env python3
"""
Create and populate Google Sheet for 2025 Tax Tracking
Uses Google Sheets API v4
"""

import json
import os
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ Google API libraries not installed")
    print("Installing required libraries...")
    os.system("pip3 install --quiet google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    print("✓ Libraries installed. Please run script again.")
    exit(0)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def authenticate_google():
    """Authenticate with Google using OAuth"""
    print("Authenticating with Google...")
    print("\nThis will open a browser window for you to authorize access.")
    print("Please sign in with: ericfbrown1@gmail.com")
    input("\nPress Enter to continue...")
    
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import pickle
    
    creds = None
    token_file = 'token.pickle'
    
    # Load existing token if available
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Need to create credentials.json first
            if not os.path.exists('credentials.json'):
                print("\n" + "="*80)
                print("❌ CREDENTIALS NOT FOUND")
                print("="*80)
                print("\nYou need to create OAuth credentials:")
                print("1. Go to: https://console.cloud.google.com/apis/credentials")
                print("2. Create OAuth 2.0 Client ID (Desktop app)")
                print("3. Download as 'credentials.json' and save to this directory")
                print("\nOr provide Service Account JSON key file")
                print("="*80)
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    print("✓ Authenticated successfully")
    return creds

def create_spreadsheet(service, title="Income Tax Tracking Items"):
    """Create a new Google Spreadsheet"""
    print(f"\nCreating spreadsheet: {title}")
    
    spreadsheet = {
        'properties': {
            'title': title
        },
        'sheets': [{
            'properties': {
                'title': '2025 Tax Items',
                'gridProperties': {
                    'rowCount': 1000,
                    'columnCount': 6
                }
            }
        }]
    }
    
    try:
        spreadsheet = service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()
        
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')
        
        print(f"✓ Created spreadsheet")
        print(f"  ID: {spreadsheet_id}")
        print(f"  URL: {spreadsheet_url}")
        
        return spreadsheet_id, spreadsheet_url
        
    except HttpError as error:
        print(f"❌ Error creating spreadsheet: {error}")
        return None, None

def format_headers(service, spreadsheet_id):
    """Format the header row"""
    print("\nFormatting header row...")
    
    requests = [{
        'repeatCell': {
            'range': {
                'sheetId': 0,
                'startRowIndex': 0,
                'endRowIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {
                        'red': 0.2,
                        'green': 0.2,
                        'blue': 0.8
                    },
                    'textFormat': {
                        'foregroundColor': {
                            'red': 1.0,
                            'green': 1.0,
                            'blue': 1.0
                        },
                        'fontSize': 11,
                        'bold': True
                    },
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    }, {
        'updateSheetProperties': {
            'properties': {
                'sheetId': 0,
                'gridProperties': {
                    'frozenRowCount': 1
                }
            },
            'fields': 'gridProperties.frozenRowCount'
        }
    }]
    
    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        print("✓ Formatted headers")
    except HttpError as error:
        print(f"⚠ Warning: Could not format headers: {error}")

def populate_spreadsheet(service, spreadsheet_id, json_file="tax_emails_2025.json"):
    """Populate spreadsheet with tax email data"""
    print(f"\nLoading data from {json_file}...")
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        return False
    
    print(f"Found {len(data)} items to add")
    
    # Prepare data for spreadsheet
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
        # Clean description
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
    
    # Write to spreadsheet
    print("Writing data to spreadsheet...")
    
    range_name = '2025 Tax Items!A1'
    body = {
        'values': rows
    }
    
    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"✓ Updated {result.get('updatedRows')} rows")
        return True
        
    except HttpError as error:
        print(f"❌ Error writing data: {error}")
        return False

def share_spreadsheet(service, spreadsheet_id, email="ericfbrown1@gmail.com"):
    """Share spreadsheet with specific email"""
    print(f"\nSharing spreadsheet with {email}...")
    
    from googleapiclient.discovery import build as drive_build
    
    try:
        # Build Drive API service
        drive_service = drive_build('drive', 'v3', credentials=service._http.credentials)
        
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()
        
        print(f"✓ Shared with {email}")
        return True
        
    except HttpError as error:
        print(f"⚠ Warning: Could not share spreadsheet: {error}")
        print(f"  Please manually share at: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        return False

def main():
    print("=" * 80)
    print("GOOGLE SHEETS TAX TRACKING SETUP")
    print("=" * 80)
    
    # Authenticate
    creds = authenticate_google()
    if not creds:
        return
    
    # Build service
    service = build('sheets', 'v4', credentials=creds)
    
    # Create spreadsheet
    spreadsheet_id, spreadsheet_url = create_spreadsheet(service)
    if not spreadsheet_id:
        return
    
    # Populate with data
    if not populate_spreadsheet(service, spreadsheet_id):
        return
    
    # Format headers
    format_headers(service, spreadsheet_id)
    
    # Share spreadsheet
    share_spreadsheet(service, spreadsheet_id)
    
    print("\n" + "=" * 80)
    print("✓ SUCCESS! TAX TRACKING SHEET CREATED")
    print("=" * 80)
    print(f"\n📊 Spreadsheet URL:")
    print(f"   {spreadsheet_url}")
    print(f"\n✉ Shared with: ericfbrown1@gmail.com")
    print(f"\n📈 Total Items: {len(open('tax_emails_2025.json').read().split('date_received')) - 1}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
