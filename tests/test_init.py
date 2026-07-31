"""Unit tests for custom_components/easy_stock/__init__.py."""
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.easy_stock import (
    async_remove_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.easy_stock.const import DOMAIN
from custom_components.easy_stock.frontend import CARD_URL_BASE, DATA_FRONTEND


async def _setup_storage_mode(hass):
    """Bring up http + lovelace and hand back the resource collection."""
    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, "lovelace", {})
    return hass.data[LOVELACE_DATA].resources


def _card_items(resources):
    return [i for i in resources.async_items() if i["url"].startswith(CARD_URL_BASE)]


def _mock_coordinator():
    """Patch out the network-backed coordinator async_setup_entry builds."""
    return patch(
        "custom_components.easy_stock.StockDataCoordinator",
        MagicMock(return_value=AsyncMock()),
    )


async def test_unload_entry_without_stored_data_succeeds(hass):
    """Unloading must not raise KeyError when the entry's data was never stored.

    This happens when async_setup_entry failed partway before
    hass.data[DOMAIN][entry.entry_id] was populated, or in tests where
    async_setup_entry is mocked out entirely. Previously this used
    hass.data[DOMAIN].pop(entry.entry_id) without a default, which raised
    KeyError (silently swallowed by Home Assistant, but reported as an
    unload failure rather than a success).
    """
    entry = MockConfigEntry(domain=DOMAIN, data={"symbol": "AAPL"})
    entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {})

    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=True
    ):
        result = await async_unload_entry(hass, entry)

    assert result is True


async def test_async_setup_registers_the_card(hass):
    """The component's async_setup is the seam that registers the card.

    Nothing else covered this: test_frontend.py calls async_register_card
    directly and test_config_flow.py patches async_setup out entirely, so
    deleting the call from __init__ left the suite green.
    """
    resources = await _setup_storage_mode(hass)

    assert await async_setup(hass, {}) is True

    assert DATA_FRONTEND in hass.data
    await resources.async_get_info()
    assert len(_card_items(resources)) == 1


async def test_setup_survives_a_failing_card_registration(hass):
    """A card problem must never cost the user their sensors.

    An exception out of a component's async_setup makes
    _async_setup_component log and return False, the domain never enters
    hass.config.components and every config entry fails to set up.
    """
    assert await async_setup_component(hass, "http", {})

    with patch(
        "custom_components.easy_stock.async_register_card",
        side_effect=OSError("truncated download"),
    ):
        assert await async_setup(hass, {}) is True

    # The rest of async_setup still ran.
    assert DOMAIN in hass.data


async def test_re_adding_an_entry_restores_the_card_without_a_restart(hass):
    """Delete the last entry, add a new one: the card must come back.

    Removing a config entry does not unload the component --
    ConfigEntries._async_remove never touches hass.config.components -- so
    ConfigEntries.async_setup takes its `entry.domain in components` branch
    and only entry.async_setup runs. The module level async_setup is not
    re-run, so async_setup_entry has to re-register the card itself.
    """
    resources = await _setup_storage_mode(hass)
    assert await async_setup(hass, {}) is True

    # HA deletes the entry from the registry before calling async_remove_entry,
    # so the entry being removed is deliberately never added to hass.
    await async_remove_entry(hass, MockConfigEntry(domain=DOMAIN, data={"symbol": "AAPL"}))
    await resources.async_get_info()
    assert _card_items(resources) == []
    assert DATA_FRONTEND not in hass.data

    entry = MockConfigEntry(domain=DOMAIN, data={"symbol": "MSFT"})
    entry.add_to_hass(hass)
    with _mock_coordinator(), patch.object(
        hass.config_entries, "async_forward_entry_setups", return_value=None
    ):
        assert await async_setup_entry(hass, entry) is True

    await resources.async_get_info()
    assert len(_card_items(resources)) == 1


async def test_entry_setup_does_not_re_register_an_existing_card(hass):
    """The guard is load-bearing: static paths are not registered twice.

    hass.http.async_register_static_paths appends to the aiohttp route table
    every time it is called, so an unguarded re-registration would add litter
    on every entry setup.
    """
    await _setup_storage_mode(hass)
    assert await async_setup(hass, {}) is True

    entry = MockConfigEntry(domain=DOMAIN, data={"symbol": "MSFT"})
    entry.add_to_hass(hass)
    with _mock_coordinator(), patch.object(
        hass.config_entries, "async_forward_entry_setups", return_value=None
    ), patch("custom_components.easy_stock.async_register_card") as mock_register:
        assert await async_setup_entry(hass, entry) is True

    assert mock_register.call_count == 0
