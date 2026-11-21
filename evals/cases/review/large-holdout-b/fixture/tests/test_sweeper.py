import unittest

from stockroom.reservations import EXPIRED, HELD, ReservationBook, UnknownReservation
from stockroom.sweeper import SweepResult, sweep

from tests.helpers import make_stock


class SweepTests(unittest.TestCase):
    def test_expires_only_due_reservations(self):
        stock, clock = make_stock()
        book = ReservationBook(stock, clock)
        short = book.reserve("o-1", "web", "TEA-01", 4, ["west"], ttl=60)
        long = book.reserve("o-2", "web", "TEA-01", 2, ["west"], ttl=3600)
        clock.advance(120)
        self.assertEqual(sweep(book, clock()), SweepResult(expired=1, units=4))
        self.assertEqual((short.status, long.status), (EXPIRED, HELD))
        self.assertEqual(stock.available("TEA-01", "west"), 6)
        clock.advance(8 * 86400)
        sweep(book, clock())
        self.assertRaises(UnknownReservation, book.get, short.id)


if __name__ == "__main__":
    unittest.main()
