"""
auth_google.py
One-time Google OAuth setup. Completes the browser authentication flow
and saves token.json for use by send_email.py.

Run this once before using the pipeline:
    python tools/auth_google.py

If token.json already exists and is valid, exits immediately.
Re-run if you see authentication errors in send_email.py.
"""

import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for Gmail sending
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"


def authenticate() -> None:
    if not CREDENTIALS_FILE.exists():
        print(f"Error: {CREDENTIALS_FILE} not found.")
        print("Download your OAuth credentials from Google Cloud Console:")
        print("  APIs & Services > Credentials > OAuth 2.0 Client IDs > Download JSON")
        print(f"  Save it as: {CREDENTIALS_FILE}")
        sys.exit(1)

    creds = None

    # Check for existing valid token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.valid:
        print(f"Already authenticated. token.json is valid.")
        print(f"Token location: {TOKEN_FILE}")
        return

    # Refresh expired token if possible
    if creds and creds.expired and creds.refresh_token:
        print("Token expired — refreshing...")
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            print("Token refreshed successfully.")
            return
        except Exception as e:
            print(f"Token refresh failed: {e}")
            print("Re-running full OAuth flow...")

    # Full OAuth flow — opens browser
    print("Opening browser for Google OAuth authentication...")
    print("Sign in with the Gmail account you want to send reports from.")
    print("You may see a 'Google hasn't verified this app' warning — click Advanced > Proceed.\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"\nAuthentication successful! token.json saved to {TOKEN_FILE}")
    print("You can now run the full pipeline.")


if __name__ == "__main__":
    authenticate()
