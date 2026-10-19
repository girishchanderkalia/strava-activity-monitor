from github_storage import load_athletes, save_athletes

athletes, sha = load_athletes()

print(athletes)
print(sha)

athletes.append(
    {
        "athlete_id": 999999,
        "firstname": "Test",
        "lastname": "User",
        "refresh_token": "dummy"
    }
)

save_athletes(athletes, sha)

print("Saved")