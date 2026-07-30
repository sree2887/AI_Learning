"""
publish_to_sheets.py
--------------------
Writes the top 10 stock recommendations to a Google Sheet.
Creates a new tab named with today's date (YYYY-MM-DD) each run.

Usage:
    python tools/publish_to_sheets.py

Inputs (from .env):
    GOOGLE_SHEET_ID

Auth:
    credentials.json  — Google OAuth client credentials (download from Google Cloud Console)
    token.json        — Auto-generated after first auth flow

File inputs:
    .tmp/top10.json

Outputs:
    Writes to Google Sheet. Prints the sheet URL on success.
"""

import os
import json
from datetime import date

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

INPUT_PATH = ".tmp/top10.json"
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = [
    "Rank", "Ticker", "Company", "Score", "Sentiment",
    "Price", "Change %", "Article Count", "Key News Driver",
    "Source", "Impact Reason", "Risk Note", "URL"
]


def get_credentials() -> Credentials:
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[publish_to_sheets] Input not found: {INPUT_PATH}. Run generate_top10.py first.")
        return

    if not SHEET_ID:
        print("[publish_to_sheets] GOOGLE_SHEET_ID not set in .env")
        return

    if not os.path.exists("credentials.json"):
        print("[publish_to_sheets] credentials.json not found. Download it from Google Cloud Console.")
        return

    with open(INPUT_PATH, encoding="utf-8") as f:
        top10 = json.load(f)

    creds = get_credentials()
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID)

    tab_name = str(date.today())
    try:
        ws = sheet.add_worksheet(title=tab_name, rows=20, cols=len(HEADERS))
    except Exception:
        ws = sheet.worksheet(tab_name)
        ws.clear()

    rows = [HEADERS]
    for s in top10:
        rows.append([
            s.get("rank", ""),
            s.get("ticker", ""),
            s.get("company", ""),
            s.get("composite_score", ""),
            s.get("sentiment", ""),
            s.get("price", ""),
            s.get("change_pct", ""),
            s.get("article_count", ""),
            s.get("key_news", ""),
            s.get("source", ""),
            s.get("impact_reason", ""),
            s.get("risk_note", ""),
            s.get("url", ""),
        ])

    ws.update(rows, "A1")

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={ws.id}"
    print(f"[publish_to_sheets] Published {len(top10)} stocks to tab '{tab_name}'")
    print(f"[publish_to_sheets] Sheet URL: {url}")


if __name__ == "__main__":
    main()
