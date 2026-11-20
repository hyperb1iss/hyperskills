from ledger.accounts import create_account
from ledger.db import Store
from ledger.migrations import migrate

CHART = [
    ("1000", "Operating bank", "asset"),
    ("1100", "Bank clearing", "asset"),
    ("1200", "Receivables", "asset"),
    ("2000", "Payables", "liability"),
    ("3000", "Owner equity", "equity"),
    ("4000", "Subscription revenue", "income"),
    ("5000", "Hosting", "expense"),
    ("5100", "Contractors", "expense"),
]


def make_store():
    store = Store()
    migrate(store)
    for code, name, kind in CHART:
        create_account(store, code, name, kind)
    return store
