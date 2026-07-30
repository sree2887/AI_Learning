"""
score_stocks.py
---------------
Aggregates news sentiment signals and stock data into a composite buy score
for each ticker. Applies the scoring logic defined in CLAUDE.md.

Scoring weights:
    1. News sentiment (impact_score)   — 40%
    2. Event type (relevance_score)    — 20%
    3. Recency                         — 20%
    4. Price momentum (change_pct)     — 20%

Usage:
    python tools/score_stocks.py

File inputs:
    .tmp/ticker_news.json
    .tmp/stock_data.json

Outputs:
    .tmp/scored_stocks.json  — list of dicts sorted by composite_score desc:
        ticker, company, composite_score, sentiment, key_news, source, url,
        impact_reason, price, volume, change_pct, hype_flag
"""

import os
import json
from datetime import datetime, timezone
from collections import defaultdict

INPUT_NEWS = ".tmp/ticker_news.json"
INPUT_STOCKS = ".tmp/stock_data.json"
OUTPUT_PATH = ".tmp/scored_stocks.json"


def recency_weight(published_at: str) -> float:
    """Returns 1.0 for articles < 12h old, decaying to 0.1 at 48h+."""
    try:
        from dateutil import parser as dtparser
        pub = dtparser.parse(published_at)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        hours_old = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
        if hours_old < 12:
            return 1.0
        elif hours_old < 24:
            return 0.7
        elif hours_old < 48:
            return 0.4
        else:
            return 0.1
    except Exception:
        return 0.5  # default if date parse fails


def main():
    for path in [INPUT_NEWS, INPUT_STOCKS]:
        if not os.path.exists(path):
            print(f"[score_stocks] Missing input: {path}")
            return

    with open(INPUT_NEWS, encoding="utf-8") as f:
        articles = json.load(f)
    with open(INPUT_STOCKS, encoding="utf-8") as f:
        stock_data = json.load(f)

    # Accumulate signals per ticker
    ticker_signals: dict[str, list[dict]] = defaultdict(list)
    ticker_company: dict[str, str] = {}

    for a in articles:
        for t in a.get("tickers", []):
            ticker = t.get("ticker")
            if not ticker:
                continue
            ticker_company[ticker] = t.get("company", ticker)
            ticker_signals[ticker].append({
                "impact_score": a.get("impact_score", 0.0),
                "relevance_score": a.get("relevance_score", 0.0),
                "published_at": a.get("published_at", ""),
                "sentiment": a.get("sentiment", "neutral"),
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "url": a.get("url", ""),
                "impact_reason": a.get("impact_reason", ""),
            })

    scored = []
    for ticker, signals in ticker_signals.items():
        sd = stock_data.get(ticker, {})

        # Weighted aggregate
        sentiment_score = sum(s["impact_score"] * recency_weight(s["published_at"]) for s in signals) / len(signals)
        relevance_score = sum(s["relevance_score"] for s in signals) / len(signals)
        momentum_score = min(max(sd.get("change_pct", 0) / 10, -1.0), 1.0)  # normalize % to -1..1

        composite = (
            sentiment_score * 0.40 +
            relevance_score * 0.20 +
            recency_weight(signals[0]["published_at"]) * 0.20 +
            momentum_score * 0.20
        )

        # Flag if score is high but based only on many articles with low relevance (hype signal)
        avg_relevance = relevance_score
        hype_flag = composite > 0.5 and avg_relevance < 0.3

        # Pick the most impactful article as the key driver
        key = max(signals, key=lambda s: abs(s["impact_score"]))

        scored.append({
            "ticker": ticker,
            "company": ticker_company.get(ticker, ticker),
            "composite_score": round(composite, 4),
            "sentiment": key["sentiment"],
            "key_news": key["title"],
            "source": key["source"],
            "url": key["url"],
            "impact_reason": key["impact_reason"],
            "price": sd.get("price"),
            "volume": sd.get("volume"),
            "change_pct": sd.get("change_pct"),
            "article_count": len(signals),
            "hype_flag": hype_flag,
        })

    scored.sort(key=lambda x: x["composite_score"], reverse=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)

    print(f"[score_stocks] Scored {len(scored)} tickers. Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
