# YouTube Trend Analysis — SOP

## Objective

Collect YouTube performance data for the AI & automation niche, analyze trends and content gaps, generate a professional slide deck, and deliver it to your inbox via Gmail.

**Output:** An 8-slide .pptx report emailed to `sree2887@gmail.com`

---

## Inputs Required

| Input | Location | Notes |
|---|---|---|
| YouTube API Key | `.env` → `YOUTUBE_API_KEY` | See google_oauth_setup.md |
| Gmail OAuth token | `token.json` | Run `auth_google.py` once to create |
| Sender/Recipient email | `.env` → `SENDER_EMAIL`, `RECIPIENT_EMAIL` | Both set to sree2887@gmail.com |

---

## Pre-Run Checklist

Before running, verify:

- [ ] `.env` has `YOUTUBE_API_KEY`, `SENDER_EMAIL`, `RECIPIENT_EMAIL`
- [ ] `credentials.json` exists in project root
- [ ] `token.json` exists (if not, run `python tools/auth_google.py`)
- [ ] Network connection is available
- [ ] Check quota: `python tools/quota_tracker.py` — should show < 10,000 units used today

---

## Running the Pipeline

### Full run (recommended)

```bash
python tools/run_pipeline.py
```

Runs all 5 phases: fetch → analyze → charts → deck → email.

### Skip API calls (re-run analysis on today's data)

```bash
python tools/run_pipeline.py --skip-fetch
```

Use when you've already fetched data today and want to tweak analysis or charts without using quota.

### Test run (no email)

```bash
python tools/run_pipeline.py --skip-email
```

Generates the deck but doesn't send. Open `.tmp/output/youtube_trends_YYYY-MM-DD.pptx` to review.

---

## Pipeline Steps

### Step 1 — Fetch Trending Videos (~5 units)
```bash
python tools/fetch_trending_videos.py --max-videos 200
```
- Fetches top 200 trending Science & Tech videos (YouTube category ID 28)
- Output: `.tmp/raw_trending.json`

### Step 2 — Fetch Channel Stats (~3 units)
```bash
python tools/fetch_channel_stats.py
```
- Fetches stats for ~25 curated AI/automation channels
- To add/remove channels: edit `AI_CHANNELS` list in `tools/fetch_channel_stats.py`
- Output: `.tmp/raw_channel_stats.json`

### Step 3 — Fetch Video Details (~28 units)
```bash
python tools/fetch_video_details.py --videos-per-channel 5
```
- Fetches 5 most recent videos per channel
- Output: `.tmp/raw_video_details.json`

### Step 4 — Analyze Trends (offline — no quota)
```bash
python tools/analyze_trends.py
```
- Keyword extraction, engagement rate calculation, content gap scoring
- Output: `.tmp/analyzed_trends.json`

### Step 5 — Generate Charts (offline — no quota)
```bash
python tools/generate_charts.py
```
- Renders 5 chart PNGs: keywords, top videos, channel comparison, engagement scatter, content gaps
- Output: `.tmp/charts/*.png`

### Step 6 — Build Slide Deck (offline — no quota)
```bash
python tools/build_slide_deck.py
```
- Assembles 8-slide dark-themed .pptx
- Output: `.tmp/output/youtube_trends_YYYY-MM-DD.pptx`

### Step 7 — Send Email
```bash
python tools/send_email.py --deck .tmp/output/youtube_trends_YYYY-MM-DD.pptx
```
- Sends deck as attachment with HTML summary body
- Delivered to: sree2887@gmail.com

---

## Quota Rules

**Daily limit: 10,000 units. Typical run uses ~36 units.**

| Rule | Reason |
|---|---|
| Never call `search.list` | Costs 100 units per call — destroys quota fast |
| Run once per day maximum | Quota resets at midnight Pacific Time |
| Use `--skip-fetch` if re-running | Avoids burning quota on re-analysis |

Check quota status anytime:
```bash
python tools/quota_tracker.py
```

---

## Output Files

| File | Description |
|---|---|
| `.tmp/raw_trending.json` | Raw trending video data from YouTube |
| `.tmp/raw_channel_stats.json` | Channel subscriber/view stats |
| `.tmp/raw_video_details.json` | Recent videos per channel |
| `.tmp/analyzed_trends.json` | Processed insights (central data contract) |
| `.tmp/charts/*.png` | 5 chart images |
| `.tmp/output/youtube_trends_YYYY-MM-DD.pptx` | Final slide deck |

All `.tmp/` files are regenerated each run and are disposable.

---

## Edge Cases & Fixes

| Issue | Fix |
|---|---|
| `token.json` expired or invalid | Run `python tools/auth_google.py` |
| Quota exhausted | Wait until midnight Pacific, or use `--skip-fetch` |
| Channel returns no data | Remove its ID from `AI_CHANNELS` in `fetch_channel_stats.py` |
| Chart looks wrong | Run `python tools/generate_charts.py` standalone and check `.tmp/charts/` |
| Deck has layout issues | Adjust `Inches()` values in `build_slide_deck.py` |
| Gmail "App not verified" warning | Click Advanced > Proceed — expected for personal OAuth apps |
| Email attachment too large | Reduce `--max-videos` or `--videos-per-channel` |

---

## Customizing the Channel List

Edit `AI_CHANNELS` in [tools/fetch_channel_stats.py](../tools/fetch_channel_stats.py):

```python
AI_CHANNELS = [
    ("CHANNEL_ID_HERE", "Channel Name"),
    ...
]
```

To find a channel ID: go to the channel page, view source, search for `"channelId"`.

---

## Improvement Log

| Date | Change |
|---|---|
| 2026-03-13 | Initial pipeline created |
