"""Stock reports for warehouse supervisors."""
from datetime import timedelta

from . import inventory


def stock_report(store, catalog, warehouse_id):
    """One line per SKU stocked in warehouse_id, ordered by SKU.

    on_hand is what the shelves hold; available is what a new reservation could
    still take, so the difference is stock promised to open reservations.
    """
    with store.lock:
        lines = {}
        for bin_ in store.bins(warehouse_id=warehouse_id):
            line = lines.setdefault(bin_.sku, {
                "sku": bin_.sku,
                "description": catalog.describe(bin_.sku),
                "bins": 0,
                "on_hand": 0,
            })
            line["bins"] += 1
            line["on_hand"] += bin_.quantity
        for sku, line in lines.items():
            line["available"] = inventory.available(store, warehouse_id, sku)
        return [lines[sku] for sku in sorted(lines)]


def expiring_lots(store, warehouse_id, today, within_days=14):
    """Bins in warehouse_id whose lot expires on or before today + within_days, soonest first."""
    horizon = today + timedelta(days=within_days)
    found = [bin_ for bin_ in store.bins(warehouse_id=warehouse_id)
             if bin_.lot_expires is not None and bin_.lot_expires <= horizon]
    return sorted(found, key=lambda bin_: (bin_.lot_expires, bin_.bin_id))


def low_stock(store, warehouse_id, threshold):
    """SKUs in warehouse_id with fewer than threshold available units, as (sku, available)."""
    skus = sorted({bin_.sku for bin_ in store.bins(warehouse_id=warehouse_id)})
    levels = [(sku, inventory.available(store, warehouse_id, sku)) for sku in skus]
    return [(sku, units) for sku, units in levels if units < threshold]


def send_low_stock_alerts(store, notifier, recipient, warehouse_id, threshold):
    """Notify recipient once per low SKU; return the SKUs alerted.

    A failed send raises NotifyError after the SKUs before it were sent, and the
    caller retries the whole report on its next run.
    """
    alerted = []
    for sku, units in low_stock(store, warehouse_id, threshold):
        notifier.send(recipient, "low_stock",
                      {"warehouse_id": warehouse_id, "sku": sku, "available": units})
        alerted.append(sku)
    return alerted
