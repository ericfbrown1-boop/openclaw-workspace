#!/usr/bin/env python3
"""
Dropbox API client for Jarvis
Usage: 
  dropbox-cli.py list [path]           - List files in path
  dropbox-cli.py search <query>        - Search for files
  dropbox-cli.py read <path>           - Read file content
  dropbox-cli.py download <path> [out] - Download file
  dropbox-cli.py upload <local> <path> - Upload file
  dropbox-cli.py mkdir <path>          - Create folder
  dropbox-cli.py info <path>           - Get file metadata
"""

import sys
import json
import requests
import os
import subprocess
from datetime import datetime, timedelta

# Auto-refresh token integration
AUTH_CONFIG = os.path.expanduser("~/.openclaw/workspace/.dropbox_auth.json")
AUTH_SCRIPT = os.path.expanduser("~/.openclaw/workspace/dropbox-auth.py")

def get_valid_token():
    """Get a valid access token (auto-refresh if needed)"""
    # Check if auth system is configured
    if os.path.exists(AUTH_CONFIG):
        try:
            with open(AUTH_CONFIG, 'r') as f:
                config = json.load(f)
            
            access_token = config.get("access_token")
            token_expiry = config.get("token_expiry")
            
            # Check if token is expired or about to expire (within 5 minutes)
            if token_expiry:
                expiry = datetime.fromisoformat(token_expiry)
                if datetime.now() >= expiry - timedelta(minutes=5):
                    # Token expired, refresh it
                    if os.path.exists(AUTH_SCRIPT):
                        subprocess.run([sys.executable, AUTH_SCRIPT, "refresh"], 
                                     capture_output=True, check=True)
                        # Reload config
                        with open(AUTH_CONFIG, 'r') as f:
                            config = json.load(f)
                        access_token = config.get("access_token")
            
            return access_token
        except Exception as e:
            print(f"⚠️  Auto-refresh failed: {e}", file=sys.stderr)
            print(f"   Using fallback token", file=sys.stderr)
    
    # Fallback to hardcoded token
    return "sl.u.AGX_8JZXZLAV1zyJVv9VEAT0vnm12N3Y_2chrPuZLBSQ-zc1Q6eRqXLgKv5qnN6Z-gcMPnAMtzjlq6_D-dFZNwbMZn8wtghsFFncU0_a6qpOy2bYjn2m81jEi_hkUqdEgr_KHsRQqtY4V5MOBo0i2f4EhVXLw3um124NYfefku-6T3hcH_QAWnoDT0R_JneUGb_8IPrwEWjeUHWpYrxKBTPCq25bGUe-swAS6SJKP8kQ2sMeAvIEsx8CUZPfVhVri_cPMyWO2sWT_Dh-e_3MkEUot3GwV0cPruqJ2nWg22azK45irUdj9Jo9MYN76h9tOLaqikkLBrDYe3zMmBhF14tYvNjla6qFyc22T__aAsADinBViLZ-gRL1x0lZQtMTz-OPAGpUjeugJRg8H9iegC1bqV7uVIX4E_jJdx5TldGFEX4z2_Iz0IZKjaOk-tG0Ky0aTJcUBdFLqfztkhAZdG2BOiGZQHlPRAh2STqe-HPYExGh70WCipYWY5SfUOMFESRroFK4rnG58hFbPYIKhFWk3wXFnnYOBQumX_XRTd6I_B81LaD45LIKAk4T3vzCN9FU_8vXQnF6C0ycLLSNTIboDQPQm0KxN5hT_VuElbIyQ_Qk7QV3pAmFkt2h3CuAK0SzDLGSXtEdXBC8BJZ-P2ggeVBta7ynlqC4mS17rWX3FP9dNvn_SLrMEz55cgLzU_j_7PLsdnNAE_Rp3VdTOBk_YARNwAe5mCKEGvWwXRY1OeZlcrrhom9GCNqiPQIxsh1V5jWRz9kUjK5Ne4wOOQuvpnL_-GcS0ACOeVsay3shSYtH2WOqr8kJMVHUzic8TfkfEZfIT-cQXv3yKu1Iry6Lc-1JBuAXVycUFhubdbADV4cNel0VeqcgcxTBxLS655ItFK4Ea4E5YdZmC4Ix81A7RYLt5_R_DRKSwD5U5ZSoh8EmECGe-74-vNsX8NDU_vWS2dLo2Nwt8KQti8Zsv-OgepfZj4kQGrDsA0OLYSjMJS3Hu6B6zHehN8hUt4dWWNjK-lKGBZstfT0StZlC7UG2ec4W8nUin4f-YckDYs4aRFm4Bw0WjETFP-KBzcuK2YXF8AsHelewc9UqN2F1QhiW5o81WbqPGqjjpkGbH1uqDOmRyMEW_oUt1PCC1pBGvhdSK8M_rIJQb1MRDTi5_iacgxVy--GUCqma4Yn46lfZf_1QYrLSd55PDEKDNpRjSecXN80KGzdDJA-xOeV0wztwCJcyB9dj-oYggWk1xWfRcJ0g7VnonC5ktbL5ddl7woxpN-u74U7IP6SpsiKGyUUz"

