"""Refund file ingestion."""
import logging

log = logging.getLogger("ingest")


def parse_refunds(lines):
    """Parse 'id,amount,reason' lines. Malformed lines are skipped."""
    refunds = []
    for number, line in enumerate(lines, 1):
        parts = line.strip().split(",")
        try:
            refunds.append({"id": parts[0], "amount": float(parts[1]), "reason": parts[2]})
        except (IndexError, ValueError):
            log.warning("refunds line %d skipped: %r", number, line)
    return refunds
