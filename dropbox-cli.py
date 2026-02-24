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

TOKEN = "sl.u.AGXXWnj5954ZdBuwjxCt6CHEGOoKzDMMaY7rVMFE74QBQER6Z7dlqc1fdQ5cIkqbNJ4rclydzu6jkA3SCfaIRjwHVFINHgQmjugj2ja7_CkW9UqU_DE3mAc3jbLBRtmgjYNhY9wH38YXpuhRCjc-vJfW4p0pIdSFkg9iAyxIT3xk0dNvyaOkBIi2dL96WSU0UOIVFc6bTKFIYFVZ92_vAktNQhGrMTRvUs-2FaZb2T1FxcABfJHBOEPl_sodpVxgB2YwnUhCOcLGNiiKXa8R7N1_TrSpb-NIqm_fAEZbtaCJmGA1LZyBeP74m39qMYKC-dMR_XfT176dPn30GwekygUZ5FcZ-qS-yLV0kDmO_SuzGCy9UKaXGlbVnlZ76ORAe34E0ZqP8N7WimTEIP1R2ePuAFRL_ig3M4RQ15qszHCrNKpzwXp3odvMiGVQxmKk2ZJUmsOPocfy18MapBfYd0jVhCtictIR5XE0iZG6nkaWVOWeXTv3Iyi8skISpC6KDKN3sfC5Rt56G2oDrJcPBX46LcA-JN6eul0UT8uUtAJY28MxXw9XXM8jBCOyFq3Wn53Yg0O43TYnNsMozftSekmW7rQw6lLG5O-B4dBXFDAF7lmszEMWvj4lK0bLOLKIj-zY5_YcPBFdYpMoAwp5QUjox_appOPwQjyFwzPt-559aKKohhlCJGMB4n2aGBnNAXZw0rBfWQs2FqknTn8LwjD72tWc1rKhZpmDRxBEB1GjLV0j_hS7qWSwA95pmEnakhiY4AxRkZD-eY7e69NNYEC1ocBdEIrzoaEAqMLfhCuisbJGqr8BCHq7K4gg7xIgOVrjg0mKxBksu4srKpfDj09ud9k4C_AW9t6D_5K0_OtIrm3vYXcpHcHDbmGhKqyDYv9Tc563L4CkmiI6fxxJnejxH-P-D1c2o4JusKIRoFLWJtEniYy7rryg5eI83sw3zN6Y9MB5s4HsBWIyVuSNyARug18CDr308FJJcSlK8k721PeS4-xk3tpzp3jChec3m8tOZfs9mRmiCH2re-fpHjp_dRfSLxbiju1l1STCNLp7Gcidj1_QKHTH_NViTAtI6SZXKgXnw6HQ-wC4Fszy8z1n0-RL3gzW7wJVvP5mBpcKu072jFR70wnwFbkPioYqAUueJjLaCnk1AiuF5HG9CnqIuJGMswpZe5aaX2juG2wadSRtYml-xXjQXOqTvgMQ_oNJwgku_WhQzE4SUp95AxjSd80OEKxDCwHPLkYSlgsI3117bnN6GGem703gWtswwvpx9UhcXKfp-KNC5WVrxDUp"

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
