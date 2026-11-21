import unittest
from datetime import datetime, timedelta, timezone

from stockpile import inventory, reservations
from stockpile.models import CANCELLED, CONFIRMED, EXPIRED, HELD, PICKED, Bin
from stockpile.store import Store

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)


class ReservationTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.add_bin(Bin("A-01", "WH-1", "TEA-0001", 10))
        self.store.add_bin(Bin("A-02", "WH-1", "CUP-0002", 4))

    def hold(self, quantity, bin_id="A-01", sku="TEA-0001", hold=None):
        return reservations.reserve(self.store, "key-1", "order-1", sku, bin_id, quantity, NOW, hold)

    def test_hold_reduces_free_stock_but_not_the_shelf(self):
        reservation = self.hold(4)
        self.assertEqual(reservation.status, HELD)
        self.assertEqual(inventory.free_in_bin(self.store, "A-01"), 6)
        self.assertEqual(self.store.bin("A-01").quantity, 10)

    def test_holds_cannot_promise_more_than_is_free(self):
        self.hold(7)
        with self.assertRaises(reservations.InsufficientStock):
            self.hold(4)
        self.assertEqual(len(self.store.reservations()), 1)

    def test_wrong_sku_is_rejected(self):
        with self.assertRaises(reservations.WrongSku):
            self.hold(1, bin_id="A-02")

    def test_confirm_then_pick_takes_units_off_the_shelf(self):
        reservation = self.hold(3)
        self.assertEqual(reservations.confirm(self.store, reservation.reservation_id, NOW).status,
                         CONFIRMED)
        self.assertEqual(reservations.pick(self.store, reservation.reservation_id).status, PICKED)
        self.assertEqual(self.store.bin("A-01").quantity, 7)
        self.assertEqual(inventory.free_in_bin(self.store, "A-01"), 7)

    def test_cancel_frees_the_units(self):
        reservation = self.hold(5)
        self.assertEqual(reservations.cancel(self.store, reservation.reservation_id).status, CANCELLED)
        self.assertEqual(inventory.free_in_bin(self.store, "A-01"), 10)

    def test_short_pick_changes_nothing(self):
        reservation = self.hold(6)
        reservations.confirm(self.store, reservation.reservation_id, NOW)
        inventory.adjust(self.store, "A-01", 5)
        with self.assertRaises(reservations.ShortPick):
            reservations.pick(self.store, reservation.reservation_id)
        self.assertEqual(self.store.bin("A-01").quantity, 5)
        self.assertEqual(self.store.reservation(reservation.reservation_id).status, CONFIRMED)

    def test_a_hold_window_sets_expires_at(self):
        self.assertEqual(self.hold(2, hold=timedelta(minutes=15)).expires_at, NOW + timedelta(minutes=15))
        self.assertIsNone(self.hold(1).expires_at)
        for hold in (timedelta(0), timedelta(minutes=-5), reservations.MAX_HOLD + timedelta(seconds=1)):
            with self.subTest(hold=hold), self.assertRaises(ValueError):
                self.hold(1, hold=hold)

    def test_a_lapsed_hold_frees_its_units_before_the_worker_runs(self):
        reservation = self.hold(6, hold=timedelta(minutes=10))
        self.assertEqual(inventory.free_in_bin(self.store, "A-01", NOW), 4)
        self.assertEqual(inventory.free_in_bin(self.store, "A-01", reservation.expires_at), 10)
        self.assertEqual(self.store.reservation(reservation.reservation_id).status, HELD)

    def test_expire_hold_only_expires_lapsed_holds(self):
        reservation = self.hold(2, hold=timedelta(minutes=10))
        rid = reservation.reservation_id
        self.assertFalse(reservations.expire_hold(self.store, rid, NOW))
        self.assertTrue(reservations.expire_hold(self.store, rid, reservation.expires_at))
        self.assertEqual(self.store.reservation(rid).status, EXPIRED)
        self.assertFalse(reservations.expire_hold(self.store, rid, reservation.expires_at))

    def test_status_only_moves_forward(self):
        reservation = self.hold(1)
        reservations.cancel(self.store, reservation.reservation_id)
        with self.assertRaises(reservations.InvalidTransition):
            reservations.confirm(self.store, reservation.reservation_id, NOW)


if __name__ == "__main__":
    unittest.main()
