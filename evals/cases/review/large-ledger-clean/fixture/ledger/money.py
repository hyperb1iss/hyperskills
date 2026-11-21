"""Amounts are integers in minor units of their currency: cents, pence, or whole yen."""
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

BASE_CURRENCY = "USD"
EXPONENTS = {"USD": 2, "EUR": 2, "GBP": 2, "CHF": 2, "JPY": 0}


class AmountError(ValueError):
    pass


def exponent(currency):
    try:
        return EXPONENTS[currency]
    except KeyError:
        raise AmountError(f"unsupported currency {currency!r}") from None


def parse_amount(text, currency=BASE_CURRENCY):
    """'1,234.50' or '-12' to minor units of currency; more decimals than it has is an error."""
    scale = 10 ** exponent(currency)
    cleaned = text.strip().replace(",", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise AmountError(f"not an amount: {text!r}") from None
    if not value.is_finite():
        raise AmountError(f"not an amount: {text!r}")
    minor = value * scale
    if minor != minor.to_integral_value():
        raise AmountError(f"too many decimal places for {currency}: {text!r}")
    return int(minor)


def format_amount(minor, currency=BASE_CURRENCY):
    digits = exponent(currency)
    sign = "-" if minor < 0 else ""
    whole, fraction = divmod(abs(minor), 10 ** digits)
    if not digits:
        return f"{sign}{whole:,}"
    return f"{sign}{whole:,}.{fraction:0{digits}d}"


def to_major(minor, currency):
    return Decimal(minor).scaleb(-exponent(currency))


def to_minor(amount, currency):
    """Round a Decimal amount of currency to whole minor units, half to even."""
    return int(amount.scaleb(exponent(currency)).to_integral_value(rounding=ROUND_HALF_EVEN))
