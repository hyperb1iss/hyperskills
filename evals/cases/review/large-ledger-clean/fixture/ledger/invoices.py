"""Customer invoices and the payments applied to them, in the ledger currency.

Issuing an invoice debits receivables and credits revenue. A payment debits the
bank and credits receivables; a payment larger than what is still open is refused.
"""
from dataclasses import dataclass
from datetime import date

from .journal import Entry, Line, post

RECEIVABLES = "1200"
BUCKETS = (("0-30", 30), ("31-60", 60), ("61-90", 90))


class InvoiceError(ValueError):
    pass


@dataclass(frozen=True)
class Invoice:
    id: int
    customer: str
    issued_on: date
    amount: int
    revenue_account: str


def _invoice(row):
    return Invoice(row["id"], row["customer"], date.fromisoformat(row["issued_on"]), row["amount"],
                   row["revenue_account"])


def issue_invoice(store, customer, issued_on, amount, revenue_account="4000"):
    if amount <= 0:
        raise InvoiceError("invoice amount must be positive")
    entry = post(store, Entry(issued_on, f"Invoice for {customer}",
                              [Line(RECEIVABLES, debit=amount), Line(revenue_account, credit=amount)]))
    return _invoice(store.insert("invoices", {"customer": customer, "issued_on": issued_on.isoformat(),
                                              "amount": amount, "revenue_account": revenue_account,
                                              "entry_id": entry.id}))


def open_amount(store, invoice_id, as_of=None):
    """What is still owed on an invoice, counting payments made on or before as_of."""
    invoice = store.one("invoices", id=invoice_id)
    paid = sum(row["amount"] for row in store.select("payments", invoice_id=invoice_id)
               if as_of is None or date.fromisoformat(row["paid_on"]) <= as_of)
    return invoice["amount"] - paid


def apply_payment(store, invoice_id, paid_on, amount, bank_account="1000"):
    """Record a payment; returns what remains open afterwards."""
    if amount <= 0:
        raise InvoiceError("payment amount must be positive")
    remaining = open_amount(store, invoice_id)
    if amount > remaining:
        raise InvoiceError(f"payment of {amount} exceeds the open amount {remaining}")
    entry = post(store, Entry(paid_on, f"Payment on invoice {invoice_id}",
                              [Line(bank_account, debit=amount), Line(RECEIVABLES, credit=amount)]))
    store.insert("payments", {"invoice_id": invoice_id, "paid_on": paid_on.isoformat(), "amount": amount,
                              "entry_id": entry.id})
    return remaining - amount


def aging(store, as_of):
    """Open amounts by age in days since issue: 0-30, 31-60, 61-90, and over 90."""
    totals = {name: 0 for name, _ in BUCKETS}
    totals["90+"] = 0
    for row in store.table("invoices"):
        issued = date.fromisoformat(row["issued_on"])
        if issued > as_of:
            continue
        owed = open_amount(store, row["id"], as_of)
        if not owed:
            continue
        age = (as_of - issued).days
        bucket = next((name for name, limit in BUCKETS if age <= limit), "90+")
        totals[bucket] += owed
    return totals
