#!/usr/bin/env python3
"""
Test Google Drive Labels API
Read and display labels for the Tanium Benefits folder
"""

import subprocess
import json
import sys

FOLDER_ID = "0BxKRLOeWEujkbk5qNTdDUllkVWc"
FOLDER_NAME = "Tanium Benefits"

def get_access_token():
    """Get OAuth access token from gog"""
    # Try to get a fresh token by making a simple Drive API call
    result = subprocess.run(
        ['gog', 'drive', 'get', FOLDER_ID, '--json'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to access Drive: {result.stderr}")
        return None
    
    # Extract token from gog's OAuth credentials
    # gog stores tokens in ~/.gog/credentials/
    import os
    import glob
    
    cred_paths = glob.glob(os.path.expanduser('~/.gog/credentials/*/token.json'))
    if not cred_paths:
        print("❌ No gog credentials found")
        return None
    
    try:
        with open(cred_paths[0], 'r') as f:
            creds = json.load(f)
            return creds.get('access_token')
    except Exception as e:
        print(f"❌ Failed to read token: {e}")
        return None

def list_available_labels(token):
    """List all available labels in the Drive"""
    import requests
    
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://drivelabels.googleapis.com/v2/labels'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        labels = data.get('labels', [])
        
        print(f"\n📋 Available Labels ({len(labels)}):")
        print("=" * 60)
        
        for label in labels:
            label_id = label.get('id', 'N/A')
            name = label.get('name', 'N/A')
            label_type = label.get('labelType', 'N/A')
            print(f"  • {name}")
            print(f"    ID: {label_id}")
            print(f"    Type: {label_type}")
            print()
        
        return labels
    else:
        print(f"\n❌ Failed to list labels:")
        print(f"   Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def get_file_labels(token, file_id):
    """Get labels applied to a specific file/folder"""
    import requests
    
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://www.googleapis.com/drive/v3/files/{file_id}'
    params = {'fields': 'id,name,labelInfo'}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        label_info = data.get('labelInfo', {})
        
        print(f"\n📁 Folder: {data.get('name')}")
        print(f"   ID: {data.get('id')}")
        print("=" * 60)
        
        labels = label_info.get('labels', [])
        if labels:
            print(f"\n🏷️  Applied Labels ({len(labels)}):")
            for label in labels:
                print(f"  • Label ID: {label.get('id')}")
                fields = label.get('fields', {})
                for field_id, field_values in fields.items():
                    print(f"    Field {field_id}: {field_values}")
        else:
            print("\n   No labels applied to this folder")
        
        return label_info
    else:
        print(f"\n❌ Failed to get file labels:")
        print(f"   Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def main():
    print("🦞 Testing Google Drive Labels API")
    print("=" * 60)
    print(f"Target: {FOLDER_NAME}")
    print(f"Folder ID: {FOLDER_ID}\n")
    
    # Get access token
    print("🔑 Getting OAuth access token...")
    token = get_access_token()
    
    if not token:
        print("\n❌ Cannot proceed without access token")
        print("\nTroubleshooting:")
        print("  1. Ensure gog is authenticated: gog auth login")
        print("  2. Check Drive Labels API is enabled in Google Cloud Console")
        return 1
    
    print("✅ Access token obtained\n")
    
    # List available labels
    labels = list_available_labels(token)
    
    # Get labels on the Tanium Benefits folder
    file_labels = get_file_labels(token, FOLDER_ID)
    
    print("\n" + "=" * 60)
    print("✅ Drive Labels API test complete!")
    
    return 0

if __name__ == '__main__':
    try:
        import requests
    except ImportError:
        print("❌ Error: 'requests' library not found")
        print("   Install with: pip3 install requests")
        sys.exit(1)
    
    sys.exit(main())
