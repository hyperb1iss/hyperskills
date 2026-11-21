# Stock reservations with expiry and partial fulfillment

Sales channels can now hold stock for an order line while the customer checks out, instead of finding at pick time that another order took it.

- `stockroom/reservations.py` adds `ReservationBook`. It holds units for one order line across bins and warehouses, all or nothing by default or partially with `allow_partial`, with one held reservation per channel, order, and SKU. A hold expires after `ttl_seconds` (default `STOCKROOM_RESERVATION_TTL`, 900 s, capped by `STOCKROOM_MAX_RESERVATION_TTL`). `fulfill` picks exactly the held bins, and an expired hold is released instead of picked.
- `stockroom/sweeper.py` adds `sweep()`, which the host scheduler runs once a minute. It releases expired holds and forgets finished reservations after seven days.
- Bins now track `reserved` units. `Stock.available()` now means units free to promise (on hand minus reserved), and the new `Stock.on_hand()` returns physical units. The stock report shows on hand, reserved, and available, and the low-stock list uses units free to promise.
- The API adds `reserve`, `release_reservation`, and `fulfill_reservation` for channel keys with the `reservations:write` role. A reservation is visible only to its own channel. Without a `warehouse_id`, a reservation draws from warehouses in `STOCKROOM_WAREHOUSE_PRIORITY` order, then the rest by id.
- Fixes the pick-path report from the east warehouse: when a SKU sat in several bins received on the same day, `pick()` sent pickers to them in the order the bins were created, zigzagging across the aisle. Picks and reservations now share `picking.plan()`, which visits those bins in walk order (`pick_order`). `test_same_day_bins_are_picked_in_walk_order` covers it.

Tests cover holds, partial and multi-warehouse allocation, duplicate holds, release, fulfillment, expiry, the sweeper and pruning, the new handlers, and the report columns.
