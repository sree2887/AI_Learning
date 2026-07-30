"""
generate_top10.py
-----------------
Reads scored stocks, applies final filters, and produces a clean top 10
ranked list for publishing.

Usage:
    python tools/generate_top10.py

File inputs:
    .tmp/scored_stocks.json

Outputs:
    .tmp/top10.json  — list of top 10 stocks with all fields plus:
        rank (1–10), risk_note (if hype_flag is set)

    Also prints a formatted summary table to stdout.
"""

import os
import json

INPUT_PATH = ".tmp/scored_stocks.json"
OUTPUT_PATH = ".tmp/top10.json"


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[generate_top10] Input not found: {INPUT_PATH}. Run score_stocks.py first.")
        return

    with open(INPUT_PATH, encoding="utf-8") as f:
        stocks = json.load(f)

    # Only include bullish-leaning stocks (composite_score > 0)
    candidates = [s for s in stocks if s["composite_score"] > 0]

    top10 = candidates[:10]
    for i, s in enumerate(top10):
        s["rank"] = i + 1
        s["risk_note"] = "HIGH RISK: Score driven by hype, low fundamental backing" if s.get("hype_flag") else ""

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(top10, f, indent=2, ensure_ascii=False)

    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'RANK':<5} {'TICKER':<8} {'COMPANY':<25} {'SCORE':<8} {'SENT':<10} {'PRICE':<8} {'CHG%'}")
    print("-" * 80)
    for s in top10:
        price = f"${s['price']:.2f}" if s.get("price") else "N/A"
        chg = f"{s['change_pct']:+.2f}%" if s.get("change_pct") is not None else "N/A"
        flag = " [HYPE WARNING]" if s.get("hype_flag") else ""
        print(f"{s['rank']:<5} {s['ticker']:<8} {s['company'][:24]:<25} {s['composite_score']:<8.4f} {s['sentiment']:<10} {price:<8} {chg}{flag}")
    print("=" * 80)
    print(f"\nGenerated {len(top10)} recommendations. Saved to {OUTPUT_PATH}")
    print("\nNOTE: For research and informational purposes only. Not financial advice.")


if __name__ == "__main__":
    main()
