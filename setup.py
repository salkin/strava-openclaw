#!/usr/bin/env python3
"""Interactive setup wizard for the Strava OpenClaw skill.

Guides the user through creating a Strava API application, completing
the OAuth flow, and saving credentials to ~/.strava_credentials.json.
"""
import json
import os
import sys

try:
    from stravalib.client import Client
except ImportError:
    print("❌ stravalib is not installed. Run: pip install stravalib")
    sys.exit(1)

CREDENTIALS_PATH = os.path.expanduser("~/.strava_credentials.json")

print("🏃 Strava OpenClaw Skill — Setup Wizard")
print("=" * 50)
print()
print("Step 1 — Create a Strava API application")
print("-" * 50)
print("1. Open https://www.strava.com/settings/api in your browser")
print("2. Click 'Create & Manage Your App'")
print("3. Fill in the form:")
print("   • Application Name : OpenClaw Strava")
print("   • Category         : Tool or Analytics")
print("   • Website          : http://localhost")
print("   • Auth Callback Domain: localhost")
print("4. Copy the Client ID and Client Secret shown on the page.")
print()

client_id = input("Enter your Client ID: ").strip()
client_secret = input("Enter your Client Secret: ").strip()

if not client_id or not client_secret:
    print("❌ Both Client ID and Client Secret are required.")
    sys.exit(1)

try:
    int(client_id)
except ValueError:
    print("❌ Client ID must be a number.")
    sys.exit(1)

# Build the OAuth authorization URL
client = Client()
authorize_url = client.authorization_url(
    client_id=int(client_id),
    redirect_uri="http://localhost:8282/authorized",
    scope=["read", "read_all", "activity:read_all", "profile:read_all"],
)

print()
print("Step 2 — Authorize access")
print("-" * 50)
print("Open the URL below in your browser and click 'Authorize':")
print()
print(authorize_url)
print()
print(
    "After authorizing, your browser will be redirected to a URL that"
    " won't load (that's expected)."
)
print("Copy the ENTIRE URL from your browser's address bar and paste it below.")
print()

redirect_url = input("Paste the redirect URL here: ").strip()

if not redirect_url or "code=" not in redirect_url:
    print("❌ Invalid redirect URL — it must contain a 'code=' parameter.")
    sys.exit(1)

print()
print("Step 3 — Exchanging authorization code for tokens…")

try:
    code = client.parse_response_code(redirect_url)
    token_response = client.exchange_code_for_token(
        client_id=int(client_id),
        client_secret=client_secret,
        code=code,
    )

    credentials = {
        "access_token": token_response["access_token"],
        "refresh_token": token_response["refresh_token"],
        "expires_at": token_response["expires_at"],
        "client_id": int(client_id),
        "client_secret": client_secret,
    }

    with open(CREDENTIALS_PATH, "w") as f:
        json.dump(credentials, f, indent=2)
    os.chmod(CREDENTIALS_PATH, 0o600)

    print()
    print("✅ Setup complete!")
    print(f"✅ Credentials saved to {CREDENTIALS_PATH}")
    print()
    print("You can now use the skill:")
    print("  python3 strava_activities.py fetch   # recent activities")
    print("  python3 strava_activities.py stats   # athlete stats")
    print("  python3 strava_activities.py last    # last activity")

except Exception as exc:
    print(f"❌ Setup failed: {exc}")
    sys.exit(1)
