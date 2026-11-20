# storefront

Checkout logic for the shop service: catalog, cart, tax, invoices, orders, and loyalty points.

storefront is internal to the shop service. Code outside this package calls only `Catalog.from_rows` and `place_order`; every other function and class is internal, so their signatures and units can change in one pull request as long as this package stays consistent.

Catalog prices are dollar strings with at most two decimal places. The catalog import job rejects anything else before it reaches `Catalog.from_rows`.

Run the tests from this directory with `python -m unittest discover -s tests -t .`.
