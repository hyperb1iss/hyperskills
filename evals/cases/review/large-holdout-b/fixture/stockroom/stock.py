"""Stock levels by warehouse and bin."""

from .models import Event
from .picking import plan


class UnknownBin(KeyError):
    pass


class InsufficientStock(Exception):
    def __init__(self, sku, warehouse_id, requested, available):
        super().__init__(f"{sku} in {warehouse_id}: requested {requested}, available {available}")
        self.sku = sku
        self.warehouse_id = warehouse_id
        self.requested = requested
        self.available = available


class Stock:
    """Every bin at one site. ``clock`` returns the current aware datetime."""

    def __init__(self, clock, events):
        self._clock = clock
        self._events = events
        self._bins = {}

    @property
    def events(self):
        return self._events

    def add_bin(self, new_bin):
        key = (new_bin.warehouse_id, new_bin.bin_id)
        if key in self._bins:
            raise ValueError(f"bin {new_bin.bin_id} already exists in {new_bin.warehouse_id}")
        self._bins[key] = new_bin
        return new_bin

    def bin(self, warehouse_id, bin_id):
        try:
            return self._bins[(warehouse_id, bin_id)]
        except KeyError:
            raise UnknownBin(f"{warehouse_id}/{bin_id}") from None

    def bins(self, sku, warehouse_id=None):
        """Bins holding ``sku``, in the order they were added."""
        return [
            b for b in self._bins.values()
            if b.sku == sku and (warehouse_id is None or b.warehouse_id == warehouse_id)
        ]

    def warehouse_ids(self):
        return sorted({warehouse_id for warehouse_id, _ in self._bins})

    def skus(self, warehouse_id=None):
        return sorted({b.sku for b in self._bins.values() if warehouse_id in (None, b.warehouse_id)})

    def on_hand(self, sku, warehouse_id=None):
        """Units of ``sku`` physically in stock, in one warehouse or across all of them."""
        return sum(b.on_hand for b in self.bins(sku, warehouse_id))

    def reserved(self, sku, warehouse_id=None):
        """Units of ``sku`` held by reservations."""
        return sum(b.reserved for b in self.bins(sku, warehouse_id))

    def available(self, sku, warehouse_id=None):
        """Units of ``sku`` free to promise: on hand minus reserved."""
        return sum(b.free for b in self.bins(sku, warehouse_id))

    def home_bin(self, sku, warehouse_id):
        """The bin receipts and count adjustments go to: the SKU's first bin there."""
        bins = self.bins(sku, warehouse_id)
        if not bins:
            raise UnknownBin(f"{warehouse_id}: no bin for {sku}")
        return bins[0]

    def adjust(self, sku, warehouse_id, bin_id, delta, reason):
        """Change a bin's count by ``delta``; the home bin when ``bin_id`` is None."""
        target = self.bin(warehouse_id, bin_id) if bin_id else self.home_bin(sku, warehouse_id)
        if target.sku != sku:
            raise ValueError(f"bin {target.bin_id} holds {target.sku}, not {sku}")
        if target.on_hand + delta < 0:
            raise InsufficientStock(sku, warehouse_id, -delta, target.on_hand)
        target.on_hand += delta
        self._record("adjust", sku, warehouse_id, delta, f"{target.bin_id}: {reason}")
        return target

    def receive(self, sku, warehouse_id, quantity, received_on, bin_id=None):
        """Put ``quantity`` received units away, in the home bin unless ``bin_id`` is given."""
        target = self.bin(warehouse_id, bin_id) if bin_id else self.home_bin(sku, warehouse_id)
        if target.on_hand == 0:
            target.received_on = received_on
        target.on_hand += quantity
        self._record("receive", sku, warehouse_id, quantity, target.bin_id)
        return target

    def pick(self, sku, warehouse_id, quantity):
        """Take ``quantity`` units for an order and return the (bin_id, units) taken.

        Stock is taken oldest-received first so that it rotates; perishable SKUs
        carry a best-before date. Units held by reservations are never taken.
        Raises InsufficientStock, taking nothing, if too few units are free.
        """
        takes, shortfall = plan(self.bins(sku, warehouse_id), quantity)
        if shortfall:
            raise InsufficientStock(sku, warehouse_id, quantity, quantity - shortfall)
        for take in takes:
            self.bin(warehouse_id, take.bin_id).on_hand -= take.quantity
        detail = ",".join(f"{take.bin_id}x{take.quantity}" for take in takes)
        self._record("pick", sku, warehouse_id, -quantity, detail)
        return takes

    def hold(self, warehouse_id, bin_id, quantity):
        """Reserve ``quantity`` free units in a bin."""
        target = self.bin(warehouse_id, bin_id)
        if quantity > target.free:
            raise InsufficientStock(target.sku, warehouse_id, quantity, target.free)
        target.reserved += quantity

    def unhold(self, warehouse_id, bin_id, quantity):
        """Return held units to free stock."""
        target = self.bin(warehouse_id, bin_id)
        target.reserved = max(target.reserved - quantity, 0)

    def take_held(self, warehouse_id, bin_id, quantity):
        """Pick units that were held and return how many were actually in the bin."""
        target = self.bin(warehouse_id, bin_id)
        units = min(quantity, target.on_hand)
        target.on_hand -= units
        target.reserved = max(target.reserved - quantity, 0)
        self._record("pick", target.sku, warehouse_id, -units, f"{bin_id}x{units} reserved")
        return units

    def _record(self, kind, sku, warehouse_id, quantity, detail=""):
        self._events.record(Event(self._clock(), kind, sku, warehouse_id, quantity, detail))
