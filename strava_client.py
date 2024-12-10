import json
import time
from datetime import datetime

import requests

from config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_TOKEN_URL


def get_valid_token():
    # This function stays the same as before
    with open(".strava_tokens.json", "r") as f:
        tokens = json.load(f)

    if tokens["expires_at"] < time.time():
        response = requests.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "refresh_token": tokens["refresh_token"],
                "grant_type": "refresh_token",
            },
        )

        new_tokens = response.json()
        with open(".strava_tokens.json", "w") as f:
            json.dump(new_tokens, f)
        return new_tokens["access_token"]

    return tokens["access_token"]


def get_activities(limit=10):
    access_token = get_valid_token()

    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"per_page": limit},
    )

    if response.ok:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def display_activity(activity):
    # Convert date to more readable format
    date = activity["start_date_local"].split("T")[0]
    time = activity["start_date_local"].split("T")[1][:5]

    # Convert speed to min/km pace if it's a run
    if activity["type"] == "Run":
        pace = 16.6667 / activity["average_speed"]
        pace_mins = int(pace)
        pace_secs = int((pace - pace_mins) * 60)
        pace_str = f"{pace_mins}:{pace_secs:02d} /km"
    else:
        pace_str = f"{activity['average_speed'] * 3.6:.1f} km/h"

    print(
        f"""
Activity: {activity['name']}
Date: {date} at {time}
Type: {activity['type']}
Distance: {activity['distance']/1000:.2f}km
Duration: {activity['moving_time']/60:.0f} minutes
Pace: {pace_str}
Elevation Gain: {activity['total_elevation_gain']}m""",
        end="",
    )

    if activity.get("average_heartrate"):
        print(f"\nAverage Heart Rate: {activity['average_heartrate']:.0f} bpm")

    if activity.get("kudos_count"):
        print(f"\nKudos: {activity['kudos_count']}")

    print("\n----------------------------------------")


def format_activity_for_receipt(activity):
    # Calculate splits from the activity data
    splits = []
    if activity.get("splits_metric"):
        for split in activity["splits_metric"]:
            splits.append(
                {
                    "km": f"{split['split']:.0f}".zfill(2),  # Zero pad to 2 digits
                    "time": f"{split['moving_time'] // 60}:{(split['moving_time'] % 60):02d}",
                }
            )

    # Format pace
    avg_pace_seconds = (
        activity["moving_time"] / activity["distance"]
    ) * 1000  # Convert to min/km
    avg_pace_mins = int(avg_pace_seconds // 60)
    avg_pace_secs = int(avg_pace_seconds % 60)

    return {
        "date": activity["start_date_local"].split("T")[0],
        "time": activity["start_date_local"].split("T")[1][:5],
        "splits": splits,
        "stats": {
            "distance": f"{activity['distance']/1000:.2f}",
            "moving_time": f"{activity['moving_time']//60}:{(activity['moving_time']%60):02d}",
            "avg_pace": f"{avg_pace_mins}:{avg_pace_secs:02d}",
        },
        "name": activity["name"],
    }


def monitor_new_activities():
    print("Starting Strava activity monitor...")
    print("Checking every 5 minutes for new activities (Press Ctrl+C to stop)")

    latest_activity_id = None

    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            activities = get_activities(limit=1)

            if activities and (
                latest_activity_id is None or activities[0]["id"] != latest_activity_id
            ):
                if latest_activity_id is not None:  # Don't show on first run
                    print("\n🏃 New activity detected! 🏃")
                latest_activity_id = activities[0]["id"]
                display_activity(activities[0])

            print(f"\rLast checked: {current_time}", end="", flush=True)
            time.sleep(300)  # 5 minutes = 300 seconds

    except KeyboardInterrupt:
        print("\nStopping activity monitor")


if __name__ == "__main__":
    monitor_new_activities()
