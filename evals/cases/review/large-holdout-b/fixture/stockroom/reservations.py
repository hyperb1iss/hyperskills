"""Reservations: units held for an order until it is picked or the hold expires."""

import itertools
from dataclasses import dataclass
from datetime import timedelta

from .picking import plan

HELD = "held"
FULFILLED = "fulfilled"
RELEASED = "released"
EXPIRED = "expired"


class ReservationError(Exception):
    pass


class UnknownReservation(ReservationError):
    pass


class DuplicateReservation(ReservationError):
    pass


class NotHeld(ReservationError):
    pass


class ReservationExpired(ReservationError):
    pass


class Unavailable(ReservationError):
    def __init__(self, sku, requested, available):
        super().__init__(f"{sku}: requested {requested}, available {available}")
        self.available = available


@dataclass(frozen=True)
class Allocation:
    warehouse_id: str
    bin_id: str
    quantity: int


@dataclass
class Reservation:
    id: str
    order_id: str
    channel: str
    sku: str
    requested: int
    allocations: tuple
    created_at: object
    expires_at: object
    status: str = HELD

    @property
    def held(self):
        return sum(allocation.quantity for allocation in self.allocations)

    @property
    def shortfall(self):
        return self.requested - self.held


def order_warehouses(warehouse_ids, priority):
    """Warehouses named in ``priority`` first, in that order, then the rest by id."""
    known = set(warehouse_ids)
    first = list(dict.fromkeys(warehouse_id for warehouse_id in priority if warehouse_id in known))
    return first + sorted(known - set(first))


class ReservationBook:
    """Every reservation at one site; the host keeps one alongside its Stock."""

    def __init__(self, stock, clock):
        self._stock = stock
        self._clock = clock
        self._by_id = {}
        self._ids = itertools.count(1)

    def reserve(self, order_id, channel, sku, quantity, warehouses, ttl, allow_partial=False):
        """Hold ``quantity`` units of ``sku`` for one order line, trying warehouses in
        the order given. With ``allow_partial``, hold what is free and report the
        shortfall; without it, hold all or nothing.
        """
        if any(r.status == HELD and (r.channel, r.order_id, r.sku) == (channel, order_id, sku)
               for r in self._by_id.values()):
            raise DuplicateReservation(f"{channel}/{order_id} already holds {sku}")
        allocations = []
        remaining = quantity
        for warehouse_id in warehouses:
            if remaining == 0:
                break
            takes, remaining = plan(self._stock.bins(sku, warehouse_id), remaining)
            allocations.extend(Allocation(warehouse_id, take.bin_id, take.quantity) for take in takes)
        held = quantity - remaining
        if held == 0 or (remaining and not allow_partial):
            raise Unavailable(sku, quantity, held)
        for allocation in allocations:
            self._stock.hold(allocation.warehouse_id, allocation.bin_id, allocation.quantity)
        now = self._clock()
        reservation = Reservation(
            id=f"res_{next(self._ids):06d}",
            order_id=order_id,
            channel=channel,
            sku=sku,
            requested=quantity,
            allocations=tuple(allocations),
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )
        self._by_id[reservation.id] = reservation
        return reservation

    def get(self, reservation_id):
        try:
            return self._by_id[reservation_id]
        except (KeyError, TypeError):
            raise UnknownReservation(str(reservation_id)) from None

    def release(self, reservation_id, status=RELEASED):
        """Give a held reservation's units back to free stock."""
        reservation = self._held(reservation_id)
        for allocation in reservation.allocations:
            self._stock.unhold(allocation.warehouse_id, allocation.bin_id, allocation.quantity)
        reservation.status = status
        return reservation

    def fulfill(self, reservation_id):
        """Pick a reservation's units and return the allocations actually picked. A bin
        that lost stock after the hold yields what it has; an expired hold is released.
        """
        reservation = self._held(reservation_id)
        if self._clock() >= reservation.expires_at:
            self.release(reservation_id, status=EXPIRED)
            raise ReservationExpired(reservation_id)
        picked = []
        for allocation in reservation.allocations:
            units = self._stock.take_held(allocation.warehouse_id, allocation.bin_id, allocation.quantity)
            picked.append(Allocation(allocation.warehouse_id, allocation.bin_id, units))
        reservation.status = FULFILLED
        return picked

    def due(self, now):
        """Held reservations whose expiry is at or before ``now``."""
        return [r for r in self._by_id.values() if r.status == HELD and r.expires_at <= now]

    def prune(self, before):
        """Forget finished reservations whose hold would have ended before ``before``."""
        for reservation in [r for r in self._by_id.values() if r.status != HELD and r.expires_at < before]:
            del self._by_id[reservation.id]

    def _held(self, reservation_id):
        reservation = self.get(reservation_id)
        if reservation.status != HELD:
            raise NotHeld(f"{reservation_id} is {reservation.status}")
        return reservation

