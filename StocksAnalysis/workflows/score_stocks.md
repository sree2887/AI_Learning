# Workflow: Score Stocks

## Objective
Map news articles to specific stock tickers, fetch current market data,
and compute a composite buy score for each ticker.

## Required Inputs
- `ANTHROPIC_API_KEY` set in `.env` (for ticker mapping)
- `ALPHA_VANTAGE_API_KEY` set in `.env` (for market data)
- `.tmp/sentiment_news.json` (from `analyze_sentiment` workflow)

## Steps

### Step 1 — Map articles to tickers
1. Run `tools/map_to_tickers.py`
2. Verify `.tmp/ticker_news.json` — articles should have a `tickers` array
3. Check that well-known companies in headlines are getting correct ticker mappings

### Step 2 — Fetch stock market data
1. Check how many unique tickers were found (printed to console)
2. **If > 25 tickers**: Alpha Vantage free tier allows only 25/day. Confirm with user before running.
3. Run `tools/fetch_stock_data.py`
4. Verify `.tmp/stock_data.json` — should have price, volume, change_pct per ticker

### Step 3 — Compute composite scores
1. Run `tools/score_stocks.py`
2. Verify `.tmp/scored_stocks.json` — sorted by `composite_score` descending
3. Scan for `hype_flag: true` entries and note them

## Scoring Weights
| Signal | Weight |
|---|---|
| News sentiment (impact_score) | 40% |
| Article relevance score | 20% |
| Recency of coverage | 20% |
| Price momentum (change_pct) | 20% |

## Edge Cases
- **Ticker wrongly mapped**: Claude occasionally maps companies to wrong tickers — spot-check top 10 results
- **Stock data missing**: If Alpha Vantage returns empty for a ticker, that ticker gets no price/momentum data but still scores on news signals alone
- **Hype flag triggered**: Flag means high score but low fundamental backing — surface this to user in final output

## Next Step
→ `workflows/generate_top10.md`
