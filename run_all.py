from sync import sync_activities
from excel import update_excel
from github_storage import load_athletes
from sync import sync_activities
from excel import update_excel

athletes, _ = load_athletes()

print(f"Loaded {len(athletes)} athletes from GitHub")

sync_activities()
update_excel()

print("Challenge Updated")
