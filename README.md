## walking channge monitor

The leaderboard refreshes on demand when someone visits `/leaderboard`:

- A cache younger than 15 minutes is displayed without fetching Strava data.
- A cache at least 15 minutes old is rebuilt and saved before displaying the page.
- If the cache does not exist, the first visit builds it.
- If rebuilding fails, the last successful cache is displayed with a warning.
  Without a usable cache, the page returns HTTP 503.

The page shows the cache state (`fresh`, `refreshed`, or `stale`) and the last
successful update time in UTC. New updates also store a precise ISO timestamp;
existing minute-resolution UTC timestamps remain supported.

No updates happen while nobody visits. Reloading the page checks freshness but
does not force a Strava fetch. The admin refresh still forces an update.
There is no leaderboard GitHub Actions workflow. Deploy these changes to Render
and push the workflow removal to GitHub's default branch to replace the
scheduled updates.

Automatic and admin refreshes are serialized within the web process to avoid
duplicate builds from simultaneous visits. Render is configured with one worker,
four threads, and a 120-second worker timeout so health checks can run during a
refresh. Multiple workers or instances would
require a shared refresh lock.

Keep-awake requests use `/health`, which does not read or refresh the leaderboard.
The first stale-cache visit waits for the Strava fetch and GitHub cache write.