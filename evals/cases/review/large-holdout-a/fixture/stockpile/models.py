"""Typed views of store rows: bins and reservations.

The store keeps plain dict rows, as the database does. from_row and to_row are
exact inverses, and to_row returns only JSON-compatible values.
"""
from dataclasses import dataclass
from datetime import date, datetime

from .clock import format_timestamp, parse_timestamp

HELD = "held"
CONFIRMED = "confirmed"
PICKED = "picked"
CANCELLED = "cancelled"
EXPIRED = "expired"

# A reservation only moves forward along these edges.
TRANSITIONS = {
    HELD: (CONFIRMED, CANCELLED, EXPIRED),
    CONFIRMED: (PICKED, CANCELLED),
    PICKED: (),
    CANCELLED: (),
    EXPIRED: (),
}


@dataclass
class Bin:
    """A shelf location holding one SKU.

    quantity counts every unit on the shelf, including units promised to
    reservations that have not been picked yet. lot_expires is the sell-by date
    of the lot in the bin, or None for stock that does not expire.
    """

    bin_id: str
    warehouse_id: str
    sku: str
    quantity: int
    lot_expires: date = None

    @classmethod
    def from_row(cls, row):
        lot = row["lot_expires"]
        return cls(row["bin_id"], row["warehouse_id"], row["sku"], row["quantity"],
                   date.fromisoformat(lot) if lot else None)

    def to_row(self):
        return {
            "bin_id": self.bin_id,
            "warehouse_id": self.warehouse_id,
            "sku": self.sku,
            "quantity": self.quantity,
            "lot_expires": self.lot_expires.isoformat() if self.lot_expires else None,
        }


@dataclass
class Reservation:
    """Units of one SKU in one bin promised to an order.

    expires_at is when the hold lapses if it is still HELD by then, or None for
    a hold that waits until it is confirmed or cancelled.
    """

    reservation_id: int
    key_id: str
    order_ref: str
    sku: str
    bin_id: str
    quantity: int
    status: str
    created_at: datetime
    expires_at: datetime = None

    def lapsed(self, now):
        """True once a HELD reservation has reached its expires_at."""
        return self.status == HELD and self.expires_at is not None and self.expires_at <= now

    @classmethod
    def from_row(cls, row):
        return cls(row["reservation_id"], row["key_id"], row["order_ref"], row["sku"],
                   row["bin_id"], row["quantity"], row["status"],
                   parse_timestamp(row["created_at"]),
                   parse_timestamp(row["expires_at"]) if row["expires_at"] else None)

    def to_row(self):
        return {
            "reservation_id": self.reservation_id,
            "key_id": self.key_id,
            "order_ref": self.order_ref,
            "sku": self.sku,
            "bin_id": self.bin_id,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": format_timestamp(self.created_at),
            "expires_at": format_timestamp(self.expires_at) if self.expires_at else None,
        }
