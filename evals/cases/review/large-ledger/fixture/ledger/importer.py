"""Import bank statement CSVs as journal entries against a clearing account.

Columns: date (YYYY-MM-DD), reference, description, amount (positive is money
in, in the bank account's currency). Each bank feed is a source. A statement
line already imported, by import_key(source, reference), is skipped, so
re-running an import is safe. Rows that cannot be posted are reported with
their line number and the rest of the file continues.
"""
import csv
from dataclasses import dataclass, field
from datetime import date

from .accounts import get_account
from .fx import MissingRate
from .journal import Entry, Line, post
from .money import parse_amount


class StatementError(ValueError):
    pass


@dataclass
class ImportResult:
    posted: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    rejected: list = field(default_factory=list)


def import_key(source, reference):
    return f"{source}:{reference}"


def read_statement(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield reader.line_num, row


def _entry(row, day, amount, source, bank_account, clearing_account):
    reference = row["reference"].strip()
    memo = (row.get("description") or "").strip() or reference
    if amount > 0:
        lines = [Line(bank_account, debit=amount), Line(clearing_account, credit=amount)]
    else:
        lines = [Line(clearing_account, debit=-amount), Line(bank_account, credit=-amount)]
    return Entry(day, memo, lines, source=source, external_id=reference)


def import_statement(store, path, source, bank_account, clearing_account):
    currency = get_account(store, bank_account).currency
    if get_account(store, clearing_account).currency != currency:
        raise StatementError(f"clearing account {clearing_account} is not in {currency}")
    result = ImportResult()
    known = {row["key"] for row in store.table("import_keys")}
    for line_no, row in read_statement(path):
        reference = (row.get("reference") or "").strip()
        if not reference:
            result.rejected.append(f"line {line_no}: missing reference")
            continue
        key = import_key(source, reference)
        if key in known:
            result.skipped.append(reference)
            continue
        try:
            day = date.fromisoformat((row.get("date") or "").strip())
            amount = parse_amount(row.get("amount") or "", currency)
            if amount == 0:
                raise ValueError("zero amount")
            entry = post(store, _entry(row, day, amount, source, bank_account, clearing_account))
        except (ValueError, MissingRate) as error:
            result.rejected.append(f"line {line_no}: {error}")
            continue
        store.insert("import_keys", {"key": key})
        known.add(key)
        result.posted.append(entry.id)
    return result
