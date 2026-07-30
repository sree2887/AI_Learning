"""
analyze_sentiment.py
--------------------
Uses the Claude API to score each relevant article for sentiment and
projected market impact. Batches articles to minimize API calls.

Usage:
    python tools/analyze_sentiment.py

Inputs (from .env):
    ANTHROPIC_API_KEY

File inputs:
    .tmp/relevant_news.json

Outputs:
    .tmp/sentiment_news.json  — articles with added fields:
        sentiment       ("positive" | "negative" | "neutral")
        impact_score    (float -1.0 to 1.0, negative = bearish, positive = bullish)
        impact_reason   (one-line explanation)
"""

import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

INPUT_PATH = ".tmp/relevant_news.json"
OUTPUT_PATH = ".tmp/sentiment_news.json"

BATCH_SIZE = 10  # articles per Claude call to stay within token limits


def build_prompt(articles: list[dict]) -> str:
    items = ""
    for i, a in enumerate(articles):
        items += f"\n[{i}] Title: {a['title']}\nDescription: {a.get('description', '')}\n"

    return f"""You are a financial analyst. For each news article below, respond with a JSON array.
Each element must have these exact keys:
  - "index": the article number shown in brackets
  - "sentiment": one of "positive", "negative", "neutral"
  - "impact_score": a float from -1.0 (very bearish) to 1.0 (very bullish)
  - "impact_reason": one sentence explaining the market impact

Respond ONLY with the JSON array. No markdown, no explanation.

Articles:
{items}"""


def analyze_batch(client: anthropic.Anthropic, articles: list[dict]) -> list[dict]:
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
        idx = r["index"]
        articles[idx]["sentiment"] = r["sentiment"]
        articles[idx]["impact_score"] = r["impact_score"]
        articles[idx]["impact_reason"] = r["impact_reason"]
    return articles


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[analyze_sentiment] Input not found: {INPUT_PATH}. Run filter_relevance.py first.")
        return

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[analyze_sentiment] ANTHROPIC_API_KEY not set in .env")
        return

    client = anthropic.Anthropic(api_key=api_key)

    with open(INPUT_PATH, encoding="utf-8") as f:
        articles = json.load(f)

    enriched = []
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        print(f"[analyze_sentiment] Processing articles {i}–{i + len(batch) - 1}...")
        try:
            enriched.extend(analyze_batch(client, batch))
        except Exception as e:
            print(f"[analyze_sentiment] Batch failed: {e}")
            # Keep articles without sentiment rather than dropping them
            for a in batch:
                a.setdefault("sentiment", "neutral")
                a.setdefault("impact_score", 0.0)
                a.setdefault("impact_reason", "Analysis unavailable")
            enriched.extend(batch)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"[analyze_sentiment] Saved {len(enriched)} articles to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
