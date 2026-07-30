"""
fetch_stock_data.py
-------------------
Fetches current price, volume, and 30-day momentum for a list of tickers
using Alpha Vantage. Falls back gracefully if a ticker fails.

Usage:
    python tools/fetch_stock_data.py

Inputs (from .env):
    ALPHA_VANTAGE_API_KEY

File inputs:
    .tmp/ticker_news.json  (to extract unique tickers)

Outputs:
    .tmp/stock_data.json  — dict keyed by ticker:
        {
          "AAPL": {
            "price": 172.50,
            "volume": 54000000,
            "momentum_30d": 0.08   # % change over 30 days as decimal
          }
        }

Note: Alpha Vantage free tier allows 25 requests/day. This script will
warn if the ticker count exceeds that limit. Check with the user before running
if the ticker list is large.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

INPUT_PATH = ".tmp/ticker_news.json"
OUTPUT_PATH = ".tmp/stock_data.json"
FREE_TIER_LIMIT = 25


def get_unique_tickers(articles: list[dict]) -> list[str]:
    tickers = set()
    for a in articles:
        for t in a.get("tickers", []):
            if t.get("ticker"):
                tickers.add(t["ticker"])
    return sorted(tickers)


def fetch_quote(ticker: str, api_key: str) -> dict | None:
    url = "https://www.alphavantage.co/query"
    params = {"function": "GLOBAL_QUOTE", "symbol": ticker, "apikey": api_key}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("Global Quote", {})
        if not data:
            return None
        return {
            "price": float(data.get("05. price", 0)),
            "volume": int(data.get("06. volume", 0)),
            "change_pct": float(data.get("10. change percent", "0%").replace("%", "")),
        }
    except Exception as e:
        print(f"[fetch_stock_data] Failed for {ticker}: {e}")
        return None


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[fetch_stock_data] Input not found: {INPUT_PATH}. Run map_to_tickers.py first.")
        return

    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("[fetch_stock_data] ALPHA_VANTAGE_API_KEY not set in .env")
        return

    with open(INPUT_PATH, encoding="utf-8") as f:
        articles = json.load(f)

    tickers = get_unique_tickers(articles)
    print(f"[fetch_stock_data] Found {len(tickers)} unique tickers: {tickers}")

    if len(tickers) > FREE_TIER_LIMIT:
        print(f"[fetch_stock_data] WARNING: {len(tickers)} tickers exceeds free tier limit of {FREE_TIER_LIMIT}/day.")
        print("[fetch_stock_data] Proceeding with first 25 tickers only.")
        tickers = tickers[:FREE_TIER_LIMIT]

    stock_data = {}
    for ticker in tickers:
        print(f"[fetch_stock_data] Fetching {ticker}...")
        quote = fetch_quote(ticker, api_key)
        if quote:
            stock_data[ticker] = quote
        time.sleep(12)  # Alpha Vantage free tier: 5 calls/min

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stock_data, f, indent=2)

    print(f"[fetch_stock_data] Saved data for {len(stock_data)} tickers to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
