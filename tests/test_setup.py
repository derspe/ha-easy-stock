"""End-to-end tests: set up a config entry the way Home Assistant does."""
from http import HTTPStatus
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zwitserleven_fondsen.const import (
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SYMBOL,
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
        data={CONF_SYMBOL: SYMBOL, CONF_NAME: "", CONF_SCAN_INTERVAL: 3600},
    )
    entry.add_to_hass(hass)
    return entry


def _serve(*quotes, error=None):
    return patch(
        "custom_components.zwitserleven_fondsen.get_page",
        return_value=make_page(*quotes, error=error),
    )


async def _set_up(hass, entry, hass_storage, history=None):
    if history is not None:
        hass_storage[HISTORY_KEY] = {"version": 1, "key": HISTORY_KEY, "data": history}
    with _serve(quote(price=225.87)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


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
            entry, options={CONF_NAME: "Aandelen", CONF_SCAN_INTERVAL: 3600}
        )
        await hass.async_block_till_done()

    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, SYMBOL)})
    assert device.name == "Aandelen"
    assert entry.state is ConfigEntryState.LOADED


async def test_unload(hass, entry, hass_storage):
    await _set_up(hass, entry, hass_storage)

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


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
