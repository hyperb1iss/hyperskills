"""Posting balanced journal entries.

An entry is a set of lines whose debits equal its credits. Posting validates the
entry, checks the period is open, and stores one entries row plus one lines row
per line. Posted entries are never edited; a correction is a reversal plus a new
entry.

Lines store the amount in their account's currency and the base amount it was
booked at, converted at the rate in effect on the posting date. Conversion
rounding is booked to ROUNDING_ACCOUNT.
"""
from dataclasses import dataclass, field
from datetime import date

from .accounts import get_account
from .fx import load_rates, to_base
from .money import BASE_CURRENCY, format_amount
from .periods import ensure_open

ROUNDING_ACCOUNT = "7990"


class JournalError(ValueError):
    pass


@dataclass(frozen=True)
class Line:
    account: str
    debit: int = 0
    credit: int = 0
    memo: str = ""

    def __post_init__(self):
        if self.debit < 0 or self.credit < 0:
            raise JournalError("line amounts must not be negative")
        if bool(self.debit) == bool(self.credit):
            raise JournalError("a line has either a debit or a credit")


@dataclass
class Entry:
    posted_on: date
    memo: str
    lines: list = field(default_factory=list)
    source: str = None
    external_id: str = None
    id: int = None


def _line_rows(store, entry):
    rates = load_rates(store)
    rows = []
    for line in entry.lines:
        currency = get_account(store, line.account).currency
        base = to_base(rates, line.debit or line.credit, currency, entry.posted_on)
        rows.append({"account": line.account, "currency": currency, "debit": line.debit, "credit": line.credit,
                     "base_debit": base if line.debit else 0, "base_credit": base if line.credit else 0,
                     "memo": line.memo})
    if len({row["currency"] for row in rows}) == 1:
        debits = sum(row["debit"] for row in rows)
        credits = sum(row["credit"] for row in rows)
        if debits != credits:
            raise JournalError(f"entry does not balance: debits {debits}, credits {credits}")
    residue = sum(row["base_debit"] - row["base_credit"] for row in rows)
    tolerance = sum(1 for row in rows if row["currency"] != BASE_CURRENCY)
    if abs(residue) > tolerance:
        raise JournalError(f"entry does not balance in {BASE_CURRENCY}: off by {format_amount(residue)}")
    if residue:
        get_account(store, ROUNDING_ACCOUNT)
        amount = abs(residue)
        rows.append({"account": ROUNDING_ACCOUNT, "currency": BASE_CURRENCY,
                     "debit": amount if residue < 0 else 0, "credit": amount if residue > 0 else 0,
                     "base_debit": amount if residue < 0 else 0, "base_credit": amount if residue > 0 else 0,
                     "memo": "Conversion rounding"})
    return rows


def _insert(store, posted_on, memo, rows, source=None, external_id=None):
    ensure_open(store, posted_on)
    entry_row = store.insert("entries", {"posted_on": posted_on.isoformat(), "memo": memo,
                                         "source": source, "external_id": external_id})
    for row in rows:
        store.insert("lines", dict(row, entry_id=entry_row["id"]))
    return entry_row["id"]


def post(store, entry):
    """Validate and store an entry; returns it with its id set."""
    if len(entry.lines) < 2:
        raise JournalError("an entry needs at least two lines")
    rows = _line_rows(store, entry)
    entry.id = _insert(store, entry.posted_on, entry.memo, rows, entry.source, entry.external_id)
    return entry


def post_adjustment(store, posted_on, memo, amounts):
    """Post signed base amounts as (account, amount) pairs without moving foreign balances."""
    if sum(amount for _, amount in amounts) != 0:
        raise JournalError("adjustment does not balance")
    rows = []
    for code, amount in amounts:
        currency = get_account(store, code).currency
        native = amount if currency == BASE_CURRENCY else 0
        rows.append({"account": code, "currency": currency, "debit": max(native, 0), "credit": max(-native, 0),
                     "base_debit": max(amount, 0), "base_credit": max(-amount, 0), "memo": memo})
    return _insert(store, posted_on, memo, rows)


def lines_for(store, account, through=None):
    """(posted_on, line row) pairs for an account, oldest first, optionally through a date."""
    dates = {row["id"]: date.fromisoformat(row["posted_on"]) for row in store.table("entries")}
    found = [(dates[row["entry_id"]], row) for row in store.table("lines") if row["account"] == account]
    if through is not None:
        found = [(day, row) for day, row in found if day <= through]
    return sorted(found, key=lambda pair: (pair[0], pair[1]["id"]))


def reverse(store, entry_id, on):
    """Post the mirror image of an entry on another day, at the original base amounts; returns its id."""
    original = store.one("entries", id=entry_id)
    rows = [{"account": row["account"], "currency": row["currency"], "debit": row["credit"],
             "credit": row["debit"], "base_debit": row["base_credit"], "base_credit": row["base_debit"],
             "memo": row["memo"]}
            for row in store.select("lines", entry_id=entry_id)]
    return _insert(store, on, f"Reversal of entry {entry_id}: {original['memo']}", rows)
