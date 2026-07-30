# Workflow: Generate Top 10

## Objective
Produce the final ranked list of top 10 stock buy candidates and publish
it to Google Sheets for review.

## Required Inputs
- `.tmp/scored_stocks.json` (from `score_stocks` workflow)

## Steps

### Step 1 — Generate ranked list
1. Run `tools/generate_top10.py`
2. Review the printed table in the console
3. Flag any entries with ⚠ HYPE for manual review before publishing
4. If fewer than 10 stocks have `composite_score > 0`, re-run the pipeline with `--hours 48` to pull more news

### Step 2 — Generate PDF report
1. Run `tools/generate_pdf.py`
2. Verify the file appears in `reports/top10_YYYY-MM-DD.pdf`
3. Open the PDF and review the summary table and detail cards

## Expected Output

**Console**: formatted table with rank, ticker, company, score, sentiment, price, change %

**PDF** (`reports/top10_YYYY-MM-DD.pdf`):
- Summary table with all 10 stocks
- Detail card per stock: sentiment, score, key news driver, source, impact reason, risk note

## Interpreting Results
- **Score > 0.5**: Strong bullish signal — multiple positive news drivers with price confirmation
- **Score 0.2–0.5**: Moderate signal — worth watching
- **Score < 0.2**: Weak signal — likely filtered out before top 10
- **Risk Note populated**: Treat with caution — score may be inflated by hype

## Important Disclaimer
All output is for **research and informational purposes only**.
Not financial advice. Always verify news sources before making any investment decision.

## Cadence
Run this full pipeline daily (or on-demand) to get a fresh top 10 based on current news.
Each run produces a new dated PDF in `reports/` — old reports are preserved automatically.
