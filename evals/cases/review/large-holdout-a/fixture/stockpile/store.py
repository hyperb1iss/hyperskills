"""In-memory tables standing in for the database.

Rows are plain dicts keyed by primary key; the query methods return typed
models. The API service and the background jobs share one Store from different
threads, so every method takes self.lock. An operation that reads and then
writes based on what it read holds the lock across both steps, so no other
writer can change the rows in between; the lock is reentrant for that reason.
"""
import threading

from .models import HELD, Bin, Reservation

SCHEMA_VERSION = 4
TABLES = ("bins", "reservations", "keys")


class NotFound(LookupError):
    pass


class Store:
    def __init__(self, schema_version=SCHEMA_VERSION):
        self.lock = threading.RLock()
        self.schema_version = schema_version
        self.tables = {name: {} for name in TABLES}
        self._last_id = {}

    @classmethod
    def load(cls, tables, schema_version):
        """A store over existing rows, such as a snapshot from before a migration."""
        store = cls(schema_version)
        for name, rows in tables.items():
            store.tables[name] = {key: dict(row) for key, row in rows.items()}
            numbered = [key for key in rows if isinstance(key, int)]
            if numbered:
                store._last_id[name] = max(numbered)
        return store

    def next_id(self, table):
        """A fresh integer id for table, never handed out before."""
        with self.lock:
            value = self._last_id.get(table, 0) + 1
            self._last_id[table] = value
            return value

    def add_bin(self, bin_):
        with self.lock:
            if bin_.bin_id in self.tables["bins"]:
                raise ValueError(f"bin {bin_.bin_id} already exists")
            self.tables["bins"][bin_.bin_id] = bin_.to_row()

    def bin(self, bin_id):
        with self.lock:
            row = self.tables["bins"].get(bin_id)
            if row is None:
                raise NotFound(f"no bin {bin_id}")
            return Bin.from_row(row)

    def bins(self, warehouse_id=None, sku=None):
        """Bins matching every filter given, ordered by bin_id."""
        with self.lock:
            rows = [row for row in self.tables["bins"].values()
                    if (warehouse_id is None or row["warehouse_id"] == warehouse_id)
                    and (sku is None or row["sku"] == sku)]
            return [Bin.from_row(row) for row in sorted(rows, key=lambda row: row["bin_id"])]

    def set_bin_quantity(self, bin_id, quantity):
        if quantity < 0:
            raise ValueError(f"bin {bin_id} cannot hold {quantity} units")
        with self.lock:
            if bin_id not in self.tables["bins"]:
                raise NotFound(f"no bin {bin_id}")
            self.tables["bins"][bin_id]["quantity"] = quantity

    def insert_reservation(self, reservation):
        with self.lock:
            self.tables["reservations"][reservation.reservation_id] = reservation.to_row()

    def reservation(self, reservation_id):
        with self.lock:
            row = self.tables["reservations"].get(reservation_id)
            if row is None:
                raise NotFound(f"no reservation {reservation_id}")
            return Reservation.from_row(row)

    def save_reservation(self, reservation):
        with self.lock:
            if reservation.reservation_id not in self.tables["reservations"]:
                raise NotFound(f"no reservation {reservation.reservation_id}")
            self.tables["reservations"][reservation.reservation_id] = reservation.to_row()

    def reservations(self, bin_id=None, status=None):
        """Reservations matching every filter given, ordered by id."""
        with self.lock:
            rows = [row for row in self.tables["reservations"].values()
                    if (bin_id is None or row["bin_id"] == bin_id)
                    and (status is None or row["status"] == status)]
            return [Reservation.from_row(row)
                    for row in sorted(rows, key=lambda row: row["reservation_id"])]

    def holds_expiring_before(self, moment):
        """HELD reservations with an expires_at earlier than moment, soonest first."""
        with self.lock:
            due = [Reservation.from_row(row) for row in self.tables["reservations"].values()
                   if row["status"] == HELD and row["expires_at"] is not None]
        return sorted((reservation for reservation in due if reservation.expires_at < moment),
                      key=lambda reservation: (reservation.expires_at, reservation.reservation_id))

    def put_key(self, row):
        with self.lock:
            self.tables["keys"][row["key_id"]] = dict(row)

    def key_row(self, key_id):
        with self.lock:
            row = self.tables["keys"].get(key_id)
            return dict(row) if row is not None else None
