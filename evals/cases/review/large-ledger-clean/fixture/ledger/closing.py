"""Month-end close: revalue foreign balances, check the trial balance, lock the period."""
from .balances import trial_balance
from .periods import PeriodClosed, closed_through
from .revaluation import FX_GAIN, FX_LOSS, revalue


class CloseError(ValueError):
    pass


def close_period(store, end, gain_account=FX_GAIN, loss_account=FX_LOSS):
    """Close the books through end; returns the trial balance the period closed on."""
    last = closed_through(store)
    if last is not None and end <= last:
        raise PeriodClosed(f"already closed through {last}")
    revaluation = revalue(store, end, gain_account, loss_account)
    balances = trial_balance(store, end)
    off_by = sum(balances.values())
    if off_by:
        raise CloseError(f"trial balance through {end} is off by {off_by}")
    store.insert("periods", {"end": end.isoformat(), "revaluation_entry": revaluation.entry_id})
    return balances
