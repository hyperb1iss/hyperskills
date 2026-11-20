"""Period-end revaluation: restate each foreign balance at the closing rate and post the difference.

Running it twice for the same day posts nothing the second time.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .accounts import list_accounts
from .balances import balance, foreign_balance
from .fx import load_rates
from .journal import post_adjustment
from .money import BASE_CURRENCY, to_major, to_minor

FX_GAIN = "7910"
FX_LOSS = "7920"


@dataclass
class Revaluation:
    period_end: date
    adjustments: dict = field(default_factory=dict)
    entry_id: Optional[int] = None


def revalue(store, period_end, gain_account=FX_GAIN, loss_account=FX_LOSS):
    """Restate every foreign-currency balance at the period end's closing rate."""
    rates = load_rates(store)
    adjustments = []
    for account in list_accounts(store):
        if account.currency == BASE_CURRENCY:
            continue
        native = foreign_balance(store, account.code, period_end)
        carried = balance(store, account.code, period_end)
        if native == 0 and carried == 0:
            continue
        rate = rates.closing(account.currency, period_end)
        if rate is None:
            continue
        restated = to_minor(to_major(native, account.currency) * rate, BASE_CURRENCY)
        if restated != carried:
            adjustments.append((account.code, restated - carried))
    result = Revaluation(period_end, dict(adjustments))
    net = sum(amount for _, amount in adjustments)
    if net:
        adjustments.append((gain_account if net > 0 else loss_account, -net))
    if adjustments:
        result.entry_id = post_adjustment(store, period_end, f"Revaluation at {period_end}", adjustments)
    return result
