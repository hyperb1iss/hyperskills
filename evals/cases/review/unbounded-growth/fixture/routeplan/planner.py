"""Turn a list of delivery stops into an ordered route."""
from dataclasses import dataclass, field


@dataclass
class Plan:
    stops: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)


def distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def plan_route(client, depot, addresses):
    plan = Plan()
    points = client.lookup_many(addresses)
    for address in addresses:
        point = points[address]
        if point is None:
            plan.unresolved.append(address)
        else:
            plan.stops.append((address, point))
    plan.stops.sort(key=lambda stop: distance(depot, stop[1]))
    return plan
