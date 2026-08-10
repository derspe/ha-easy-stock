"""Unit tests for StockSensor's exposed attributes."""
from types import SimpleNamespace

from custom_components.easy_stock.sensor import StockSensor
from custom_components.easy_stock.const import CONF_SYMBOL, CONF_NAME

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


def _sensor(data=COORDINATOR_DATA):
    coordinator = SimpleNamespace(data=data, async_add_listener=lambda *a, **k: None)
    entry = SimpleNamespace(
        data={CONF_SYMBOL: SYMBOL, CONF_NAME: "Apple"},
        options={},
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
