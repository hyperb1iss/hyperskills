import unittest

from routeplan.client import GeocodeClient
from routeplan.planner import plan_route

POINTS = {"1 a st": (1.0, 0.0), "2 b st": (-1.5, 0.0), "3 c st": (3.0, 0.0)}


class Backend:
    def geocode_batch(self, keys):
        return {key: POINTS[key] for key in keys if key in POINTS}


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.client = GeocodeClient(Backend(), clock=lambda: 0)

    def test_unknown_addresses_are_reported(self):
        plan = plan_route(self.client, (0.0, 0.0), ["1 A St", "99 Nowhere Ln"])
        self.assertEqual([address for address, _ in plan.stops], ["1 A St"])
        self.assertEqual(plan.unresolved, ["99 Nowhere Ln"])

    def test_closest_stops_come_first(self):
        plan = plan_route(self.client, (0.0, 0.0), ["3 C St", "1 A St"])
        self.assertEqual([address for address, _ in plan.stops], ["1 A St", "3 C St"])


if __name__ == "__main__":
    unittest.main()
