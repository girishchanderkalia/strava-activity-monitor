import json

from github_storage import (
    load_leaderboard_cache
)


def render_dashboard():

    data = load_leaderboard_cache()

    updated_at = data.get(
        "updated_at",
        "Unknown"
    )

    athletes = data["leaderboard"]

    challenge_name = data["challenge_name"]
    goal_km = data["goal_km"]

    start_date = data["start_date"]
    end_date = data["end_date"]

    days_remaining = data["days_remaining"]

    today_champion = data["today_champion"]
    streak_leader = data["streak_leader"]

    recent_activities = data.get(
        "recent_activities",
        []
    )

    activity_map = {}

    for activity in recent_activities:

        activity_map.setdefault(
            activity["name"],
            []
        ).append(activity)

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    rows = ""

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

            <td>
                🔥 {athlete['streak']}
            </td>

            <td>

                <div class="progress">

                    <div
                        class="progress-bar"
                        role="progressbar"
                        style="width: {min(athlete['goal_percent'], 100)}%;">

                        {athlete['goal_percent']}%

                    </div>

                </div>

            </td>

            <td>

                <button
                    class="btn btn-sm btn-outline-primary"
                    onclick="showActivity('{athlete['name']}')">

                    👣 Walks

                </button>

            </td>

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

<meta
name="viewport"
content="width=device-width, initial-scale=1">

<link
href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
rel="stylesheet">

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

</head>

<body>

<nav class="navbar navbar-expand-lg navbar-dark bg-success shadow-sm rounded mb-4">

<div class="container-fluid">

<a
class="navbar-brand fw-bold"
href="/leaderboard">

🚶 Walking Challenge

</a>

<div>

<a
class="btn btn-light"
href="/leaderboard">

🏆 Leaderboard

</a>

<a
class="btn btn-warning ms-2"
href="/">

➕ Join

</a>

<a
class="btn btn-secondary ms-2"
href="/admin">

⚙️ Admin

</a>

</div>

</div>

</nav>

<div class="container-fluid px-3 py-3">

<h1>
🚶 {challenge_name}
</h1>

<p class="text-muted">
{start_date} → {end_date}
</p>

<p class="text-muted">
Last Updated:
<strong>{updated_at}</strong>
</p>

<div class="row g-3 mb-4">

    <div class="col-12 col-md-4">

        <div class="card">

            <div class="card-body">

                <h6>🏆 Leader</h6>

                <h3 class="fw-bold">
                {leader}
                </h3>

            </div>

        </div>

    </div>

    <div class="col-6 col-md-2">

        <div class="card">

            <div class="card-body">

                <h6>👥 Participants</h6>

                <h3 class="fw-bold">
                {participants}
                </h3>

            </div>

        </div>

    </div>

    <div class="col-6 col-md-2">

        <div class="card">

            <div class="card-body">

                <h6>🚶 Group KM</h6>

                <h3 class="fw-bold">
                {total_distance}
                </h3>

            </div>

        </div>

    </div>

    <div class="col-6 col-md-2">

        <div class="card">

            <div class="card-body">

                <h6>📅 Days Left</h6>

                <h3 class="fw-bold">
                {days_remaining}
                </h3>

            </div>

        </div>

    </div>

    <div class="col-6 col-md-2">

        <div class="card">

            <div class="card-body">

                <h6>🎯 Goal</h6>

                <h3 class="fw-bold">
                {goal_km}
                </h3>

            </div>

        </div>

    </div>

</div>

<div class="row g-3 mb-4">

    <div class="col-md-6">

        <div class="card border-success">

            <div class="card-body">

                <h5>
                🏆 Today's Champion
                </h5>

                <p>
                {
                    today_champion["name"]
                    if today_champion
                    else "No walks today"
                }
                </p>

                <strong>
                {
                    f"{today_champion['today_km']} km"
                    if today_champion
                    else "-"
                }
                </strong>

            </div>

        </div>

    </div>

    <div class="col-md-6">

        <div class="card border-warning">

            <div class="card-body">

                <h5>
                🔥 Streak Leader
                </h5>

                <p>
                {
                    streak_leader["name"]
                    if streak_leader
                    else "No active streak"
                }
                </p>

                <strong>
                {
                    f"{streak_leader['streak']} days"
                    if streak_leader
                    else "-"
                }
                </strong>

            </div>

        </div>

    </div>

</div>

<div class="table-responsive">

<table class="table table-striped table-hover">

<thead>

<tr>

<th>Rank</th>
<th>Name</th>
<th>Today KM</th>
<th>Challenge KM</th>
<th>🔥 Streak</th>
<th>🎯 Goal %</th>
<th>👣 Walks</th>

</tr>

</thead>

<tbody>

{rows}

</tbody>

</table>

</div>

</div>

<div
class="modal fade"
id="activityModal"
tabindex="-1">

<div class="modal-dialog">

<div class="modal-content">

<div class="modal-header">

<h5
id="activityTitle"
class="modal-title">

👣 Activity History

</h5>

<button
type="button"
class="btn-close"
data-bs-dismiss="modal">

</button>

</div>

<div
id="activityBody"
class="modal-body">

</div>

</div>

</div>

</div>

<script>

const activities =
{json.dumps(activity_map)};

function formatDate(dateString) {{

    const date = new Date(dateString);

    const now = new Date();

    const today =
        now.toDateString();

    const yesterday =
        new Date(
            now.getTime()
            - 86400000
        ).toDateString();

    const activityDay =
        date.toDateString();

    const time =
        date.toLocaleTimeString(
            [],
            {
                hour: '2-digit',
                minute: '2-digit'
            }
        );

    if (activityDay === today) {

        return `Today ${time}`;

    }

    if (activityDay === yesterday) {

        return `Yesterday ${time}`;

    }

    return date.toLocaleDateString(
        'en-GB',
        {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        }
    ) + ` ${time}`;
}}

function showActivity(name) {{

    const athleteActivities =
        activities[name] || [];

    let html = "";

    athleteActivities.forEach(
        activity => {{

            html += `
            <div class="mb-3">

                <strong>
                    ${{activity.title}}
                </strong>

                <br>

                🚶 ${activity.distance.toFixed(1)} km

                <br>

                <small class="text-muted">
                    ${formatDate(activity.date)}
                </small>

            </div>

            <hr>
            `;
        }}
    );

    if (
        athleteActivities.length === 0
    ) {{

        html =
            "No recent activities.";

    }}

    document.getElementById(
        "activityTitle"
    ).innerHTML =
        "👣 " +
        name +
        " Activity History";

    document.getElementById(
        "activityBody"
    ).innerHTML =
        html;

    const modal =
        new bootstrap.Modal(
            document.getElementById(
                "activityModal"
            )
        );

    modal.show();
}}

</script>

</body>

</html>
"""

    return html