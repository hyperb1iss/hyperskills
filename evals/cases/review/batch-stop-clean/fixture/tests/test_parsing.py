import unittest
from datetime import datetime, timezone

from gridmeter.parsing import RowError, parse_row


def row(**overrides):
    values = {"meter": "m-1", "timestamp": "2026-03-01 10:00", "value": "1.5", "unit": "kWh"}
    values.update(overrides)
    return values


class ParseRowTests(unittest.TestCase):
    def test_kwh_row(self):
        reading = parse_row(row())
        self.assertEqual(reading.wh, 1500)
        self.assertEqual(reading.taken_at, datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc))

    def test_unit_defaults_to_kwh(self):
        self.assertEqual(parse_row(row(unit="")).wh, 1500)

    def test_missing_meter(self):
        with self.assertRaises(RowError):
            parse_row(row(meter=" "))

    def test_bad_timestamp(self):
        with self.assertRaisesRegex(RowError, "meter m-1: bad timestamp"):
            parse_row(row(timestamp="yesterday"))

    def test_bad_value_names_the_meter(self):
        with self.assertRaisesRegex(RowError, "meter m-1: not a number"):
            parse_row(row(value="abc"))

    def test_offset_timestamp_is_stored_in_utc(self):
        reading = parse_row(row(timestamp="2026-03-01T11:00:00+01:00"))
        self.assertEqual(reading.taken_at, datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc))

    def test_timestamp_needs_a_time_and_an_offset(self):
        for value in ("2026-03-01", "2026-03-01T10:00"):
            with self.subTest(value=value), self.assertRaises(RowError):
                parse_row(row(timestamp=value))

    def test_negative_value(self):
        with self.assertRaises(RowError):
            parse_row(row(value="-2"))


if __name__ == "__main__":
    unittest.main()
