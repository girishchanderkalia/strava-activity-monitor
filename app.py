from flask import Flask, redirect, request
import requests
import json
import os
from github_storage import (load_athletes, save_athletes )
from dashboard import render_dashboard

app = Flask(__name__)

import os

CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")


@app.route("/")
def home():

    auth_url = (
        "https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&approval_prompt=force"
        "&scope=read,activity:read_all"
    )

    return f"""
    <h1>Walking Challenge</h1>
    <a href="{auth_url}">
        Connect Strava
    </a>
    """


@app.route("/callback")
def callback():

    code = request.args.get("code")

    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
    )

    data = response.json()

    athlete = data["athlete"]

    record = {
        "athlete_id": athlete["id"],
        "firstname": athlete["firstname"],
        "lastname": athlete["lastname"],
        "refresh_token": data["refresh_token"]
    }


    athletes, sha = load_athletes()

    try:
        athletes, sha = load_athletes()
        existing = next(
            (
                a for a in athletes
                if a["athlete_id"] == record["athlete_id"]
            ),
            None
        )
        if existing:
            existing["refresh_token"] = (record["refresh_token"] )
        else:
            athletes.append(record)

        save_athletes( athletes, sha )
    except Exception as e:
        print(
            f"Failed to save athlete: {e}"
        )

    return f"""
            <h1>✅ Registration Successful</h1>
            <p> Welcome
                <b>{athlete['firstname']} {athlete['lastname']}</b>
            </p>
            <p> You have joined the Walking Challenge. </p>
            <p> You may now close this window. </p>
        """

@app.route("/leaderboard")
def leaderboard():

    return render_dashboard()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
