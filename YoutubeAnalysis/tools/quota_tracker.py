"""
quota_tracker.py
Tracks daily YouTube Data API v3 unit usage in .tmp/quota_usage.json.
Import this module in any tool that makes YouTube API calls.

YouTube quota resets at midnight Pacific Time (UTC-8 / UTC-7 DST).
Daily limit: 10,000 units.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

QUOTA_FILE = Path(__file__).parent.parent / ".tmp" / "quota_usage.json"
DAILY_LIMIT = 10_000
PACIFIC_OFFSET = timedelta(hours=-8)  # Use standard time; close enough for quota resets


def _get_pacific_date() -> str:
    """Return today's date string in Pacific Time (YYYY-MM-DD)."""
    pacific_now = datetime.now(timezone.utc) + PACIFIC_OFFSET
    return pacific_now.strftime("%Y-%m-%d")


def _load() -> dict:
    """Load quota data, resetting if it's a new Pacific day."""
    today = _get_pacific_date()
    if QUOTA_FILE.exists():
        with open(QUOTA_FILE, "r") as f:
            data = json.load(f)
        if data.get("date") == today:
            return data
    # New day or no file — reset
    return {"date": today, "units_used": 0, "units_limit": DAILY_LIMIT, "calls": []}


def _save(data: dict) -> None:
    QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUOTA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_remaining() -> int:
    """Return remaining API units for today."""
    data = _load()
    return data["units_limit"] - data["units_used"]


def check_budget(units_needed: int) -> None:
    """
    Raise an exception if there aren't enough units remaining.
    Call this BEFORE making any YouTube API requests.
    """
    remaining = get_remaining()
    if units_needed > remaining:
        raise RuntimeError(
            f"YouTube API quota insufficient. Need {units_needed} units, "
            f"only {remaining} remaining today. "
            f"Quota resets at midnight Pacific Time."
        )


def log_usage(tool_name: str, units: int) -> None:
    """
    Record API unit consumption after a successful call.
    Call this AFTER making YouTube API requests.
    """
    data = _load()
    data["units_used"] += units
    data["calls"].append({
        "tool": tool_name,
        "units": units,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    _save(data)
    print(f"[quota] {tool_name} used {units} units. "
          f"Total today: {data['units_used']}/{data['units_limit']}")


def print_status() -> None:
    """Print a human-readable quota status summary."""
    data = _load()
    used = data["units_used"]
    limit = data["units_limit"]
    remaining = limit - used
    print(f"Quota status ({data['date']} Pacific): {used}/{limit} used, {remaining} remaining")
    if data["calls"]:
        print("Calls today:")
        for call in data["calls"]:
            print(f"  {call['timestamp'][:19]}  {call['tool']:35s}  {call['units']} units")


if __name__ == "__main__":
    print_status()
