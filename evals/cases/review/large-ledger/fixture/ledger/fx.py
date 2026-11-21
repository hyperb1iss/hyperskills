"""Exchange rates: the base-currency value of one unit, in effect from its date until the next one.

Treasury also loads a closing rate dated on each period end for revaluation.
"""
import bisect
from datetime import date
from decimal import Decimal

from .money import BASE_CURRENCY, exponent, to_major, to_minor


class MissingRate(LookupError):
    pass


class RateTable:
    def __init__(self):
        self._days = {}
        self._rates = {}

    def add(self, currency, effective_on, rate):
        exponent(currency)
        if currency == BASE_CURRENCY:
            raise ValueError("the base currency has no rate")
        if rate <= 0:
            raise ValueError(f"rate must be positive, got {rate}")
        days = self._days.setdefault(currency, [])
        rates = self._rates.setdefault(currency, [])
        index = bisect.bisect_left(days, effective_on)
        if index < len(days) and days[index] == effective_on:
            rates[index] = rate
        else:
            days.insert(index, effective_on)
            rates.insert(index, rate)

    def find(self, currency, day):
        """The rate in effect on day, or None before the currency's first rate."""
        days = self._days.get(currency, [])
        index = bisect.bisect_left(days, day) - 1
        return self._rates[currency][index] if index >= 0 else None

    def closing(self, currency, day):
        """The rate dated exactly on day, or None."""
        days = self._days.get(currency, [])
        index = bisect.bisect_left(days, day)
        if index < len(days) and days[index] == day:
            return self._rates[currency][index]
        return None

    def rate_on(self, currency, day):
        rate = self.find(currency, day)
        if rate is None:
            raise MissingRate(f"no {currency} rate on or before {day}")
        return rate

    def closing_rate(self, currency, day):
        rate = self.closing(currency, day)
        if rate is None:
            raise MissingRate(f"no closing {currency} rate dated {day}")
        return rate


def load_rates(store):
    table = RateTable()
    for row in store.table("rates"):
        table.add(row["currency"], date.fromisoformat(row["effective_on"]), Decimal(row["rate"]))
    return table


def record_rate(store, currency, effective_on, rate):
    """Store a rate; a second rate for the same currency and day replaces the first."""
    RateTable().add(currency, effective_on, rate)
    for row in store.select("rates", currency=currency, effective_on=effective_on.isoformat()):
        store.table("rates").remove(row)
    store.insert("rates", {"currency": currency, "effective_on": effective_on.isoformat(), "rate": str(rate)})


def to_base(rates, minor, currency, day):
    """Convert minor units of currency on day to base-currency minor units."""
    if currency == BASE_CURRENCY:
        return minor
    return to_minor(to_major(minor, currency) * rates.rate_on(currency, day), BASE_CURRENCY)
