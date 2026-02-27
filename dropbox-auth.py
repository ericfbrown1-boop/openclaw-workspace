#!/usr/bin/env python3
"""
Dropbox OAuth 2.0 Automation with Refresh Token Support
Generates and auto-refreshes Dropbox access tokens
"""

import os
import sys
import json
import time
import webbrowser
import urllib.parse
import http.server
import socketserver
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip3 install requests")
    sys.exit(1)

# Configuration
CONFIG_FILE = os.path.expanduser("~/.openclaw/workspace/.dropbox_auth.json")
REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

class DropboxOAuth:
    def __init__(self):
        self.config = self.load_config()
        self.app_key = self.config.get("app_key")
        self.app_secret = self.config.get("app_secret")
        self.refresh_token = self.config.get("refresh_token")
        self.access_token = self.config.get("access_token")
        self.token_expiry = self.config.get("token_expiry")
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
        # Set restrictive permissions (owner read/write only)
        os.chmod(CONFIG_FILE, 0o600)
        print(f"✅ Configuration saved to {CONFIG_FILE}")
    
    def setup_app(self, app_key, app_secret):
        """Store Dropbox app credentials"""
        self.app_key = app_key
        self.app_secret = app_secret
        self.config["app_key"] = app_key
        self.config["app_secret"] = app_secret
        self.save_config()
        print("✅ Dropbox app credentials saved")
    
    def start_oauth_flow(self):
        """Start OAuth 2.0 authorization flow"""
        if not self.app_key:
            print("ERROR: App key not configured. Run: python3 dropbox-auth.py setup")
            sys.exit(1)
        
        # Build authorization URL
        auth_url = (
            "https://www.dropbox.com/oauth2/authorize"
            f"?client_id={self.app_key}"
            f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
            "&response_type=code"
            "&token_access_type=offline"  # Request refresh token
        )
        
        print("\n🔐 Starting Dropbox OAuth 2.0 flow...")
        print(f"📱 Opening browser to: {auth_url}\n")
        
        # Start local callback server
        auth_code = self.run_callback_server()
        
        if auth_code:
            # Exchange authorization code for tokens
            self.exchange_code_for_tokens(auth_code)
        else:
            print("❌ Authorization failed or was cancelled")
            sys.exit(1)
    
    def run_callback_server(self):
        """Run local HTTP server to receive OAuth callback"""
        auth_code = None
        
        class CallbackHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                nonlocal auth_code
                
                # Parse query parameters
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                
                if 'code' in params:
                    auth_code = params['code'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = """
                        <html>
                        <body style="font-family: sans-serif; text-align: center; padding-top: 100px;">
                            <h1 style="color: green;">✅ Authorization successful!</h1>
                            <p>You can close this window and return to the terminal.</p>
                        </body>
                        </html>
                    """
                    self.wfile.write(html.encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<h1>Authorization failed</h1>")
            
            def log_message(self, format, *args):
                pass  # Suppress server logs
        
        # Open browser
        webbrowser.open(f"https://www.dropbox.com/oauth2/authorize?client_id={self.app_key}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code&token_access_type=offline")
        
        # Start server
        with socketserver.TCPServer(("", REDIRECT_PORT), CallbackHandler) as httpd:
            print(f"🌐 Local callback server running on {REDIRECT_URI}")
            print("⏳ Waiting for authorization...\n")
            
            # Handle one request (the callback)
            httpd.handle_request()
        
        return auth_code
    
    def exchange_code_for_tokens(self, auth_code):
        """Exchange authorization code for access and refresh tokens"""
        print("🔄 Exchanging authorization code for tokens...")
        
        response = requests.post(
            "https://api.dropboxapi.com/oauth2/token",
            data={
                "code": auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "client_id": self.app_key,
                "client_secret": self.app_secret,
            }
        )
        
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            
            # Calculate expiry time (tokens typically last 4 hours)
            expires_in = tokens.get("expires_in", 14400)
            self.token_expiry = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            
            # Save to config
            self.config["access_token"] = self.access_token
            self.config["refresh_token"] = self.refresh_token
            self.config["token_expiry"] = self.token_expiry
            self.save_config()
            
            print("✅ Tokens obtained successfully!")
            print(f"   Access token: {self.access_token[:20]}...")
            print(f"   Refresh token: {self.refresh_token[:20]}...")
            print(f"   Expires: {self.token_expiry}")
            
            # Update dropbox-cli.py
            self.update_dropbox_cli()
        else:
            print(f"❌ Token exchange failed: {response.status_code}")
            print(f"   Response: {response.text}")
            sys.exit(1)
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            print("ERROR: No refresh token available. Run: python3 dropbox-auth.py authorize")
            sys.exit(1)
        
        print("🔄 Refreshing access token...")
        
        response = requests.post(
            "https://api.dropboxapi.com/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.app_key,
                "client_secret": self.app_secret,
            }
        )
        
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            
            # Calculate expiry time
            expires_in = tokens.get("expires_in", 14400)
            self.token_expiry = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            
            # Save to config
            self.config["access_token"] = self.access_token
            self.config["token_expiry"] = self.token_expiry
            self.save_config()
            
            print("✅ Access token refreshed successfully!")
            print(f"   New token: {self.access_token[:20]}...")
            print(f"   Expires: {self.token_expiry}")
            
            # Update dropbox-cli.py
            self.update_dropbox_cli()
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            sys.exit(1)
    
    def get_valid_token(self):
        """Get a valid access token (refresh if needed)"""
        if not self.access_token:
            print("ERROR: No access token available. Run: python3 dropbox-auth.py authorize")
            sys.exit(1)
        
        # Check if token is expired or about to expire (within 5 minutes)
        if self.token_expiry:
            expiry = datetime.fromisoformat(self.token_expiry)
            if datetime.now() >= expiry - timedelta(minutes=5):
                print("⚠️  Access token expired or expiring soon, refreshing...")
                self.refresh_access_token()
        
        return self.access_token
    
    def update_dropbox_cli(self):
        """Update the dropbox-cli.py script with new token"""
        cli_file = os.path.expanduser("~/.openclaw/workspace/dropbox-cli.py")
        
        if not os.path.exists(cli_file):
            print(f"⚠️  Warning: {cli_file} not found, skipping update")
            return
        
        print(f"📝 Updating {cli_file} with new token...")
        
        with open(cli_file, 'r') as f:
            content = f.read()
        
        # Replace token line
        import re
        pattern = r'ACCESS_TOKEN = "[^"]*"'
        replacement = f'ACCESS_TOKEN = "{self.access_token}"'
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)
            with open(cli_file, 'w') as f:
                f.write(new_content)
            print("✅ dropbox-cli.py updated with new token")
        else:
            print("⚠️  Could not find ACCESS_TOKEN in dropbox-cli.py")
    
    def show_status(self):
        """Show current authentication status"""
        print("\n📊 Dropbox Authentication Status")
        print("=" * 50)
        print(f"App Key: {'✅ Configured' if self.app_key else '❌ Not configured'}")
        print(f"App Secret: {'✅ Configured' if self.app_secret else '❌ Not configured'}")
        print(f"Refresh Token: {'✅ Available' if self.refresh_token else '❌ Not available'}")
        print(f"Access Token: {'✅ Available' if self.access_token else '❌ Not available'}")
        
        if self.token_expiry:
            expiry = datetime.fromisoformat(self.token_expiry)
            now = datetime.now()
            if now >= expiry:
                print(f"Token Status: ❌ EXPIRED at {self.token_expiry}")
            else:
                time_left = expiry - now
                hours = int(time_left.total_seconds() / 3600)
                minutes = int((time_left.total_seconds() % 3600) / 60)
                print(f"Token Expiry: {self.token_expiry}")
                print(f"Time Remaining: {hours}h {minutes}m")
        print("=" * 50)


