"""Plans which bins to take units from, for picks and for reservations."""

from typing import NamedTuple


class Take(NamedTuple):
    bin_id: str
    quantity: int


def pick_sequence(bins):
    """The order to draw stock from ``bins``."""
    return sorted(bins, key=lambda b: (b.received_on, b.pick_order, b.bin_id))


def plan(bins, quantity):
    """Split ``quantity`` across the free units in ``bins``; returns (takes, shortfall)."""
    takes = []
    remaining = quantity
    for candidate in pick_sequence(bins):
        if remaining == 0:
            break
        units = min(candidate.free, remaining)
        if units > 0:
            takes.append(Take(candidate.bin_id, units))
            remaining -= units
    return takes, remaining
