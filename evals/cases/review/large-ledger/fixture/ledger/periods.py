"""Accounting periods. Once a period is closed, nothing may be posted on or before its end."""
from datetime import date


class PeriodClosed(ValueError):
    pass


def closed_through(store):
    """The end of the latest closed period, or None when nothing is closed."""
    return max((date.fromisoformat(row["end"]) for row in store.table("periods")), default=None)


def ensure_open(store, day):
    last = closed_through(store)
    if last is not None and day <= last:
        raise PeriodClosed(f"{day} falls in a closed period (closed through {last})")


def reopen(store, end):
    """Reopen the latest period; only the most recent close can be undone."""
    last = closed_through(store)
    if last is None or last != end:
        raise PeriodClosed(f"only the latest close ({last}) can be reopened")
    store.table("periods").remove(store.one("periods", end=end.isoformat()))
