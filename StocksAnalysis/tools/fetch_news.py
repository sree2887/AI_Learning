"""
fetch_news.py
-------------
Fetches global news headlines and articles from NewsAPI and RSS feeds.
Outputs a JSON file to .tmp/raw_news.json

Usage:
    python tools/fetch_news.py [--hours 24]

Inputs (from .env):
    NEWS_API_KEY

Outputs:
    .tmp/raw_news.json  — list of article dicts with keys:
        title, description, content, url, source, published_at
"""

import os
import json
import argparse
from datetime import datetime, timedelta, timezone

import requests
import feedparser
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OUTPUT_PATH = ".tmp/raw_news.json"

# Free RSS feeds covering global financial/general news
RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.reuters.com/reuters/topNews",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",       # CNBC Business
    "https://feeds.bbci.co.uk/news/business/rss.xml",              # BBC Business
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
]


def fetch_from_newsapi(hours: int) -> list[dict]:
    if not NEWS_API_KEY:
        print("[fetch_news] NEWS_API_KEY not set, skipping NewsAPI.")
        return []

    from_dt = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "stock market OR economy OR earnings OR fed OR inflation OR GDP OR trade",
        "language": "en",
        "sortBy": "publishedAt",
        "from": from_dt,
        "pageSize": 100,
        "apiKey": NEWS_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    return [
        {
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "content": a.get("content", ""),
            "url": a.get("url", ""),
            "source": a.get("source", {}).get("name", "NewsAPI"),
            "published_at": a.get("publishedAt", ""),
        }
        for a in articles
    ]


def fetch_from_rss() -> list[dict]:
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                articles.append({
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", ""),
                    "content": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "source": feed.feed.get("title", feed_url),
                    "published_at": entry.get("published", ""),
                })
        except Exception as e:
            print(f"[fetch_news] RSS feed failed ({feed_url}): {e}")
    return articles


def main(hours: int = 24):
    os.makedirs(".tmp", exist_ok=True)
    print(f"[fetch_news] Fetching news from last {hours} hours...")

    articles = fetch_from_newsapi(hours) + fetch_from_rss()

    # Deduplicate by URL
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)

    print(f"[fetch_news] Saved {len(unique)} articles to {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=24, help="How many hours back to fetch news")
    args = parser.parse_args()
    main(args.hours)
