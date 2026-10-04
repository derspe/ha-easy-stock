"""Unit tests for the shared ZwitserlevenDataCoordinator."""
import logging
from datetime import UTC, datetime, timedelta

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zwitserleven_fondsen.coordinator import (
    ZwitserlevenDataCoordinator,
    get_coordinator,
)
from custom_components.zwitserleven_fondsen.fondsen_page import FondsenPageError

from .conftest import SYMBOL, make_page, make_store, quote


async def _coord(hass, page, history=None, symbol=SYMBOL):
    coord = ZwitserlevenDataCoordinator(hass, page)
    store = make_store(history)
    await coord.async_add_fund(symbol, store)
    return coord, store


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


async def test_returns_the_fund_quote(hass):
    coord, _ = await _coord(hass, make_page(quote()))

    data = await coord._async_update_data()

    assert data[SYMBOL] == {
        "symbol": SYMBOL,
        "long_name": "ASN Duurzaam Aandelenfonds",
        "price_date": "2026-10-02",
        "current_price": 225.87,
        "previous_close": 225.87,
        "change": 0,
        "change_pct": 0,
    }


async def test_change_against_the_previous_day(hass):
    coord, _ = await _coord(hass, make_page(quote(price=225.87)), [["2026-10-01", 220.0]])

    result = (await coord._async_update_data())[SYMBOL]

    assert result["previous_close"] == 220.0
    assert result["change"] == 5.87
    assert result["change_pct"] == round(5.87 / 220 * 100, 2)


async def test_change_survives_repeated_polls_on_the_same_day(hass):
    """The second poll of a day must still compare against the day before.

    The last history entry is today's own price by then; using it as the
    previous close dropped the change to 0 after the first poll.
    """
    coord, _ = await _coord(hass, make_page(quote(price=225.87)), [["2026-10-01", 220.0]])

    await coord._async_update_data()
    result = (await coord._async_update_data())[SYMBOL]

    assert result["previous_close"] == 220.0
    assert result["change"] == 5.87


async def test_prices_are_rounded_to_four_decimals(hass):
    coord, _ = await _coord(hass, make_page(quote(price=7.137149)), [["2026-10-01", 7.0]])

    result = (await coord._async_update_data())[SYMBOL]

    assert result["current_price"] == 7.1371
    assert result["change"] == 0.1371


# ---------------------------------------------------------------------------
# One download for every fund
# ---------------------------------------------------------------------------


async def test_one_download_updates_every_fund(hass):
    page = make_page(quote(), quote(symbol="LTAOB", name="Obligaties", price=24.56))
    coord, _ = await _coord(hass, page)
    await coord.async_add_fund("LTAOB", make_store())

    data = await coord._async_update_data()

    assert set(data) == {SYMBOL, "LTAOB"}
    assert page.async_get_funds.call_count == 1


async def test_every_entry_shares_one_coordinator(hass):
    assert get_coordinator(hass) is get_coordinator(hass)


# ---------------------------------------------------------------------------
# Schedule: at startup (entry setup) and every day at 20:00 UTC
# ---------------------------------------------------------------------------

EVENING = datetime(2026, 10, 4, 20, 0, 0, tzinfo=UTC)


async def _fire(hass, freezer, when):
    freezer.move_to(when)
    async_fire_time_changed(hass, when)
    await hass.async_block_till_done()


async def test_does_not_poll_on_an_interval(hass):
    coord, _ = await _coord(hass, make_page(quote()))
    assert coord.update_interval is None


async def test_refreshes_every_day_at_20_utc(hass, freezer):
    freezer.move_to(EVENING - timedelta(hours=2))
    page = make_page(quote())
    await _coord(hass, page)

    await _fire(hass, freezer, EVENING - timedelta(hours=1))
    assert page.async_get_funds.call_count == 0

    await _fire(hass, freezer, EVENING)
    assert page.async_get_funds.call_count == 1

    await _fire(hass, freezer, EVENING + timedelta(days=1))
    assert page.async_get_funds.call_count == 2


