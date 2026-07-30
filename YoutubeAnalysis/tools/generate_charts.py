"""
generate_charts.py
Renders all chart PNGs to .tmp/charts/ from analyzed_trends.json.
No network calls — fully offline.

Usage:
    python tools/generate_charts.py
    python tools/generate_charts.py --analysis .tmp/analyzed_trends.json --output-dir .tmp/charts/

Output files:
    trending_keywords.png   - Horizontal bar: top 20 keywords by weighted score
    top_videos_table.png    - Table image: top 10 videos with metrics
    channel_comparison.png  - Grouped bar: channel performance comparison
    engagement_analysis.png - Scatter: views vs engagement rate
    content_gaps.png        - Horizontal bar: content opportunity scores
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for file output
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

DEFAULT_ANALYSIS = Path(__file__).parent.parent / ".tmp" / "analyzed_trends.json"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / ".tmp" / "charts"

# Color palette
BG_COLOR = "#1a1a2e"
ACCENT = "#e94560"
ACCENT2 = "#0f3460"
TEXT_COLOR = "#eaeaea"
GRID_COLOR = "#2d2d4e"
COLORS = ["#e94560", "#0f3460", "#16213e", "#533483", "#e8a838",
          "#2ec4b6", "#ff9f1c", "#7b2d8b", "#3a86ff", "#06d6a0"]


def apply_dark_style(fig, ax):
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)
    ax.grid(color=GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.7)


def chart_trending_keywords(data: dict, output_path: Path) -> None:
    keywords = data.get("top_keywords", [])[:20]
    if not keywords:
        print("  Skipping keywords chart: no data")
        return

    labels = [k["keyword"] for k in keywords]
    scores = [k["frequency"] * (k["avg_views"] / 1000) for k in keywords]

    # Normalize scores for color intensity
    max_score = max(scores) or 1
    colors = plt.cm.YlOrRd([s / max_score for s in scores])

    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    bars = ax.barh(labels[::-1], scores[::-1], color=colors[::-1], edgecolor="none", height=0.7)

    apply_dark_style(fig, ax)
    ax.set_xlabel("Weighted Score (frequency × avg views / 1K)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Trending Keywords in AI & Automation", color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=15)

    # Value labels
    for bar, score in zip(bars, scores[::-1]):
        ax.text(bar.get_width() + max_score * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{score:,.0f}", va="center", ha="left", color=TEXT_COLOR, fontsize=8)

    ax.set_xlim(0, max_score * 1.15)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  Saved: {output_path}")


def chart_top_videos_table(data: dict, output_path: Path) -> None:
    videos = data.get("top_videos", [])[:10]
    if not videos:
        print("  Skipping videos table: no data")
        return

    fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.axis("off")

    col_labels = ["#", "Title", "Channel", "Views", "Engagement"]
    rows = []
    for i, v in enumerate(videos, 1):
        title = v["title"][:45] + "…" if len(v["title"]) > 45 else v["title"]
        channel = v["channel"][:20] + "…" if len(v["channel"]) > 20 else v["channel"]
        rows.append([
            str(i),
            title,
            channel,
            f"{v['views']:,}",
            f"{v['engagement_rate']*100:.2f}%",
        ])

    col_widths = [0.04, 0.42, 0.22, 0.16, 0.16]
    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        colWidths=col_widths,
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(GRID_COLOR)
        if row == 0:
            cell.set_facecolor(ACCENT)
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#16213e")
            cell.set_text_props(color=TEXT_COLOR)
        else:
            cell.set_facecolor(BG_COLOR)
            cell.set_text_props(color=TEXT_COLOR)

    ax.set_title("Top 10 Performing Videos by Engagement Rate",
                 color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  Saved: {output_path}")


def chart_channel_comparison(data: dict, output_path: Path) -> None:
    channels = data.get("channel_metrics", [])[:10]
    channels = [c for c in channels if c["avg_views_per_video"] > 0]
    if not channels:
        print("  Skipping channel comparison: no data")
        return

    labels = [c["channel"][:18] for c in channels]
    avg_views = [c["avg_views_per_video"] / 1000 for c in channels]  # in thousands
    engagement = [c["engagement_rate"] * 100 for c in channels]  # as percentage

    x = np.arange(len(labels))
    width = 0.4

    fig, ax1 = plt.subplots(figsize=(14, 7), dpi=150)
    apply_dark_style(fig, ax1)

    bars1 = ax1.bar(x - width / 2, avg_views, width, label="Avg Views (K)",
                    color=ACCENT, alpha=0.9, edgecolor="none")
    ax1.set_ylabel("Avg Views per Video (K)", color=TEXT_COLOR, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=TEXT_COLOR)

    ax2 = ax1.twinx()
    ax2.set_facecolor(BG_COLOR)
    bars2 = ax2.bar(x + width / 2, engagement, width, label="Engagement Rate (%)",
                    color="#0f3460", alpha=0.9, edgecolor="none")
    ax2.set_ylabel("Engagement Rate (%)", color=TEXT_COLOR, fontsize=10)
    ax2.tick_params(axis="y", labelcolor=TEXT_COLOR)
    for spine in ax2.spines.values():
        spine.set_color(GRID_COLOR)

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=35, ha="right", color=TEXT_COLOR, fontsize=9)
    ax1.set_title("Channel Performance Comparison", color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=15)

    legend = fig.legend(handles=[bars1, bars2], labels=["Avg Views (K)", "Engagement Rate (%)"],
                        loc="upper right", facecolor=BG_COLOR, edgecolor=GRID_COLOR,
                        labelcolor=TEXT_COLOR, fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  Saved: {output_path}")


def chart_engagement_analysis(data: dict, output_path: Path) -> None:
    videos = data.get("top_videos", [])
    if not videos:
        print("  Skipping engagement scatter: no data")
        return

    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
    apply_dark_style(fig, ax)

    views = [v["views"] for v in videos]
    engagement = [v["engagement_rate"] * 100 for v in videos]
    likes = [v["likes"] for v in videos]
    channels = [v["channel"] for v in videos]

    # Normalize size
    max_likes = max(likes) or 1
    sizes = [max(30, (l / max_likes) * 400) for l in likes]

    # Color by channel
    unique_channels = list(set(channels))
    color_map = {ch: COLORS[i % len(COLORS)] for i, ch in enumerate(unique_channels)}
    point_colors = [color_map[ch] for ch in channels]

    scatter = ax.scatter(views, engagement, s=sizes, c=point_colors, alpha=0.8, edgecolors="none")

    # Label top points
    for i, v in enumerate(videos[:5]):
        ax.annotate(
            v["title"][:30] + "…" if len(v["title"]) > 30 else v["title"],
            (views[i], engagement[i]),
            textcoords="offset points", xytext=(8, 4),
            fontsize=7, color=TEXT_COLOR, alpha=0.9
        )

    ax.set_xlabel("View Count", color=TEXT_COLOR, fontsize=10)
    ax.set_ylabel("Engagement Rate (%)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Views vs Engagement Rate (bubble size = likes)",
                 color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=15)

    # Channel legend
    handles = [mpatches.Patch(color=color_map[ch], label=ch[:20]) for ch in unique_channels[:8]]
    legend = ax.legend(handles=handles, loc="upper right", facecolor=BG_COLOR,
                       edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  Saved: {output_path}")


def chart_content_gaps(data: dict, output_path: Path) -> None:
    gaps = data.get("content_gaps", [])[:10]
    if not gaps:
        print("  Skipping content gaps chart: no data")
        return

    labels = [g["topic"] for g in gaps]
    scores = [g["opportunity_score"] for g in gaps]

    # Color by score tier
    bar_colors = []
    for s in scores:
        if s >= 70:
            bar_colors.append("#06d6a0")   # green: high opportunity
        elif s >= 40:
            bar_colors.append("#e8a838")   # amber: medium
        else:
            bar_colors.append(ACCENT)      # red: lower

    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
    apply_dark_style(fig, ax)

    bars = ax.barh(labels[::-1], scores[::-1], color=bar_colors[::-1],
                   edgecolor="none", height=0.65)

    for bar, score, gap in zip(bars, scores[::-1], gaps[::-1]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{score}  ({gap['video_count']} videos, {gap['avg_engagement_rate']*100:.1f}% eng)",
                va="center", ha="left", color=TEXT_COLOR, fontsize=8)

    ax.set_xlim(0, 115)
    ax.set_xlabel("Opportunity Score (0–100)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Content Gap Analysis — Opportunity by Topic",
                 color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=15)

    # Legend
    handles = [
        mpatches.Patch(color="#06d6a0", label="High Opportunity (≥70)"),
        mpatches.Patch(color="#e8a838", label="Medium Opportunity (40–69)"),
        mpatches.Patch(color=ACCENT, label="Lower Opportunity (<40)"),
    ]
    ax.legend(handles=handles, loc="lower right", facecolor=BG_COLOR,
              edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  Saved: {output_path}")


def generate_all_charts(analysis_path: Path, output_dir: Path) -> None:
    if not analysis_path.exists():
        print(f"Error: {analysis_path} not found. Run analyze_trends.py first.")
        sys.exit(1)

    with open(analysis_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating charts to {output_dir}...\n")

    chart_trending_keywords(data, output_dir / "trending_keywords.png")
    chart_top_videos_table(data, output_dir / "top_videos_table.png")
    chart_channel_comparison(data, output_dir / "channel_comparison.png")
    chart_engagement_analysis(data, output_dir / "engagement_analysis.png")
    chart_content_gaps(data, output_dir / "content_gaps.png")

    print(f"\nAll charts generated in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate charts from analyzed trend data")
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    generate_all_charts(args.analysis, args.output_dir)


if __name__ == "__main__":
    main()
