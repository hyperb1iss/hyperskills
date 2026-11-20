import unittest

from stockroom.reservations import (
    EXPIRED,
    FULFILLED,
    DuplicateReservation,
    NotHeld,
    ReservationBook,
    ReservationExpired,
    Unavailable,
)

from tests.helpers import make_stock


def make_book():
    stock, clock = make_stock()
    return ReservationBook(stock, clock), stock, clock


class ReserveTests(unittest.TestCase):
    def test_all_or_nothing_by_default(self):
        book, stock, _ = make_book()
        with self.assertRaises(Unavailable) as caught:
            book.reserve("o-1", "web", "MUG-02", 5, ["east"], ttl=600)
        self.assertEqual(caught.exception.available, 3)
        self.assertEqual(stock.reserved("MUG-02"), 0)

    def test_partial_hold_reports_shortfall(self):
        book, _, _ = make_book()
        reservation = book.reserve("o-1", "web", "MUG-02", 5, ["east"], ttl=600, allow_partial=True)
        self.assertEqual((reservation.held, reservation.shortfall), (3, 2))

    def test_spills_into_the_next_warehouse(self):
        book, _, _ = make_book()
        reservation = book.reserve("o-1", "web", "TEA-01", 20, ["east", "west"], ttl=600)
        self.assertEqual([(a.warehouse_id, a.quantity) for a in reservation.allocations],
                         [("east", 10), ("east", 6), ("west", 4)])

    def test_one_held_reservation_per_order_line(self):
        book, _, _ = make_book()
        book.reserve("o-1", "web", "TEA-01", 1, ["east"], ttl=600)
        with self.assertRaises(DuplicateReservation):
            book.reserve("o-1", "web", "TEA-01", 1, ["east"], ttl=600)
        book.reserve("o-1", "app", "TEA-01", 1, ["east"], ttl=600)


class LifecycleTests(unittest.TestCase):
    def test_release_frees_units(self):
        book, stock, _ = make_book()
        reservation = book.reserve("o-1", "web", "TEA-01", 5, ["west"], ttl=600)
        book.release(reservation.id)
        self.assertEqual(stock.available("TEA-01", "west"), 8)
        with self.assertRaises(NotHeld):
            book.release(reservation.id)

    def test_fulfill_picks_held_units(self):
        book, stock, _ = make_book()
        reservation = book.reserve("o-1", "web", "TEA-01", 5, ["west"], ttl=600)
        picked = book.fulfill(reservation.id)
        self.assertEqual([(p.bin_id, p.quantity) for p in picked], [("W-03", 5)])
        self.assertEqual((reservation.status, stock.on_hand("TEA-01", "west"), stock.reserved("TEA-01")),
                         (FULFILLED, 3, 0))

    def test_fulfill_after_expiry_releases_instead(self):
        book, stock, clock = make_book()
        reservation = book.reserve("o-1", "web", "TEA-01", 5, ["west"], ttl=60)
        clock.advance(60)
        with self.assertRaises(ReservationExpired):
            book.fulfill(reservation.id)
        self.assertEqual((reservation.status, stock.on_hand("TEA-01", "west")), (EXPIRED, 8))


if __name__ == "__main__":
    unittest.main()
