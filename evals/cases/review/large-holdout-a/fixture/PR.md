# Warehouse-scoped keys and expiring holds for kiosks

In-store kiosks are going to reserve stock for walk-in customers through this API. Two things are missing for that: a kiosk's key should only be able to touch its own store's warehouse, and a cart abandoned at a kiosk should not pin stock until someone cancels it by hand. This change adds both, plus the schema migration they need.

**Warehouse scopes.** Every API key now carries a scope, the list of warehouses it may act in, where `"*"` stands for all of them. `issue_key` takes the scope (`issue_key(store, OPERATOR, ["WH-12"])`) and `set_scope` replaces it later. Every handler checks the scope against the warehouse involved: the bin's warehouse for `reserve`, the reservation's bin's warehouse for `confirm`, `cancel`, and `pick`, and the path's warehouse for `stock`. A request outside the key's scope gets the same 403 `forbidden` response that a role failure already gets.

**Expiring holds.** A reserve request may now include `hold_minutes` (1 to 1440). The hold gets an `expires_at`; once that passes, its units count as free again straight away and `confirm` answers 409 `hold_expired`. The new `ExpiryWorker` in `stockpile/worker.py` runs in the worker process: it sends the reserving key a `hold_expiring` notice when the hold comes within five minutes of its deadline (once per worker process; a restarted worker may send it again), and marks lapsed holds `expired`. Holds made without `hold_minutes` never lapse.

**Compatibility.** Migration 0004 gives every existing reservation `expires_at = null` and every existing key the `"*"` scope, so nothing changes for current clients at deploy. Request bodies only gain an optional field and responses only gain `expires_at`. The `expired` status and the `hold_expired` error can only come from holds made with `hold_minutes`, which no current client sends.

Tests cover the scope checks, hold windows and their bounds, lapsed holds freeing stock and refusing confirmation, the worker's notices and expiry, and the migration.
