"""Order pricing."""

BULK_THRESHOLD = 10
BULK_DISCOUNT = 0.1


def order_total(unit_price, quantity):
    """Total for an order. Orders at or above the bulk threshold get the bulk discount."""
    total = unit_price * quantity
    if quantity > BULK_THRESHOLD:
        total *= 1 - BULK_DISCOUNT
    return round(total, 2)
