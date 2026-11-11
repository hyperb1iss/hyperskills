"""Nightly invoice sync."""
import logging

log = logging.getLogger("jobs")


def sync_invoices(invoices, client):
    """Push each invoice to billing. Returns the number synced."""
    synced = 0
    for invoice in invoices:
        try:
            client.upsert_invoice(invoice)
        except Exception as exc:
            log.warning("invoice %s not synced: %s", invoice.get("id"), exc)
            continue
        synced += 1
    return synced
