"""Unit tests for ZwitserleverSensor's exposed attributes."""
from types import SimpleNamespace

from custom_components.zwitserleven_fondsen.sensor import ZwitserleverSensor
from custom_components.zwitserleven_fondsen.const import CONF_SYMBOL, CONF_NAME

from .conftest import SYMBOL

COORDINATOR_DATA = {
    "symbol": SYMBOL,
    "long_name": "Test Fund",
    "current_price": 225.87,
    "price_is_live": False,
}


def _sensor(data=COORDINATOR_DATA):
    coordinator = SimpleNamespace(data=data, async_add_listener=lambda *a, **k: None)
    entry = SimpleNamespace(
        data={CONF_SYMBOL: SYMBOL, CONF_NAME: "Test Fund"},
        options={},
        title="Test Fund",
    )
    return ZwitserleverSensor(coordinator, entry)


def test_exposes_symbol_and_name_attributes():
    """The card needs symbol and fund name attributes."""
    attrs = _sensor().extra_state_attributes
    assert attrs["symbol"] == SYMBOL
    assert attrs["long_name"] == "Test Fund"


def test_exposes_price_is_live_attribute():
    """The card needs to know if the price is current."""
    assert _sensor().extra_state_attributes["price_is_live"] is False


def test_returns_no_attributes_without_coordinator_data():
    assert _sensor(data=None).extra_state_attributes == {}
