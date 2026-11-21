"""Schema 3: API keys get a role and a revoked flag.

Before roles existed every key could reserve, so keys without a role become
operators, which keeps what they could do. Keys get revoked = False unless the
row already says otherwise.
"""
VERSION = 3


def upgrade(store, now):
    keys = {}
    for key_id, row in store.tables["keys"].items():
        upgraded = dict(row)
        upgraded.setdefault("role", "operator")
        upgraded.setdefault("revoked", False)
        keys[key_id] = upgraded
    store.tables["keys"] = keys
