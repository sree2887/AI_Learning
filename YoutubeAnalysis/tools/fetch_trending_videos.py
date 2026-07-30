"""
fetch_trending_videos.py
Fetches the top trending Science & Technology videos from YouTube Data API v3.

Usage:
    python tools/fetch_trending_videos.py
    python tools/fetch_trending_videos.py --max-videos 100 --output .tmp/raw_trending.json

Quota cost: 1 unit per page (50 videos). Default 200 videos = ~4 units.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add project root to path for quota_tracker import
sys.path.insert(0, str(Path(__file__).parent))
import quota_tracker

load_dotenv()

YOUTUBE_CATEGORY_SCIENCE_TECH = "28"
DEFAULT_OUTPUT = Path(__file__).parent.parent / ".tmp" / "raw_trending.json"


def fetch_trending(api_key: str, max_videos: int, output_path: Path) -> None:
    youtube = build("youtube", "v3", developerKey=api_key)

    videos = []
    next_page_token = None
    pages_fetched = 0
    max_pages = (max_videos + 49) // 50  # ceiling division

    print(f"Fetching up to {max_videos} trending Science & Tech videos...")

    while len(videos) < max_videos and pages_fetched < max_pages:
        units_needed = 1
        quota_tracker.check_budget(units_needed)

        kwargs = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "videoCategoryId": YOUTUBE_CATEGORY_SCIENCE_TECH,
            "regionCode": "US",
            "maxResults": min(50, max_videos - len(videos)),
        }
        if next_page_token:
            kwargs["pageToken"] = next_page_token

        try:
            response = youtube.videos().list(**kwargs).execute()
        except HttpError as e:
            print(f"YouTube API error: {e}")
            sys.exit(1)

        quota_tracker.log_usage("fetch_trending_videos", units_needed)
        pages_fetched += 1

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})

            videos.append({
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "description": snippet.get("description", "")[:500],  # truncate
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration": content.get("duration", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            })

        next_page_token = response.get("nextPageToken")
        print(f"  Page {pages_fetched}: fetched {len(response.get('items', []))} videos "
              f"(total so far: {len(videos)})")

        if not next_page_token:
            break

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_videos": len(videos),
        "videos": videos,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(videos)} videos saved to {output_path}")
    quota_tracker.print_status()


def main():
    parser = argparse.ArgumentParser(description="Fetch trending YouTube videos (Science & Tech)")
    parser.add_argument("--max-videos", type=int, default=200,
                        help="Maximum number of videos to fetch (default: 200)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Output JSON file path (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("Error: YOUTUBE_API_KEY not set in .env")
        sys.exit(1)

    fetch_trending(api_key, args.max_videos, args.output)


if __name__ == "__main__":
    main()
