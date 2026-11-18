"""Unit tests for StockDataCoordinator."""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import aiohttp
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
    make_hourly_payload,
    mock_http,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bars_today(price=1.0):
    """One intraday bar on today's date — what a day with trading actually looks like."""
    noon = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    return make_hourly_payload([(noon, price)])


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

    called_url = mock_session.get.call_args_list[0][0][0]
    assert called_url == YAHOO_CHART_URL.format(symbol=SYMBOL)


async def test_subsequent_call_uses_mini_url(hass):
    """Existing history with < 250 entries → mini 5d URL."""
    history = [[d, p] for d, p in SAMPLE_DAYS]
    coord = _coord(hass, history=history)
    patcher, mock_session = mock_http(make_yahoo_payload())

    with patcher:
        await coord._async_update_data()

    called_url = mock_session.get.call_args_list[0][0][0]
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

    called_url = mock_session.get.call_args_list[0][0][0]
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
    """No trading windows → price_is_live falls back to "did it trade today"."""
    await hass.config.async_set_time_zone("UTC")
    coord = _coord(hass)
    last_close = SAMPLE_DAYS[-1][1]
    meta = round(last_close * 1.005, 4)  # 0.5% above close

    patcher, _ = mock_http(
        make_yahoo_payload(meta_price=meta, trading_period=None),
        hourly_payload=_bars_today(meta),
    )

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
    await hass.config.async_set_time_zone("UTC")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days = SAMPLE_DAYS[:-1] + [(today_str, 195.00)]
    coord = _coord(hass)
    patcher, _ = mock_http(
        make_yahoo_payload(days_prices=days, trading_period=make_trading_period(open_now=False)),
        hourly_payload=_bars_today(195.00),
    )

    with patcher:
        result = await coord._async_update_data()

    assert result["market_state"] == "CLOSED"
    assert result["price_is_live"] is False


async def test_traded_today_stays_true_after_the_session_ended(hass):
    """The card needs "did it trade today" — that stays true once the market shuts."""
    await hass.config.async_set_time_zone("UTC")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days = SAMPLE_DAYS[:-1] + [(today_str, 195.00)]
    coord = _coord(hass)
    patcher, _ = mock_http(
        make_yahoo_payload(days_prices=days, trading_period=make_trading_period(open_now=False)),
        hourly_payload=_bars_today(195.00),
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


# ---------------------------------------------------------------------------
# Day boundary (issue #17)
# ---------------------------------------------------------------------------


async def test_a_stock_has_not_traded_today_in_the_local_hours_before_utc_midnight(hass, freezer):
    """Saturday 00:30 in Berlin is still Friday in UTC.

    The card cuts its 1T series at *local* midnight, so while the coordinator
    called Friday "today" it kept writing Yahoo's post-close revisions of the
    Friday price into what the card reads as Saturday. Those two hours of noise
    were the entire content of the weekend chart.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2024-05-31T22:30:00+00:00")  # Sat 00:30 local, Fri 22:30 UTC

    days = [("2024-05-30", 100.0), ("2024-05-31", 101.0)]  # last session: Friday
    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=days,
            meta_price=101.0,
            trading_period=make_trading_period(open_now=False),
        )
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is False


async def test_a_stock_has_traded_today_while_its_session_is_running(hass, freezer):
    """Guard for the above: the ordinary case must keep reporting True."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2024-05-31T13:00:00+00:00")  # Fri 15:00 local, mid-session

    days = [("2024-05-30", 100.0), ("2024-05-31", 101.0)]
    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=days,
            meta_price=101.0,
            trading_period=make_trading_period(open_now=True),
        ),
        hourly_payload=make_hourly_payload(
            [(datetime(2024, 5, 31, 12, 0, tzinfo=timezone.utc), 101.0)]
        ),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is True


# ---------------------------------------------------------------------------
# traded_today from Yahoo's last trade timestamp (issue #17, gold on a weekend)
# ---------------------------------------------------------------------------

