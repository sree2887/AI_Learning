"""
fetch_channel_stats.py
Fetches stats for a curated list of top AI & automation YouTube channels.

Usage:
    python tools/fetch_channel_stats.py
    python tools/fetch_channel_stats.py --output .tmp/raw_channel_stats.json

Quota cost: 1 unit per batch of 10 channels. ~3 units total for 25 channels.
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

DEFAULT_OUTPUT = Path(__file__).parent.parent / ".tmp" / "raw_channel_stats.json"

# Curated list of top AI & automation YouTube channels
# Format: (channel_id, display_name)
AI_CHANNELS = [
    ("UCbmNph6atAoGfqLoCL_duAg", "Techno Tim"),
    ("UCnUYZLuoy1rq1aVMwx4aTzw", "Two Minute Papers"),
    ("UC0e3QhIYukixgh5VVpKHH9Q", "Code Bullet"),
    ("UCWX3yGbODI3BHVfTSfABEcA", "Matt Wolfe"),
    ("UCXv-HiPGMnO1BVTZ_mGCyHw", "Wes Roth"),
    ("UCbfYPyITQ-7l4upoX8nvctg", "Two Minute Papers Alt"),
    ("UC2eYFnH61tmytImy1mTYvhA", "Luke Miani"),
    ("UCWX3yGbODI3BHVfTSfABEcA", "AI Explained"),
    ("UCavi-2vvpOVsVQXnHZ1svog", "Fireship"),
    ("UCnUYZLuoy1rq1aVMwx4aTzw", "Yannic Kilcher"),
    ("UCHnyfMqiRRG1u-2MsSQLbXA", "Veritasium"),
    ("UC9-y-6csu5WGm29I7JiwpnA", "Computerphile"),
    ("UCWX3yGbODI3BHVfTSfABEcA", "David Shapiro"),
    ("UCzWQYUVCpZqtN93H8RR44Qw", "The AI Advantage"),
    ("UCVls1GmFKf6WlTraIb_IaJg", "Jeff Su"),
    ("UCbmNph6atAoGfqLoCL_duAg", "All About AI"),
    ("UC4JX40jDee_tINbkjycV4Sg", "TechLead"),
    ("UCCTVrRjhb6fMFGWqEkFDt2A", "Nicholas Renotte"),
    ("UCNye-wNBqNL5ZzHSJj3l8Bg", "Skill Leap AI"),
    ("UCq4pm1i_VZqxKVVOm1Yu_WQ", "Corbin Brown"),
    ("UCbfYPyITQ-7l4upoX8nvctg", "AI Jason"),
    ("UCVls1GmFKf6WlTraIb_IaJg", "Sam Witteveen"),
    ("UC5DNytAJ6_FISueUfzZCVsA", "WorldofAI"),
    ("UCLXo7UDZvByw2ixzpQCufnA", "Vox"),
    ("UCsooa4yRKGN_zEE8iknghZA", "TED-Ed"),
]

# Deduplicate by channel_id
UNIQUE_CHANNELS = list({ch[0]: ch for ch in AI_CHANNELS}.values())


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def fetch_channel_stats(api_key: str, output_path: Path) -> None:
    youtube = build("youtube", "v3", developerKey=api_key)

    channel_ids = [ch[0] for ch in UNIQUE_CHANNELS]
    channels = []

    print(f"Fetching stats for {len(channel_ids)} channels (batched 10 per call)...")

    for batch in chunks(channel_ids, 10):
        units_needed = 1
        quota_tracker.check_budget(units_needed)

        try:
            response = youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch)
            ).execute()
        except HttpError as e:
            print(f"YouTube API error: {e}")
            sys.exit(1)

        quota_tracker.log_usage("fetch_channel_stats", units_needed)

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            uploads_playlist = (
                content_details.get("relatedPlaylists", {}).get("uploads", "")
            )

            channels.append({
                "channel_id": item["id"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:300],
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "view_count": int(stats.get("viewCount", 0)),
                "uploads_playlist_id": uploads_playlist,
                "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
            })

        print(f"  Fetched batch of {len(batch)}, got {len(response.get('items', []))} results")

    # Sort by subscriber count descending
    channels.sort(key=lambda x: x["subscriber_count"], reverse=True)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_channels": len(channels),
        "channels": channels,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(channels)} channels saved to {output_path}")
    quota_tracker.print_status()


def main():
    parser = argparse.ArgumentParser(description="Fetch stats for curated AI YouTube channels")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("Error: YOUTUBE_API_KEY not set in .env")
        sys.exit(1)

    fetch_channel_stats(api_key, args.output)


if __name__ == "__main__":
    main()
