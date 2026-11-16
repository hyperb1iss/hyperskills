"""Nightly account sync."""
import logging

log = logging.getLogger("jobs")


def sync_accounts(accounts, client):
    """Push each account to billing. Returns the number synced."""
    synced = 0
    for account in accounts:
        try:
            client.upsert_account(account)
        except Exception as exc:
            log.warning("account %s not synced: %s", account.get("id"), exc)
            continue
        synced += 1
    return synced
