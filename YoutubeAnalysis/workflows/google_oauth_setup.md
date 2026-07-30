# Google OAuth Setup — One-Time Guide

This workflow sets up the Google Cloud project and OAuth credentials needed for Gmail sending. **You only need to do this once.**

---

## Prerequisites

- A Google account (the Gmail you want to send reports from)
- Access to [console.cloud.google.com](https://console.cloud.google.com)

---

## Step 1: Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown at the top → **New Project**
3. Name it `YouTubeAnalysis` → click **Create**
4. Make sure this project is selected in the top dropdown

---

## Step 2: Enable Required APIs

1. Go to **APIs & Services > Library**
2. Search for and enable each of these:
   - **YouTube Data API v3** — for fetching video data
   - **Gmail API** — for sending the report email

---

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** → click **Create**
3. Fill in:
   - **App name**: `YouTube Analyzer`
   - **User support email**: your Gmail
   - **Developer contact email**: your Gmail
4. Click **Save and Continue**
5. On the **Scopes** screen — click **Save and Continue** (no changes needed)
6. On the **Test users** screen — click **Add Users**, add your Gmail → **Save and Continue**
7. Click **Back to Dashboard**

---

## Step 4: Create OAuth 2.0 Client ID

1. Go to **APIs & Services > Credentials**
2. Click **+ Create Credentials > OAuth 2.0 Client ID**
3. Application type: **Desktop app**
4. Name: `YouTube Analyzer Local`
5. Click **Create**
6. In the popup — click **Download JSON**
7. Save the file as `credentials.json` in the project root:
   ```
   c:\Users\sreel\Documents\AI_Learning\YoutubeAnalysis\credentials.json
   ```

---

## Step 5: Create YouTube API Key

1. Go to **APIs & Services > Credentials**
2. Click **+ Create Credentials > API Key**
3. Copy the key
4. Click **Edit API Key** (pencil icon):
   - Under **API restrictions** → select **Restrict key** → choose **YouTube Data API v3**
   - Click **Save**
5. Add the key to `.env`:
   ```
   YOUTUBE_API_KEY=your_key_here
   ```

---

## Step 6: Run Authentication

From the project root, run:

```bash
python tools/auth_google.py
```

- A browser window will open
- Sign in with your Gmail account
- You may see **"Google hasn't verified this app"** — click **Advanced > Go to YouTube Analyzer (unsafe)**
- Click **Allow**
- The browser will show "The authentication flow has completed"
- `token.json` will be saved to the project root

---

## Verification

After completing setup, run a quick check:

```bash
# Verify YouTube API key works
python tools/fetch_trending_videos.py --max-videos 10

# Verify Gmail auth works (sends a test email)
python tools/send_email.py --deck .tmp/output/youtube_trends_2026-03-13.pptx --skip-email
```

---

## Re-Authentication

`token.json` automatically refreshes when it expires. If you get an authentication error:

```bash
python tools/auth_google.py
```

This will refresh or re-run the OAuth flow as needed.

---

## Files Created by This Setup

| File | Purpose | In .gitignore? |
|---|---|---|
| `credentials.json` | OAuth client credentials from Google | ✅ Yes |
| `token.json` | Your access/refresh tokens | ✅ Yes |
| `.env` | API keys and email settings | ✅ Yes |

All sensitive files are gitignored — they will never be committed.
