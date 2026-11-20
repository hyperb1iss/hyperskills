"""Point-in-time stock figures for count sheets and the nightly finance export.

The host's scheduler calls nightly_export() once a day after the last shift.
"""


def warehouse_snapshot(stock, warehouse_id):
    """Units of each SKU physically in ``warehouse_id``, keyed by SKU."""
    return {sku: stock.available(sku, warehouse_id) for sku in stock.skus(warehouse_id)}


def nightly_export(stock, today):
    """Rows for the finance export: (date, warehouse, sku, units on the shelves)."""
    rows = []
    for warehouse_id in stock.warehouse_ids():
        for sku, units in sorted(warehouse_snapshot(stock, warehouse_id).items()):
            rows.append((today.isoformat(), warehouse_id, sku, units))
    return rows
