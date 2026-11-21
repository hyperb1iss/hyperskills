# Add daily and weekly email digests

Users can now ask for one digest email a day or a week, instead of or as well as immediate notifications. This adds the preferences, the schedule, the email, and an hourly job that sends them.

- **Preferences.** `digest` ("off", "daily", or "weekly"), `digest_hour` (local hour), and `digest_weekday` for weekly digests. Muted kinds are left out of digests just as they are left out of immediate mail.
- **Schedule** (`cadence.py`). A digest is due during the user's chosen local hour, and for weekly digests on the chosen weekday. The scheduler runs the job at minute 5 of every hour; the schedule entry ships with the deploy config change.
- **Collection and rendering** (`collect.py`, `render.py`). Events are grouped by kind in a fixed order, newest first, and capped at `DIGEST_MAX_EVENTS` (50) with "and N more" lines. Every digest links to the notification settings page.
- **Sending** (`sender.py`). Each digest is sent on its own: a relay failure fails that digest and the rest still go out. A failed digest does not move the user's window, so its events go into the user's next one. That holds for a first digest too: the start of a user's first window is recorded as soon as they are due, so a retry covers the same window.
- **Ledger** (`ledger.py`). The ledger stores where each user's last window ended. A digest covers the events after the previous cutoff up to the run time, and that run time becomes the next cutoff. Consecutive windows tile time, so no event ever falls between two digests, even when runs are late or skipped. A run that misses a user's hour skips that day's digest, and the next one covers the gap. A rerun within the same hour sends nothing. If a run dies after sending but before the ledger is saved, those users can see the same events again next time; we prefer that to losing them. A window never reaches back more than `DIGEST_LOOKBACK_DAYS` (14).
- **Command.** `digests digest [--dry-run [--now T]]`. A dry run prints what would be sent and touches neither the relay nor the ledger. `--now` previews a dry run at another time; it is refused without `--dry-run`, so a real run always uses the clock.

Tests cover the schedule, collection and rendering, the sender, the job (reruns, failures and their retries, weekly digests), the ledger, and the new command with a dry run.
