# AI_Learning

A collection of AI learning projects, spanning agent workflow design, a browser game, financial/media data analysis pipelines, and general AI experimentation.

## Projects

### [`Agents_Workflows/`](Agents_Workflows)
A Python starter project (managed with `uv`) for exploring agent workflow design. See its own `LEARNING_PLAN.md` and `PROGRESS.md` for the learning roadmap.

### [`StocksAnalysis/`](StocksAnalysis)
An agentic pipeline that analyzes global news to surface a ranked "top 10 stocks to buy" report. Built on a **Workflows / Agents / Tools (WAT)** architecture:
- `workflows/` — plain-language SOPs for each stage (ingest news → filter relevance → analyze sentiment → score stocks → generate top-10 PDF report)
- `tools/` — the Python scripts that do the actual work (news fetching, sentiment scoring, ticker mapping, stock scoring, PDF generation, Google Sheets publishing)
- Requires API credentials in a local `.env` (not committed)

### [`YoutubeAnalysis/`](YoutubeAnalysis)
A YouTube trend-analysis pipeline, also built on the WAT pattern: fetches trending videos and channel stats, analyzes trends, generates charts and a slide deck, exports a PDF report, and can email it out. Includes a Google OAuth setup workflow for the YouTube Data API.

### [`ai-playground/`](ai-playground)
General experimentation with AI tooling — a memory-augmented chatbot (`chatbot.py`, `memory_system.py`), a PDF reader, and voice assistant scripts.

### [`uigen/`](uigen)
An AI-powered React component generator: users describe a component in a chat interface, Claude generates it via file-system tools, and the result is compiled with Babel and rendered live in an iframe. Next.js + Prisma based; see `uigen/CLAUDE.md` for setup and architecture details.

### [`FirstGame/`](FirstGame)
"Maze Escape" — a small single-file browser maze game (`index.html`).

## Purpose

A personal, ongoing collection of AI-related learning projects rather than a single unified application — each subfolder is largely self-contained.
