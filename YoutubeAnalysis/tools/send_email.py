"""
send_email.py
Sends the YouTube trends .pptx as a Gmail attachment with an HTML summary body.

Usage:
    python tools/send_email.py --deck .tmp/output/youtube_trends_2026-03-13.pptx
    python tools/send_email.py --deck .tmp/output/youtube_trends_2026-03-13.pptx \
        --analysis .tmp/analyzed_trends.json

Requires token.json (run auth_google.py first).
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
PROJECT_ROOT = Path(__file__).parent.parent
TOKEN_FILE = PROJECT_ROOT / "token.json"
DEFAULT_ANALYSIS = PROJECT_ROOT / ".tmp" / "analyzed_trends.json"


def get_credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        print("Error: token.json not found. Run auth_google.py first.")
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            print("Error: token.json is invalid or expired. Run auth_google.py to re-authenticate.")
            sys.exit(1)

    return creds


def build_html_body(analysis_path: Path, report_date: str) -> str:
    """Build an HTML email body with top insights from the analysis."""
    insights = []
    top_videos = []
    top_gaps = []

    if analysis_path.exists():
        with open(analysis_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        insights = data.get("executive_summary", [])[:3]
        top_videos = data.get("top_videos", [])[:3]
        top_gaps = data.get("content_gaps", [])[:3]

    # Build insights HTML
    insights_html = "".join(
        f'<li style="margin-bottom:8px;">{ins}</li>' for ins in insights
    ) or "<li>See attached deck for full analysis.</li>"

    # Build top videos HTML
    videos_html = ""
    for v in top_videos:
        videos_html += f"""
        <tr>
            <td style="padding:6px 8px; border-bottom:1px solid #2d2d4e;">{v['title'][:55]}</td>
            <td style="padding:6px 8px; border-bottom:1px solid #2d2d4e;">{v['channel']}</td>
            <td style="padding:6px 8px; border-bottom:1px solid #2d2d4e;">{v['views']:,}</td>
            <td style="padding:6px 8px; border-bottom:1px solid #2d2d4e;">{v['engagement_rate']*100:.2f}%</td>
        </tr>"""

    # Build gaps HTML
    gaps_html = "".join(
        f'<li style="margin-bottom:6px;"><strong>{g["topic"]}</strong> — '
        f'Score: {g["opportunity_score"]}/100 ({g["rationale"]})</li>'
        for g in top_gaps
    ) or "<li>See attached deck for full analysis.</li>"

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; background:#0d0d1a; color:#eaeaea; margin:0; padding:0;">
<div style="max-width:680px; margin:0 auto; padding:0;">

    <!-- Header -->
    <div style="background:#1a1a2e; padding:32px 36px; border-bottom:3px solid #e94560;">
        <h1 style="color:#e94560; font-size:24px; margin:0 0 6px 0;">
            AI &amp; Automation YouTube Trends
        </h1>
        <p style="color:#888; font-size:13px; margin:0;">Weekly Intelligence Report &mdash; {report_date}</p>
    </div>

    <!-- Key Insights -->
    <div style="background:#16213e; padding:28px 36px; border-bottom:1px solid #2d2d4e;">
        <h2 style="color:#e94560; font-size:16px; margin:0 0 16px 0; text-transform:uppercase; letter-spacing:1px;">
            Key Insights
        </h2>
        <ul style="margin:0; padding-left:20px; color:#eaeaea; font-size:13px; line-height:1.7;">
            {insights_html}
        </ul>
    </div>

    <!-- Top Videos -->
    {"" if not top_videos else f'''
    <div style="background:#1a1a2e; padding:28px 36px; border-bottom:1px solid #2d2d4e;">
        <h2 style="color:#e94560; font-size:16px; margin:0 0 16px 0; text-transform:uppercase; letter-spacing:1px;">
            Top Videos This Week
        </h2>
        <table style="width:100%; border-collapse:collapse; font-size:12px; color:#eaeaea;">
            <thead>
                <tr style="background:#0f3460;">
                    <th style="padding:8px; text-align:left;">Title</th>
                    <th style="padding:8px; text-align:left;">Channel</th>
                    <th style="padding:8px; text-align:left;">Views</th>
                    <th style="padding:8px; text-align:left;">Engagement</th>
                </tr>
            </thead>
            <tbody>{videos_html}</tbody>
        </table>
    </div>
    '''}

    <!-- Content Gaps -->
    <div style="background:#16213e; padding:28px 36px; border-bottom:1px solid #2d2d4e;">
        <h2 style="color:#e94560; font-size:16px; margin:0 0 16px 0; text-transform:uppercase; letter-spacing:1px;">
            Top Content Opportunities
        </h2>
        <ul style="margin:0; padding-left:20px; color:#eaeaea; font-size:13px; line-height:1.8;">
            {gaps_html}
        </ul>
    </div>

    <!-- Footer -->
    <div style="background:#0f0f1a; padding:20px 36px; text-align:center;">
        <p style="color:#555; font-size:11px; margin:0;">
            Full analysis attached as YouTube_Trends_{report_date}.pptx<br>
            Generated by YouTube Trend Analyzer &mdash; WAT Framework
        </p>
    </div>

</div>
</body>
</html>
"""


def send_report(deck_path: Path, analysis_path: Path,
                sender: str, recipient: str) -> None:
    if not deck_path.exists():
        print(f"Error: Deck not found at {deck_path}")
        sys.exit(1)

    report_date = datetime.now().strftime("%Y-%m-%d")
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    # Build email
    msg = MIMEMultipart("mixed")
    msg["To"] = recipient
    msg["From"] = sender
    msg["Subject"] = f"AI & Automation YouTube Trends Report — {report_date}"

    # HTML body
    html_body = build_html_body(analysis_path, report_date)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Attach .pptx
    with open(deck_path, "rb") as f:
        pptx_data = f.read()

    attachment = MIMEApplication(pptx_data,
                                  _subtype="vnd.openxmlformats-officedocument.presentationml.presentation")
    attachment.add_header("Content-Disposition", "attachment",
                          filename=f"YouTube_Trends_{report_date}.pptx")
    msg.attach(attachment)

    # Encode and send
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"Email sent successfully to {recipient}")
        print(f"Subject: AI & Automation YouTube Trends Report — {report_date}")
    except HttpError as e:
        print(f"Gmail API error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Send YouTube trends report via Gmail")
    parser.add_argument("--deck", type=Path, required=True,
                        help="Path to the .pptx file to send")
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS,
                        help="Path to analyzed_trends.json for email body content")
    parser.add_argument("--to", type=str, default=os.getenv("RECIPIENT_EMAIL"),
                        help="Recipient email (default: RECIPIENT_EMAIL from .env)")
    parser.add_argument("--from-email", type=str, default=os.getenv("SENDER_EMAIL"),
                        help="Sender email (default: SENDER_EMAIL from .env)")
    args = parser.parse_args()

    if not args.to:
        print("Error: RECIPIENT_EMAIL not set in .env and --to not provided")
        sys.exit(1)
    if not args.from_email:
        print("Error: SENDER_EMAIL not set in .env and --from-email not provided")
        sys.exit(1)

    send_report(args.deck, args.analysis, args.from_email, args.to)


if __name__ == "__main__":
    main()
