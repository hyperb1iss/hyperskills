"""Ticket prices and fees, in cents."""
from dataclasses import dataclass

SERVICE_FEE_RATE = 0.06
MIN_SERVICE_FEE = 75
MAX_SERVICE_FEE = 900


@dataclass(frozen=True)
class Quote:
    face_value: int
    service_fee: int
    tax: int

    @property
    def total(self):
        return self.face_value + self.service_fee + self.tax


def service_fee(face_value):
    if face_value == 0:
        return 0
    fee = round(face_value * SERVICE_FEE_RATE)
    return max(MIN_SERVICE_FEE, min(MAX_SERVICE_FEE, fee))


def group_discount(face_value, quantity):
    """Ten percent off each ticket for groups of eight or more."""
    if quantity < 1:
        raise ValueError("quantity must be at least 1")
    if quantity >= 8:
        return round(face_value * 0.9)
    return face_value


def quote(face_value, tax_rate):
    if face_value < 0:
        raise ValueError("face value cannot be negative")
    fee = service_fee(face_value)
    tax = round((face_value + fee) * tax_rate)
    return Quote(face_value, fee, tax)


def refund_amount(quote_, days_before_event):
    """Full refund up to a week out, face value only after that, nothing in the last day."""
    if days_before_event >= 7:
        return quote_.total
    if days_before_event >= 1:
        return quote_.face_value
    return 0
