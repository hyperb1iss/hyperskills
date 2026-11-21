"""HTTP-facing handlers. Each takes (ctx, principal, body) and returns (status, body).

Request bodies are decoded JSON objects; the router has already checked that.
"""

from dataclasses import dataclass
from datetime import date, datetime

from .auth import can_access_warehouse, visible_warehouses
from .events import EXPORT_FIELDS, export_rows
from .reports import low_stock, stock_report
from .reservations import (
    DuplicateReservation,
    NotHeld,
    ReservationExpired,
    UnknownReservation,
    Unavailable,
    order_warehouses,
)
from .stock import InsufficientStock, UnknownBin


@dataclass
class Context:
    stock: object
    settings: object
    reservations: object = None


def _positive_int(value):
    return type(value) is int and value > 0


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def get_stock(ctx, principal, body):
    if not principal.has_role("stock:read"):
        return 403, {"error": "forbidden"}
    warehouses = visible_warehouses(principal, ctx.stock.warehouse_ids())
    requested = body.get("warehouse_id")
    if requested is not None:
        if requested not in warehouses:
            return 403, {"error": "forbidden"}
        warehouses = [requested]
    return 200, {"rows": stock_report(ctx.stock, warehouses)}


def get_low_stock(ctx, principal, body):
    if not principal.has_role("stock:read"):
        return 403, {"error": "forbidden"}
    warehouses = visible_warehouses(principal, ctx.stock.warehouse_ids())
    return 200, {"rows": low_stock(ctx.stock, warehouses, ctx.settings.low_stock_threshold)}


def get_events(ctx, principal, body):
    """Audit export of stock movements after ``since`` (ISO 8601), admins only."""
    if not principal.is_admin:
        return 403, {"error": "forbidden"}
    try:
        since = datetime.fromisoformat(body.get("since", ""))
    except (TypeError, ValueError):
        return 400, {"error": "invalid_since"}
    if since.tzinfo is None:
        return 400, {"error": "invalid_since"}
    return 200, {"fields": list(EXPORT_FIELDS), "rows": export_rows(ctx.stock.events.since(since))}


def adjust(ctx, principal, body):
    sku, warehouse_id, delta = body.get("sku"), body.get("warehouse_id"), body.get("delta")
    if not principal.has_role("stock:write") or not can_access_warehouse(principal, warehouse_id):
        return 403, {"error": "forbidden"}
    if not _text(sku) or not _text(body.get("reason")):
        return 400, {"error": "invalid_request"}
    if type(delta) is not int or delta == 0 or abs(delta) > ctx.settings.max_adjustment:
        return 400, {"error": "invalid_delta", "max": ctx.settings.max_adjustment}
    try:
        target = ctx.stock.adjust(sku, warehouse_id, body.get("bin_id"), delta, body["reason"])
    except UnknownBin:
        return 404, {"error": "unknown_bin"}
    except InsufficientStock as exc:
        return 409, {"error": "insufficient_stock", "available": exc.available}
    return 200, {"bin": target.bin_id, "on_hand": target.on_hand}


def receive(ctx, principal, body):
    sku, warehouse_id, quantity = body.get("sku"), body.get("warehouse_id"), body.get("quantity")
    if not principal.has_role("stock:write") or not can_access_warehouse(principal, warehouse_id):
        return 403, {"error": "forbidden"}
    if not _text(sku) or not _positive_int(quantity):
        return 400, {"error": "invalid_request"}
    try:
        received_on = date.fromisoformat(body.get("received_on", ""))
    except (TypeError, ValueError):
        return 400, {"error": "invalid_date"}
    try:
        target = ctx.stock.receive(sku, warehouse_id, quantity, received_on, body.get("bin_id"))
    except UnknownBin:
        return 404, {"error": "unknown_bin"}
    return 200, {"bin": target.bin_id, "on_hand": target.on_hand}


