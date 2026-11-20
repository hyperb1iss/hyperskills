"""Reservation lifecycle: hold, confirm, pick, cancel, and expire.

A hold promises units of one SKU in one bin to an order without moving them.
Confirming it commits the order; picking takes the units off the shelf. A hold
with a hold window lapses at expires_at unless confirmed first, and the expiry
worker then marks it expired. Status changes go through _transition, which
enforces models.TRANSITIONS, so each change happens at most once. Callers pass
`now` so tests control time.
"""
from datetime import timedelta

from . import inventory
from .models import CANCELLED, CONFIRMED, EXPIRED, HELD, PICKED, TRANSITIONS, Reservation

MAX_HOLD = timedelta(hours=24)


class InsufficientStock(Exception):
    pass


class WrongSku(ValueError):
    pass


class InvalidTransition(Exception):
    pass


class HoldExpired(InvalidTransition):
    """The hold lapsed before it was confirmed."""


class ShortPick(Exception):
    """A bin holds fewer units than were promised from it; it needs a cycle count."""


def reserve(store, key_id, order_ref, sku, bin_id, quantity, now, hold=None):
    """Hold quantity units of sku in bin_id and return the new Reservation.

    With a hold window (a timedelta up to MAX_HOLD) the hold lapses at
    now + hold; without one it lasts until confirmed or cancelled. Checking free
    stock and writing the hold happen under the store lock, so two concurrent
    holds never promise the same units.
    """
    if quantity < 1:
        raise ValueError("quantity must be at least 1")
    if hold is not None and not timedelta(0) < hold <= MAX_HOLD:
        raise ValueError(f"a hold window must be positive and at most {MAX_HOLD}")
    with store.lock:
        bin_ = store.bin(bin_id)
        if bin_.sku != sku:
            raise WrongSku(f"bin {bin_id} holds {bin_.sku}, not {sku}")
        free = inventory.free_in_bin(store, bin_id, now)
        if free < quantity:
            raise InsufficientStock(f"bin {bin_id} has {max(free, 0)} free units, {quantity} requested")
        reservation = Reservation(store.next_id("reservations"), key_id, order_ref, sku,
                                  bin_id, quantity, HELD, now, now + hold if hold else None)
        store.insert_reservation(reservation)
    return reservation


def _transition(store, reservation_id, status):
    reservation = store.reservation(reservation_id)
    if status not in TRANSITIONS[reservation.status]:
        raise InvalidTransition(
            f"reservation {reservation_id} is {reservation.status} and cannot become {status}")
    reservation.status = status
    store.save_reservation(reservation)
    return reservation


def confirm(store, reservation_id, now):
    """Confirm a hold. A lapsed hold cannot be confirmed, even before the
    worker marks it expired, because its units were only promised until then."""
    with store.lock:
        reservation = store.reservation(reservation_id)
        if reservation.lapsed(now) or reservation.status == EXPIRED:
            raise HoldExpired(f"reservation {reservation_id} lapsed at "
                              f"{reservation.expires_at.isoformat()}")
        return _transition(store, reservation_id, CONFIRMED)


def cancel(store, reservation_id):
    with store.lock:
        return _transition(store, reservation_id, CANCELLED)


def expire_hold(store, reservation_id, now):
    """Mark one lapsed hold expired and return True, or return False if it has not lapsed.

    The worker calls this for holds it saw as due, and a client may confirm or
    cancel in between, so the check is repeated under the lock.
    """
    with store.lock:
        if not store.reservation(reservation_id).lapsed(now):
            return False
        _transition(store, reservation_id, EXPIRED)
        return True


def pick(store, reservation_id):
    """Take a confirmed reservation's units off the shelf.

    The bin is checked before anything changes, so a short bin leaves both the
    reservation and the bin as they were.
    """
    with store.lock:
        reservation = store.reservation(reservation_id)
        if PICKED not in TRANSITIONS[reservation.status]:
            raise InvalidTransition(
                f"reservation {reservation_id} is {reservation.status} and cannot be picked")
        on_shelf = store.bin(reservation.bin_id).quantity
        if on_shelf < reservation.quantity:
            raise ShortPick(f"bin {reservation.bin_id} has {on_shelf} units, "
                            f"{reservation.quantity} promised")
        store.set_bin_quantity(reservation.bin_id, on_shelf - reservation.quantity)
        return _transition(store, reservation_id, PICKED)
