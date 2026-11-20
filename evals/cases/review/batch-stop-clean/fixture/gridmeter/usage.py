"""Consumption from cumulative register readings."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Interval:
    meter_id: str
    start: datetime
    end: datetime
    wh: int


class RegisterWentBackwards(ValueError):
    pass


def intervals(readings):
    """Pair consecutive readings of one meter into consumption intervals."""
    ordered = sorted(readings, key=lambda r: r.taken_at)
    if len({r.meter_id for r in ordered}) > 1:
        raise ValueError("intervals() takes readings for a single meter")
    result = []
    for before, after in zip(ordered, ordered[1:]):
        used = after.wh - before.wh
        if used < 0:
            raise RegisterWentBackwards(f"meter {after.meter_id} dropped at {after.taken_at:%Y-%m-%d %H:%M}")
        result.append(Interval(after.meter_id, before.taken_at, after.taken_at, used))
    return result


def daily_totals(interval_list):
    """Sum consumption by the UTC day each interval ends on."""
    totals = {}
    for interval in interval_list:
        day = interval.end.date()
        totals[day] = totals.get(day, 0) + interval.wh
    return dict(sorted(totals.items()))
