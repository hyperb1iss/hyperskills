"""Proof for the reservations change: one test per independent property.

Run with the fixture root on sys.path. All three fail on the defect fixture and
pass on the clean one.
"""
import unittest
from datetime import date, datetime, timezone

from stockroom import api
from stockroom.counting import reconcile
from stockroom.events import EventLog
from stockroom.models import Bin, Principal
from stockroom.reservations import ReservationBook
from stockroom.settings import Settings
from stockroom.stock import Stock


def clock():
    return datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc)


def make_stock():
    stock = Stock(clock, EventLog())
    stock.add_bin(Bin("east", "E-01", "TEA-01", on_hand=10, pick_order=1, received_on=date(2026, 3, 1)))
    stock.add_bin(Bin("east", "E-09", "TEA-01", on_hand=6, pick_order=9, received_on=date(2026, 3, 20)))
    stock.add_bin(Bin("west", "W-03", "TEA-01", on_hand=8, pick_order=3, received_on=date(2026, 3, 5)))
    return stock


class ReservationsProof(unittest.TestCase):
    def test_reserve_without_warehouse_stays_in_callers_warehouses(self):
        stock = make_stock()
        ctx = api.Context(stock, Settings(), ReservationBook(stock, clock))
        east_only = Principal("k-east", frozenset({"reservations:write"}), frozenset({"east"}), "web")
        status, _ = api.reserve(ctx, east_only, {"sku": "TEA-01", "order_id": "o-9", "quantity": 20,
                                                 "allow_partial": True})
        self.assertEqual(status, 201)
        self.assertEqual(stock.bin("west", "W-03").reserved, 0)

    def test_cycle_count_of_reserved_stock_posts_nothing(self):
        stock = make_stock()
        ReservationBook(stock, clock).reserve("o-1", "web", "TEA-01", 5, ["east"], ttl=600)
        posted = reconcile(stock, "east", {"TEA-01": 16})
        self.assertEqual(posted, {})
        self.assertEqual(stock.on_hand("TEA-01", "east"), 16)

    def test_pick_takes_oldest_stock_first(self):
        stock = make_stock()
        stock.add_bin(Bin("west", "W-20", "JAM-5", on_hand=5, pick_order=20, received_on=date(2026, 2, 1)))
        stock.add_bin(Bin("west", "W-04", "JAM-5", on_hand=5, pick_order=4, received_on=date(2026, 3, 25)))
        self.assertEqual(stock.pick("JAM-5", "west", 3), [("W-20", 3)])


if __name__ == "__main__":
    unittest.main()
