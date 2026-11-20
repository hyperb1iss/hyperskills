"""Schema 4: holds can lapse, and keys carry a warehouse scope.

Every existing reservation gets expires_at None: it was made without a hold
window, so it lasts until confirmed or cancelled, as before. Every existing key
gets the ["*"] scope, so no client loses access at deploy; an admin narrows a
key afterwards with access.set_scope.
"""
from ..access import WILDCARD

VERSION = 4


def upgrade(store, now):
    reservations = {reservation_id: dict(row, expires_at=None)
                    for reservation_id, row in store.tables["reservations"].items()}
    keys = {key_id: dict(row, warehouses=[WILDCARD]) for key_id, row in store.tables["keys"].items()}
    store.tables["reservations"] = reservations
    store.tables["keys"] = keys
