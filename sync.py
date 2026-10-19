import json
import requests
from datetime import datetime, timedelta

with open("config.json") as f:
    config = json.load(f)

CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]


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

    return response.json()["access_token"]


def sync_activities():

    with open("data/athletes.json") as f:
        athletes = json.load(f)

    all_activities = []

    after = int(
        (
            datetime.now()
            - timedelta(days=30)
        ).timestamp()
    )

    for athlete in athletes:

        print(
            f"Fetching "
            f"{athlete['firstname']} "
            f"{athlete['lastname']}"
        )

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
                "after": after,
                "per_page": 200
            }
        )

        activities = response.json()

        for activity in activities:

            sport = activity.get(
                "sport_type",
                activity.get("type")
            )

            if sport in ["Walk", "Hike"]:

                all_activities.append({
                    "athlete_id":
                    athlete["athlete_id"],

                    "name":
                    f"{athlete['firstname']} "
                    f"{athlete['lastname']}",

                    "activity_id":
                    activity["id"],

                    "date":
                    activity["start_date_local"],

                    "distance_km":
                    round(
                        activity["distance"]/1000,
                        2
                    ),

                    "moving_minutes":
                    round(
                        activity["moving_time"]/60,
                        1
                    )
                })

    with open(
        "data/activities.json",
        "w"
    ) as f:
        json.dump(
            all_activities,
            f,
            indent=2
        )

    print(
        f"Saved "
        f"{len(all_activities)} activities"
    )


if __name__ == "__main__":
    sync_activities()