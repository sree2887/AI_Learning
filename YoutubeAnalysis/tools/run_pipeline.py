"""
run_pipeline.py
Orchestrates the full YouTube trend analysis pipeline.
Calls all tools in sequence via subprocess.

Usage:
    python tools/run_pipeline.py                  # Full run
    python tools/run_pipeline.py --skip-fetch     # Skip API calls, reuse .tmp/ data
    python tools/run_pipeline.py --skip-email     # Run everything but don't send email

Flags:
    --skip-fetch   Skips fetch_trending_videos, fetch_channel_stats, fetch_video_details.
                   Use when you've already fetched data today and want to re-run analysis
                   without burning API quota.
    --skip-email   Runs analysis, charts, and deck building but does not send the email.
                   Useful for testing output before delivery.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
TMP_DIR = PROJECT_ROOT / ".tmp"
OUTPUT_DIR = TMP_DIR / "output"

PYTHON = sys.executable  # Use the same Python that launched this script


def run(label: str, args: list) -> None:
    """Run a subprocess command, print output, and exit on failure."""
    print(f"\n{'-'*60}")
    print(f"  STEP: {label}")
    print(f"{'-'*60}")

    result = subprocess.run(
        [PYTHON] + [str(a) for a in args],
        cwd=str(PROJECT_ROOT),
        capture_output=False,  # Print output in real time
    )

    if result.returncode != 0:
        print(f"\n[ERROR] Step '{label}' failed with exit code {result.returncode}")
        print("Pipeline halted. Fix the error above and re-run.")
        sys.exit(result.returncode)

    print(f"  [OK] {label} completed")


def find_latest_deck() -> Path | None:
    """Find the most recently created .pptx in the output directory."""
    if not OUTPUT_DIR.exists():
        return None
    decks = sorted(OUTPUT_DIR.glob("youtube_trends_*.pptx"), reverse=True)
    return decks[0] if decks else None


def main():
    parser = argparse.ArgumentParser(
        description="Run the full YouTube trend analysis pipeline"
    )
    parser.add_argument(
        "--skip-fetch", action="store_true",
        help="Skip YouTube API fetch steps (reuse existing .tmp/ raw data)"
    )
    parser.add_argument(
        "--skip-email", action="store_true",
        help="(Deprecated — no longer used)"
    )
    args = parser.parse_args()

    start_time = datetime.now()
    date_str = start_time.strftime("%Y-%m-%d")
    deck_path = OUTPUT_DIR / f"youtube_trends_{date_str}.pptx"

    print(f"\n{'='*60}", flush=True)
    print(f"  YouTube Trend Analyzer — {date_str}")
    if args.skip_fetch:
        print("  Mode: SKIP FETCH (using existing raw data)")
    if args.skip_email:
        print("  Mode: SKIP EMAIL (PDF only)")
    print(f"{'='*60}")

    # ── Phase 1: Data Collection ──────────────────────────────
    if not args.skip_fetch:
        run("Fetch Trending Videos",
            [TOOLS_DIR / "fetch_trending_videos.py", "--max-videos", "200"])

        run("Fetch Channel Stats",
            [TOOLS_DIR / "fetch_channel_stats.py"])

        run("Fetch Video Details",
            [TOOLS_DIR / "fetch_video_details.py", "--videos-per-channel", "5"])
    else:
        print("\n[SKIP] Fetch steps skipped — using existing .tmp/ raw data")

    # ── Phase 2: Analysis ──────────────────────────────────────
    run("Analyze Trends",
        [TOOLS_DIR / "analyze_trends.py"])

    # ── Phase 3: Visualization ─────────────────────────────────
    run("Generate Charts",
        [TOOLS_DIR / "generate_charts.py"])

    # ── Phase 4: Export PDF ────────────────────────────────────
    pdf_path = OUTPUT_DIR / f"youtube_trends_{date_str}.pdf"
    run("Export PDF",
        [TOOLS_DIR / "export_pdf.py", "--output", pdf_path])

    # ── Summary ────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    print(f"\n{'='*60}", flush=True)
    print(f"  Pipeline complete in {elapsed}s")
    print(f"  PDF ready at: {pdf_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
