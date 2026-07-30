# Workflow: Filter Market Relevance

## Objective
Remove articles that have no meaningful connection to financial markets or publicly
traded companies, reducing noise before expensive AI calls.

## Required Inputs
- `.tmp/raw_news.json` (from `ingest_news` workflow)

## Steps
1. Run `tools/filter_relevance.py --threshold 0.4`
2. Check the console output — aim for at least 30 relevant articles
3. If fewer than 30 pass, lower threshold to `0.3` and rerun
4. If more than 300 pass, raise threshold to `0.5` to keep downstream costs low

## Expected Output
`.tmp/relevant_news.json` — filtered articles sorted by `relevance_score` descending

## Edge Cases
- **Too few articles**: Lower threshold or re-run `ingest_news` with `--hours 48`
- **Too many articles**: Raise threshold; the scoring is keyword-based so borderline articles add little signal
- **All sports/entertainment news**: Check that `fetch_news.py` RSS feeds are still live

## Tuning Notes
- The keyword list in `filter_relevance.py` can be extended as new market-moving themes emerge
- Consider adding sector-specific terms (e.g., "semiconductor", "biotech", "EV") if a specific industry is in focus

## Next Step
→ `workflows/analyze_sentiment.md`
