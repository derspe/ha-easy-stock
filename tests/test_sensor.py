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


def test_suggests_the_symbol_as_the_object_id():
    assert _sensor().suggested_object_id == SYMBOL


async def test_a_long_name_does_not_make_a_long_entity_id(hass):
    """The name is Yahoo's long one; the entity id stays the symbol's (sensor.vgwl_de)."""
    from unittest.mock import patch

    from homeassistant.helpers import entity_registry as er
    from homeassistant.setup import async_setup_component
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.easy_stock.const import DOMAIN

    from .conftest import make_store, make_yahoo_payload, mock_http

    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, "lovelace", {})
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SYMBOL: "VGWL.DE", CONF_NAME: "Vanguard FTSE All-World UCITS ETF", "scan_interval": 900},
        title="Vanguard FTSE All-World UCITS ETF",
    )
    entry.add_to_hass(hass)

    patcher, _ = mock_http(make_yahoo_payload())
    with patcher, patch("custom_components.easy_stock.Store", return_value=make_store()):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    sensor = registry.async_get("sensor.vgwl_de")
    assert sensor is not None, [e.entity_id for e in registry.entities.values()]
    assert hass.states.get("sensor.vgwl_de").name == "Vanguard FTSE All-World UCITS ETF"
