"""Stock levels: what is on the shelf, what is promised, and what is free.

A bin's quantity counts every unit physically present. Units promised to a
reservation stay on the shelf until it is picked, so the free stock in a bin is
its quantity minus what reservations still hold there. Receiving and cycle
counts change quantity directly and never touch reservations.
"""
from .clock import utcnow
from .models import CANCELLED, PICKED


def reserved_in_bin(store, bin_id, now):
    """Units in bin_id promised to reservations that still hold stock at now."""
    return sum(reservation.quantity for reservation in store.reservations(bin_id=bin_id)
               if reservation.status not in (PICKED, CANCELLED) and not reservation.lapsed(now))


def free_in_bin(store, bin_id, now=None):
    """Free units in bin_id at now, which defaults to the current time.

    A hold stops holding stock at its expires_at, without waiting for the
    expiry worker's next pass.
    """
    with store.lock:
        return store.bin(bin_id).quantity - reserved_in_bin(store, bin_id, now or utcnow())


def available(store, warehouse_id, sku, now=None):
    """Units of sku in warehouse_id that a new reservation could take at now."""
    now = now or utcnow()
    with store.lock:
        return sum(max(free_in_bin(store, bin_.bin_id, now), 0)
                   for bin_ in store.bins(warehouse_id=warehouse_id, sku=sku))


def receive(store, bin_id, units):
    """Add units delivered to bin_id; return the new quantity."""
    if units < 1:
        raise ValueError("a delivery adds at least one unit")
    with store.lock:
        quantity = store.bin(bin_id).quantity + units
        store.set_bin_quantity(bin_id, quantity)
        return quantity


def adjust(store, bin_id, counted):
    """Record a cycle count: set bin_id to the counted quantity and return the change.

    A count below what reservations hold there is still recorded; the bin then
    shows negative free stock until those reservations are picked, cancelled, or
    lapse.
    """
    if counted < 0:
        raise ValueError("a count cannot be negative")
    with store.lock:
        before = store.bin(bin_id).quantity
        store.set_bin_quantity(bin_id, counted)
        return counted - before
