"""The hourly digest job."""

from dataclasses import dataclass, field
from datetime import timedelta

from . import cadence
from .collect import collect_digest
from .render import render_digest
from .sender import FAILED, INVALID, SENT, send_batch


@dataclass
class JobReport:
    due: int = 0
    empty: int = 0
    already_sent: int = 0
    results: list = field(default_factory=list)

    def count(self, status):
        return sum(1 for result in self.results if result.status == status)

    def summary(self):
        counts = {"due": self.due, "empty": self.empty, "already_sent": self.already_sent}
        counts.update((status, self.count(status)) for status in (SENT, FAILED, INVALID))
        return " ".join(f"{name}={value}" for name, value in counts.items())


class DigestJob:
    """Sends the digests that are due at a given time.

    The scheduler runs it at minute 5 of every hour. With ``record=False`` the job
    renders and sends to ``transport`` but leaves the ledger untouched, which is
    what ``digests digest --dry-run`` uses.
    """

    def __init__(self, users, prefs, events, ledger, transport, settings, is_due=cadence.is_due, record=True):
        self._users = users
        self._prefs = prefs
        self._events = events
        self._ledger = ledger
        self._transport = transport
        self._settings = settings
        self._is_due = is_due
        self._record = record

    def run(self, now):
        report = JobReport()
        oldest = now - timedelta(days=self._settings.digest_lookback_days)
        batch = []
        for user in self._users.active():
            prefs = self._prefs.get(user.id)
            local_now = user.local(now)
            if not self._is_due(prefs, local_now):
                continue
            report.due += 1
            previous = self._ledger.cutoff_for(user.id)
            if previous is not None and previous >= cadence.slot_start(local_now):
                report.already_sent += 1
                continue
            since = previous if previous is not None else cadence.first_window_start(prefs, now)
            since = max(since, oldest)
            digest = collect_digest(self._events, user, prefs, since, now, self._settings.digest_max_events)
            if digest.is_empty():
                report.empty += 1
                self._advance(user.id, now)
                continue
            batch.append((user.id, render_digest(user, digest, prefs.digest, self._settings)))
        report.results = send_batch(self._transport, batch)
        for result in report.results:
            if result.status == SENT:
                # Each window is (previous cutoff, now], and now becomes the next
                # cutoff, so consecutive digests tile time: no event falls between
                # two digests, however late or irregular the runs are.
                self._advance(result.key, now)
        if self._record:
            self._ledger.save()
        return report

    def _advance(self, user_id, cutoff):
        if self._record:
            self._ledger.record(user_id, cutoff)
