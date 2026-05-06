#!/usr/bin/env python3
"""Strava skill for OpenClaw — fetch activities and stats."""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from stravalib.client import Client


CREDENTIALS_PATH = os.path.expanduser("~/.strava_credentials.json")
DEFAULT_ACTIVITY_LIMIT = 10


def load_credentials():
    """Load OAuth credentials from the config file."""
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Credentials not found at {CREDENTIALS_PATH}")
        print("Run the setup script first: python3 setup.py")
        sys.exit(1)

    with open(CREDENTIALS_PATH, "r") as f:
        return json.load(f)


def save_credentials(creds):
    """Persist credentials (e.g. after a token refresh)."""
    with open(CREDENTIALS_PATH, "w") as f:
        json.dump(creds, f, indent=2)
    os.chmod(CREDENTIALS_PATH, 0o600)


def get_client():
    """Return an authenticated Strava client, refreshing the token if needed."""
    creds = load_credentials()
    client = Client()

    # Refresh the access token when it has expired
    if time.time() > creds.get("expires_at", 0):
        token_response = client.refresh_access_token(
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
            refresh_token=creds["refresh_token"],
        )
        creds["access_token"] = token_response["access_token"]
        creds["refresh_token"] = token_response["refresh_token"]
        creds["expires_at"] = token_response["expires_at"]
        save_credentials(creds)

    client.access_token = creds["access_token"]
    return client


def refresh_token():
    """Force-refresh the access token using the stored refresh token."""
    creds = load_credentials()
    client = Client()
    token_response = client.refresh_access_token(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        refresh_token=creds["refresh_token"],
    )
    creds["access_token"] = token_response["access_token"]
    creds["refresh_token"] = token_response["refresh_token"]
    creds["expires_at"] = token_response["expires_at"]
    save_credentials(creds)
    expires_dt = datetime.fromtimestamp(creds["expires_at"], tz=timezone.utc)
    print(f"✅ Access token refreshed. Expires at {expires_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")


def meters_to_km(meters):
    """Convert meters to kilometers."""
    return float(meters) / 1000.0 if meters else 0.0


def format_duration(td):
    """Format a timedelta as HH:MM:SS."""
    return str(td).split(".")[0] if td else "N/A"


def fetch_activities(limit=DEFAULT_ACTIVITY_LIMIT):
    """Fetch and display recent activities."""
    client = get_client()
    activities = list(client.get_activities(limit=limit))

    if not activities:
        print("No activities found.")
        return

    print(f"📊 Recent {len(activities)} activities:\n")
    for i, activity in enumerate(activities, 1):
        distance_km = meters_to_km(activity.distance)
        moving_time = format_duration(activity.moving_time)
        date_str = (
            activity.start_date_local.strftime("%Y-%m-%d %H:%M")
            if activity.start_date_local
            else "N/A"
        )
        print(f"{i}. {activity.name}")
        print(
            f"   Type: {activity.type} | Distance: {distance_km:.2f} km"
            f" | Time: {moving_time}"
        )
        print(f"   Date: {date_str}\n")


def show_stats():
    """Display athlete stats (recent run/ride totals)."""
    client = get_client()
    athlete = client.get_athlete()
    full_name = f"{athlete.firstname} {athlete.lastname}".strip()
    print(f"👤 {full_name}")
    if athlete.city and athlete.state:
        print(f"📍 {athlete.city}, {athlete.state}")

    stats = client.get_athlete_stats()

    if stats.recent_run_totals:
        run_km = meters_to_km(stats.recent_run_totals.distance)
        run_time = format_duration(stats.recent_run_totals.moving_time)
        print(f"\n🏃 Recent Running (last 4 weeks):")
        print(f"   Distance: {run_km:.2f} km")
        print(f"   Time: {run_time}")
        print(f"   Runs: {stats.recent_run_totals.count}")

    if stats.recent_ride_totals:
        ride_km = meters_to_km(stats.recent_ride_totals.distance)
        ride_time = format_duration(stats.recent_ride_totals.moving_time)
        print(f"\n🚴 Recent Cycling (last 4 weeks):")
        print(f"   Distance: {ride_km:.2f} km")
        print(f"   Time: {ride_time}")
        print(f"   Rides: {stats.recent_ride_totals.count}")


