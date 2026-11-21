"""Product catalog."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


def to_cents(amount):
    """Convert a dollar amount such as "12.99" to integer cents, rounding half up."""
    return int((Decimal(amount) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price: Decimal
    weight_grams: int = 0

    @property
    def price_cents(self):
        return to_cents(self.price)


class UnknownProduct(KeyError):
    pass


class Catalog:
    def __init__(self, products=()):
        self._products = {product.sku: product for product in products}

    def get(self, sku):
        try:
            return self._products[sku]
        except KeyError:
            raise UnknownProduct(sku) from None

    def __contains__(self, sku):
        return sku in self._products

    @classmethod
    def from_rows(cls, rows):
        """Build a catalog from (sku, name, price, weight_grams) string rows."""
        return cls(
            Product(sku, name, Decimal(price), int(weight))
            for sku, name, price, weight in rows
        )
