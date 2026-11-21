"""Record imported statement references so a re-import skips them.

Entries gain the bank feed they came from (source) and the statement reference
(external_id). import_keys holds one row per imported reference.
"""


def apply(store):
    store.table("import_keys")
    for entry in store.table("entries"):
        entry.setdefault("source", None)
        entry.setdefault("external_id", None)
        if entry["external_id"]:
            store.insert("import_keys", {"key": entry["external_id"]})
