#!/usr/bin/env python3
"""
Dropbox OAuth Token Generator
Automates generation of new Dropbox access tokens using app credentials.
"""

import requests
import webbrowser
import sys
from urllib.parse import urlencode, parse_qs, urlparse
import json

class DropboxOAuthHelper:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = "http://localhost"  # For local testing
        
    def get_authorization_url(self):
        """Generate the authorization URL for user to approve"""
        params = {
            'client_id': self.app_key,
            'response_type': 'code',
            'token_access_type': 'offline',  # Get refresh token too
        }
        auth_url = f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"
        return auth_url
    
    def exchange_code_for_token(self, authorization_code):
        """Exchange authorization code for access token"""
        url = "https://api.dropbox.com/oauth2/token"
        
        data = {
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'client_id': self.app_key,
            'client_secret': self.app_secret,
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            tokens = response.json()
            return tokens
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    
    def refresh_access_token(self, refresh_token):
        """Use refresh token to get new access token"""
        url = "https://api.dropbox.com/oauth2/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.app_key,
            'client_secret': self.app_secret,
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            tokens = response.json()
            return tokens
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None


def main():
    print("="*60)
    print("DROPBOX OAUTH TOKEN GENERATOR")
    print("="*60)
    
    # Get app credentials
    if len(sys.argv) >= 3:
        app_key = sys.argv[1]
        app_secret = sys.argv[2]
        print(f"\n✓ Using provided credentials")
        print(f"  App Key: {app_key[:10]}...")
    else:
        print("\nEnter your Dropbox app credentials:")
        print("(Find these at https://www.dropbox.com/developers/apps)")
        app_key = input("\nApp Key: ").strip()
        app_secret = input("App Secret: ").strip()
    
    helper = DropboxOAuthHelper(app_key, app_secret)
    
    # Check if we have a refresh token to use
    print("\n" + "="*60)
    print("OPTION 1: Use existing refresh token (if you have one)")
    print("="*60)
    refresh_token = input("\nRefresh token (or press Enter to skip): ").strip()
    
    if refresh_token:
        print("\n🔄 Using refresh token to get new access token...")
        tokens = helper.refresh_access_token(refresh_token)
        
        if tokens:
            print("\n" + "="*60)
            print("✅ NEW ACCESS TOKEN GENERATED!")
            print("="*60)
            print(f"\nAccess Token:\n{tokens['access_token']}")
            print(f"\nExpires in: {tokens.get('expires_in', 'N/A')} seconds")
            
            # Save to file
            with open('/tmp/dropbox_new_token.txt', 'w') as f:
                f.write(tokens['access_token'])
            print(f"\n💾 Token saved to: /tmp/dropbox_new_token.txt")
            return
    
    # Option 2: Full OAuth flow
    print("\n" + "="*60)
    print("OPTION 2: Generate new token via OAuth flow")
    print("="*60)
    
    # Step 1: Get authorization URL
    auth_url = helper.get_authorization_url()
    
    print("\n📋 STEP 1: Authorize the app")
    print("-"*60)
    print(f"\nAuthorization URL:\n{auth_url}")
    print("\n1. Click the URL above (or copy/paste into browser)")
    print("2. Click 'Allow' to authorize the app")
    print("3. Copy the authorization code from the URL")
    print("   (It will be after 'code=' in the redirected URL)")
    
    # Try to open browser automatically
    try:
        print("\n🌐 Opening browser automatically...")
        webbrowser.open(auth_url)
    except:
        print("\n⚠️  Couldn't open browser automatically - use the URL above")
    
    # Step 2: Get authorization code from user
    print("\n📋 STEP 2: Enter authorization code")
    print("-"*60)
    auth_code = input("\nAuthorization code: ").strip()
    
    if not auth_code:
        print("\n❌ No authorization code provided. Exiting.")
        return
    
    # Step 3: Exchange code for tokens
    print("\n🔄 Exchanging authorization code for access token...")
    tokens = helper.exchange_code_for_token(auth_code)
    
    if tokens:
        print("\n" + "="*60)
        print("✅ SUCCESS! NEW TOKENS GENERATED")
        print("="*60)
        
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in')
        
        print(f"\n🔑 Access Token:\n{access_token}")
        
        if refresh_token:
            print(f"\n🔄 Refresh Token (save this!):\n{refresh_token}")
            print("\n💡 Save the refresh token! You can use it to generate")
            print("   new access tokens without re-authorizing.")
        
        if expires_in:
            print(f"\n⏱️  Expires in: {expires_in} seconds ({expires_in/3600:.1f} hours)")
        
        # Save to files
        with open('/tmp/dropbox_new_token.txt', 'w') as f:
            f.write(access_token)
        
        if refresh_token:
            with open('/tmp/dropbox_refresh_token.txt', 'w') as f:
                f.write(refresh_token)
        
        # Save full response
        with open('/tmp/dropbox_tokens.json', 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print("\n💾 Tokens saved:")
        print("   Access token: /tmp/dropbox_new_token.txt")
        if refresh_token:
            print("   Refresh token: /tmp/dropbox_refresh_token.txt")
        print("   Full response: /tmp/dropbox_tokens.json")
        
        print("\n" + "="*60)
        print("🎉 DONE! Share the access token with Jarvis.")
        print("="*60)
    else:
        print("\n❌ Failed to generate tokens. Check your credentials.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted. Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
