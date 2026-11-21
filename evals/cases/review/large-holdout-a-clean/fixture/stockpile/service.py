"""Request handlers for the reservation API.

The web layer outside this package parses JSON, turns path ids into ints, and
routes each request to handle():

    POST /reservations                 reserve
    POST /reservations/<id>/confirm    confirm
    POST /reservations/<id>/cancel     cancel
    POST /reservations/<id>/pick       pick
    GET  /stock/<warehouse>/<sku>      stock

Each handler authenticates the caller, checks its role, validates the input,
checks that the key's scope covers the warehouse involved (a bin's warehouse
for reservations), and then calls into reservations or inventory. Failures
come back as {"error": code, "message": text}; the status codes and error codes
are part of the API contract that existing clients rely on.

A reserve body may add hold_minutes to make the hold lapse unless confirmed in
time. Bodies without it behave as before, and responses only gain fields
(expires_at, null for holds that do not lapse), so existing clients are
unaffected.
"""
from dataclasses import dataclass, field
from datetime import timedelta

from . import inventory, reservations
from .access import Forbidden, Unauthorized, authenticate, authorize, require_role
from .catalog import normalize_sku
from .clock import format_timestamp
from .store import NotFound

ROUTES = ("reserve", "confirm", "cancel", "pick", "stock")
MAX_HOLD_MINUTES = int(reservations.MAX_HOLD.total_seconds() // 60)


@dataclass
class Request:
    headers: dict = field(default_factory=dict)
    body: object = None


@dataclass
class Response:
    status: int
    body: dict


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code


def _quantity(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("quantity must be a positive integer")
    return value


def _order_ref(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 64:
        raise ValueError("order_ref must be a nonempty string of at most 64 characters")
    return value.strip()


def _hold_window(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_HOLD_MINUTES:
        raise ValueError(f"hold_minutes must be an integer from 1 to {MAX_HOLD_MINUTES}")
    return timedelta(minutes=value)


class ReservationService:
    def __init__(self, store, clock):
        self.store = store
        self.clock = clock

    def handle(self, route, request, *args):
        """Run the handler for route and turn failures into error responses."""
        if route not in ROUTES:
            raise ValueError(f"unknown route {route!r}")
        try:
            return getattr(self, "_" + route)(request, *args)
        except Unauthorized as error:
            status, code, message = 401, "unauthorized", str(error)
        except Forbidden as error:
            status, code, message = 403, "forbidden", str(error)
        except ApiError as error:
            status, code, message = error.status, error.code, str(error)
        return Response(status, {"error": code, "message": message})

    def _caller(self, request, action):
        key = authenticate(self.store, request.headers.get("Authorization"))
        require_role(key, action)
        return key

    def _body(self, request):
        if not isinstance(request.body, dict):
            raise ApiError(400, "invalid_request", "body must be a JSON object")
        return request.body

    def _reserve(self, request):
        key = self._caller(request, "reserve")
        body = self._body(request)
        try:
            sku = normalize_sku(body.get("sku"))
            quantity = _quantity(body.get("quantity"))
            order_ref = _order_ref(body.get("order_ref"))
            hold = _hold_window(body.get("hold_minutes"))
            bin_id = body.get("bin_id")
            if not isinstance(bin_id, str):
                raise ValueError("bin_id is required")
            authorize(key, "reserve", self.store.bin(bin_id).warehouse_id)
            reservation = reservations.reserve(self.store, key.key_id, order_ref, sku, bin_id,
                                               quantity, self.clock(), hold)
        except NotFound as error:
            raise ApiError(400, "invalid_request", str(error))
        except ValueError as error:
            raise ApiError(400, "invalid_request", str(error))
        except reservations.InsufficientStock as error:
            raise ApiError(409, "insufficient_stock", str(error))
        return Response(201, self._view(reservation))

    def _reservation(self, reservation_id):
        try:
            return self.store.reservation(reservation_id)
        except NotFound as error:
            raise ApiError(404, "not_found", str(error))

    def _step(self, request, reservation_id, action, step):
        key = self._caller(request, action)
        reservation = self._reservation(reservation_id)
        authorize(key, action, self.store.bin(reservation.bin_id).warehouse_id)
        try:
            return Response(200, self._view(step(reservation_id)))
        except reservations.HoldExpired as error:
            raise ApiError(409, "hold_expired", str(error))
        except reservations.InvalidTransition as error:
            raise ApiError(409, "invalid_transition", str(error))
        except reservations.ShortPick as error:
            raise ApiError(409, "short_pick", str(error))

    def _confirm(self, request, reservation_id):
        return self._step(request, reservation_id, "confirm",
                          lambda rid: reservations.confirm(self.store, rid, self.clock()))

    def _cancel(self, request, reservation_id):
        return self._step(request, reservation_id, "cancel",
                          lambda rid: reservations.cancel(self.store, rid))

    def _pick(self, request, reservation_id):
        return self._step(request, reservation_id, "pick",
                          lambda rid: reservations.pick(self.store, rid))

    def _stock(self, request, warehouse_id, sku):
        key = self._caller(request, "view")
        try:
            sku = normalize_sku(sku)
        except ValueError as error:
            raise ApiError(400, "invalid_request", str(error))
        authorize(key, "view", warehouse_id)
        units = inventory.available(self.store, warehouse_id, sku, self.clock())
        return Response(200, {"warehouse_id": warehouse_id, "sku": sku, "available": units})

    def _view(self, reservation):
        return {
            "reservation_id": reservation.reservation_id,
            "order_ref": reservation.order_ref,
            "sku": reservation.sku,
            "bin_id": reservation.bin_id,
            "quantity": reservation.quantity,
            "status": reservation.status,
            "created_at": format_timestamp(reservation.created_at),
            "expires_at": format_timestamp(reservation.expires_at) if reservation.expires_at else None,
        }
