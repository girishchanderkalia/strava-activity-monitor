import runpy
import sys
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch

import requests


ROOT = Path(__file__).resolve().parent
NOW = datetime(2026, 10, 23, 4, 0, tzinfo=timezone.utc)


def cache_data(updated=NOW):
    return {
        "updated_at": updated.strftime("%d %b %Y %H:%M"),
        "updated_at_utc": updated.isoformat(),
        "challenge_name": "Test challenge",
        "individual_goal": 100,
        "start_date": "01 Oct 2026",
        "end_date": "31 Oct 2026",
        "days_remaining": 8,
        "today_champion": None,
        "streak_leader": None,
        "leaderboard": [],
        "recent_activities": [],
    }


class LeaderboardCacheTests(unittest.TestCase):
    def setUp(self):
        self.storage = types.ModuleType("github_storage")
        self.storage.load_leaderboard_cache = Mock(return_value=cache_data())
        self.storage.save_leaderboard_cache = Mock()
        self.storage.load_athletes = Mock()
        self.storage.save_athletes = Mock()
        self.storage.load_challenge = Mock()
        self.builder = types.ModuleType("leaderboard")
        self.builder.build_leaderboard = Mock(return_value=cache_data())
        self.modules = patch.dict(sys.modules, {
            "github_storage": self.storage,
            "leaderboard": self.builder,
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)
        service = runpy.run_path(str(ROOT / "leaderboard_cache.py"))
        self.service = types.ModuleType("leaderboard_cache")
        self.service.__dict__.update(service)
        self.clock = Mock(wraps=datetime)
        self.clock.now.return_value = NOW
        clock_patch = patch.dict(
            self.service.get_leaderboard.__globals__, {"datetime": self.clock}
        )
        clock_patch.start()
        self.addCleanup(clock_patch.stop)

    def client(self):
        with patch.dict(sys.modules, {"leaderboard_cache": self.service}):
            with patch.dict("os.environ", {"ADMIN_KEY": "test-key"}):
                app = runpy.run_path(str(ROOT / "app.py"))["app"]
        return app.test_client()

    def test_fresh_cache_does_not_fetch_or_save(self):
        self.storage.load_leaderboard_cache.return_value = cache_data(
            NOW - timedelta(minutes=14, seconds=59)
        )
        result = self.service.get_leaderboard()
        self.assertEqual(result.state, "fresh")
        self.builder.build_leaderboard.assert_not_called()
        self.storage.save_leaderboard_cache.assert_not_called()

    def test_exactly_fifteen_minutes_triggers_refresh_and_persists(self):
        self.storage.load_leaderboard_cache.return_value = cache_data(
            NOW - timedelta(minutes=15)
        )
        result = self.service.get_leaderboard()
        self.assertEqual(result.state, "refreshed")
        self.assertEqual(result.data, cache_data())
        self.builder.build_leaderboard.assert_called_once_with()
        self.storage.save_leaderboard_cache.assert_called_once_with(result.data)

    def test_legacy_timestamp_is_utc_and_obeys_boundary(self):
        for minutes, expected in ((14, False), (15, True)):
            with self.subTest(minutes=minutes):
                data = cache_data(NOW - timedelta(minutes=minutes))
                del data["updated_at_utc"]
                self.assertEqual(self.service.is_cache_stale(data, NOW), expected)

    def test_missing_invalid_naive_and_future_timestamps_are_stale(self):
        for data in (
            {},
            {"updated_at": "invalid"},
            {"updated_at_utc": None},
            {"updated_at_utc": "2026-10-23T04:00:00"},
            cache_data(NOW + timedelta(minutes=1)),
        ):
            with self.subTest(data=data):
                self.assertTrue(self.service.is_cache_stale(data, NOW))

    def test_missing_cache_is_built(self):
        response = requests.Response()
        response.status_code = 404
        self.storage.load_leaderboard_cache.side_effect = requests.HTTPError(
            response=response
        )
        result = self.service.get_leaderboard()
        self.assertEqual(result.state, "refreshed")
        self.storage.save_leaderboard_cache.assert_called_once_with(result.data)

    def test_load_failure_is_not_treated_as_missing_cache(self):
        response = requests.Response()
        response.status_code = 403
        self.storage.load_leaderboard_cache.side_effect = requests.HTTPError(
            response=response
        )
        with self.assertLogs(level="ERROR"):
            result = self.service.get_leaderboard()
        self.assertEqual(result.state, "unavailable")
        self.assertIsNone(result.data)
        self.builder.build_leaderboard.assert_not_called()

    def test_refresh_failure_preserves_stale_data_and_shows_warning(self):
        stale = cache_data(NOW - timedelta(hours=1))
        self.storage.load_leaderboard_cache.return_value = stale
        self.builder.build_leaderboard.side_effect = requests.Timeout("timeout")
        with self.assertLogs(level="ERROR"):
            response = self.client().get("/leaderboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cache: <strong>stale</strong>", response.data)
        self.assertIn(b"Showing the last successful update", response.data)
        self.assertIn(stale["updated_at"].encode(), response.data)
        self.storage.save_leaderboard_cache.assert_not_called()

    def test_failed_cache_write_does_not_report_refresh_success(self):
        self.storage.load_leaderboard_cache.return_value = cache_data(
            NOW - timedelta(hours=1)
        )
        self.storage.save_leaderboard_cache.side_effect = requests.Timeout()
        with self.assertLogs(level="ERROR"):
            result = self.service.get_leaderboard()
        self.assertEqual(result.state, "stale")
        self.assertIsNotNone(result.error)
        self.assertEqual(
            result.data, self.storage.load_leaderboard_cache.return_value
        )

    def test_unavailable_cache_returns_503(self):
        self.storage.load_leaderboard_cache.side_effect = requests.ConnectionError()
        with self.assertLogs(level="ERROR"):
            response = self.client().get("/leaderboard")
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"Could not load", response.data)

    def test_first_build_failure_returns_503(self):
        response = requests.Response()
        response.status_code = 404
        self.storage.load_leaderboard_cache.side_effect = requests.HTTPError(
            response=response
        )
        self.builder.build_leaderboard.side_effect = requests.Timeout()
        with self.assertLogs(level="ERROR"):
            result = self.client().get("/leaderboard")
        self.assertEqual(result.status_code, 503)
        self.assertIn(b"refresh failed", result.data)

    def test_health_get_and_head_do_not_access_cache(self):
        client = self.client()
        for method in (client.get, client.head):
            self.assertEqual(method("/health").status_code, 200)
        self.storage.load_leaderboard_cache.assert_not_called()
        self.builder.build_leaderboard.assert_not_called()

    def test_admin_refresh_forces_build_even_when_fresh(self):
        response = self.client().get("/refresh?key=test-key")
        self.assertEqual(response.status_code, 200)
        self.builder.build_leaderboard.assert_called_once_with()
        self.storage.save_leaderboard_cache.assert_called_once()

    def test_unauthorized_admin_refresh_does_not_build(self):
        response = self.client().get("/refresh?key=wrong")
        self.assertEqual(response.status_code, 401)
        self.builder.build_leaderboard.assert_not_called()

    def test_admin_refresh_failure_does_not_claim_success(self):
        self.builder.build_leaderboard.side_effect = requests.Timeout()
        with self.assertLogs(level="ERROR"):
            response = self.client().get("/refresh?key=test-key")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"Refresh complete", response.data)

    def test_simultaneous_visits_only_build_once(self):
        started = Event()
        release = Event()
        current = [cache_data(NOW - timedelta(hours=1))]
        self.storage.load_leaderboard_cache.side_effect = lambda: current[0]

        def build():
            started.set()
            if not release.wait(timeout=5):
                raise TimeoutError("Test refresh was not released")
            return cache_data()

        def save(data):
            current[0] = data

        self.builder.build_leaderboard.side_effect = build
        self.storage.save_leaderboard_cache.side_effect = save
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.service.get_leaderboard)
            try:
                self.assertTrue(started.wait(timeout=5))
                second = pool.submit(self.service.get_leaderboard)
            finally:
                release.set()
            self.assertEqual(first.result(timeout=5).state, "refreshed")
            self.assertEqual(second.result(timeout=5).state, "fresh")
        self.builder.build_leaderboard.assert_called_once()
        self.storage.save_leaderboard_cache.assert_called_once()


if __name__ == "__main__":
    unittest.main()
