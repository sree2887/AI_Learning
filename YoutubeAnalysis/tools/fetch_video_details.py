"""
fetch_video_details.py
Fetches recent videos for each channel in raw_channel_stats.json using playlistItems.list,
then enriches them with full statistics via videos.list.

Usage:
    python tools/fetch_video_details.py
    python tools/fetch_video_details.py --channel-stats .tmp/raw_channel_stats.json --videos-per-channel 5

Quota cost: ~1 unit per channel (playlistItems.list) + ~1 unit per 10 videos (videos.list)
Approx total: 25 channels × 1 + 3 batch calls = ~28 units
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

sys.path.insert(0, str(Path(__file__).parent))
import quota_tracker

load_dotenv()

DEFAULT_CHANNEL_STATS = Path(__file__).parent.parent / ".tmp" / "raw_channel_stats.json"
DEFAULT_OUTPUT = Path(__file__).parent.parent / ".tmp" / "raw_video_details.json"


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def fetch_video_details(api_key: str, channel_stats_path: Path,
                        videos_per_channel: int, output_path: Path) -> None:
    if not channel_stats_path.exists():
        print(f"Error: {channel_stats_path} not found. Run fetch_channel_stats.py first.")
        sys.exit(1)

    with open(channel_stats_path, "r", encoding="utf-8") as f:
        channel_data = json.load(f)

    youtube = build("youtube", "v3", developerKey=api_key)
    all_video_ids = []
    channel_video_map = {}  # video_id -> channel_title

    print(f"Collecting recent {videos_per_channel} video IDs per channel...")

    for channel in channel_data["channels"]:
        playlist_id = channel.get("uploads_playlist_id")
        if not playlist_id:
            continue

        quota_tracker.check_budget(1)
        try:
            response = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=videos_per_channel
            ).execute()
        except HttpError as e:
            print(f"  Warning: Could not fetch playlist for {channel['title']}: {e}")
            continue

        quota_tracker.log_usage("fetch_video_details:playlistItems", 1)

        for item in response.get("items", []):
            vid_id = item["snippet"]["resourceId"]["videoId"]
            all_video_ids.append(vid_id)
            channel_video_map[vid_id] = channel["title"]

        print(f"  {channel['title']}: {len(response.get('items', []))} videos queued")

    print(f"\nFetching full stats for {len(all_video_ids)} videos (batched 50 per call)...")

    videos = []
    for batch in chunks(all_video_ids, 50):
        quota_tracker.check_budget(1)
        try:
            response = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch)
            ).execute()
        except HttpError as e:
            print(f"YouTube API error: {e}")
            sys.exit(1)

        quota_tracker.log_usage("fetch_video_details:videos", 1)

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})

            videos.append({
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": channel_video_map.get(item["id"], snippet.get("channelTitle", "")),
                "published_at": snippet.get("publishedAt", ""),
                "description": snippet.get("description", "")[:500],
                "tags": snippet.get("tags", []),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration": content.get("duration", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            })

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_videos": len(videos),
        "videos": videos,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(videos)} channel videos saved to {output_path}")
    quota_tracker.print_status()


def main():
    parser = argparse.ArgumentParser(description="Fetch recent videos for curated AI channels")
    parser.add_argument("--channel-stats", type=Path, default=DEFAULT_CHANNEL_STATS)
    parser.add_argument("--videos-per-channel", type=int, default=5)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("Error: YOUTUBE_API_KEY not set in .env")
        sys.exit(1)

    fetch_video_details(api_key, args.channel_stats, args.videos_per_channel, args.output)


if __name__ == "__main__":
    main()
