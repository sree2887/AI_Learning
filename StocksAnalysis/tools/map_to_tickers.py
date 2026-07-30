"""
map_to_tickers.py
-----------------
Uses the Claude API to extract company names and map them to stock tickers
from each sentiment-scored article.

Usage:
    python tools/map_to_tickers.py

Inputs (from .env):
    ANTHROPIC_API_KEY

File inputs:
    .tmp/sentiment_news.json

Outputs:
    .tmp/ticker_news.json  — articles with added field:
        tickers: list of {"ticker": "AAPL", "company": "Apple Inc."}
"""

import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

INPUT_PATH = ".tmp/sentiment_news.json"
OUTPUT_PATH = ".tmp/ticker_news.json"

BATCH_SIZE = 15


def build_prompt(articles: list[dict]) -> str:
    items = ""
    for i, a in enumerate(articles):
        items += f"\n[{i}] {a['title']} — {a.get('description', '')}"

    return f"""You are a financial data specialist. For each article, identify all publicly traded companies mentioned and their US stock tickers (NYSE or NASDAQ). If a company is not publicly traded or you are not confident about the ticker, omit it.

Respond ONLY with a JSON array. Each element:
  - "index": article number
  - "tickers": array of {{"ticker": "...", "company": "..."}}

If no publicly traded companies are mentioned, use an empty array for tickers.

Articles:
{items}"""


def map_batch(client: anthropic.Anthropic, articles: list[dict]) -> list[dict]:
    prompt = build_prompt(articles)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    results = json.loads(raw)
    for r in results:
        articles[r["index"]]["tickers"] = r.get("tickers", [])
    return articles


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[map_to_tickers] Input not found: {INPUT_PATH}. Run analyze_sentiment.py first.")
        return

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[map_to_tickers] ANTHROPIC_API_KEY not set in .env")
        return

    client = anthropic.Anthropic(api_key=api_key)

    with open(INPUT_PATH, encoding="utf-8") as f:
        articles = json.load(f)

    enriched = []
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        print(f"[map_to_tickers] Mapping tickers for articles {i}–{i + len(batch) - 1}...")
        try:
            enriched.extend(map_batch(client, batch))
        except Exception as e:
            print(f"[map_to_tickers] Batch failed: {e}")
            for a in batch:
                a.setdefault("tickers", [])
            enriched.extend(batch)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"[map_to_tickers] Saved {len(enriched)} articles to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
