import unittest
from datetime import time

from routeplan.windows import Window, overlap, parse_window


class WindowTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_window("09:00-12:30"), Window(time(9, 0), time(12, 30)))

    def test_blank_is_all_day(self):
        self.assertTrue(parse_window(" ").contains(time(23, 0)))

    def test_end_is_exclusive(self):
        window = parse_window("09:00-12:00")
        self.assertTrue(window.contains(time(9, 0)))
        self.assertFalse(window.contains(time(12, 0)))

    def test_rejects_garbage_and_backwards_windows(self):
        for text in ("morning", "12:00-09:00", "09:00-10:00-11:00"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_window(text)

    def test_overlap(self):
        self.assertEqual(overlap(parse_window("09:00-12:00"), parse_window("11:00-14:00")), parse_window("11:00-12:00"))
        self.assertIsNone(overlap(parse_window("09:00-11:00"), parse_window("11:00-14:00")))


if __name__ == "__main__":
    unittest.main()
