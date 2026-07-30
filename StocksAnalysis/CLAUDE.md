# Agent Instructions

## Project Purpose

This project analyzes global news to predict near-term stock market trends and surface the **top 10 stocks to buy** for near-future profit. The pipeline runs end-to-end: news ingestion → relevance filtering → sentiment/impact analysis → stock scoring → ranked output delivered as a PDF report.

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team
- Key workflows for this project:
  - `workflows/ingest_news.md` — fetch and normalize global news from multiple sources
  - `workflows/filter_market_relevance.md` — filter stories by market/sector relevance
  - `workflows/analyze_sentiment.md` — score each story for sentiment and projected market impact
  - `workflows/score_stocks.md` — map news signals to individual tickers and compute a buy score
  - `workflows/generate_top10.md` — rank stocks and generate a PDF report of the top 10

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: To run a full analysis cycle, read `workflows/ingest_news.md`, gather inputs, then call the appropriate tools in sequence through to `workflows/generate_top10.md`

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data operations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast
- Key tools for this project:
  - `tools/fetch_news.py` — pulls headlines and articles from news APIs (e.g. NewsAPI, GDELT, RSS feeds)
  - `tools/filter_relevance.py` — scores articles for financial/market relevance
  - `tools/analyze_sentiment.py` — runs sentiment and impact scoring on filtered articles
  - `tools/map_to_tickers.py` — maps companies/sectors mentioned in news to stock tickers
  - `tools/score_stocks.py` — aggregates signals into a per-ticker buy score
  - `tools/fetch_stock_data.py` — pulls current price, volume, and momentum data
  - `tools/generate_top10.py` — ranks all scored tickers and outputs the top 10
  - `tools/generate_pdf.py` — renders the ranked list as a formatted PDF report in reports/

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
- Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**What goes where:**
- **Deliverables**: Final PDF reports saved to `reports/` — named `top10_YYYY-MM-DD.pdf`
- **Intermediates**: Temporary processing files in `.tmp/` that can be regenerated

**Directory layout:**
```
.tmp/            # Temporary files (scraped data, intermediate exports). Regenerated as needed.
reports/         # Final PDF output — one file per run, named by date
tools/           # Python scripts for deterministic execution
workflows/       # Markdown SOPs defining what to do and how
.env             # API keys and environment variables (NEVER store secrets anywhere else)
```

**Core principle:** Local files are just for processing. `reports/` holds the final deliverables. Everything in `.tmp/` is disposable.

## Stock Scoring Logic

When scoring stocks, consider these signal categories in order of weight:

1. **News sentiment** — positive/negative/neutral tone of relevant articles (highest weight)
2. **Event type** — earnings beats, product launches, regulatory approvals carry more weight than general mentions
3. **Recency** — stories from the last 24–48 hours outweigh older ones
4. **Sector momentum** — broader sector tailwinds amplify individual stock signals
5. **Price/volume confirmation** — prefer stocks where news aligns with recent price/volume action

The final output is a ranked list of the **top 10 buy candidates** with: ticker, company name, composite score, key news driver, and a one-line rationale.

## Important Constraints

- **Never make financial advice claims.** Output is for research and informational purposes only.
- **Always cite the news source** behind each stock's ranking so I can verify the reasoning.
- If a stock scores well purely on hype without fundamental backing, flag it as high-risk.
- If market data APIs cost credits (e.g. Alpha Vantage, Polygon), check with me before running bulk calls.

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

The end goal every run: a fresh, well-reasoned top 10 stock list backed by today's global news.

Stay pragmatic. Stay reliable. Keep learning.
