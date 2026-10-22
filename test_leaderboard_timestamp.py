import runpy
import sys
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parent


class LeaderboardTimestampTests(unittest.TestCase):
    def test_manual_and_scheduled_refresh_save_utc_timestamp(self):
        storage = types.ModuleType("github_storage")
        storage.load_athletes = Mock(return_value=([], None))
        storage.load_challenge = Mock(return_value={
            "name": "Test",
            "goal_km": 100,
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        })
        storage.load_leaderboard_cache = Mock()
        storage.save_athletes = Mock()
        storage.save_leaderboard_cache = Mock()

        clock = Mock(wraps=datetime)
        clock.now.return_value = datetime(
            2026, 10, 22, 1, 36, tzinfo=timezone.utc
        )

        with patch.dict(sys.modules, {"github_storage": storage}):
            builder = runpy.run_path(str(ROOT / "leaderboard.py"))
            build_leaderboard = builder["build_leaderboard"]
            leaderboard_module = types.ModuleType("leaderboard")
            leaderboard_module.build_leaderboard = build_leaderboard

            with patch.dict(build_leaderboard.__globals__, {"datetime": clock}):
                with patch.dict(sys.modules, {"leaderboard": leaderboard_module}):
                    for entry in ("manual", "scheduled"):
                        with self.subTest(entry=entry):
                            storage.save_leaderboard_cache.reset_mock()
                            clock.now.reset_mock()

                            if entry == "manual":
                                with patch.dict("os.environ", {"ADMIN_KEY": "test-key"}):
                                    app = runpy.run_path(str(ROOT / "app.py"))["app"]
                                    response = app.test_client().get(
                                        "/refresh?key=test-key"
                                    )
                                self.assertEqual(response.status_code, 200)
                            else:
                                runpy.run_path(str(ROOT / "sync_leaderboard.py"))

                            storage.save_leaderboard_cache.assert_called_once()
                            saved = storage.save_leaderboard_cache.call_args.args[0]
                            self.assertEqual(saved["updated_at"], "22 Oct 2026 01:36")
                            clock.now.assert_called_with(timezone.utc)


if __name__ == "__main__":
    unittest.main()
