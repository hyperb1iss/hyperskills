import unittest

from stockroom import api
from stockroom.models import Principal
from stockroom.reservations import ReservationBook
from stockroom.settings import Settings

from tests.helpers import make_stock

ADMIN = Principal("k-admin", frozenset({"admin"}))
EAST_CLERK = Principal("k-clerk", frozenset({"stock:read", "stock:write"}), frozenset({"east"}))
WEB = Principal("k-web", frozenset({"reservations:write", "stock:write"}), frozenset({"east", "west"}), "web")
APP = Principal("k-app", frozenset({"reservations:write", "stock:write"}), frozenset({"east", "west"}), "app")


def make_ctx(**settings):
    stock, clock = make_stock()
    return api.Context(stock, Settings(**settings), ReservationBook(stock, clock))


class StockHandlerTests(unittest.TestCase):
    def test_get_stock_limited_to_visible_warehouses(self):
        status, body = api.get_stock(make_ctx(), EAST_CLERK, {})
        self.assertEqual(status, 200)
        self.assertEqual({row["warehouse"] for row in body["rows"]}, {"east"})

    def test_get_stock_for_hidden_warehouse_is_forbidden(self):
        status, _ = api.get_stock(make_ctx(), EAST_CLERK, {"warehouse_id": "west"})
        self.assertEqual(status, 403)

    def test_adjust_validates_delta(self):
        ctx = make_ctx(max_adjustment=5)
        body = {"sku": "TEA-01", "warehouse_id": "east", "delta": 6, "reason": "count"}
        self.assertEqual(api.adjust(ctx, EAST_CLERK, body)[0], 400)
        body["delta"] = True
        self.assertEqual(api.adjust(ctx, EAST_CLERK, body)[0], 400)

    def test_adjust_in_other_warehouse_is_forbidden(self):
        body = {"sku": "TEA-01", "warehouse_id": "west", "delta": 1, "reason": "count"}
        self.assertEqual(api.adjust(make_ctx(), EAST_CLERK, body)[0], 403)

    def test_receive_and_pick(self):
        ctx = make_ctx()
        body = {"sku": "MUG-02", "warehouse_id": "east", "quantity": 2, "received_on": "2026-04-01"}
        self.assertEqual(api.receive(ctx, EAST_CLERK, body), (200, {"bin": "E-04", "on_hand": 5}))
        status, picked = api.pick(ctx, EAST_CLERK, {"sku": "MUG-02", "warehouse_id": "east", "quantity": 4})
        self.assertEqual((status, picked["takes"]), (200, [{"bin": "E-04", "quantity": 4}]))

    def test_receive_rejects_bad_date(self):
        body = {"sku": "MUG-02", "warehouse_id": "east", "quantity": 2, "received_on": "April"}
        self.assertEqual(api.receive(make_ctx(), EAST_CLERK, body)[0], 400)


class ReserveHandlerTests(unittest.TestCase):
    def test_reserve_without_warehouse_follows_priority(self):
        ctx = make_ctx(warehouse_priority=("west",))
        status, body = api.reserve(ctx, WEB, {"sku": "TEA-01", "order_id": "o-1", "quantity": 10})
        self.assertEqual(status, 201)
        self.assertEqual([(a["warehouse"], a["quantity"]) for a in body["allocations"]], [("west", 8), ("east", 2)])

    def test_reserve_needs_a_channel_key(self):
        body = {"sku": "TEA-01", "order_id": "o-1", "quantity": 1, "warehouse_id": "east"}
        self.assertEqual(api.reserve(make_ctx(), EAST_CLERK, body)[0], 403)

    def test_reserve_in_forbidden_warehouse(self):
        limited = Principal("k-web2", frozenset({"reservations:write"}), frozenset({"east"}), "web")
        body = {"sku": "TEA-01", "order_id": "o-1", "quantity": 1, "warehouse_id": "west"}
        self.assertEqual(api.reserve(make_ctx(), limited, body)[0], 403)

    def test_reserve_validates_quantity_and_ttl(self):
        ctx = make_ctx(max_reservation_ttl=900)
        base = {"sku": "TEA-01", "order_id": "o-1", "warehouse_id": "east"}
        self.assertEqual(api.reserve(ctx, WEB, dict(base, quantity=0))[0], 400)
        self.assertEqual(api.reserve(ctx, WEB, dict(base, quantity=1, ttl_seconds=901))[0], 400)


class ReservationHandlerTests(unittest.TestCase):
    def setUp(self):
        self.ctx = make_ctx()
        _, body = api.reserve(self.ctx, WEB, {"sku": "TEA-01", "order_id": "o-1", "quantity": 4,
                                              "warehouse_id": "west"})
        self.reservation_id = body["id"]

    def test_other_channel_sees_unknown_reservation(self):
        body = {"reservation_id": self.reservation_id}
        self.assertEqual(api.release_reservation(self.ctx, APP, body)[0], 404)
        self.assertEqual(api.fulfill_reservation(self.ctx, APP, body)[0], 404)

    def test_fulfill(self):
        status, body = api.fulfill_reservation(self.ctx, WEB, {"reservation_id": self.reservation_id})
        self.assertEqual((status, body["picked"]), (200, [{"warehouse": "west", "bin": "W-03", "quantity": 4}]))


if __name__ == "__main__":
    unittest.main()
