"""Releases reservations whose hold has expired.

The host's scheduler calls sweep() once a minute, so a hold can outlive its
expiry by up to a minute; fulfill() checks the expiry itself.
"""

from dataclasses import dataclass
from datetime import timedelta

from .reservations import EXPIRED

RETENTION = timedelta(days=7)


@dataclass(frozen=True)
class SweepResult:
    expired: int
    units: int


def sweep(book, now):
    """Expire every held reservation due at ``now``, forget finished ones older than
    RETENTION, and return what was released."""
    expired = units = 0
    for reservation in book.due(now):
        units += reservation.held
        book.release(reservation.id, status=EXPIRED)
        expired += 1
    book.prune(now - RETENTION)
    return SweepResult(expired=expired, units=units)
