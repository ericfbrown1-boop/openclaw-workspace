#!/usr/bin/env python3
"""
Dropbox API client for Jarvis — Self-contained with inline token refresh
Credentials stored in ~/.openclaw/workspace/.dropbox_auth.json (chmod 600)

Usage:
  dropbox-cli.py list [path]           - List files in path
  dropbox-cli.py search <query>        - Search for files
  dropbox-cli.py read <path>           - Read file content
  dropbox-cli.py download <path> [out] - Download file
  dropbox-cli.py upload <local> <path> - Upload file
  dropbox-cli.py mkdir <path>          - Create folder
  dropbox-cli.py info <path>           - Get file metadata
  dropbox-cli.py status                - Show auth status
"""

import sys
import json
import requests
import os
from datetime import datetime, timedelta

# ─── Auth Configuration ──────────────────────────────────────────────
# All credentials live in this single config file (chmod 600).
# Refresh token is PERMANENT (never expires unless app is revoked).
# Access token is SHORT-LIVED (4 hours) and auto-refreshed inline.
AUTH_CONFIG_PATH = os.path.expanduser("~/.openclaw/workspace/.dropbox_auth.json")


def _load_config():
    """Load the auth config file. Dies if missing."""
    if not os.path.exists(AUTH_CONFIG_PATH):
        print(f"❌ Auth config not found: {AUTH_CONFIG_PATH}", file=sys.stderr)
        print("   Run dropbox-auth.py to set up credentials.", file=sys.stderr)
        sys.exit(1)
    try:
        with open(AUTH_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Failed to read auth config: {e}", file=sys.stderr)
        sys.exit(1)


def _save_config(data):
    """Persist config to disk with secure permissions."""
    os.makedirs(os.path.dirname(AUTH_CONFIG_PATH), exist_ok=True)
    with open(AUTH_CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    os.chmod(AUTH_CONFIG_PATH, 0o600)


def _refresh_access_token(config):
    """Use the permanent refresh token to get a new 4-hour access token."""
    resp = requests.post(
        "https://api.dropboxapi.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": config["refresh_token"],
            "client_id": config["app_key"],
            "client_secret": config["app_secret"],
        },
        timeout=15,
    )
    resp.raise_for_status()
    tokens = resp.json()
    config["access_token"] = tokens["access_token"]
    expires_in = tokens.get("expires_in", 14400)
    config["token_expiry"] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
    _save_config(config)
    return config["access_token"]


def get_valid_token():
    """
    Return a valid access token. Transparent to callers:
    1. Load config from disk.
    2. If token exists and has >5 min left, use it.
    3. Otherwise, refresh inline (one HTTP call, ~200ms).
    Never fails unless Dropbox API is down or app is revoked.
    """
    config = _load_config()
    access_token = config.get("access_token")
    token_expiry = config.get("token_expiry")

    if access_token and token_expiry:
        try:
            expiry = datetime.fromisoformat(token_expiry)
            if datetime.now() < expiry - timedelta(minutes=5):
                return access_token
        except ValueError:
            pass  # Bad expiry string — just refresh

    # Refresh needed
    return _refresh_access_token(config)


# ─── API Helpers ─────────────────────────────────────────────────────

def _headers(content_type="application/json"):
    return {
        "Authorization": f"Bearer {get_valid_token()}",
        "Content-Type": content_type,
    }


def list_folder(path=""):
    """List files in a Dropbox folder."""
    url = "https://api.dropboxapi.com/2/files/list_folder"
    data = {"path": path if path else "", "recursive": False}
    response = requests.post(url, headers=_headers(), json=data, timeout=30)
    if response.status_code == 200:
        result = response.json()
        for entry in result.get("entries", []):
            tag = "📁" if entry[".tag"] == "folder" else "📄"
            size = ""
            if entry.get("size"):
                mb = entry["size"] / (1024 * 1024)
                size = f"  ({mb:.1f} MB)" if mb >= 1 else f"  ({entry['size']} B)"
            print(f"{tag} {entry['name']}{size}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False


def search_files(query):
    """Search for files in Dropbox."""
    url = "https://api.dropboxapi.com/2/files/search_v2"
    data = {"query": query, "options": {"max_results": 20}}
    response = requests.post(url, headers=_headers(), json=data, timeout=30)
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
    """Read content of a text file."""
    url = "https://content.dropboxapi.com/2/files/download"
    headers = {
        "Authorization": f"Bearer {get_valid_token()}",
        "Dropbox-API-Arg": json.dumps({"path": path}),
    }
    response = requests.post(url, headers=headers, timeout=60)
    if response.status_code == 200:
        print(response.text)
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False


def download_file(path, output_path=None):
    """Download a file from Dropbox."""
    url = "https://content.dropboxapi.com/2/files/download"
    headers = {
        "Authorization": f"Bearer {get_valid_token()}",
        "Dropbox-API-Arg": json.dumps({"path": path}),
    }
    response = requests.post(url, headers=headers, timeout=120)
    if response.status_code == 200:
        if not output_path:
            output_path = os.path.basename(path)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded to: {output_path}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False


def create_folder(dropbox_path):
    """Create a folder in Dropbox."""
    url = "https://api.dropboxapi.com/2/files/create_folder_v2"
    data = {"path": dropbox_path, "autorename": False}
    response = requests.post(url, headers=_headers(), json=data, timeout=15)
    if response.status_code == 200:
        result = response.json()
        metadata = result.get("metadata", {})
        print(f"✅ Created folder: {metadata.get('path_display', dropbox_path)}")
        return True
    else:
        if "path/conflict/folder" in response.text:
            print(f"ℹ️  Folder already exists: {dropbox_path}")
            return True
        print(f"Error: {response.status_code} - {response.text}")
        return False


def upload_file(local_path, dropbox_path):
    """Upload a file to Dropbox."""
    url = "https://content.dropboxapi.com/2/files/upload"
    with open(local_path, 'rb') as f:
        file_data = f.read()
    headers = {
        "Authorization": f"Bearer {get_valid_token()}",
        "Content-Type": "application/octet-stream",
        "Dropbox-API-Arg": json.dumps({
            "path": dropbox_path,
            "mode": "overwrite",
            "autorename": False,
        }),
    }
    response = requests.post(url, headers=headers, data=file_data, timeout=120)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Uploaded: {local_path} → {result['path_display']}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False


def get_metadata(path):
    """Get file/folder metadata."""
    url = "https://api.dropboxapi.com/2/files/get_metadata"
    data = {"path": path}
    response = requests.post(url, headers=_headers(), json=data, timeout=15)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False


def show_status():
    """Show current auth status."""
    config = _load_config()
    access_token = config.get("access_token")
    token_expiry = config.get("token_expiry")
    print("\n📊 Dropbox Auth Status")
    print("=" * 50)
    print(f"Config File:   {AUTH_CONFIG_PATH}")
    print(f"App Key:       ✅ {config.get('app_key', 'MISSING')}")
    print("App Secret:    ✅ (configured)" if config.get("app_secret") else "App Secret:    ❌ MISSING")
    print("Refresh Token: ✅ (permanent, never expires)" if config.get("refresh_token") else "Refresh Token: ❌ MISSING")
    if access_token:
        print(f"Access Token:  ✅ {access_token[:25]}...")
    else:
        print("Access Token:  ⚠️  Not cached (will refresh on next call)")
    if token_expiry:
        try:
            expiry = datetime.fromisoformat(token_expiry)
            now = datetime.now()
            if now >= expiry:
                print("Token Status:  🔄 Expired (will auto-refresh)")
            else:
                remaining = expiry - now
                hours = int(remaining.total_seconds() / 3600)
                minutes = int((remaining.total_seconds() % 3600) / 60)
                print(f"Token Expiry:  {token_expiry}")
                print(f"Time Left:     {hours}h {minutes}m")
        except ValueError:
            print("Token Expiry:  ⚠️  Invalid format")
    print("=" * 50)
    print("\n💡 Refresh token is permanent. You will NEVER need to")
    print("   re-authorize unless you revoke the Dropbox app.")


# ─── CLI Entry Point ─────────────────────────────────────────────────

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
    elif command == "status":
        show_status()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