GOLD_DAYS = [("2026-09-03", 4491.70), ("2026-09-04", 4429.80)]
GOLD_LAST_TRADE = int(datetime(2026, 9, 4, 19, 0, tzinfo=timezone.utc).timestamp())


async def test_a_future_that_rested_all_weekend_has_not_traded_today(hass, freezer):
    """Gold's daily candle is the pit close, regularMarketPrice the electronic one.

    The two sat 1.06 % apart over the weekend, and the old rule read any such
    difference as "a session must be running", so the card drew a rising line
    for an asset that had not traded since Friday.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-09-05T09:15:00+00:00")  # Sat 11:15 local

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=GOLD_DAYS,
            meta_price=4476.60,
            market_time=GOLD_LAST_TRADE,
            trading_period=make_trading_period(open_now=False),
        )
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is False
    # still the last price anyone paid, not the pit close
    assert data["current_price"] == pytest.approx(4476.60)
    # the close before Friday's session, so the change describes Friday
    assert data["previous_close"] == pytest.approx(4491.70)


async def test_a_running_session_counts_before_yahoo_writes_todays_candle(hass, freezer):
    """The case the old rule existed for, and which must keep working."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-09-08T09:15:00+00:00")  # Tue 11:15 local

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-09-04", 100.0), ("2026-09-07", 101.0)],
            meta_price=102.0,
            market_time=int(datetime(2026, 9, 8, 9, 10, tzinfo=timezone.utc).timestamp()),
            trading_period=make_trading_period(open_now=True),
        ),
        hourly_payload=make_hourly_payload(
            [(datetime(2026, 9, 8, 8, 0, tzinfo=timezone.utc), 102.0)]
        ),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is True
    assert data["current_price"] == pytest.approx(102.0)
    assert data["previous_close"] == pytest.approx(101.0)


async def test_the_price_heuristic_is_the_last_resort(hass, freezer):
    """With no intraday series and no last-trade stamp, the oldest rule decides.

    Yahoo has dropped fields before, and the intraday request can fail, so the
    chain still ends somewhere rather than reporting "did not trade".
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-09-08T09:15:00+00:00")

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-09-04", 100.0), ("2026-09-07", 101.0)],
            meta_price=102.0,
            trading_period=make_trading_period(open_now=True),
        ),
        hourly_raises=aiohttp.ClientError("no intraday"),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is True


# ---------------------------------------------------------------------------
# traded_today from intraday bars (measured weekend 17./18.10.2026)
# ---------------------------------------------------------------------------


async def test_a_refreshed_fx_quote_on_a_sunday_is_not_a_trade(hass, freezer):
    """Yahoo refreshes the FX quote over the weekend while the bars stay stale.

    Measured on Sunday 18.10.2026 at 22:34 Berlin: `regularMarketTime` jumped to
    a stamp 14 minutes old and the price moved, while the newest hourly bar was
    still the previous Friday and `currentTradingPeriod` still described the
    Friday session. Reading the quote — its price or its timestamp — calls that a
    trading day. The bars do not.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-10-18T20:34:00+00:00")  # Sun 22:34 Berlin

    days = [("2026-10-15", 0.82775), ("2026-10-16", 0.82361)]  # last session: Friday
    friday_bar = datetime(2026, 10, 16, 20, 0, tzinfo=timezone.utc)

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=days,
            meta_price=0.8253,  # refreshed quote
            market_time=int(datetime(2026, 10, 18, 20, 20, tzinfo=timezone.utc).timestamp()),
            trading_period=make_trading_period(open_now=False),
        ),
        hourly_payload=make_hourly_payload([(friday_bar, 0.82361)]),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is False


