"""When a user's digest is due, and where its first window starts."""

from datetime import timedelta

PERIODS = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}


def is_due(prefs, local_now):
    """Whether ``prefs`` asks for a digest in the hour containing ``local_now``.

    ``local_now`` is the current time in the user's own offset.
    """
    if prefs.digest not in PERIODS:
        return False
    if local_now.hour != prefs.digest_hour:
        return False
    if prefs.digest == "weekly":
        return local_now.weekday() == prefs.digest_weekday
    return True


def slot_start(local_now):
    """Start of the delivery slot, the local hour, that contains ``local_now``."""
    return local_now.replace(minute=0, second=0, microsecond=0)


def first_window_start(prefs, now):
    """Start of a user's first digest window: one period before ``now``."""
    return now - PERIODS[prefs.digest]
