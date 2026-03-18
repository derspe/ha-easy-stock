"""Unit tests for EasyStockConfigFlow and EasyStockOptionsFlow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.easy_stock.const import (
    DOMAIN,
    CONF_SYMBOL,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)


# Patch out the actual HA setup so no coordinator/network calls are made
_SETUP_PATCHES = (
    patch("custom_components.easy_stock.async_setup", return_value=True),
    patch("custom_components.easy_stock.async_setup_entry", return_value=True),
)


async def _init_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


# ---------------------------------------------------------------------------
# Config flow
# ---------------------------------------------------------------------------


async def test_user_step_shows_form(hass):
    """Initial step returns a form."""
    result = await _init_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_config_flow_creates_entry(hass):
    """Submitting valid data creates a config entry."""
    result = await _init_flow(hass)

    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SYMBOL: "AAPL", CONF_NAME: "Apple", CONF_SCAN_INTERVAL: 900},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SYMBOL] == "AAPL"
    assert result["data"][CONF_NAME] == "Apple"
    assert result["data"][CONF_SCAN_INTERVAL] == 900


async def test_symbol_normalized_to_uppercase(hass):
    """Lowercase ticker input is stored as uppercase."""
    result = await _init_flow(hass)

    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SYMBOL: "aapl", CONF_NAME: "", CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
        )

    assert result["data"][CONF_SYMBOL] == "AAPL"


async def test_duplicate_symbol_aborts(hass):
    """Configuring the same symbol twice triggers an abort."""
    for _ in range(2):
        result = await _init_flow(hass)
        with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_SYMBOL: "TSLA", CONF_NAME: "", CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
            )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------


async def test_options_flow_shows_form(hass):
    """Options flow init step shows a form pre-filled with current values."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SYMBOL: "MSFT", CONF_NAME: "Microsoft", CONF_SCAN_INTERVAL: 900},
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_saves_new_values(hass):
    """Submitting options form saves updated name and interval."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SYMBOL: "MSFT", CONF_NAME: "Microsoft", CONF_SCAN_INTERVAL: 900},
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_NAME: "MSFT Stock", CONF_SCAN_INTERVAL: 1800},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_NAME] == "MSFT Stock"
    assert entry.options[CONF_SCAN_INTERVAL] == 1800
