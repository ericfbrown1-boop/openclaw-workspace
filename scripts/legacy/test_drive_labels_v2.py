#!/usr/bin/env python3
"""
Test Google Drive Labels API - V2
Uses Google API client library with gog credentials
"""

import os
import json
import sys

FOLDER_ID = "0BxKRLOeWEujkbk5qNTdDUllkVWc"
FOLDER_NAME = "Tanium Benefits"

def test_with_curl():
    """Test Drive Labels API using curl with gog-generated requests"""
    import subprocess
    
    print("🦞 Testing Google Drive Labels API")
    print("=" * 60)
    print(f"Target: {FOLDER_NAME}")
    print(f"Folder ID: {FOLDER_ID}\n")
    
    # First, let's just check if the API is enabled by trying to access it
    print("🔍 Testing API accessibility...\n")
    
    # Get basic file info first to confirm Drive API works
    print("1️⃣  Testing basic Drive API access...")
    result = subprocess.run(
        ['gog', 'drive', 'get', FOLDER_ID, '--json'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"   ✅ Drive API working")
        print(f"   Folder: {data.get('file', {}).get('name')}")
        print(f"   Modified: {data.get('file', {}).get('modifiedTime')}")
    else:
        print(f"   ❌ Drive API failed: {result.stderr}")
        return 1
    
    print("\n2️⃣  Checking for Drive Labels API...")
    
    # Try to check if labels are even in the file metadata
    # Drive API v3 includes labelInfo field if labels are applied
    result = subprocess.run(
        ['curl', '-s',
         f'https://www.googleapis.com/drive/v3/files/{FOLDER_ID}?fields=id,name,labelInfo',
         '-H', 'Authorization: Bearer $(gog auth tokens export ericfbrown1@gmail.com --json | jq -r .access_token)'],
        capture_output=True,
        text=True,
        shell=True
    )
    
    print(f"   Response: {result.stdout[:200]}...")
    
    # The issue is we can't easily get the token from gog
    print("\n⚠️  Direct API testing requires OAuth token extraction")
    print("   gog CLI doesn't expose tokens easily for security reasons\n")
    
    print("=" * 60)
    print("📝 Summary:")
    print("  • Drive API: ✅ Working")
    print("  • Labels API: ❓ Need proper authentication")
    print("\n💡 Recommendation:")
    print("  Enable Drive Labels API in Cloud Console, then:")
    print("  • Labels will appear automatically in file metadata")
    print("  • gog drive get <fileId> will show labelInfo field")
    print("  • Or use Drive web UI to apply/view labels")
    
    return 0

if __name__ == '__main__':
    sys.exit(test_with_curl())
