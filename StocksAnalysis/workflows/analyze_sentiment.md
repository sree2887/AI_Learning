# Workflow: Analyze Sentiment

## Objective
Use Claude (Haiku model) to score each relevant article for sentiment
(positive/negative/neutral) and projected market impact (-1.0 to 1.0).

## Required Inputs
- `ANTHROPIC_API_KEY` set in `.env`
- `.tmp/relevant_news.json` (from `filter_market_relevance` workflow)

## Steps
1. Run `tools/analyze_sentiment.py`
2. Monitor console for batch progress
3. Verify `.tmp/sentiment_news.json` — every article should have `sentiment`, `impact_score`, `impact_reason`

## Expected Output
`.tmp/sentiment_news.json` — all relevant articles enriched with:
- `sentiment`: "positive" | "negative" | "neutral"
- `impact_score`: float -1.0 (very bearish) to 1.0 (very bullish)
- `impact_reason`: one-sentence explanation

## Cost Awareness
- Uses `claude-haiku-4-5` for efficiency (~$0.25/1M input tokens)
- Batches 10 articles per call; 100 articles ≈ 10 API calls
- Check Anthropic dashboard if you're unsure about remaining credits

## Edge Cases
- **JSON parse error from Claude**: The script catches this and falls back to neutral/0.0 for that batch
- **Rate limit hit**: Add a `time.sleep(2)` between batches in `analyze_sentiment.py`
- **Impact scores all near 0**: May mean articles are genuinely mixed — check a sample manually

## Next Step
→ `workflows/score_stocks.md` (after running `map_to_tickers.py`)
