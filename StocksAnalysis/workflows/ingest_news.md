# Workflow: Ingest News

## Objective
Fetch global news from the last 24 hours from NewsAPI and RSS feeds and save
a deduplicated raw article list for downstream processing.

## Required Inputs
- `NEWS_API_KEY` set in `.env` (optional but recommended — RSS feeds work without it)
- Internet access

## Steps
1. Run `tools/fetch_news.py --hours 24`
2. Verify `.tmp/raw_news.json` exists and contains articles
3. Spot-check 3–5 articles to confirm titles and dates look correct

## Expected Output
`.tmp/raw_news.json` — list of article dicts with:
- `title`, `description`, `content`, `url`, `source`, `published_at`

## Edge Cases
- **NewsAPI returns 0 results**: Check API key and query terms. RSS feeds will still run.
- **RSS feed times out**: feedparser silently skips failed feeds — check the console for warnings.
- **Duplicate articles**: Deduplication is done by URL; near-duplicate articles with different URLs will both be kept.

## Next Step
→ `workflows/filter_market_relevance.md`
