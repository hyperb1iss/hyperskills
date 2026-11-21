import unittest
from datetime import date, datetime, timezone

from gridmeter.parsing import Reading
from gridmeter.usage import RegisterWentBackwards, daily_totals, intervals


def reading(hour, wh, meter="m-1", day=1):
    return Reading(meter, datetime(2026, 3, day, hour, 0, tzinfo=timezone.utc), wh)


class UsageTests(unittest.TestCase):
    def test_intervals_follow_time_order(self):
        result = intervals([reading(12, 1500), reading(10, 1000), reading(11, 1200)])
        self.assertEqual([i.wh for i in result], [200, 300])

    def test_single_reading_has_no_interval(self):
        self.assertEqual(intervals([reading(10, 1000)]), [])

    def test_register_going_backwards_is_an_error(self):
        with self.assertRaises(RegisterWentBackwards):
            intervals([reading(10, 1000), reading(11, 900)])

    def test_mixed_meters_are_rejected(self):
        with self.assertRaises(ValueError):
            intervals([reading(10, 1000), reading(11, 1100, meter="m-2")])

    def test_daily_totals(self):
        result = intervals([reading(22, 1000), reading(23, 1400), reading(1, 1500, day=2)])
        self.assertEqual(daily_totals(result), {date(2026, 3, 1): 400, date(2026, 3, 2): 100})


if __name__ == "__main__":
    unittest.main()