# Get token with auto-refresh
TOKEN = get_valid_token()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def list_folder(path=""):
    """List files in a Dropbox folder"""
    url = "https://api.dropboxapi.com/2/files/list_folder"
    data = {"path": path if path else "", "recursive": False}
    
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        result = response.json()
        for entry in result.get("entries", []):
            tag = "📁" if entry[".tag"] == "folder" else "📄"
            print(f"{tag} {entry['name']} ({entry['path_display']})")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def search_files(query):
    """Search for files in Dropbox"""
    url = "https://api.dropboxapi.com/2/files/search_v2"
    data = {
        "query": query,
        "options": {
            "max_results": 20
        }
    }
    
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        result = response.json()
        for match in result.get("matches", []):
            metadata = match.get("metadata", {}).get("metadata", {})
            name = metadata.get("name", "Unknown")
            path = metadata.get("path_display", "")
            print(f"📄 {name} → {path}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def read_file(path):
    """Read content of a text file"""
    url = "https://content.dropboxapi.com/2/files/download"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Dropbox-API-Arg": json.dumps({"path": path})
    }
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(response.text)
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def download_file(path, output_path=None):
    """Download a file from Dropbox"""
    import os
    url = "https://content.dropboxapi.com/2/files/download"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Dropbox-API-Arg": json.dumps({"path": path})
    }
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        # If no output path specified, use the filename from Dropbox
        if not output_path:
            filename = os.path.basename(path)
            output_path = filename
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded to: {output_path}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def create_folder(dropbox_path):
    """Create a folder in Dropbox"""
    url = "https://api.dropboxapi.com/2/files/create_folder_v2"
    data = {
        "path": dropbox_path,
        "autorename": False
    }
    
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        result = response.json()
        metadata = result.get("metadata", {})
        print(f"✅ Created folder: {metadata.get('path_display', dropbox_path)}")
        return True
    else:
        # Check if folder already exists
        if "path/conflict/folder" in response.text:
            print(f"ℹ️  Folder already exists: {dropbox_path}")
            return True
        print(f"Error: {response.status_code} - {response.text}")
        return False

def upload_file(local_path, dropbox_path):
    """Upload a file to Dropbox"""
    import os
    url = "https://content.dropboxapi.com/2/files/upload"
    
    # Read the file
    with open(local_path, 'rb') as f:
        file_data = f.read()
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/octet-stream",
        "Dropbox-API-Arg": json.dumps({
            "path": dropbox_path,
            "mode": "overwrite",
            "autorename": False
        })
    }
    
    response = requests.post(url, headers=headers, data=file_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Uploaded: {local_path} → {result['path_display']}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def get_metadata(path):
    """Get file/folder metadata"""
    url = "https://api.dropboxapi.com/2/files/get_metadata"
    data = {"path": path}
    
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        path = sys.argv[2] if len(sys.argv) > 2 else ""
        list_folder(path)
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: dropbox-cli.py search <query>")
            sys.exit(1)
        search_files(sys.argv[2])
    elif command == "read":
        if len(sys.argv) < 3:
            print("Usage: dropbox-cli.py read <path>")
            sys.exit(1)
        read_file(sys.argv[2])
    elif command == "download":
        if len(sys.argv) < 3:
            print("Usage: dropbox-cli.py download <path> [output]")
            sys.exit(1)
        output = sys.argv[3] if len(sys.argv) > 3 else None
        download_file(sys.argv[2], output)
    elif command == "upload":
        if len(sys.argv) < 4:
            print("Usage: dropbox-cli.py upload <local_path> <dropbox_path>")
            sys.exit(1)
        upload_file(sys.argv[2], sys.argv[3])
    elif command == "mkdir":
        if len(sys.argv) < 3:
            print("Usage: dropbox-cli.py mkdir <dropbox_path>")
            sys.exit(1)
        create_folder(sys.argv[2])
    elif command == "info":
        if len(sys.argv) < 3:
            print("Usage: dropbox-cli.py info <path>")
            sys.exit(1)
        get_metadata(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