async def test_placeholder_bars_over_a_weekend_are_not_a_trade(hass, freezer):
    """Yahoo emits null-close bars on Saturdays; they must not count."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-10-17T07:05:00+00:00")  # Sat 09:05 Berlin

    saturday = datetime(2026, 10, 17, 8, 0, tzinfo=timezone.utc)
    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-10-15", 0.82775), ("2026-10-16", 0.82361)],
            meta_price=0.8236,
            market_time=int(datetime(2026, 10, 16, 20, 59, tzinfo=timezone.utc).timestamp()),
            trading_period=make_trading_period(open_now=False),
        ),
        hourly_payload=make_hourly_payload([(saturday, None)]),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is False


async def test_a_bar_today_counts_as_traded(hass, freezer):
    """The ordinary weekday case must keep working."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-10-19T13:00:00+00:00")  # Mon 15:00 Berlin

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-10-16", 100.0), ("2026-10-19", 101.0)],
            meta_price=101.5,
            market_time=int(datetime(2026, 10, 19, 12, 55, tzinfo=timezone.utc).timestamp()),
            trading_period=make_trading_period(open_now=True),
        ),
        hourly_payload=make_hourly_payload(
            [(datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc), 101.5)]
        ),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is True


async def test_a_failing_intraday_request_falls_back_to_the_old_rule(hass, freezer):
    """A flaky second request must not make the sensor worse than before."""
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-10-19T13:00:00+00:00")

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-10-16", 100.0), ("2026-10-19", 101.0)],
            meta_price=101.5,
            market_time=int(datetime(2026, 10, 19, 12, 55, tzinfo=timezone.utc).timestamp()),
            trading_period=make_trading_period(open_now=True),
        ),
        hourly_raises=aiohttp.ClientError("boom"),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is True
    assert data["current_price"] == pytest.approx(101.5)


async def test_a_resting_fx_pair_is_closed_even_with_a_fresh_quote(hass, freezer):
    """The session state must not believe the weekend quote refresh either.

    FX carries a 24-hour window like crypto, so only the age of the last tick
    separated "open" from "resting" — and that tick was refreshed on Sunday
    evening while nothing traded.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-10-18T20:34:00+00:00")  # Sun 22:34 Berlin

    now = int(datetime(2026, 10, 18, 20, 34, tzinfo=timezone.utc).timestamp())
    continuous = {
        "pre": {"start": now - 86400, "end": now - 86400},
        "regular": {"start": now - 86400, "end": now + 60},
        "post": {"start": now + 60, "end": now + 60},
    }

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-10-15", 0.82775), ("2026-10-16", 0.82361)],
            meta_price=0.8253,
            market_time=now - 840,  # refreshed fourteen minutes ago
            trading_period=continuous,
        ),
        hourly_payload=make_hourly_payload(
            [(datetime(2026, 10, 16, 20, 0, tzinfo=timezone.utc), 0.82361)]
        ),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is False
    assert data["market_state"] == "CLOSED"
    assert data["price_is_live"] is False


async def test_a_saturday_candle_does_not_outvote_the_missing_bars(hass, freezer):
    """Yahoo stamps a daily candle with Saturday's date while nothing trades.

    Captured 24.10.2026 at 09:09 Berlin for `CHF=X`, the hour @AnAnalogGuy's
    screenshot was taken: `regularMarketTime` carried Saturday 06:21, and the
    daily series had grown a candle whose epoch equals that very timestamp, so
    its UTC date is Saturday. That makes *both* older signals say "traded
    today" — the last-trade stamp and the `last_date == today_str` branch. The
    intraday bars were the only ones that knew better: the newest one with a
    price was the previous Friday at 21:00 UTC.

    This guards the order of those branches: the bars have to win.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-10-24T07:09:00+00:00")  # Sat 09:09 Berlin

    saturday_stamp = int(datetime(2026, 10, 24, 4, 21, tzinfo=timezone.utc).timestamp())
    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-10-22", 0.8198), ("2026-10-24", 0.8241)],  # last one is today
            meta_price=0.8241,
            market_time=saturday_stamp,
            trading_period=make_trading_period(open_now=False),
        ),
        hourly_payload=make_hourly_payload(
            [(datetime(2026, 10, 23, 21, 0, tzinfo=timezone.utc), 0.8241)]  # Friday only
        ),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is False


