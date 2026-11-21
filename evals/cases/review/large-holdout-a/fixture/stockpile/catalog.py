"""SKU codes and product descriptions."""
import re
from dataclasses import dataclass

SKU_PATTERN = re.compile(r"[A-Z]{3}-\d{4,8}")


def normalize_sku(text):
    """Return the canonical form of a SKU code or raise ValueError.

    A code is three letters, a dash, and four to eight digits. Lowercase letters
    and surrounding whitespace are tolerated; anything else is rejected rather
    than guessed at.
    """
    if not isinstance(text, str):
        raise ValueError("sku must be a string")
    code = text.strip().upper()
    if not SKU_PATTERN.fullmatch(code):
        raise ValueError(f"malformed sku {text!r}")
    return code


@dataclass(frozen=True)
class Product:
    sku: str
    description: str
    unit: str = "each"


class Catalog:
    """Product descriptions by SKU, loaded at startup and read-only afterwards."""

    def __init__(self, products=()):
        self._products = {}
        for product in products:
            self.add(product)

    def add(self, product):
        sku = normalize_sku(product.sku)
        if sku in self._products:
            raise ValueError(f"duplicate sku {sku}")
        self._products[sku] = Product(sku, product.description, product.unit)

    def describe(self, sku):
        """The description for sku, or the code itself for a product not in the catalog."""
        product = self._products.get(normalize_sku(sku))
        return product.description if product else sku

    def __contains__(self, sku):
        try:
            return normalize_sku(sku) in self._products
        except ValueError:
            return False

    def __len__(self):
        return len(self._products)
