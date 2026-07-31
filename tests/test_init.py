"""Unit tests for custom_components/easy_stock/__init__.py."""
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.easy_stock import async_unload_entry
from custom_components.easy_stock.const import DOMAIN


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
