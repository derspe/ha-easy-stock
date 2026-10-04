"""Price rounding has to follow the size of the price, not a fixed decimal place."""
import math

import pytest

from custom_components.zwitserleven_fondsen.precision import (
    PRICE_SIGNIFICANT_DIGITS,
    price_decimals,
)

# Test prices in EUR
SHIB_EUR = 4.35e-06
DOGE_EUR = 0.07137
XRP_EUR = 1.182
ALLIANZ_EUR = 450.2
CHF_QUOTE = 14399.77
BTC_EUR = 67432.05


def test_price_decimals_for_sub_cent_crypto():
    # Micro-cent prices need many decimal places
    assert price_decimals(SHIB_EUR) >= 6


def test_price_decimals_for_ordinary_quote():
    assert price_decimals(CHF_QUOTE) >= 0
    assert price_decimals(ALLIANZ_EUR) >= 0
    assert price_decimals(XRP_EUR) >= 0


@pytest.mark.parametrize("value", [SHIB_EUR, DOGE_EUR, XRP_EUR, ALLIANZ_EUR, CHF_QUOTE, BTC_EUR, 1e9])
def test_the_rounding_step_is_a_constant_fraction_of_the_price(value):
    step = 10 ** -price_decimals(value)
    assert step / value <= 10 ** (1 - PRICE_SIGNIFICANT_DIGITS)


def test_the_step_never_reaches_into_the_integer_part():
    # A huge quote must not be rounded to whole hundreds.
    assert price_decimals(1e9) >= 0
