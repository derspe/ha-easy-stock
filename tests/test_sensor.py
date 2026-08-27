"""Unit tests for StockSensor's exposed attributes."""
from types import SimpleNamespace

from custom_components.easy_stock.sensor import StockSensor
from custom_components.easy_stock.const import (
    CONF_SYMBOL,
    CONF_NAME,
    CONF_PURCHASE_PRICE,
    CONF_QUANTITY,
)

from .conftest import SYMBOL

COORDINATOR_DATA = {
    "symbol": SYMBOL,
    "long_name": "Apple Inc.",
    "currency": "USD",
    "market_state": "CLOSED",
    "current_price": 195.0,
    "previous_close": 190.0,
    "change": 5.0,
    "change_pct": 2.63,
    "price_is_live": False,
    "traded_today": True,
}


def _sensor(data=COORDINATOR_DATA, options=None):
    coordinator = SimpleNamespace(data=data, async_add_listener=lambda *a, **k: None)
    entry = SimpleNamespace(
        data={CONF_SYMBOL: SYMBOL, CONF_NAME: "Apple"},
        options=options or {},
        title="Apple",
    )
    return StockSensor(coordinator, entry)


def test_exposes_traded_today_attribute():
    """The card distinguishes "traded today" from "market open" and needs both."""
    assert _sensor().extra_state_attributes["traded_today"] is True


def test_exposes_market_state_and_price_is_live_independently():
    attrs = _sensor().extra_state_attributes
    assert attrs["market_state"] == "CLOSED"
    assert attrs["price_is_live"] is False


def test_returns_no_attributes_without_coordinator_data():
    assert _sensor(data=None).extra_state_attributes == {}


def test_no_position_attributes_without_a_purchase_price():
    """The attribute set stays unchanged for anyone tracking prices only."""
    attrs = _sensor().extra_state_attributes
    assert "purchase_price" not in attrs
    assert "gain_pct" not in attrs


def test_purchase_price_from_options_adds_position_attributes():
    attrs = _sensor(
        options={CONF_PURCHASE_PRICE: 150.0, CONF_QUANTITY: 10}
    ).extra_state_attributes
    assert attrs["purchase_price"] == 150.0
    assert attrs["quantity"] == 10
    assert attrs["invested"] == 1500.0
    assert attrs["position_value"] == 1950.0
    assert attrs["gain_total"] == 450.0
    assert attrs["gain_pct"] == 30.0


def test_position_attributes_do_not_shadow_the_daily_change():
    """change/change_pct stay the day's move, not the move since purchase."""
    attrs = _sensor(options={CONF_PURCHASE_PRICE: 150.0}).extra_state_attributes
    assert attrs["change"] == 5.0
    assert attrs["change_pct"] == 2.63
    assert attrs["gain_per_unit"] == 45.0
