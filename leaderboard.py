from github_storage import (
    load_athletes,
    load_challenge
)

import requests
import os

from datetime import datetime, timedelta
from github_storage import (
    load_leaderboard_cache
)

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
    goal_km = challenge["goal_km"]

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

        walk_days = set()

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
                .replace("Z", "+00:00")
            )

            distance_km = (
                activity["distance"] / 1000
            )

            walk_days.add(
                activity_date.date()
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

        streak = 0

        check_day = today

        while check_day in walk_days:

            streak += 1

            check_day -= timedelta(days=1)

        goal_percent = round(
            (
                challenge_km / goal_km
            ) * 100,
            1
        )

        leaderboard.append(
            {
                "name":
                f"{athlete['firstname']} "
                f"{athlete['lastname']}",

                "today_km":
                round(today_km, 1),

                "month_km":
                round(challenge_km, 1),

                "goal_percent":
                goal_percent,

                "streak":
                streak
            }
        )

    leaderboard.sort(
        key=lambda x: x["month_km"],
        reverse=True
    )

    today_champion = None

    today_walkers = [
        a
        for a in leaderboard
        if a["today_km"] > 0
    ]

    if today_walkers:

        today_champion = max(
            today_walkers,
            key=lambda x: x["today_km"]
        )

    streak_leader = None

    active_streaks = [
        a
        for a in leaderboard
        if a["streak"] > 0
    ]

    if active_streaks:

        streak_leader = max(
            active_streaks,
            key=lambda x: x["streak"]
        )

    days_remaining = (
        end_date.date() - today
    ).days

    return {

        "challenge_name":
        challenge_name,

        "goal_km":
        goal_km,

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

        "today_champion":
        today_champion,

        "streak_leader":
        streak_leader,

        "leaderboard":
        leaderboard
    }