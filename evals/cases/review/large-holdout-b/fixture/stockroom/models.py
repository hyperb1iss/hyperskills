"""Records shared across the stock service."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Bin:
    """One storage location holding a single SKU.

    ``pick_order`` is the bin's place in the warehouse walk sequence; pickers
    visit lower numbers first. ``received_on`` is the receipt date of the stock
    in the bin, used to rotate stock oldest first. Bins are never removed.
    """

    warehouse_id: str
    bin_id: str
    sku: str
    on_hand: int = 0
    pick_order: int = 0
    received_on: date = date(2000, 1, 1)
    reserved: int = 0

    @property
    def free(self):
        """Units not held by a reservation; never negative, even after a count."""
        return max(self.on_hand - self.reserved, 0)


@dataclass(frozen=True)
class Principal:
    """The caller of an API request, resolved from its API key upstream.

    ``warehouses`` lists the warehouses the key may act on; admins act on all.
    ``channel`` is the sales channel the key belongs to, empty for internal keys.
    """

    key_id: str
    roles: frozenset = frozenset()
    warehouses: frozenset = frozenset()
    channel: str = ""

    @property
    def is_admin(self):
        return "admin" in self.roles

    def has_role(self, role):
        return self.is_admin or role in self.roles


@dataclass(frozen=True)
class Event:
    at: datetime
    kind: str
    sku: str
    warehouse_id: str
    quantity: int
    detail: str = ""
