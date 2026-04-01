#!/usr/bin/env python3
"""
One-time OAuth setup script for Google Drive
Run this once to authorize the app and save the token
"""

import os
import sys
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Set up paths directly without importing config to avoid early auth
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

def setup_oauth():
    """Set up OAuth credentials by opening browser for user authorization"""
    print("=" * 60)
    print("Google Drive OAuth Setup")
    print("=" * 60)
    
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"❌ Error: {CLIENT_SECRETS_FILE} not found!")
        print("Please download it from Google Cloud Console first.")
        sys.exit(1)
    
    print(f"✓ Found {CLIENT_SECRETS_FILE}")
    
    try:
        # Create the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)
        
        # This will open a browser window for authorization
        print("\n📱 Opening browser for authorization...")
        print("Please authorize the app when prompted in your browser.")
        print("-" * 60)
        
        creds = flow.run_local_server(port=0, open_browser=True)
        
        # Save the credentials to token.json
        with open(TOKEN_FILE, 'wb') as token_file:
            pickle.dump(creds, token_file)
        
        # Save the token for future use
        print("-" * 60)
        print("✅ Authorization successful!")
        print(f"✓ Token saved to: {TOKEN_FILE}")
        print("\nYou can now run the app normally:")
        print("  python app.py")
        print("\nFuture runs won't need browser authorization!")
        
    except Exception as e:
        print(f"❌ Error during authorization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_oauth()
