"""Multi-currency books: currencies and base amounts on existing rows, per-feed import keys,
a rates table, and the exchange gain, loss, and rounding accounts."""
BASE_CURRENCY = "USD"
SEEDED_ACCOUNTS = [
    ("7910", "Exchange gain", "income"),
    ("7920", "Exchange loss", "expense"),
    ("7990", "Currency conversion rounding", "expense"),
]


def apply(store):
    for account in store.table("accounts"):
        account.setdefault("currency", BASE_CURRENCY)
    for line in store.table("lines"):
        line.setdefault("currency", BASE_CURRENCY)
        line.setdefault("base_debit", line["debit"])
        line.setdefault("base_credit", line["credit"])
    store.table("rates")
    keys = store.table("import_keys")
    keys.clear()
    for entry in store.table("entries"):
        if entry.get("external_id"):
            store.insert("import_keys", {"key": f"{entry['external_id']}@{entry['source']}"})
    existing = {account["code"]: account for account in store.table("accounts")}
    for code, name, kind in SEEDED_ACCOUNTS:
        if code not in existing:
            store.insert("accounts", {"code": code, "name": name, "kind": kind, "currency": BASE_CURRENCY})
        elif existing[code]["kind"] != kind:
            raise ValueError(f"account {code} is already a {existing[code]['kind']} account; 0003 needs it for {name}")
