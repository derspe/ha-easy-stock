"""Rounding that follows the size of a price instead of a fixed decimal place.

``round(value, 4)`` is a step of 0.0001 whatever the quote is worth. Across the
range of things people put on a dashboard that step spans six orders of
magnitude relative to the price:

    14,399.77   0.0001 is 0.0000007 % of the price — far below any real move
         0.07   0.0001 is 0.14 % — wider than a quiet day, so the rounding
                itself makes the price flip between two steps and the 1T chart
                draws a sawtooth built from nothing but our own arithmetic
    0.00000435  0.0001 rounds the price to 0.0 and the sensor stops working

Rounding to significant figures keeps the step at a constant fraction of the
price, so every asset is treated the same way regardless of what it costs.
"""
import math

PRICE_SIGNIFICANT_DIGITS = 8


def price_decimals(value: float, digits: int = PRICE_SIGNIFICANT_DIGITS) -> int:
    """Decimal places that preserve `digits` significant figures of `value`.

    Never negative: a large quote is left whole rather than rounded into its
    integer part.
    """
    if not value or not math.isfinite(value):
        return digits
    return max(0, digits - 1 - math.floor(math.log10(abs(value))))


def round_price(value: float, digits: int = PRICE_SIGNIFICANT_DIGITS) -> float:
    """Round `value` to `digits` significant figures, passing 0 and NaN through."""
    if not value or not math.isfinite(value):
        return value
    return round(value, price_decimals(value, digits))
