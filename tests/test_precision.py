"""Price rounding has to follow the size of the price, not a fixed decimal place."""
import math

import pytest

from custom_components.easy_stock.precision import (
    PRICE_SIGNIFICANT_DIGITS,
    price_decimals,
    round_price,
)

# Real quotes pulled from Yahoo, spanning six orders of magnitude.
SHIB_EUR = 4.35e-06
DOGE_EUR = 0.07137
XRP_EUR = 1.182
ALLIANZ_EUR = 450.2
CHF_QUOTE = 14399.77
BTC_EUR = 67432.05


def test_a_sub_cent_crypto_price_is_not_rounded_away():
    # round(4.35e-06, 4) is 0.0 — the sensor reported a price of zero.
    assert round_price(SHIB_EUR) == pytest.approx(SHIB_EUR)


def test_a_seven_cent_quote_keeps_the_digits_a_day_of_trading_needs():
    # round(0.07137, 4) leaves a step of 0.14 % of the price, wider than the
    # sparkline's whole noise floor, so the rounding itself drew a sawtooth.
    assert round_price(DOGE_EUR) == pytest.approx(DOGE_EUR)


def test_an_ordinary_quote_is_left_alone():
    assert round_price(CHF_QUOTE) == pytest.approx(CHF_QUOTE)
    assert round_price(ALLIANZ_EUR) == pytest.approx(ALLIANZ_EUR)
    assert round_price(XRP_EUR) == pytest.approx(XRP_EUR)


@pytest.mark.parametrize("value", [SHIB_EUR, DOGE_EUR, XRP_EUR, ALLIANZ_EUR, CHF_QUOTE, BTC_EUR, 1e9])
def test_the_rounding_step_is_a_constant_fraction_of_the_price(value):
    step = 10 ** -price_decimals(value)
    assert step / value <= 10 ** (1 - PRICE_SIGNIFICANT_DIGITS)


def test_the_step_never_reaches_into_the_integer_part():
    # A huge quote must not be rounded to whole hundreds.
    assert price_decimals(1e9) >= 0


def test_a_change_is_rounded_at_the_scale_of_the_price_it_came_from():
    # The delta is tiny next to the price; rounding it on its own magnitude
    # would keep meaningless digits.
    price, previous = 67432.05, 67432.04
    decimals = price_decimals(price)
    assert round(price - previous, decimals) == pytest.approx(0.01, abs=1e-6)


@pytest.mark.parametrize("value", [0, 0.0, -0.0])
def test_zero_passes_through(value):
    assert round_price(value) == 0


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_values_pass_through_untouched(value):
    result = round_price(value)
    assert math.isnan(result) if math.isnan(value) else result == value


def test_negative_values_round_on_their_magnitude():
    assert round_price(-SHIB_EUR) == pytest.approx(-SHIB_EUR)