async def test_failed_daily_refresh_is_retried_hourly_until_it_succeeds(hass, freezer):
    freezer.move_to(EVENING - timedelta(minutes=1))
    page = make_page(error=FondsenPageError("Zwitserleven returned HTTP 503"))
    await _coord(hass, page)

    await _fire(hass, freezer, EVENING)
    await _fire(hass, freezer, EVENING + timedelta(hours=1))
    assert page.async_get_funds.call_count == 2

    page.async_get_funds.side_effect = None
    page.async_get_funds.return_value = {SYMBOL: quote()}
    await _fire(hass, freezer, EVENING + timedelta(hours=2))
    assert page.async_get_funds.call_count == 3

    # Back to the daily schedule: no more hourly retries.
    await _fire(hass, freezer, EVENING + timedelta(hours=3))
    assert page.async_get_funds.call_count == 3


async def test_schedule_stops_with_the_last_fund(hass, freezer):
    freezer.move_to(EVENING - timedelta(minutes=1))
    page = make_page(quote())
    coord, _ = await _coord(hass, page)

    coord.remove_fund(SYMBOL)
    await _fire(hass, freezer, EVENING)

    assert page.async_get_funds.call_count == 0


async def test_removed_fund_is_no_longer_updated(hass):
    coord, store = await _coord(hass, make_page(quote()))
    coord.remove_fund(SYMBOL)

    data = await coord._async_update_data()

    assert data == {}
    assert coord.history(SYMBOL) is None
    store.async_save.assert_not_called()


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


async def test_first_fetch_starts_the_history(hass):
    coord, store = await _coord(hass, make_page(quote()))

    await coord._async_update_data()

    assert coord.history(SYMBOL) == [["2026-10-02", 225.87]]
    store.async_save.assert_called_once_with([["2026-10-02", 225.87]])


async def test_new_day_is_appended(hass):
    coord, store = await _coord(hass, make_page(quote()), [["2026-10-01", 220.0]])

    await coord._async_update_data()

    assert coord.history(SYMBOL) == [["2026-10-01", 220.0], ["2026-10-02", 225.87]]
    store.async_save.assert_called_once()


async def test_same_day_correction_replaces_the_price(hass):
    coord, store = await _coord(hass, make_page(quote(price=226.0)), [["2026-10-02", 225.87]])

    await coord._async_update_data()

    assert coord.history(SYMBOL) == [["2026-10-02", 226.0]]
    store.async_save.assert_called_once()


async def test_unchanged_price_is_not_saved_again(hass):
    coord, store = await _coord(hass, make_page(quote()), [["2026-10-02", 225.87]])

    await coord._async_update_data()

    store.async_save.assert_not_called()


async def test_older_date_is_not_recorded(hass):
    coord, store = await _coord(hass, make_page(quote(date="2026-10-01")), [["2026-10-02", 225.87]])

    await coord._async_update_data()

    assert coord.history(SYMBOL) == [["2026-10-02", 225.87]]
    store.async_save.assert_not_called()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


async def test_page_error_raises_update_failed(hass):
    coord, _ = await _coord(
        hass, make_page(error=FondsenPageError("Zwitserleven returned HTTP 429"))
    )

    with pytest.raises(UpdateFailed, match="HTTP 429"):
        await coord._async_update_data()


async def test_missing_fund_is_left_out_and_logged_once(hass, caplog):
    coord, _ = await _coord(hass, make_page(quote(symbol="LTAOB")))

    with caplog.at_level(logging.WARNING):
        assert await coord._async_update_data() == {}
        assert await coord._async_update_data() == {}

    assert caplog.text.count(f"Fund {SYMBOL} is no longer listed") == 1


async def test_returning_fund_is_logged(hass, caplog):
    page = make_page(quote(symbol="LTAOB"))
    coord, _ = await _coord(hass, page)
    await coord._async_update_data()

    page.async_get_funds.return_value = {SYMBOL: quote()}
    with caplog.at_level(logging.INFO):
        data = await coord._async_update_data()

    assert SYMBOL in data
    assert f"Fund {SYMBOL} is listed on the Zwitserleven page again" in caplog.text
