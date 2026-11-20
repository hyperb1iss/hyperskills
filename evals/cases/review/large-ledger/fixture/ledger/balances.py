"""Account balances from posted lines, in the base currency unless noted."""
from .accounts import get_account, list_accounts
from .journal import lines_for
from .money import format_amount


def balance(store, code, through=None):
    """Signed base-currency balance, debits positive."""
    return sum(row["base_debit"] - row["base_credit"] for _, row in lines_for(store, code, through))


def foreign_balance(store, code, through=None):
    """Signed balance in the account's own currency, debits positive."""
    return sum(row["debit"] - row["credit"] for _, row in lines_for(store, code, through))


def natural_balance(store, code, through=None):
    """Base-currency balance with the account's normal side positive."""
    value = balance(store, code, through)
    return value if get_account(store, code).debit_normal else -value


def trial_balance(store, through=None):
    return {account.code: balance(store, account.code, through) for account in list_accounts(store)}


def format_trial_balance(store, through=None):
    rows = []
    for account in list_accounts(store):
        rows.append(f"{account.code}  {account.name:<28} {format_amount(balance(store, account.code, through)):>16}")
    return "\n".join(rows)