def main():
    if len(sys.argv) < 2:
        print("""
Dropbox OAuth 2.0 Automation Tool
==================================

Usage:
  python3 dropbox-auth.py setup <app_key> <app_secret>
      Store your Dropbox app credentials

  python3 dropbox-auth.py authorize
      Start OAuth flow to get refresh token (one-time)

  python3 dropbox-auth.py refresh
      Manually refresh the access token

  python3 dropbox-auth.py token
      Get a valid access token (auto-refresh if needed)

  python3 dropbox-auth.py status
      Show current authentication status

Example:
  # First time setup
  python3 dropbox-auth.py setup abc123key def456secret
  python3 dropbox-auth.py authorize

  # Daily use (automatic refresh)
  python3 dropbox-auth.py token
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    oauth = DropboxOAuth()
    
    if command == "setup":
        if len(sys.argv) != 4:
            print("Usage: python3 dropbox-auth.py setup <app_key> <app_secret>")
            sys.exit(1)
        oauth.setup_app(sys.argv[2], sys.argv[3])
    
    elif command == "authorize":
        oauth.start_oauth_flow()
    
    elif command == "refresh":
        oauth.refresh_access_token()
    
    elif command == "token":
        token = oauth.get_valid_token()
        print(token)
    
    elif command == "status":
        oauth.show_status()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
