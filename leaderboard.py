from github_storage import (
    load_athletes,
    load_challenge
)

import requests
import os

from datetime import datetime, timedelta

CLIENT_ID = os.environ.get(
    "STRAVA_CLIENT_ID"
)

CLIENT_SECRET = os.environ.get(
    "STRAVA_CLIENT_SECRET"
)


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

    challenge = load_challenge()

    challenge_name = challenge["name"]

    start_date = datetime.strptime(
        challenge["start_date"],
        "%Y-%m-%d"
    )

    if challenge["end_date"]:

        end_date = datetime.strptime(
            challenge["end_date"],
            "%Y-%m-%d"
        )

    else:

        end_date = (
            start_date +
            timedelta(days=30)
        )

    today = datetime.now().date()

    days_remaining = (
        end_date.date() - today
    ).days

    leaderboard = []

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

        response.raise_for_status()

        activities = response.json()

        today_km = 0

        challenge_km = 0

        for activity in activities:

            sport = activity.get(
                "sport_type",
                activity.get("type")
            )

            if sport not in [
                "Walk",
                "Hike"
            ]:
                continue

            activity_date = datetime.fromisoformat(
                activity["start_date_local"]
                .replace(
                    "Z",
                    "+00:00"
                )
            )

            distance_km = (
                activity["distance"] / 1000
            )

            if (
                start_date.date()
                <=
                activity_date.date()
                <=
                end_date.date()
            ):
                challenge_km += distance_km

            if activity_date.date() == today:
                today_km += distance_km

        leaderboard.append(
            {
                "name":
                f"{athlete['firstname']} "
                f"{athlete['lastname']}",

                "today_km":
                round(
                    today_km,
                    1
                ),

                "month_km":
                round(
                    challenge_km,
                    1
                )
            }
        )

    leaderboard.sort(
        key=lambda x: x["month_km"],
        reverse=True
    )

    return {
        "challenge_name":
        challenge_name,

        "start_date":
        start_date.strftime(
            "%d %b %Y"
        ),

        "end_date":
        end_date.strftime(
            "%d %b %Y"
        ),

        "days_remaining":
        days_remaining,

        "leaderboard":
        leaderboard
    }