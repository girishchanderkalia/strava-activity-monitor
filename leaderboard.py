from github_storage import load_athletes
import requests
import os
from datetime import datetime, timezone

CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")


def get_access_token(refresh_token):

    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
    )

    response.raise_for_status()

    return response.json()["access_token"]


def build_leaderboard():

    athletes, _ = load_athletes()

    leaderboard = []

    today = datetime.now().date()

    for athlete in athletes:

        access_token = get_access_token(
            athlete["refresh_token"]
        )

        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={
                "Authorization":
                f"Bearer {access_token}"
            },
            params={
                "per_page": 200
            }
        )

        activities = response.json()

        today_km = 0
        month_km = 0

        current_month = datetime.now().month
        current_year = datetime.now().year

        for activity in activities:

            sport = activity.get(
                "sport_type",
                activity.get("type")
            )

            if sport not in ["Walk", "Hike"]:
                continue

            activity_date = datetime.fromisoformat(
                activity["start_date_local"]
                .replace("Z", "+00:00")
            )

            distance_km = (
                activity["distance"] / 1000
            )

            if (
                activity_date.month ==
                current_month
                and
                activity_date.year ==
                current_year
            ):
                month_km += distance_km

            if activity_date.date() == today:
                today_km += distance_km

        leaderboard.append(
            {
                "name":
                f"{athlete['firstname']} {athlete['lastname']}",
                "today_km":
                round(today_km, 1),
                "month_km":
                round(month_km, 1)
            }
        )

        leaderboard.sort(
            key=lambda x: x["month_km"],
            reverse=True
        )

    return leaderboard