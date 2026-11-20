"""Cycle counts: compare counted units with the system and post the difference."""

from .snapshots import warehouse_snapshot


def count_sheet(stock, warehouse_id):
    """Rows for the printed count sheet: (sku, expected units)."""
    return sorted(warehouse_snapshot(stock, warehouse_id).items())


def reconcile(stock, warehouse_id, counted):
    """Post counted totals for a warehouse. ``counted`` maps SKU to units found.

    Each difference is posted to the SKU's home bin as a "cycle count"
    adjustment. Returns {sku: posted difference} for the SKUs that differed.
    """
    for sku, units in counted.items():
        if type(units) is not int or units < 0:
            raise ValueError(f"count for {sku} must be a non-negative integer")
    expected = warehouse_snapshot(stock, warehouse_id)
    posted = {}
    for sku, units in sorted(counted.items()):
        difference = units - expected.get(sku, 0)
        if difference:
            stock.adjust(sku, warehouse_id, None, difference, "cycle count")
            posted[sku] = difference
    return posted
