"""
export_pdf.py
Exports the YouTube trends report as a professional PDF using Playwright (headless Chromium)
and a Jinja2 HTML/CSS template.

Usage:
    python tools/export_pdf.py
    python tools/export_pdf.py --analysis .tmp/analyzed_trends.json \
        --charts-dir .tmp/charts/ \
        --output .tmp/output/youtube_trends_2026-03-13.pdf
"""

import argparse
import base64
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

DEFAULT_ANALYSIS = Path(__file__).parent.parent / ".tmp" / "analyzed_trends.json"
DEFAULT_CHARTS_DIR = Path(__file__).parent.parent / ".tmp" / "charts"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / ".tmp" / "output"
TEMPLATES_DIR = Path(__file__).parent / "templates"


def img_to_data_uri(path: Path) -> str:
    """Convert a PNG to a base64 data URI so the HTML is fully self-contained."""
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def build_pdf(analysis_path: Path, charts_dir: Path, output_path: Path) -> None:
    if not analysis_path.exists():
        print(f"Error: {analysis_path} not found. Run analyze_trends.py first.")
        sys.exit(1)

    with open(analysis_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report_date = data.get("report_date", datetime.now().strftime("%Y-%m-%d"))
    print(f"Building PDF for {report_date}...")

    # Embed all chart images as base64 data URIs (no external file references)
    charts = {
        "trending_keywords":  img_to_data_uri(charts_dir / "trending_keywords.png"),
        "top_videos_table":   img_to_data_uri(charts_dir / "top_videos_table.png"),
        "channel_comparison": img_to_data_uri(charts_dir / "channel_comparison.png"),
        "engagement_analysis": img_to_data_uri(charts_dir / "engagement_analysis.png"),
        "content_gaps":       img_to_data_uri(charts_dir / "content_gaps.png"),
    }

    missing = [k for k, v in charts.items() if not v]
    if missing:
        print(f"Warning: Missing charts: {missing} — run generate_charts.py first")

    # Render Jinja2 template to HTML string
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report.html")
    html_content = template.render(
        report_date=report_date,
        executive_summary=data.get("executive_summary", []),
        top_videos=data.get("top_videos", [])[:12],
        channel_metrics=data.get("channel_metrics", []),
        content_gaps=data.get("content_gaps", []),
        recommended_ideas=data.get("recommended_ideas", []),
        top_keywords=data.get("top_keywords", []),
        charts=charts,
    )

    # Write HTML to a temp file so Playwright can load it with file:// URL
    # (needed for Google Fonts @import and any relative paths)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(html_content)
        tmp_path = Path(tmp.name)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Rendering PDF with Playwright (headless Chromium)...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # Load the HTML file
            page.goto(f"file:///{tmp_path.as_posix()}")

            # Wait for fonts and images to load
            page.wait_for_load_state("networkidle")

            # Print to PDF — A4 landscape, no margins (CSS handles all spacing)
            page.pdf(
                path=str(output_path),
                format="A4",
                landscape=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,  # Required to render background colors/images
            )

            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    size_kb = output_path.stat().st_size / 1024
    print(f"\nDone!")
    print(f"  PDF: {output_path}")
    print(f"  Size: {size_kb:.0f} KB  |  Pages: 8")


def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    default_output = DEFAULT_OUTPUT_DIR / f"youtube_trends_{date_str}.pdf"

    parser = argparse.ArgumentParser(description="Export YouTube trends report as PDF")
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--charts-dir", type=Path, default=DEFAULT_CHARTS_DIR)
    parser.add_argument("--output", type=Path, default=default_output)
    args = parser.parse_args()

    build_pdf(args.analysis, args.charts_dir, args.output)


if __name__ == "__main__":
    main()
