"""Schema 2: bin codes become upper case, and reservations follow their bins.

Codes such as "a-01-3" and "A-01-3" used to be distinct bins by accident. Two
bins whose codes collide once upper-cased stop the migration, because merging
their stock is a decision for a person, not a script.
"""
from .common import MigrationError

VERSION = 2


def upgrade(store, now):
    bins = {}
    renamed = {}
    for bin_id, row in sorted(store.tables["bins"].items()):
        code = bin_id.strip().upper()
        if code in bins:
            raise MigrationError(f"bins {renamed.get(code, code)!r} and {bin_id!r} collide as {code!r}")
        bins[code] = dict(row, bin_id=code)
        renamed[code] = bin_id
    reservations = {}
    for reservation_id, row in store.tables["reservations"].items():
        reservations[reservation_id] = dict(row, bin_id=row["bin_id"].strip().upper())
    store.tables["bins"] = bins
    store.tables["reservations"] = reservations
