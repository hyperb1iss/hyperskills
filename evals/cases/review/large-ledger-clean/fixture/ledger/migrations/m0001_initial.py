"""Create the core tables."""


def apply(store):
    for name in ("accounts", "entries", "lines", "periods"):
        store.table(name)
