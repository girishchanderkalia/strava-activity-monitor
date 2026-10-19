from datetime import datetime, timedelta
import json
import requests
import base64
import os

TOKEN = os.environ["GITHUB_TOKEN"]
OWNER = os.environ["GITHUB_OWNER"]
REPO = os.environ["GITHUB_REPO"]

def load_challenge():

    url = (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/contents/data/challenge.json"
    )

    r = requests.get(
        url,
        headers={
            "Authorization":
            f"Bearer {TOKEN}"
        }
    )

    data = r.json()

    content = (
        base64.b64decode(
            data["content"]
        )
        .decode()
    )

    challenge = json.loads(content)

    start_date = datetime.strptime(
        challenge["start_date"],
        "%Y-%m-%d"
    )

    if not challenge["end_date"]:

        end_date = (
            start_date
            + timedelta(days=30)
        )

    else:

        end_date = datetime.strptime(
            challenge["end_date"],
            "%Y-%m-%d"
        )

    return (
        challenge["name"],
        start_date,
        end_date
    )
