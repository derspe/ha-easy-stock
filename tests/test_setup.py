"""End-to-end tests: set up a config entry the way Home Assistant does."""
from http import HTTPStatus
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zwitserleven_fondsen.const import (
    CONF_NAME,
    CONF_SYMBOL,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.zwitserleven_fondsen.fondsen_page import FondsenPageError

from .conftest import SYMBOL, make_page, quote

HISTORY_KEY = f"zwitserleven_fondsen.{SYMBOL.lower()}.history"
UNIQUE_ID = f"zwitserleven_fondsen_{SYMBOL}"


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ASN Duurzaam Aandelenfonds",
        unique_id=UNIQUE_ID,
        data={CONF_SYMBOL: SYMBOL, CONF_NAME: ""},
    )
    entry.add_to_hass(hass)
    return entry


def _serve(*quotes, error=None):
    return patch(
        "custom_components.zwitserleven_fondsen.coordinator.get_page",
        return_value=make_page(*quotes, error=error),
    )


async def _set_up(hass, entry, hass_storage, history=None):
    """Set up the integration; returns the mocked page the coordinator reads."""
    if history is not None:
        hass_storage[HISTORY_KEY] = {"version": 1, "key": HISTORY_KEY, "data": history}
    page = make_page(quote(price=225.87))
    with patch("custom_components.zwitserleven_fondsen.coordinator.get_page", return_value=page):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return page


def _entity_id(hass):
    return er.async_get(hass).async_get_entity_id("sensor", DOMAIN, UNIQUE_ID)


async def test_sets_up_a_price_sensor(hass, entry, hass_storage):
    await _set_up(hass, entry, hass_storage, history=[["2026-10-01", 220.0]])

    assert entry.state is ConfigEntryState.LOADED
    state = hass.states.get(_entity_id(hass))
    assert float(state.state) == 225.87
    assert state.attributes["unit_of_measurement"] == "EUR"
    assert state.attributes["previous_close"] == 220.0
    assert state.attributes["friendly_name"] == "ASN Duurzaam Aandelenfonds"


async def test_each_fund_is_a_device(hass, entry, hass_storage):
    await _set_up(hass, entry, hass_storage)

    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, SYMBOL)})
    assert device is not None
    assert device.name == "ASN Duurzaam Aandelenfonds"
    assert device.manufacturer == "Zwitserleven"
    assert er.async_get(hass).async_get(_entity_id(hass)).device_id == device.id


async def test_retries_setup_when_the_site_is_down(hass, entry):
    with _serve(error=FondsenPageError("Zwitserleven returned HTTP 503")):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_renaming_in_the_options_renames_the_device(hass, entry, hass_storage):
    await _set_up(hass, entry, hass_storage)

    with _serve(quote()):
        hass.config_entries.async_update_entry(
            entry, options={CONF_NAME: "Aandelen"}
        )
        await hass.async_block_till_done()

    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, SYMBOL)})
    assert device.name == "Aandelen"
    assert entry.state is ConfigEntryState.LOADED


async def test_unload(hass, entry, hass_storage):
    await _set_up(hass, entry, hass_storage)

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
    # The shared coordinator stops updating the fund.
    assert hass.data[DATA_COORDINATOR].history(SYMBOL) is None


async def test_retries_setup_when_the_fund_is_not_listed(hass, entry):
    with _serve(quote(symbol="LTAOB")):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert hass.data[DATA_COORDINATOR].history(SYMBOL) is None


async def test_funds_added_at_different_times_share_one_download(hass, entry, hass_storage):
    """However and whenever funds are added, each update downloads the page once."""
    page = make_page(quote(), quote(symbol="LTAOB", name="Obligaties", price=24.56))
    second = MockConfigEntry(
        domain=DOMAIN,
        title="Obligaties",
        unique_id="zwitserleven_fondsen_LTAOB",
        data={CONF_SYMBOL: "LTAOB", CONF_NAME: ""},
    )
    second.add_to_hass(hass)

    with patch("custom_components.zwitserleven_fondsen.coordinator.get_page", return_value=page):
        # Setting up the integration sets up both entries.
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert second.state is ConfigEntryState.LOADED

        assert entry.runtime_data is second.runtime_data
        coordinator = entry.runtime_data
        page.async_get_funds.reset_mock()

        await coordinator.async_refresh()

    assert page.async_get_funds.call_count == 1
    assert set(coordinator.data) == {SYMBOL, "LTAOB"}


async def test_sensor_goes_unavailable_when_its_fund_disappears(hass, entry, hass_storage):
    page = await _set_up(hass, entry, hass_storage)

    page.async_get_funds.return_value = {"LTAOB": quote(symbol="LTAOB")}
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(_entity_id(hass)).state == "unavailable"


async def test_removing_the_fund_deletes_its_history(hass, entry, hass_storage):
    await _set_up(hass, entry, hass_storage, history=[["2026-10-01", 220.0]])
    assert HISTORY_KEY in hass_storage

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert HISTORY_KEY not in hass_storage


# ---------------------------------------------------------------------------
# History endpoint
# ---------------------------------------------------------------------------


async def test_history_endpoint_serves_the_stored_prices(hass, entry, hass_storage, hass_client):
    await _set_up(hass, entry, hass_storage, history=[["2026-10-01", 220.0]])
    client = await hass_client()

    resp = await client.get(f"/api/zwitserleven_fondsen/history?symbol={SYMBOL.lower()}")

    assert resp.status == HTTPStatus.OK
    assert await resp.json() == {
        "symbol": SYMBOL,
        "history": [["2026-10-01", 220.0], ["2026-10-02", 225.87]],
    }


async def test_history_endpoint_unknown_fund(hass, entry, hass_storage, hass_client):
    await _set_up(hass, entry, hass_storage)
    client = await hass_client()

    resp = await client.get("/api/zwitserleven_fondsen/history?symbol=NOPE")

    assert resp.status == HTTPStatus.NOT_FOUND


async def test_history_endpoint_needs_a_symbol(hass, entry, hass_storage, hass_client):
    await _set_up(hass, entry, hass_storage)
    client = await hass_client()

    resp = await client.get("/api/zwitserleven_fondsen/history")

    assert resp.status == HTTPStatus.BAD_REQUEST
