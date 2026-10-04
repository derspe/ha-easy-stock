"""Unit tests for ZwitserleverDataCoordinator."""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.zwitserleven_fondsen.coordinator import ZwitserleverDataCoordinator
from custom_components.zwitserleven_fondsen.const import ZWITSERLEVEN_FONDSEN_URL

from .conftest import (
    SYMBOL,
    SAMPLE_DAYS,
    make_zwitserleven_html,
    make_store,
    mock_http,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _coord(hass, history=None):
    return ZwitserleverDataCoordinator(hass, SYMBOL, 900, make_store(history))


# ---------------------------------------------------------------------------
# URL and HTML parsing
# ---------------------------------------------------------------------------


async def test_fetches_from_zwitserleven_url(hass):
    """Fetches Zwitserleven fondsen page and parses HTML."""
    coord = _coord(hass, history=None)
    patcher, mock_session = mock_http(make_zwitserleven_html())

    with patcher:
        await coord._async_update_data()

    called_url = mock_session.get.call_args[0][0]
    assert called_url == ZWITSERLEVEN_FONDSEN_URL


async def test_parses_html_and_extracts_fund_data(hass):
    """Parses HTML table and extracts fund information."""
    coord = _coord(hass)
    patcher, _ = mock_http(make_zwitserleven_html())

    with patcher:
        result = await coord._async_update_data()

    assert result["symbol"] == SYMBOL
    assert result["long_name"] == "Test Fund"
    assert isinstance(result["current_price"], float)
    assert "price_is_live" in result


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


async def test_parses_response_fields(hass):
    """Parsed result dict contains all expected keys with correct values."""
    coord = _coord(hass)
    patcher, _ = mock_http(make_zwitserleven_html())

    with patcher:
        result = await coord._async_update_data()

    assert result["symbol"] == SYMBOL
    assert result["long_name"] == "Test Fund"
    assert isinstance(result["current_price"], float)
    assert "price_is_live" in result
    assert "history" not in result  # history is served via REST endpoint, not sensor state


async def test_backfill_populates_history(hass):
    """First fetch stores history (capped at 365 entries)."""
    store = make_store(history=None)
    coord = ZwitserleverDataCoordinator(hass, SYMBOL, 900, store)
    patcher, _ = mock_http(make_zwitserleven_html())

    with patcher:
        await coord._async_update_data()

    assert coord._history is not None
    assert len(coord._history) <= 365
    store.async_save.assert_called_once()


async def test_new_day_appended_to_history(hass):
    """New fetch updates history with latest price."""
    history = [[d, p] for d, p in SAMPLE_DAYS[:-1]]
    store = make_store(history=history)
    coord = ZwitserleverDataCoordinator(hass, SYMBOL, 900, store)
    patcher, _ = mock_http(make_zwitserleven_html())

    with patcher:
        await coord._async_update_data()

    # History should be updated with at least the latest price
    assert len(coord._history) >= 1
    store.async_save.assert_called_once()


# ---------------------------------------------------------------------------
# Price extraction
# ---------------------------------------------------------------------------


async def test_price_is_extracted_correctly(hass):
    """Price is correctly parsed from HTML."""
    coord = _coord(hass)
    patcher, _ = mock_http(make_zwitserleven_html())

    with patcher:
        result = await coord._async_update_data()

    assert result["current_price"] == 225.87


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


async def test_http_error_raises_update_failed(hass):
    """Non-200 HTTP status raises UpdateFailed."""
    coord = _coord(hass)
    patcher, _ = mock_http({}, status=429)

    with patcher, pytest.raises(UpdateFailed, match="HTTP 429"):
        await coord._async_update_data()


async def test_network_error_raises_update_failed(hass):
    """aiohttp.ClientError raises UpdateFailed."""
    import aiohttp

    coord = _coord(hass)

    with patch("aiohttp.ClientSession", side_effect=aiohttp.ClientError("timeout")):
        with pytest.raises(UpdateFailed, match="Network error"):
            await coord._async_update_data()


async def test_malformed_response_raises_update_failed(hass):
    """Missing fund data in HTML response raises UpdateFailed."""
    coord = _coord(hass)
    bad_html = "<html><body></body></html>"
    patcher, _ = mock_http(bad_html)

    with patcher, pytest.raises(UpdateFailed, match="Error parsing"):
        await coord._async_update_data()


async def test_missing_fund_raises_update_failed(hass):
    """Response without fund data raises UpdateFailed."""
    coord = _coord(hass)
    bad_html = "<html><body><table class='fundoverview'></table></body></html>"
    patcher, _ = mock_http(bad_html)

    with patcher, pytest.raises(UpdateFailed):
        await coord._async_update_data()


