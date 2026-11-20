"""Placing an order: invoice the cart and credit loyalty points."""

from dataclasses import dataclass

from .invoice import build_invoice
from .loyalty import points_after_purchase


@dataclass
class Account:
    customer_id: str
    tier: str = "standard"
    points: int = 0
    order_count: int = 0


@dataclass(frozen=True)
class Order:
    customer_id: str
    invoice: object
    points_earned: int


def place_order(cart, account, region):
    invoice = build_invoice(cart, region)
    before = account.points
    account.points = points_after_purchase(
        before, cart, account.tier, first_order=account.order_count == 0
    )
    account.order_count += 1
    return Order(account.customer_id, invoice, account.points - before)
