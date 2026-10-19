from leaderboard import build_leaderboard
from github_storage import save_leaderboard_cache

from datetime import datetime

leaderboard = build_leaderboard()

leaderboard["updated_at"] = (
    datetime.now()
    .strftime("%d %b %Y %H:%M")
)

save_leaderboard_cache(
    leaderboard
)

print(
    "Leaderboard cache updated"
)