def show_last_activity():
    """Display details of the most recent activity."""
    client = get_client()
    activities = list(client.get_activities(limit=1))

    if not activities:
        print("No activities found.")
        return

    activity = activities[0]
    distance_km = meters_to_km(activity.distance)
    moving_time = format_duration(activity.moving_time)
    date_str = (
        activity.start_date_local.strftime("%Y-%m-%d %H:%M")
        if activity.start_date_local
        else "N/A"
    )

    print(f"🏃 Last Activity: {activity.name}")
    print(f"   Type: {activity.type}")
    print(f"   Distance: {distance_km:.2f} km")
    print(f"   Moving Time: {moving_time}")
    print(f"   Date: {date_str}")


def fetch_activities_range(after_str, before_str=None):
    """Fetch and display activities within a date range (YYYY-MM-DD)."""
    try:
        after_dt = datetime.strptime(after_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        print(f"❌ Invalid date format for AFTER: {after_str!r}. Use YYYY-MM-DD.")
        sys.exit(1)

    before_dt = None
    if before_str:
        try:
            # Use the start of the day after `before_str` so activities across
            # all timezones on that date are included.
            before_dt = datetime.strptime(before_str, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            ) + timedelta(days=1)
        except ValueError:
            print(
                f"❌ Invalid date format for BEFORE: {before_str!r}. Use YYYY-MM-DD."
            )
            sys.exit(1)

    client = get_client()
    activities = list(
        client.get_activities(after=after_dt, before=before_dt)
    )

    if not activities:
        range_desc = f"from {after_str}"
        if before_str:
            range_desc += f" to {before_str}"
        print(f"No activities found {range_desc}.")
        return

    range_label = after_str
    if before_str:
        range_label += f" → {before_str}"
    print(f"📊 {len(activities)} activities ({range_label}):\n")
    for i, activity in enumerate(activities, 1):
        distance_km = meters_to_km(activity.distance)
        moving_time = format_duration(activity.moving_time)
        date_str = (
            activity.start_date_local.strftime("%Y-%m-%d %H:%M")
            if activity.start_date_local
            else "N/A"
        )
        print(f"{i}. {activity.name}")
        print(
            f"   Type: {activity.type} | Distance: {distance_km:.2f} km"
            f" | Time: {moving_time}"
        )
        print(f"   Date: {date_str}\n")


COMMANDS = {
    "fetch": (fetch_activities, "Fetch recent activities"),
    "stats": (show_stats, "Show athlete stats (last 4 weeks)"),
    "last": (show_last_activity, "Show the most recent activity"),
    "fetch-range": (
        fetch_activities_range,
        "Fetch activities for a date range (requires AFTER date)",
    ),
    "refresh-token": (refresh_token, "Force-refresh the Strava access token"),
}

USAGE = """\
Usage: strava_activities.py <command> [args]

Commands:
  fetch                        Fetch recent activities (default: 10)
  stats                        Show athlete stats for the last 4 weeks
  last                         Show details of the most recent activity
  fetch-range AFTER [BEFORE]   Fetch activities between two dates (YYYY-MM-DD)
  refresh-token                Force-refresh the Strava access token
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command not in COMMANDS:
        print(f"❌ Unknown command: {command!r}")
        print(USAGE)
        sys.exit(1)

    func, _ = COMMANDS[command]
    try:
        if command == "fetch-range":
            if len(sys.argv) < 3:
                print("❌ fetch-range requires an AFTER date (YYYY-MM-DD).")
                print(USAGE)
                sys.exit(1)
            after = sys.argv[2]
            before = sys.argv[3] if len(sys.argv) >= 4 else None
            func(after, before)
        else:
            func()
    except Exception as exc:
        print(f"❌ Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
