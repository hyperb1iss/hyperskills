"""Energy unit conversion. Readings are stored as whole watt-hours."""
from decimal import Decimal, InvalidOperation

FACTORS = {
    "wh": 1,
    "kwh": 1000,
}


class UnitError(ValueError):
    pass


def to_wh(value, unit):
    try:
        factor = FACTORS[unit.strip().lower()]
    except KeyError:
        raise UnitError(f"unknown unit {unit!r}") from None
    try:
        amount = Decimal(value.strip())
    except InvalidOperation:
        raise UnitError(f"not a number: {value!r}") from None
    if not amount.is_finite() or amount < 0 or amount.adjusted() > 15:
        raise UnitError(f"not a usable reading: {value!r}")
    return int((amount * factor).to_integral_value())
