import unittest
from datetime import datetime, timedelta, timezone

from stockpile.access import OPERATOR, VIEWER, WILDCARD, issue_key, set_scope
from stockpile.models import Bin
from stockpile.service import Request, ReservationService
from stockpile.store import Store

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.add_bin(Bin("A-01", "WH-1", "TEA-0001", 10))
        self.store.add_bin(Bin("B-01", "WH-2", "TEA-0001", 8))
        self.now = NOW
        self.service = ReservationService(self.store, lambda: self.now)
        self.operator_key, self.operator = issue_key(self.store, OPERATOR, ["WH-1"])
        _, self.elsewhere = issue_key(self.store, OPERATOR, ["WH-2"])
        _, self.viewer = issue_key(self.store, VIEWER, [WILDCARD])

    def call(self, route, token, body=None, *args):
        request = Request({"Authorization": "Bearer " + token}, body)
        return self.service.handle(route, request, *args)

    def reserve(self, token, **body):
        body = dict({"sku": "TEA-0001", "quantity": 2, "order_ref": "order-7", "bin_id": "A-01"}, **body)
        return self.call("reserve", token, body)

    def test_reserve_returns_the_hold(self):
        response = self.reserve(self.operator)
        self.assertEqual(response.status, 201)
        self.assertEqual(response.body["bin_id"], "A-01")
        self.assertEqual(response.body["status"], "held")

    def test_viewer_cannot_reserve(self):
        self.assertEqual(self.reserve(self.viewer).status, 403)

    def test_missing_token_is_unauthorized(self):
        response = self.service.handle("reserve", Request({}, {}))
        self.assertEqual(response.status, 401)

    def test_invalid_bodies_are_rejected(self):
        for body in ({"quantity": 0}, {"quantity": True}, {"sku": "tea"}, {"order_ref": ""},
                     {"bin_id": "Z-99"}, {"hold_minutes": 0}, {"hold_minutes": 1441},
                     {"hold_minutes": "15"}, {"hold_minutes": True}):
            with self.subTest(body=body):
                self.assertEqual(self.reserve(self.operator, **body).status, 400)
        self.assertEqual(self.call("reserve", self.operator, ["not", "an", "object"]).status, 400)

    def test_lifecycle_routes(self):
        rid = self.reserve(self.operator).body["reservation_id"]
        self.assertEqual(self.call("confirm", self.operator, None, rid).body["status"], "confirmed")
        self.assertEqual(self.call("pick", self.operator, None, rid).body["status"], "picked")
        self.assertEqual(self.call("cancel", self.operator, None, rid).status, 409)
        self.assertEqual(self.call("confirm", self.operator, None, 999).status, 404)

    def test_stock_reports_free_units(self):
        self.reserve(self.operator, quantity=3)
        response = self.call("stock", self.viewer, None, "WH-1", "tea-0001")
        self.assertEqual(response.body, {"warehouse_id": "WH-1", "sku": "TEA-0001", "available": 7})

    def test_keys_act_only_in_their_warehouses(self):
        self.assertEqual(self.reserve(self.elsewhere).status, 403)
        rid = self.reserve(self.operator).body["reservation_id"]
        self.assertEqual(self.call("confirm", self.elsewhere, None, rid).status, 403)
        self.assertEqual(self.call("stock", self.elsewhere, None, "WH-1", "TEA-0001").status, 403)
        self.assertEqual(self.reserve(self.elsewhere, bin_id="B-01").status, 201)

    def test_a_new_scope_applies_to_the_next_request(self):
        with self.assertRaises(ValueError):
            set_scope(self.store, self.operator_key.key_id, ["*", "WH-2"])
        set_scope(self.store, self.operator_key.key_id, ["WH-2"])
        self.assertEqual(self.reserve(self.operator).status, 403)
        self.assertEqual(self.reserve(self.operator, bin_id="B-01").status, 201)

    def test_confirming_a_lapsed_hold_is_a_conflict(self):
        self.assertIsNone(self.reserve(self.operator).body["expires_at"])
        body = self.reserve(self.operator, hold_minutes=10).body
        self.assertEqual(body["expires_at"], "2026-11-02T09:10:00+00:00")
        rid = body["reservation_id"]
        self.now = NOW + timedelta(minutes=10)
        response = self.call("confirm", self.operator, None, rid)
        self.assertEqual((response.status, response.body["error"]), (409, "hold_expired"))


if __name__ == "__main__":
    unittest.main()