def pick(ctx, principal, body):
    sku, warehouse_id, quantity = body.get("sku"), body.get("warehouse_id"), body.get("quantity")
    if not principal.has_role("stock:write") or not can_access_warehouse(principal, warehouse_id):
        return 403, {"error": "forbidden"}
    if not _text(sku) or not _positive_int(quantity):
        return 400, {"error": "invalid_request"}
    try:
        takes = ctx.stock.pick(sku, warehouse_id, quantity)
    except InsufficientStock as exc:
        return 409, {"error": "insufficient_stock", "available": exc.available}
    return 200, {"takes": [{"bin": bin_id, "quantity": units} for bin_id, units in takes]}


def _reservation_body(reservation):
    return {
        "id": reservation.id,
        "order_id": reservation.order_id,
        "sku": reservation.sku,
        "status": reservation.status,
        "held": reservation.held,
        "shortfall": reservation.shortfall,
        "expires_at": reservation.expires_at.isoformat(),
        "allocations": [
            {"warehouse": a.warehouse_id, "bin": a.bin_id, "quantity": a.quantity}
            for a in reservation.allocations
        ],
    }


def reserve(ctx, principal, body):
    if not principal.has_role("reservations:write") or not principal.channel:
        return 403, {"error": "forbidden"}
    sku, order_id, quantity = body.get("sku"), body.get("order_id"), body.get("quantity")
    ttl = body.get("ttl_seconds", ctx.settings.reservation_ttl)
    if not _text(sku) or not _text(order_id):
        return 400, {"error": "invalid_request"}
    if not _positive_int(quantity):
        return 400, {"error": "invalid_quantity"}
    if not _positive_int(ttl) or ttl > ctx.settings.max_reservation_ttl:
        return 400, {"error": "invalid_ttl", "max": ctx.settings.max_reservation_ttl}
    warehouse_id = body.get("warehouse_id")
    if warehouse_id is not None and not can_access_warehouse(principal, warehouse_id):
        return 403, {"error": "forbidden"}
    if warehouse_id is not None:
        warehouses = [warehouse_id]
    else:
        ordered = order_warehouses(ctx.stock.warehouse_ids(), ctx.settings.warehouse_priority)
        warehouses = visible_warehouses(principal, ordered)
    try:
        reservation = ctx.reservations.reserve(
            order_id, principal.channel, sku, quantity, warehouses, ttl,
            allow_partial=body.get("allow_partial") is True,
        )
    except DuplicateReservation:
        return 409, {"error": "duplicate_reservation"}
    except Unavailable as exc:
        return 409, {"error": "insufficient_stock", "available": exc.available}
    return 201, _reservation_body(reservation)


def _owned_reservation(ctx, principal, body):
    """The reservation named in ``body`` if the caller's channel owns it.

    A reservation of another channel is reported as unknown, so ids of other
    channels' orders cannot be probed.
    """
    reservation = ctx.reservations.get(body.get("reservation_id"))
    if principal.is_admin or (principal.channel and reservation.channel == principal.channel):
        return reservation
    raise UnknownReservation(reservation.id)


def release_reservation(ctx, principal, body):
    if not principal.has_role("reservations:write"):
        return 403, {"error": "forbidden"}
    try:
        reservation = ctx.reservations.release(_owned_reservation(ctx, principal, body).id)
    except UnknownReservation:
        return 404, {"error": "unknown_reservation"}
    except NotHeld:
        return 409, {"error": "not_held"}
    return 200, _reservation_body(reservation)


def fulfill_reservation(ctx, principal, body):
    if not principal.has_role("reservations:write") or not principal.has_role("stock:write"):
        return 403, {"error": "forbidden"}
    try:
        reservation = _owned_reservation(ctx, principal, body)
        if not all(can_access_warehouse(principal, a.warehouse_id) for a in reservation.allocations):
            return 403, {"error": "forbidden"}
        picked = ctx.reservations.fulfill(reservation.id)
    except UnknownReservation:
        return 404, {"error": "unknown_reservation"}
    except NotHeld:
        return 409, {"error": "not_held"}
    except ReservationExpired:
        return 409, {"error": "expired"}
    return 200, {
        "id": reservation.id,
        "picked": [{"warehouse": p.warehouse_id, "bin": p.bin_id, "quantity": p.quantity} for p in picked],
    }
