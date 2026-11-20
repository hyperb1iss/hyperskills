"""Sales tax by region."""

from decimal import ROUND_HALF_UP, Decimal

RATES = {
    "north": Decimal("0.0725"),
    "south": Decimal("0.0600"),
    "east": Decimal("0.0875"),
    "west": Decimal("0"),
}


class UnknownRegion(KeyError):
    pass


def rate_for(region):
    try:
        return RATES[region]
    except KeyError:
        raise UnknownRegion(region) from None


def tax_for(subtotal, region):
    """Tax on a subtotal in integer cents, rounded half up to a whole cent."""
    tax = Decimal(subtotal) * rate_for(region)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