# ---------------------------------------------------------------------------
# The trading date belongs to the exchange, not to the user (#17, Asia/Tokyo)
# ---------------------------------------------------------------------------

# 19.11.2026, 02:00 in Tokyo — which is still the 18th in New York and in London.
TOKYO_AFTER_MIDNIGHT = "2026-11-18T17:00:00+00:00"


async def test_a_us_index_after_tokyo_midnight_keeps_its_real_previous_close(hass, freezer):
    """Reported from a UTC+9 install on v0.5.1: change drops to zero at 00:00 JST.

    Candles were dated in UTC while "today" came from the Home Assistant
    timezone. In Tokyo those differ from 00:00 to 08:59, so the running US
    session no longer matched "today", and its own candle — the session in
    progress — was taken as the previous close. The change then collapses to
    zero while the market is open.
    """
    await hass.config.async_set_time_zone("Asia/Tokyo")
    freezer.move_to(TOKYO_AFTER_MIDNIGHT)

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-11-17", 24328.38), ("2026-11-18", 24309.05)],
            meta_price=24309.05,  # the running candle tracks the quote
            exchange_tz="America/New_York",
            session_hour_utc=14,  # 09:00 in New York
            trading_period=make_trading_period(open_now=True),
        ),
        hourly_payload=make_hourly_payload(
            [(datetime(2026, 11, 18, 16, 0, tzinfo=timezone.utc), 24309.05)]  # 01:00 JST
        ),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["previous_close"] == pytest.approx(24328.38)  # the session before, not itself
    assert data["change"] != 0


async def test_a_currency_pair_after_tokyo_midnight_keeps_its_real_previous_close(hass, freezer):
    """Same install reported USD/JPY recovering only after 09:00 JST."""
    await hass.config.async_set_time_zone("Asia/Tokyo")
    freezer.move_to(TOKYO_AFTER_MIDNIGHT)

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-11-17", 159.52), ("2026-11-18", 159.27)],
            meta_price=159.27,
            exchange_tz="Europe/London",
            trading_period=make_trading_period(open_now=True),
        ),
        hourly_payload=make_hourly_payload(
            [(datetime(2026, 11, 18, 16, 0, tzinfo=timezone.utc), 159.27)]
        ),
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["previous_close"] == pytest.approx(159.52)


async def test_a_tokyo_index_is_unaffected_for_a_tokyo_user(hass, freezer):
    """The reporter's control case: the Nikkei behaved correctly throughout."""
    await hass.config.async_set_time_zone("Asia/Tokyo")
    freezer.move_to(TOKYO_AFTER_MIDNIGHT)

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-11-17", 58860.43), ("2026-11-18", 59100.00)],
            meta_price=59100.00,
            exchange_tz="Asia/Tokyo",
            trading_period=make_trading_period(open_now=False),
        ),
        hourly_payload=make_hourly_payload([]),  # Tokyo has not opened yet at 02:00
    )

    with patcher:
        data = await coord._async_update_data()

    assert data["traded_today"] is False
    assert data["previous_close"] == pytest.approx(58860.43)


async def test_candles_are_dated_in_the_exchange_timezone(hass, freezer):
    """The stored history should carry session dates, not UTC dates.

    A Sydney open at 10:00 AEDT is 23:00 UTC the day before, so dating by UTC
    put every such candle one day early — the same mechanism, visible in the
    long-range charts.
    """
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-11-18T12:00:00+00:00")

    coord = _coord(hass, history=None)
    patcher, _ = mock_http(
        make_yahoo_payload(
            days_prices=[("2026-11-17", 8000.0), ("2026-11-18", 8050.0)],
            exchange_tz="Australia/Sydney",
            session_hour_utc=23,  # 10:00 in Sydney, the day after in UTC
            trading_period=make_trading_period(open_now=False),
        ),
        hourly_payload=make_hourly_payload([]),
    )

    with patcher:
        await coord._async_update_data()

    assert [d for d, _ in coord._history] == ["2026-11-18", "2026-11-19"]
