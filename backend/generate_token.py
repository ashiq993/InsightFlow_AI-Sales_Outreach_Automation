#!/usr/bin/env python3
"""
Google OAuth Token Generator
=============================

This script generates a token.json file for Google API authentication.
Run this BEFORE using Docker, as Docker containers cannot open browsers for OAuth.

Usage:
    python generate_token.py

Requirements:
    - credentials.json must exist in the same directory
    - Install dependencies: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

What it does:
    1. Opens your browser for Google OAuth login
    2. You sign in and grant permissions
    3. Saves token.json to the current directory
    4. You can then use this token with Docker
"""

import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Define the required scopes for Google APIs
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",      # For Gmail API (sending emails)
    "https://www.googleapis.com/auth/spreadsheets",      # For Google Sheets (CRM)
    "https://www.googleapis.com/auth/documents",         # For Google Docs (reports)
    "https://www.googleapis.com/auth/drive",             # For Google Drive (file storage)
]

def check_credentials_file():
    """Check if credentials.json exists"""
    if not os.path.exists("credentials.json"):
        print("❌ ERROR: credentials.json not found!")
        print("\n📋 Steps to get credentials.json:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable these APIs:")
        print("   - Gmail API")
        print("   - Google Drive API")
        print("   - Google Docs API")
        print("   - Google Sheets API")
        print("4. Go to: APIs & Services → Credentials")
        print("5. Create OAuth 2.0 Client ID (Desktop app)")
        print("6. Download the JSON file")
        print("7. Rename it to 'credentials.json'")
        print("8. Place it in this directory")
        print(f"\nCurrent directory: {os.getcwd()}")
        sys.exit(1)

def generate_token():
    """Generate token.json through OAuth flow"""
    print("=" * 60)
    print("🔐 Google OAuth Token Generator")
    print("=" * 60)
    print()
    
    # Check for credentials file
    check_credentials_file()
    
    print("✅ Found credentials.json")
    print("🌐 Starting OAuth authentication flow...")
    print()
    print("📌 What will happen:")
    print("   1. Your browser will open automatically")
    print("   2. Sign in to your Google account")
    print("   3. Review and grant the requested permissions")
    print("   4. Return to this terminal when done")
    print()
    input("Press ENTER to continue...")
    print()
    
    try:
        # Create the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", 
            SCOPES
        )
        
        # Run the local server to handle OAuth callback
        print("🚀 Opening browser for authentication...")
        creds = flow.run_local_server(port=0)
        
        # Save the credentials to token.json
        with open("token.json", "w") as token:
            token.write(creds.to_json())
        
        print()
        print("=" * 60)
        print("✅ SUCCESS! Authentication complete.")
        print("=" * 60)
        print()
        print(f"📂 token.json has been created in: {os.getcwd()}")
        print()
        print("🐳 Next steps:")
        print("   1. Keep token.json in this directory")
        print("   2. Run: docker-compose up --build")
        print("   3. Your application will use this token automatically")
        print()
        print("⏰ Token validity:")
        print("   - Tokens typically last 7 days to 6 months")
        print("   - If expired, run this script again to regenerate")
        print()
        print("=" * 60)
        
    except Exception as e:
        print()
        print("❌ ERROR: Authentication failed!")
        print(f"   Details: {str(e)}")
        print()
        print("🔍 Troubleshooting:")
        print("   1. Make sure you're signed in to Google")
        print("   2. Check if credentials.json is valid")
        print("   3. Ensure the OAuth consent screen is configured")
        print("   4. Try regenerating credentials.json from Google Cloud Console")
        sys.exit(1)

if __name__ == "__main__":
    generate_token()
