"""Order file ingestion."""
import logging

log = logging.getLogger("ingest")


def parse_orders(lines):
    """Parse 'id,amount' lines. Malformed lines are skipped."""
    orders = []
    for number, line in enumerate(lines, 1):
        parts = line.strip().split(",")
        try:
            orders.append({"id": parts[0], "amount": float(parts[1])})
        except (IndexError, ValueError):
            log.warning("orders line %d skipped: %r", number, line)
    return orders
