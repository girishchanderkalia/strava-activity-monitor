import os
import json
import base64
import requests

TOKEN = os.environ["GITHUB_TOKEN"]
OWNER = os.environ["GITHUB_OWNER"]
REPO = os.environ["GITHUB_REPO"]

FILE_PATH = "data/athletes.json"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}


def load_athletes():

    url = (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/contents/{FILE_PATH}"
    )

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    data = r.json()

    content = base64.b64decode(
        data["content"]
    ).decode()

    return json.loads(content), data["sha"]


def save_athletes(athletes, sha):

    url = (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/contents/{FILE_PATH}"
    )

    content = base64.b64encode(
        json.dumps(
            athletes,
            indent=2
        ).encode()
    ).decode()

    payload = {
        "message": "bot: Update athletes",
        "content": content,
        "sha": sha
    }

    r = requests.put(
        url,
        headers=headers,
        json=payload
    )

    r.raise_for_status()

def load_challenge():

    import json
    import base64

    url = (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/contents/data/challenge.json"
    )

    r = requests.get(
        url,
        headers=headers
    )

    r.raise_for_status()

    data = r.json()

    content = base64.b64decode(
        data["content"]
    ).decode()

    return json.loads(content)