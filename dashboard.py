from leaderboard import build_leaderboard


def render_dashboard():

    data = build_leaderboard()

    challenge_name = data["challenge_name"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    days_remaining = data["days_remaining"]

    athletes = data["leaderboard"]

    rows = ""

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for idx, athlete in enumerate(athletes):

        rank = (
            medals[idx]
            if idx < 3
            else str(idx + 1)
        )

        rows += f"""
        <tr>
            <td>{rank}</td>
            <td>{athlete['name']}</td>
            <td>{athlete['today_km']}</td>
            <td>{athlete['month_km']}</td>
        </tr>
        """

    participants = len(athletes)

    total_distance = round(
        sum(
            a["month_km"]
            for a in athletes
        ),
        1
    )

    leader = (
        athletes[0]["name"]
        if athletes
        else "N/A"
    )

    html = f"""
    <html>

    <head>

      <title>
        Walking Challenge
      </title>

      <link
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet">

    </head>

    <body class="container mt-4">

      <h1>
        🚶 {challenge_name}
      </h1>

      <p class="text-muted">
        {start_date}
        →
        {end_date}
      </p>

      <div class="row mb-4">

        <div class="col">

            <div class="card">

                <div class="card-body">

                    <h5>
                        🏆 Leader
                    </h5>

                    <h3>
                        {leader}
                    </h3>

                </div>

            </div>

        </div>

        <div class="col">

            <div class="card">

                <div class="card-body">

                    <h5>
                        👥 Participants
                    </h5>

                    <h3>
                        {participants}
                    </h3>

                </div>

            </div>

        </div>

        <div class="col">

            <div class="card">

                <div class="card-body">

                    <h5>
                        🚶 Group KM
                    </h5>

                    <h3>
                        {total_distance}
                    </h3>

                </div>

            </div>

        </div>

        <div class="col">

            <div class="card">

                <div class="card-body">

                    <h5>
                        📅 Days Left
                    </h5>

                    <h3>
                        {days_remaining}
                    </h3>

                </div>

            </div>

        </div>

      </div>

      <table class="table table-striped">

        <thead>

            <tr>

                <th>Rank</th>

                <th>Name</th>

                <th>Today KM</th>

                <th>Challenge KM</th>

            </tr>

        </thead>

        <tbody>

            {rows}

        </tbody>

      </table>

    </body>

    </html>
    """

    return html