import json
import time

import requests

from config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_TOKEN_URL


def get_valid_token():
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
        activities = response.json()
        for activity in activities:
            # Convert date to more readable format
            date = activity["start_date_local"].split("T")[0]
            time = activity["start_date_local"].split("T")[1][:5]

            # Convert speed to min/km pace if it's a run
            if activity["type"] == "Run":
                # Speed comes in meters/second, convert to min/km
                pace = 16.6667 / activity["average_speed"]  # 16.6667 = 1000/60
                pace_mins = int(pace)
                pace_secs = int((pace - pace_mins) * 60)
                pace_str = f"{pace_mins}:{pace_secs:02d} /km"
            else:
                pace_str = (
                    f"{activity['average_speed'] * 3.6:.1f} km/h"  # Convert to km/h
                )

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

            # Only print if the data exists
            if activity.get("average_heartrate"):
                print(f"\nAverage Heart Rate: {activity['average_heartrate']:.0f} bpm")

            if activity.get("kudos_count"):
                print(f"\nKudos: {activity['kudos_count']}")

            print("\n----------------------------------------")

    else:
        print(f"Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    get_activities()
