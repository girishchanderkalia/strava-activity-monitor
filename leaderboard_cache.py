import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Literal

import requests

from github_storage import load_leaderboard_cache, save_leaderboard_cache
from leaderboard import build_leaderboard


CACHE_MAX_AGE = timedelta(minutes=15)
_refresh_lock = Lock()
logger = logging.getLogger(__name__)


@dataclass
class CacheResult:
    data: dict | None
    state: Literal["fresh", "refreshed", "stale", "unavailable"]
    error: str | None = None


def is_cache_stale(data: dict, now: datetime) -> bool:
    try:
        if "updated_at_utc" in data:
            updated = datetime.fromisoformat(data["updated_at_utc"])
            if updated.tzinfo is None:
                raise ValueError("Cache timestamp must include a timezone")
        else:
            updated = datetime.strptime(
                data["updated_at"], "%d %b %Y %H:%M"
            ).replace(tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        logger.warning("Missing or invalid leaderboard cache timestamp")
        return True

    age = now - updated
    return age < timedelta(0) or age >= CACHE_MAX_AGE


def get_leaderboard(*, force: bool = False) -> CacheResult:
    # Re-read inside the lock so waiting requests see the completed refresh.
    with _refresh_lock:
        try:
            data = load_leaderboard_cache()
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                data = None
            else:
                logger.exception("Failed to load leaderboard cache")
                return CacheResult(None, "unavailable", "Could not load the leaderboard.")
        except (requests.RequestException, ValueError):
            logger.exception("Failed to load leaderboard cache")
            return CacheResult(None, "unavailable", "Could not load the leaderboard.")

        if data is not None and not force:
            if not is_cache_stale(data, datetime.now(timezone.utc)):
                return CacheResult(data, "fresh")

        try:
            refreshed = build_leaderboard()
            save_leaderboard_cache(refreshed)
        except (requests.RequestException, ValueError, KeyError, TypeError):
            logger.exception("Failed to refresh leaderboard cache")
            return CacheResult(
                data,
                "stale" if data is not None else "unavailable",
                "Leaderboard refresh failed. Please try again later.",
            )

        return CacheResult(refreshed, "refreshed")
