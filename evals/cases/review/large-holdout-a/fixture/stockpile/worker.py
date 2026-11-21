"""Background worker that warns about and expires lapsing holds.

One ExpiryWorker lives for the life of the worker process; run_forever calls
tick() on a fixed interval. Each tick looks at the HELD reservations due to
lapse within warn_ahead. Lapsed holds are marked expired; every other one gets
one hold_expiring notice, sent to the key that made the hold. A notice that
fails to send is tried again on the next tick, and a restarted worker sends
the notices again, so a client may see a notice twice. A notice still failing
when the hold lapses is dropped.
"""
import logging
import time
from datetime import timedelta

from .clock import format_timestamp
from .notify import NotifyError
from .reservations import expire_hold

log = logging.getLogger(__name__)


class ExpiryWorker:
    def __init__(self, store, notifier, clock, warn_ahead=timedelta(minutes=5)):
        self.store = store
        self.notifier = notifier
        self.clock = clock
        self.warn_ahead = warn_ahead
        self._warned = set()

    def tick(self):
        """Run one pass; return counts of holds expired and warned and of failed notices."""
        now = self.clock()
        counts = {"expired": 0, "warned": 0, "failed": 0}
        due = self.store.holds_expiring_before(now + self.warn_ahead)
        for reservation in due:
            reservation_id = reservation.reservation_id
            if reservation.expires_at <= now:
                if expire_hold(self.store, reservation_id, now):
                    counts["expired"] += 1
                self._warned.discard(reservation_id)
                continue
            if reservation_id in self._warned:
                continue
            try:
                self.notifier.send(reservation.key_id, "hold_expiring", {
                    "reservation_id": reservation_id,
                    "order_ref": reservation.order_ref,
                    "expires_at": format_timestamp(reservation.expires_at),
                })
            except NotifyError as error:
                counts["failed"] += 1
                log.warning("hold_expiring notice for reservation %s not sent: %s", reservation_id, error)
                continue
            self._warned.add(reservation_id)
            counts["warned"] += 1
        return counts

    def run_forever(self, interval=30.0, sleep=time.sleep):
        """Tick every interval seconds; a failed tick is logged and the loop goes on."""
        while True:
            try:
                self.tick()
            except Exception:
                log.exception("expiry tick failed")
            sleep(interval)
