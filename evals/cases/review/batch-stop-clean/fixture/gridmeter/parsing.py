"""Turn vendor CSV rows into readings."""
from dataclasses import dataclass
from datetime import datetime, timezone

from .units import UnitError, to_wh


@dataclass(frozen=True)
class Reading:
    meter_id: str
    taken_at: datetime
    wh: int


class RowError(ValueError):
    pass


def _parse_time(text):
    """Older drops use 'YYYY-MM-DD HH:MM' in UTC; newer ones use ISO 8601 with a time and an offset."""
    text = text.strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise ValueError(f"ISO timestamp without a UTC offset: {text!r}")
    return moment.astimezone(timezone.utc)


def parse_row(row):
    meter_id = (row.get("meter") or "").strip()
    if not meter_id:
        raise RowError("missing meter id")
    try:
        taken_at = _parse_time(row["timestamp"])
    except (KeyError, AttributeError, ValueError):
        raise RowError(f"meter {meter_id}: bad timestamp") from None
    try:
        wh = to_wh(row.get("value") or "", row.get("unit") or "kWh")
    except UnitError as error:
        raise RowError(f"meter {meter_id}: {error}") from None
    return Reading(meter_id, taken_at, wh)
