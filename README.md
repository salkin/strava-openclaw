# strava-openclaw

An [OpenClaw](https://clawdhub.com) skill that fetches your Strava activities, stats, and workout data.

## Quick Start

```bash
# Install dependencies
pip install stravalib

# Authenticate with Strava (one-time setup)
python3 setup.py

# Fetch recent activities
python3 strava_activities.py fetch

# Show athlete stats (last 4 weeks)
python3 strava_activities.py stats

# Show most recent activity
python3 strava_activities.py last
```

## Requirements

- Python 3.7+
- A free [Strava](https://www.strava.com) account
- A Strava API application (created at <https://www.strava.com/settings/api>)

## Setup

Run the interactive setup wizard:

```bash
python3 setup.py
```

The wizard guides you through creating a Strava API app and completing the OAuth flow. Credentials are saved to `~/.strava_credentials.json`.

## Files

| File | Description |
|------|-------------|
| `SKILL.md` | Skill definition and metadata for OpenClaw |
| `strava_activities.py` | Main script — fetch activities and stats |
| `setup.py` | Interactive OAuth setup wizard |

## OpenClaw Usage

After installing this skill in OpenClaw you can ask:

- "Show my recent Strava activities"
- "What are my Strava stats this week?"
- "What was my last Strava workout?"
- "Fetch my Strava activities"
