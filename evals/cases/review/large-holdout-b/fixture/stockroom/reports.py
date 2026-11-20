"""Stock reports."""


def stock_report(stock, warehouse_ids):
    """Rows per SKU and warehouse: units on hand, units reserved, and units free to promise."""
    rows = []
    for warehouse_id in warehouse_ids:
        for sku in stock.skus(warehouse_id):
            rows.append({
                "warehouse": warehouse_id,
                "sku": sku,
                "units": stock.on_hand(sku, warehouse_id),
                "reserved": stock.reserved(sku, warehouse_id),
                "available": stock.available(sku, warehouse_id),
            })
    return rows


def low_stock(stock, warehouse_ids, threshold):
    """Rows whose units free to promise are at or below ``threshold``."""
    return [row for row in stock_report(stock, warehouse_ids) if row["available"] <= threshold]
