from datetime import date, datetime, timedelta, timezone

from stockroom.events import EventLog
from stockroom.models import Bin
from stockroom.stock import Stock


class FakeClock:
    def __init__(self, start=datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc)):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


def make_stock(clock=None):
    """Two warehouses. SKU TEA-01 sits in east (two bins) and west; MUG-02 only in east."""
    clock = clock or FakeClock()
    stock = Stock(clock, EventLog())
    stock.add_bin(Bin("east", "E-01", "TEA-01", on_hand=10, pick_order=1, received_on=date(2026, 3, 1)))
    stock.add_bin(Bin("east", "E-09", "TEA-01", on_hand=6, pick_order=9, received_on=date(2026, 3, 20)))
    stock.add_bin(Bin("west", "W-03", "TEA-01", on_hand=8, pick_order=3, received_on=date(2026, 3, 5)))
    stock.add_bin(Bin("east", "E-04", "MUG-02", on_hand=3, pick_order=4, received_on=date(2026, 2, 1)))
    return stock, clock
