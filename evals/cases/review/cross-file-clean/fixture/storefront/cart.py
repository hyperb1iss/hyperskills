"""Shopping cart."""

from dataclasses import dataclass, field

MAX_QUANTITY = 99


class CartError(ValueError):
    pass


@dataclass
class CartLine:
    product: object
    quantity: int

    def total(self):
        """Line total in integer cents."""
        return self.product.price_cents * self.quantity


@dataclass
class Cart:
    lines: list = field(default_factory=list)

    def add(self, product, quantity=1):
        if quantity < 1:
            raise CartError("quantity must be at least 1")
        line = self._line_for(product.sku)
        new_quantity = quantity + (line.quantity if line else 0)
        if new_quantity > MAX_QUANTITY:
            raise CartError(f"at most {MAX_QUANTITY} of {product.sku} per order")
        if line is None:
            line = CartLine(product, 0)
            self.lines.append(line)
        line.quantity = new_quantity
        return line

    def remove(self, sku):
        self.lines = [line for line in self.lines if line.product.sku != sku]

    def subtotal(self):
        """Sum of line totals in integer cents."""
        return sum(line.total() for line in self.lines)

    def weight_grams(self):
        return sum(line.product.weight_grams * line.quantity for line in self.lines)

    def is_empty(self):
        return not self.lines

    def _line_for(self, sku):
        for line in self.lines:
            if line.product.sku == sku:
                return line
        return None
