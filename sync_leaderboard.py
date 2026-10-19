from leaderboard import build_leaderboard
from github_storage import save_leaderboard_cache

leaderboard = build_leaderboard()

save_leaderboard_cache(
    leaderboard
)

print(
    "Leaderboard cache updated"
)