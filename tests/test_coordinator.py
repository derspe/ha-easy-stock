"""Unit tests for StockDataCoordinator."""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.easy_stock.coordinator import StockDataCoordinator
from custom_components.easy_stock.const import YAHOO_CHART_URL, YAHOO_CHART_URL_MINI

from .conftest import SYMBOL, SAMPLE_DAYS, make_yahoo_payload, make_store, mock_http


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _coord(hass, history=None):
    return StockDataCoordinator(hass, SYMBOL, 900, make_store(history))


# ---------------------------------------------------------------------------
# URL selection
# ---------------------------------------------------------------------------


async def test_first_call_uses_backfill_url(hass):
    """Empty history → full 1y URL."""
    coord = _coord(hass, history=None)
    patcher, mock_session = mock_http(make_yahoo_payload())

    with patcher:
        await coord._async_update_data()

    called_url = mock_session.get.call_args[0][0]
    assert called_url == YAHOO_CHART_URL.format(symbol=SYMBOL)


async def test_subsequent_call_uses_mini_url(hass):
    """Existing history with < 250 entries → mini 5d URL."""
    history = [[d, p] for d, p in SAMPLE_DAYS]
    coord = _coord(hass, history=history)
    patcher, mock_session = mock_http(make_yahoo_payload())

    with patcher:
        await coord._async_update_data()

    called_url = mock_session.get.call_args[0][0]
    assert called_url == YAHOO_CHART_URL_MINI.format(symbol=SYMBOL)


async def test_migration_triggers_backfill(hass):
    """≥250 entries but oldest is < 355 days ago → backfill to fix truncated crypto history."""
    today = datetime.now(timezone.utc)
    # Build 250 entries starting 300 days ago (too recent — crypto migration case)
    history = [
        [(today - timedelta(days=300 - i)).strftime("%Y-%m-%d"), 100.0 + i]
        for i in range(250)
    ]
    coord = _coord(hass, history=history)
    patcher, mock_session = mock_http(make_yahoo_payload())

    with patcher:
        await coord._async_update_data()

    called_url = mock_session.get.call_args[0][0]
    assert called_url == YAHOO_CHART_URL.format(symbol=SYMBOL)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


async def test_parses_response_fields(hass):
    """Parsed result dict contains all expected keys with correct values."""
    coord = _coord(hass)
    payload = make_yahoo_payload()
    patcher, _ = mock_http(payload)

    with patcher:
        result = await coord._async_update_data()

    assert result["symbol"] == SYMBOL
    assert result["currency"] == "USD"
    assert result["long_name"] == "Apple Inc."
    assert result["market_state"] == "REGULAR"
    assert isinstance(result["current_price"], float)
    assert isinstance(result["change"], float)
    assert isinstance(result["change_pct"], float)
    assert "price_is_live" in result
    assert "history" not in result  # history is served via REST endpoint, not sensor state


async def test_backfill_populates_history(hass):
    """First fetch stores history (capped at 365 entries)."""
    store = make_store(history=None)
    coord = StockDataCoordinator(hass, SYMBOL, 900, store)
    patcher, _ = mock_http(make_yahoo_payload())

    with patcher:
        await coord._async_update_data()

    assert coord._history is not None
    assert len(coord._history) <= 365
    store.async_save.assert_called_once()


async def test_new_day_appended_to_history(hass):
    """Mini fetch appends a new trading day that isn't in history yet."""
    history = [[d, p] for d, p in SAMPLE_DAYS[:-1]]  # missing last day
    store = make_store(history=history)
    coord = StockDataCoordinator(hass, SYMBOL, 900, store)

    # Mini fetch returns only the last two days
    payload = make_yahoo_payload(days_prices=SAMPLE_DAYS[-2:])
    patcher, _ = mock_http(payload)

    with patcher:
        await coord._async_update_data()

    assert coord._history[-1][0] == SAMPLE_DAYS[-1][0]
    store.async_save.assert_called_once()


async def test_no_duplicate_appended_when_date_unchanged(hass):
    """Mini fetch with no new date leaves history unchanged."""
    history = [[d, p] for d, p in SAMPLE_DAYS]
    store = make_store(history=history)
    coord = StockDataCoordinator(hass, SYMBOL, 900, store)

    # All fetched dates already in history
    patcher, _ = mock_http(make_yahoo_payload())

    with patcher:
        await coord._async_update_data()

    assert len(coord._history) == len(SAMPLE_DAYS)
    store.async_save.assert_not_called()


# ---------------------------------------------------------------------------
# Price logic
# ---------------------------------------------------------------------------


async def test_price_is_live_when_last_date_is_today(hass):
    """When the latest candle date == today, meta_price is used and price_is_live=True."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days = SAMPLE_DAYS[:-1] + [(today_str, 195.00)]
    meta = 196.50

    coord = _coord(hass)
    patcher, _ = mock_http(make_yahoo_payload(days_prices=days, meta_price=meta))

    with patcher:
        result = await coord._async_update_data()

    assert result["current_price"] == meta
    assert result["price_is_live"] is True


async def test_price_is_live_when_meta_differs_from_last_close(hass):
    """Old candle date but meta_price differs by >0.01% → live pre/after-market price."""
    coord = _coord(hass)
    last_close = SAMPLE_DAYS[-1][1]
    meta = round(last_close * 1.005, 4)  # 0.5% above close

    patcher, _ = mock_http(make_yahoo_payload(meta_price=meta))

    with patcher:
        result = await coord._async_update_data()

    assert result["current_price"] == meta
    assert result["price_is_live"] is True


async def test_price_is_stale_when_meta_matches_last_close(hass):
    """Old candle date and meta_price == last close → stale, price_is_live=False."""
    coord = _coord(hass)
    last_close = SAMPLE_DAYS[-1][1]

    patcher, _ = mock_http(make_yahoo_payload(meta_price=last_close))

    with patcher:
        result = await coord._async_update_data()

    assert result["current_price"] == last_close
    assert result["price_is_live"] is False


async def test_change_and_change_pct_calculation(hass):
    """change = current - prev_close; change_pct = change / prev_close * 100."""
    coord = _coord(hass)
    last_close = SAMPLE_DAYS[-1][1]  # 189.30
    prev_close = SAMPLE_DAYS[-2][1]  # 188.00

    patcher, _ = mock_http(make_yahoo_payload(meta_price=last_close))

    with patcher:
        result = await coord._async_update_data()

    expected_change = round(last_close - prev_close, 4)
    expected_pct = round((last_close - prev_close) / prev_close * 100, 2)
    assert result["change"] == pytest.approx(expected_change, abs=0.001)
    assert result["change_pct"] == pytest.approx(expected_pct, abs=0.01)


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
    """Missing 'result' key in Yahoo response raises UpdateFailed."""
    coord = _coord(hass)
    bad_payload = {"chart": {"result": None, "error": "Not found"}}
    patcher, _ = mock_http(bad_payload)

    with patcher, pytest.raises(UpdateFailed, match="Error parsing"):
        await coord._async_update_data()


async def test_missing_timestamps_raises_update_failed(hass):
    """Response without timestamps/indicators raises UpdateFailed."""
    coord = _coord(hass)
    bad_payload = {"chart": {"result": [{"meta": {}}], "error": None}}
    patcher, _ = mock_http(bad_payload)

    with patcher, pytest.raises(UpdateFailed):
        await coord._async_update_data()
