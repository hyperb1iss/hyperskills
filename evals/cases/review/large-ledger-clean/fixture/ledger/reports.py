"""Income statement for a date range. Income and expense accounts are kept in the ledger currency."""
from datetime import timedelta

from .accounts import list_accounts
from .balances import natural_balance
from .money import format_amount


def period_total(store, code, start, end):
    """Natural-side movement on an account from start through end."""
    before = natural_balance(store, code, start - timedelta(days=1))
    return natural_balance(store, code, end) - before


def income_statement(store, start, end):
    income = {a.code: period_total(store, a.code, start, end) for a in list_accounts(store, "income")}
    expenses = {a.code: period_total(store, a.code, start, end) for a in list_accounts(store, "expense")}
    return {"income": income, "expenses": expenses,
            "net": sum(income.values()) - sum(expenses.values())}


def format_income_statement(store, start, end):
    statement = income_statement(store, start, end)
    names = {a.code: a.name for a in list_accounts(store)}
    out = [f"Income statement {start} to {end}"]
    for heading in ("income", "expenses"):
        out.append(heading.capitalize())
        for code, amount in sorted(statement[heading].items()):
            if amount:
                out.append(f"  {code} {names[code]:<26} {format_amount(amount):>14}")
    out.append(f"Net {format_amount(statement['net']):>40}")
    return "\n".join(out)

