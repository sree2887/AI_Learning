"""
analyze_trends.py
Pure Python analysis of raw YouTube data — no API calls, no network requests.
Produces analyzed_trends.json which is the central data contract for all downstream tools.

Usage:
    python tools/analyze_trends.py
    python tools/analyze_trends.py --trending .tmp/raw_trending.json \
        --channel-stats .tmp/raw_channel_stats.json \
        --video-details .tmp/raw_video_details.json \
        --output .tmp/analyzed_trends.json
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_TRENDING = Path(__file__).parent.parent / ".tmp" / "raw_trending.json"
DEFAULT_CHANNEL_STATS = Path(__file__).parent.parent / ".tmp" / "raw_channel_stats.json"
DEFAULT_VIDEO_DETAILS = Path(__file__).parent.parent / ".tmp" / "raw_video_details.json"
DEFAULT_OUTPUT = Path(__file__).parent.parent / ".tmp" / "analyzed_trends.json"

# Common words to filter out of keyword analysis
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "this", "that", "was", "are",
    "be", "as", "i", "you", "we", "he", "she", "they", "my", "your", "his",
    "her", "our", "its", "what", "how", "why", "when", "who", "which",
    "will", "can", "do", "did", "has", "have", "had", "not", "no", "new",
    "all", "get", "got", "just", "more", "than", "so", "if", "up", "out",
    "about", "after", "before", "into", "over", "under", "then", "now",
    "use", "using", "used", "make", "made", "let", "vs", "via", "de",
    "full", "best", "top", "first", "last", "one", "two", "three", "also",
    "like", "just", "very", "much", "too", "most", "some", "any", "every",
    "day", "week", "year", "time", "way", "thing", "here", "there",
}

# Topic clusters for content gap analysis
TOPIC_CLUSTERS = {
    "AI Agents": ["agent", "agents", "agentic", "autonomous", "multi-agent", "automate"],
    "Large Language Models": ["llm", "llms", "gpt", "claude", "gemini", "mistral", "language model"],
    "AI Automation": ["automation", "automate", "workflow", "n8n", "zapier", "make", "pipeline"],
    "AI Tools & Apps": ["tool", "tools", "app", "apps", "software", "platform", "saas"],
    "Prompt Engineering": ["prompt", "prompting", "prompts", "chain-of-thought", "reasoning"],
    "AI for Business": ["business", "startup", "entrepreneur", "money", "income", "revenue", "side"],
    "AI Coding": ["code", "coding", "programming", "developer", "github", "cursor", "copilot"],
    "AI Image/Video": ["image", "video", "midjourney", "stable diffusion", "sora", "runway", "generate"],
    "AI News & Updates": ["news", "update", "release", "launch", "announcement", "latest"],
    "AI Safety & Ethics": ["safety", "alignment", "ethics", "risk", "agi", "superintelligence"],
    "Open Source AI": ["open source", "opensource", "open-source", "hugging face", "ollama", "local"],
    "AI Productivity": ["productivity", "workflow", "efficiency", "organize", "notion", "obsidian"],
}


def parse_iso_duration(duration: str) -> int:
    """Convert ISO 8601 duration (PT14M32S) to seconds."""
    if not duration:
        return 0
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def compute_engagement_rate(views: int, likes: int, comments: int) -> float:
    if views == 0:
        return 0.0
    return round((likes + comments) / views, 4)


def extract_keywords(videos: list) -> list:
    """Extract and rank keywords from video titles and tags."""
    keyword_views = defaultdict(list)

    for video in videos:
        views = video.get("view_count", 0)
        title = video.get("title", "").lower()
        tags = [t.lower() for t in video.get("tags", [])]

        # Tokenize title
        words = re.findall(r"[a-z][a-z0-9\-']*[a-z0-9]|[a-z]", title)
        words = [w for w in words if w not in STOPWORDS and len(w) > 2]

        # Also add 2-word phrases from title
        title_words = title.split()
        bigrams = [
            f"{title_words[i]} {title_words[i+1]}"
            for i in range(len(title_words) - 1)
            if title_words[i] not in STOPWORDS and title_words[i+1] not in STOPWORDS
        ]

        for kw in words + tags + bigrams:
            keyword_views[kw].append(views)

    # Compute stats per keyword
    results = []
    for kw, view_list in keyword_views.items():
        if len(view_list) < 2:  # require at least 2 occurrences
            continue
        results.append({
            "keyword": kw,
            "frequency": len(view_list),
            "avg_views": int(sum(view_list) / len(view_list)),
            "total_views": sum(view_list),
        })

    # Sort by frequency × avg_views (weighted score)
    results.sort(key=lambda x: x["frequency"] * x["avg_views"], reverse=True)
    return results[:30]


def score_content_gaps(all_videos: list, keywords: list) -> list:
    """
    Identify content gaps: topics with high engagement on existing videos
    but relatively low video count — opportunity for new content.
    """
    gaps = []
    total_videos = len(all_videos)

    for topic, topic_keywords in TOPIC_CLUSTERS.items():
        matching_videos = [
            v for v in all_videos
            if any(kw in (v.get("title", "") + " ".join(v.get("tags", []))).lower()
                   for kw in topic_keywords)
        ]

        if not matching_videos:
            continue

        avg_engagement = sum(
            compute_engagement_rate(v["view_count"], v["like_count"], v["comment_count"])
            for v in matching_videos
        ) / len(matching_videos)

        avg_views = sum(v["view_count"] for v in matching_videos) / len(matching_videos)
        saturation = len(matching_videos) / max(total_videos, 1)

        # High engagement + low saturation = high opportunity
        opportunity_score = int(min(100, (avg_engagement * 1000 + (1 - saturation) * 50)))

        gaps.append({
            "topic": topic,
            "video_count": len(matching_videos),
            "avg_engagement_rate": round(avg_engagement, 4),
            "avg_views": int(avg_views),
            "opportunity_score": opportunity_score,
            "rationale": (
                f"{len(matching_videos)} videos found, avg {avg_engagement*100:.1f}% engagement rate, "
                f"avg {int(avg_views):,} views"
            ),
        })

    gaps.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return gaps[:10]


def compute_channel_metrics(channel_stats: list, video_details: list) -> list:
    """Compute per-channel performance metrics."""
    channel_videos = defaultdict(list)
    for v in video_details:
        channel_videos[v["channel_title"]].append(v)

    metrics = []
    for ch in channel_stats:
        title = ch["title"]
        ch_videos = channel_videos.get(title, [])

        if not ch_videos:
            avg_views = 0
            avg_engagement = 0.0
            upload_freq = 0.0
        else:
            avg_views = int(sum(v["view_count"] for v in ch_videos) / len(ch_videos))
            avg_engagement = sum(
                compute_engagement_rate(v["view_count"], v["like_count"], v["comment_count"])
                for v in ch_videos
            ) / len(ch_videos)

            # Estimate upload frequency from publish dates
            dates = []
            for v in ch_videos:
                try:
                    dt = datetime.fromisoformat(v["published_at"].replace("Z", "+00:00"))
                    dates.append(dt)
                except Exception:
                    pass

            if len(dates) >= 2:
                dates.sort()
                span_days = (dates[-1] - dates[0]).days or 1
                upload_freq = round(len(dates) / (span_days / 7), 2)
            else:
                upload_freq = 0.0

        metrics.append({
            "channel": title,
            "subscriber_count": ch["subscriber_count"],
            "total_views": ch["view_count"],
            "avg_views_per_video": avg_views,
            "engagement_rate": round(avg_engagement, 4),
            "upload_frequency_per_week": upload_freq,
            "recent_video_count": len(ch_videos),
        })

    metrics.sort(key=lambda x: x["avg_views_per_video"], reverse=True)
    return metrics


def generate_executive_summary(top_keywords: list, top_videos: list,
                                channel_metrics: list, content_gaps: list) -> list:
    """Generate 4-5 plain-language insights from the data."""
    insights = []

    if top_keywords:
        top3 = ", ".join(f'"{k["keyword"]}"' for k in top_keywords[:3])
        insights.append(f"Top trending keywords this week: {top3} — these appear in the highest-view videos.")

    if top_videos:
        best = top_videos[0]
        insights.append(
            f'"{best["title"]}" by {best["channel"]} is the top performing video with '
            f'{best["views"]:,} views and {best["engagement_rate"]*100:.1f}% engagement rate.'
        )

    if channel_metrics:
        top_ch = channel_metrics[0]
        insights.append(
            f'{top_ch["channel"]} leads in average views per video '
            f'({top_ch["avg_views_per_video"]:,} avg), '
            f'uploading ~{top_ch["upload_frequency_per_week"]} videos/week.'
        )

    if content_gaps:
        gap = content_gaps[0]
        insights.append(
            f'Highest content opportunity: "{gap["topic"]}" — '
            f'only {gap["video_count"]} videos tracked but strong engagement '
            f'({gap["avg_engagement_rate"]*100:.1f}% avg). '
            f'Consider creating content here.'
        )

    avg_eng = sum(v["engagement_rate"] for v in top_videos) / max(len(top_videos), 1)
    insights.append(
        f"Average engagement rate across top videos: {avg_eng*100:.1f}%. "
        f"Videos above {avg_eng*100*1.5:.1f}% are significantly outperforming the baseline."
    )

    return insights


def generate_content_ideas(content_gaps: list, top_keywords: list) -> list:
    """Generate actionable content ideas based on gaps and trends."""
    ideas = []
    top_kws = [k["keyword"] for k in top_keywords[:10]]

    for gap in content_gaps[:4]:
        topic = gap["topic"]
        # Match a trending keyword to this topic
        related_kw = next(
            (kw for kw in top_kws
             if any(word in kw for word in topic.lower().split())), None
        )
        if related_kw:
            ideas.append(f"{topic}: \"How to use {related_kw} for [specific use case]\"")
        else:
            ideas.append(f"{topic}: Deep-dive tutorial targeting the {topic.lower()} audience")

    # Add a trending-keyword based idea
    if top_keywords:
        kw = top_keywords[0]["keyword"]
        ideas.append(f"Trending topic breakdown: \"Everything you need to know about {kw} in 2026\"")

    if top_keywords and len(top_keywords) > 1:
        kw1, kw2 = top_keywords[0]["keyword"], top_keywords[1]["keyword"]
        ideas.append(f"Comparison video: \"{kw1} vs {kw2} — which should you use?\"")

    return ideas[:6]


def analyze(trending_path: Path, channel_stats_path: Path,
            video_details_path: Path, output_path: Path) -> None:

    # Load all raw data
    all_videos = []

    if trending_path.exists():
        with open(trending_path, "r", encoding="utf-8") as f:
            trending_data = json.load(f)
        all_videos.extend(trending_data.get("videos", []))
        print(f"Loaded {len(trending_data.get('videos', []))} trending videos")
    else:
        print(f"Warning: {trending_path} not found, skipping trending videos")

    channel_stats = []
    if channel_stats_path.exists():
        with open(channel_stats_path, "r", encoding="utf-8") as f:
            channel_data = json.load(f)
        channel_stats = channel_data.get("channels", [])
        print(f"Loaded {len(channel_stats)} channels")
    else:
        print(f"Warning: {channel_stats_path} not found, skipping channel stats")

    video_details = []
    if video_details_path.exists():
        with open(video_details_path, "r", encoding="utf-8") as f:
            details_data = json.load(f)
        video_details = details_data.get("videos", [])
        all_videos.extend(video_details)
        print(f"Loaded {len(video_details)} channel videos")
    else:
        print(f"Warning: {video_details_path} not found, skipping video details")

    if not all_videos:
        print("Error: No video data found. Run the fetch tools first.")
        sys.exit(1)

    # Deduplicate by video_id
    seen = set()
    unique_videos = []
    for v in all_videos:
        if v["video_id"] not in seen:
            seen.add(v["video_id"])
            unique_videos.append(v)
    print(f"Total unique videos for analysis: {len(unique_videos)}")

    # Run analyses
    print("\nExtracting keywords...")
    top_keywords = extract_keywords(unique_videos)

    print("Ranking top videos by engagement...")
    for v in unique_videos:
        v["engagement_rate"] = compute_engagement_rate(
            v["view_count"], v["like_count"], v["comment_count"]
        )
    top_videos_raw = sorted(unique_videos, key=lambda x: x["engagement_rate"], reverse=True)[:15]
    top_videos = [
        {
            "title": v["title"],
            "channel": v["channel_title"],
            "views": v["view_count"],
            "likes": v["like_count"],
            "comments": v["comment_count"],
            "engagement_rate": v["engagement_rate"],
            "published_at": v.get("published_at", ""),
            "video_url": f"https://youtube.com/watch?v={v['video_id']}",
            "thumbnail_url": v.get("thumbnail_url", ""),
        }
        for v in top_videos_raw
    ]

    print("Computing channel metrics...")
    channel_metrics = compute_channel_metrics(channel_stats, video_details if video_details else unique_videos)

    print("Scoring content gaps...")
    content_gaps = score_content_gaps(unique_videos, top_keywords)

    print("Generating executive summary...")
    executive_summary = generate_executive_summary(top_keywords, top_videos, channel_metrics, content_gaps)
    content_ideas = generate_content_ideas(content_gaps, top_keywords)

    output = {
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "total_videos_analyzed": len(unique_videos),
        "top_keywords": top_keywords[:20],
        "top_videos": top_videos,
        "channel_metrics": channel_metrics[:15],
        "content_gaps": content_gaps,
        "executive_summary": executive_summary,
        "recommended_ideas": content_ideas,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nAnalysis complete. Results saved to {output_path}")
    print(f"  Top keyword: {top_keywords[0]['keyword'] if top_keywords else 'N/A'}")
    print(f"  Top video: {top_videos[0]['title'][:60] if top_videos else 'N/A'}")
    print(f"  Top content gap: {content_gaps[0]['topic'] if content_gaps else 'N/A'}")


def main():
    parser = argparse.ArgumentParser(description="Analyze YouTube trend data")
    parser.add_argument("--trending", type=Path, default=DEFAULT_TRENDING)
    parser.add_argument("--channel-stats", type=Path, default=DEFAULT_CHANNEL_STATS)
    parser.add_argument("--video-details", type=Path, default=DEFAULT_VIDEO_DETAILS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    analyze(args.trending, args.channel_stats, args.video_details, args.output)


if __name__ == "__main__":
    main()
