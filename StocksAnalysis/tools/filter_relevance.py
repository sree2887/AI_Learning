"""
filter_relevance.py
-------------------
Reads raw articles from .tmp/raw_news.json and scores each for financial
market relevance. Keeps only articles above a relevance threshold.

Usage:
    python tools/filter_relevance.py [--threshold 0.4]

Inputs:
    .tmp/raw_news.json

Outputs:
    .tmp/relevant_news.json  — filtered list of articles with added field:
        relevance_score (float 0–1)
"""

import json
import argparse
import re
import os

INPUT_PATH = ".tmp/raw_news.json"
OUTPUT_PATH = ".tmp/relevant_news.json"

# Keywords that signal market-relevant content
HIGH_WEIGHT_TERMS = [
    "earnings", "revenue", "profit", "loss", "forecast", "guidance",
    "merger", "acquisition", "ipo", "buyback", "dividend",
    "fed", "federal reserve", "interest rate", "inflation", "cpi", "pce",
    "gdp", "unemployment", "jobs report", "nonfarm",
    "tariff", "trade war", "sanctions", "oil price", "crude",
    "nasdaq", "s&p", "dow jones", "russell", "stock market",
    "analyst", "upgrade", "downgrade", "price target", "rating",
    "bankruptcy", "default", "debt ceiling", "treasury",
]

LOW_WEIGHT_TERMS = [
    "economy", "financial", "market", "invest", "shares", "fund",
    "bank", "tech", "sector", "growth", "quarter", "annual",
    "supply chain", "demand", "consumer", "retail", "manufacturing",
]


def score_relevance(text: str) -> float:
    text_lower = text.lower()
    score = 0.0
    for term in HIGH_WEIGHT_TERMS:
        if term in text_lower:
            score += 0.15
    for term in LOW_WEIGHT_TERMS:
        if term in text_lower:
            score += 0.05
    return min(score, 1.0)


def main(threshold: float = 0.4):
    if not os.path.exists(INPUT_PATH):
        print(f"[filter_relevance] Input not found: {INPUT_PATH}. Run fetch_news.py first.")
        return

    with open(INPUT_PATH, encoding="utf-8") as f:
        articles = json.load(f)

    scored = []
    for a in articles:
        combined = f"{a.get('title', '')} {a.get('description', '')} {a.get('content', '')}"
        score = score_relevance(combined)
        if score >= threshold:
            a["relevance_score"] = round(score, 3)
            scored.append(a)

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)

    print(f"[filter_relevance] {len(scored)}/{len(articles)} articles passed threshold {threshold}")
    print(f"[filter_relevance] Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.4)
    args = parser.parse_args()
    main(args.threshold)
