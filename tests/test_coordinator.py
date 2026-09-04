"""Unit tests for StockDataCoordinator."""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.easy_stock.coordinator import StockDataCoordinator
from custom_components.easy_stock.const import YAHOO_CHART_URL, YAHOO_CHART_URL_MINI

from .conftest import (
    SYMBOL,
    SAMPLE_DAYS,
    make_trading_period,
    make_yahoo_payload,
    make_store,
    mock_http,
)


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


async def test_todays_history_entry_is_refreshed_while_the_session_runs(hass):
    """Yahoo rewrites today's candle as the session runs — the stored point must follow.

    Appending only on a new date froze today's entry at the first intraday sample
    seen, so every stored "daily close" was whatever the price happened to be at
    the first poll of that day.
    """
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history = [[d, p] for d, p in SAMPLE_DAYS] + [[today_str, 190.00]]
    store = make_store(history=history)
    coord = StockDataCoordinator(hass, SYMBOL, 900, store)

    payload = make_yahoo_payload(days_prices=SAMPLE_DAYS[-1:] + [(today_str, 195.00)])
    patcher, _ = mock_http(payload)

    with patcher:
        await coord._async_update_data()

    assert coord._history[-1] == [today_str, 195.00]
    assert len(coord._history) == len(SAMPLE_DAYS) + 1  # refreshed, not appended
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
    """No trading windows → fall back to the heuristic: meta_price moved → live."""
    coord = _coord(hass)
    last_close = SAMPLE_DAYS[-1][1]
    meta = round(last_close * 1.005, 4)  # 0.5% above close

    patcher, _ = mock_http(make_yahoo_payload(meta_price=meta, trading_period=None))

    with patcher:
        result = await coord._async_update_data()

    assert result["current_price"] == meta
    assert result["price_is_live"] is True


async def test_price_is_stale_when_meta_matches_last_close(hass):
    """No trading windows, old candle and meta_price == last close → stale."""
    coord = _coord(hass)
    last_close = SAMPLE_DAYS[-1][1]

    patcher, _ = mock_http(make_yahoo_payload(meta_price=last_close, trading_period=None))

    with patcher:
        result = await coord._async_update_data()

    assert result["current_price"] == last_close
    assert result["price_is_live"] is False


# ---------------------------------------------------------------------------
# Market state (issue #13 — Yahoo dropped meta.marketState)
# ---------------------------------------------------------------------------


async def test_market_state_derived_when_yahoo_omits_it(hass):
    """Open regular window and no marketState field → REGULAR, not the CLOSED default."""
    coord = _coord(hass)
    patcher, _ = mock_http(make_yahoo_payload())

    with patcher:
        result = await coord._async_update_data()

    assert result["market_state"] == "REGULAR"


async def test_market_state_closed_after_the_session_ended(hass):
    """Session over but still the same UTC day (Tokyo case) → CLOSED, price not live."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days = SAMPLE_DAYS[:-1] + [(today_str, 195.00)]
    coord = _coord(hass)
    patcher, _ = mock_http(
        make_yahoo_payload(days_prices=days, trading_period=make_trading_period(open_now=False))
    )

    with patcher:
        result = await coord._async_update_data()

    assert result["market_state"] == "CLOSED"
    assert result["price_is_live"] is False


async def test_traded_today_stays_true_after_the_session_ended(hass):
    """The card needs "did it trade today" — that stays true once the market shuts."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days = SAMPLE_DAYS[:-1] + [(today_str, 195.00)]
    coord = _coord(hass)
    patcher, _ = mock_http(
        make_yahoo_payload(days_prices=days, trading_period=make_trading_period(open_now=False))
    )

    with patcher:
        result = await coord._async_update_data()

    assert result["traded_today"] is True


async def test_traded_today_false_when_the_last_candle_is_old(hass):
    coord = _coord(hass)
    last_close = SAMPLE_DAYS[-1][1]
    patcher, _ = mock_http(make_yahoo_payload(meta_price=last_close, trading_period=None))

    with patcher:
        result = await coord._async_update_data()

    assert result["traded_today"] is False


async def test_market_state_falls_back_to_closed_without_trading_windows(hass):
    """Undeterminable session → keep the documented CLOSED default for the attribute."""
    coord = _coord(hass)
    patcher, _ = mock_http(make_yahoo_payload(trading_period=None))

    with patcher:
        result = await coord._async_update_data()

    assert result["market_state"] == "CLOSED"


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


# ---------------------------------------------------------------------------
# Price precision (issue #17)
# ---------------------------------------------------------------------------


async def test_a_sub_cent_price_is_not_rounded_to_zero(hass):
    """round(4.35e-06, 4) reported SHIB-EUR as a price of 0.00."""
    days = [("2024-01-02", 4.11e-06), ("2024-01-03", 4.35e-06)]
    coord = _coord(hass, history=None)
    patcher, _ = mock_http(make_yahoo_payload(days_prices=days, meta_price=4.35e-06))

    with patcher:
        data = await coord._async_update_data()

    assert data["current_price"] == pytest.approx(4.35e-06)
    assert data["previous_close"] == pytest.approx(4.11e-06)


async def test_the_stored_daily_history_keeps_sub_cent_prices(hass):
    """The 1M/YTD/1J charts read this store, so it must survive the same rounding."""
    days = [("2024-01-02", 4.11e-06), ("2024-01-03", 4.35e-06)]
    coord = _coord(hass, history=None)
    patcher, _ = mock_http(make_yahoo_payload(days_prices=days))

    with patcher:
        await coord._async_update_data()

    assert [p for _, p in coord._history] == pytest.approx([4.11e-06, 4.35e-06])


async def test_a_seven_cent_quote_keeps_more_than_four_decimals(hass):
    """0.0001 on a 0.07 quote is a 0.14 % step — wider than a quiet day."""
    days = [("2024-01-02", 0.070113), ("2024-01-03", 0.071372)]
    coord = _coord(hass, history=None)
    patcher, _ = mock_http(make_yahoo_payload(days_prices=days, meta_price=0.071372))

    with patcher:
        data = await coord._async_update_data()

    assert data["current_price"] == pytest.approx(0.071372)


async def test_an_ordinary_quote_is_unaffected(hass):
    """The change must not regress for the prices the card already handled."""
    days = [("2024-01-02", 445.2), ("2024-01-03", 450.6)]
    coord = _coord(hass, history=None)
    patcher, _ = mock_http(make_yahoo_payload(days_prices=days, meta_price=450.6))

    with patcher:
        data = await coord._async_update_data()

    assert data["current_price"] == pytest.approx(450.6)
    assert data["previous_close"] == pytest.approx(445.2)
    assert data["change"] == pytest.approx(5.4)

