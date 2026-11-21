"""Chart of accounts. Only assets and liabilities may be held in a foreign currency."""
from dataclasses import dataclass

from .money import BASE_CURRENCY, exponent

KINDS = ("asset", "liability", "equity", "income", "expense")
DEBIT_NORMAL = {"asset", "expense"}
FOREIGN_KINDS = {"asset", "liability"}


class AccountError(ValueError):
    pass


@dataclass(frozen=True)
class Account:
    code: str
    name: str
    kind: str
    currency: str = BASE_CURRENCY

    @property
    def debit_normal(self):
        return self.kind in DEBIT_NORMAL


def _from_row(row):
    return Account(row["code"], row["name"], row["kind"], row["currency"])


def create_account(store, code, name, kind, currency=BASE_CURRENCY):
    if kind not in KINDS:
        raise AccountError(f"unknown account kind {kind!r}")
    if not code.isdigit() or len(code) != 4:
        raise AccountError(f"account codes are four digits, got {code!r}")
    exponent(currency)
    if currency != BASE_CURRENCY and kind not in FOREIGN_KINDS:
        raise AccountError(f"{kind} accounts are kept in {BASE_CURRENCY}")
    if store.select("accounts", code=code):
        raise AccountError(f"account {code} already exists")
    return _from_row(store.insert("accounts", {"code": code, "name": name, "kind": kind, "currency": currency}))


def get_account(store, code):
    rows = store.select("accounts", code=code)
    if not rows:
        raise AccountError(f"no account {code}")
    return _from_row(rows[0])


def list_accounts(store, kind=None):
    accounts = [_from_row(row) for row in sorted(store.table("accounts"), key=lambda row: row["code"])]
    return [account for account in accounts if kind is None or account.kind == kind]
