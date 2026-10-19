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
            <!DOCTYPE html>
            <html>

            <head>
                <title>Walking Challenge</title>

                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1">

                <link
                href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
                rel="stylesheet">

            </head>

            <body class="bg-light">

            <div class="container">

            <div class="row justify-content-center mt-5">

            <div class="col-md-8">

            <div class="card shadow">

            <div class="card-body text-center p-5">

            <h1 class="mb-3">
            🚶 Walking Challenge
            </h1>

            <h4 class="text-muted mb-4">
            Compete with friends and family
            </h4>

            <p class="lead">

            Connect your Strava account and automatically
            participate in the challenge leaderboard.

            </p>

            <div class="my-4">

            ✅ Automatic tracking<br>
            ✅ Live leaderboard<br>
            ✅ Daily champions<br>
            ✅ Streak tracking

            </div>

            <a
            href="{auth_url}"
            class="btn btn-warning btn-lg">

            🔗 Connect Strava

            </a>

            <div class="mt-4 text-muted">

            Your walking activities will be used
            only for challenge rankings.

            </div>

            </div>

            </div>

            </div>

            </div>

            </div>

            </body>

            </html>
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
            <!DOCTYPE html>

            <html>

           <head>

                <title>
                Registration Successful
                </title>

                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1">

                <meta
                    http-equiv="refresh"
                    content="3;url=/leaderboard">

                <link
                href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
                rel="stylesheet">

            </head>

            <body class="bg-light">

            </head>

            <body class="bg-light">

            <div class="container">

            <div class="row justify-content-center mt-5">

            <div class="col-md-7">

            <div class="card shadow">

            <div class="card-body text-center p-5">

            <h1 class="text-success">
            ✅ Registration Successful
            </h1>

            <h3 class="mt-4">

            Welcome

            <br>

            <strong>
            {athlete['firstname']}
            {athlete['lastname']}
            </strong>

            </h3>

            <p class="lead mt-4">

            You have successfully joined
            the Walking Challenge.

            </p>

            <hr>

            <p>

            Your future walking activities
            will now automatically contribute
            to the leaderboard.

            </p>

            <div class="mt-4">

            <a
            href="/leaderboard"
            class="btn btn-primary btn-lg">

            🏆 View Leaderboard

            </a>

            </div>

            <div class="mt-4 text-muted">

             Redirecting to leaderboard in 3 seconds...

            </div>

            </div>

            </div>

            </div>

            </div>

            </div>

            </body>

            </html>
            """

@app.route("/leaderboard")
def leaderboard():

    return render_dashboard()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
