"""Invoices for carts."""

from dataclasses import dataclass

from .tax import tax_for


@dataclass(frozen=True)
class InvoiceLine:
    sku: str
    name: str
    quantity: int
    amount: int


@dataclass(frozen=True)
class Invoice:
    region: str
    lines: tuple
    subtotal: int
    tax: int

    @property
    def total(self):
        return self.subtotal + self.tax

    def render(self):
        rows = [
            f"{line.quantity:>3} x {line.name:<24} {format_money(line.amount):>10}"
            for line in self.lines
        ]
        rows.append(f"{'Subtotal':<30} {format_money(self.subtotal):>10}")
        rows.append(f"{'Tax (' + self.region + ')':<30} {format_money(self.tax):>10}")
        rows.append(f"{'Total':<30} {format_money(self.total):>10}")
        return "\n".join(rows)


def build_invoice(cart, region):
    if cart.is_empty():
        raise ValueError("cannot invoice an empty cart")
    lines = tuple(
        InvoiceLine(line.product.sku, line.product.name, line.quantity, line.total())
        for line in cart.lines
    )
    subtotal = cart.subtotal()
    return Invoice(region, lines, subtotal, tax_for(subtotal, region))


def format_money(cents):
    sign = "-" if cents < 0 else ""
    dollars, remainder = divmod(abs(cents), 100)
    return f"{sign}${dollars:,}.{remainder:02d}"
