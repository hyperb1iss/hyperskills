# Compute cart, tax, and invoice amounts in integer cents

Cart and invoice totals are Decimal dollars today, and tax is rounded on a dollar subtotal, so every consumer that needs cents does its own conversion and rounding. This moves the arithmetic to integer cents. Catalog prices stay in dollars for now; a product converts its price once, with half-up rounding.

- `Product.price_cents` converts the dollar price through the new `to_cents` helper.
- `CartLine.total()` and `Cart.subtotal()` return integer cents.
- `tax_for` takes a subtotal in cents and returns tax in whole cents, rounded half up as before.
- `Invoice` amounts are cents, and `format_money` takes cents for display.

Tests are updated to the new units.
