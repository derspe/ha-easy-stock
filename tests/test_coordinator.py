"""Unit tests for ZwitserlevenDataCoordinator."""
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.zwitserleven_fondsen.coordinator import ZwitserlevenDataCoordinator
from custom_components.zwitserleven_fondsen.fondsen_page import FondsenPageError

from .conftest import SYMBOL, make_page, make_store, quote


def _coord(hass, page, history=None):
    store = make_store(history)
    return ZwitserlevenDataCoordinator(hass, SYMBOL, 3600, store, page), store


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


async def test_returns_the_fund_quote(hass):
    coord, _ = _coord(hass, make_page(quote()))

    result = await coord._async_update_data()

    assert result["symbol"] == SYMBOL
    assert result["long_name"] == "ASN Duurzaam Aandelenfonds"
    assert result["price_date"] == "2026-10-02"
    assert result["current_price"] == 225.87
    assert "history" not in result  # history is served via REST endpoint, not sensor state


async def test_change_against_the_previous_day(hass):
    coord, _ = _coord(hass, make_page(quote(price=225.87)), [["2026-10-01", 220.0]])

    result = await coord._async_update_data()

    assert result["previous_close"] == 220.0
    assert result["change"] == 5.87
    assert result["change_pct"] == round(5.87 / 220 * 100, 2)


async def test_change_survives_repeated_polls_on_the_same_day(hass):
    """The second poll of a day must still compare against the day before.

    The last history entry is today's own price by then; using it as the
    previous close dropped the change to 0 after the first poll.
    """
    coord, _ = _coord(hass, make_page(quote(price=225.87)), [["2026-10-01", 220.0]])

    await coord._async_update_data()
    result = await coord._async_update_data()

    assert result["previous_close"] == 220.0
    assert result["change"] == 5.87


async def test_prices_are_rounded_to_four_decimals(hass):
    coord, _ = _coord(hass, make_page(quote(price=7.137149)), [["2026-10-01", 7.0]])

    result = await coord._async_update_data()

    assert result["current_price"] == 7.1371
    assert result["change"] == 0.1371


async def test_first_price_ever_has_no_change(hass):
    coord, _ = _coord(hass, make_page(quote()))

    result = await coord._async_update_data()

    assert result["previous_close"] == 225.87
    assert result["change"] == 0


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


async def test_first_fetch_starts_the_history(hass):
    coord, store = _coord(hass, make_page(quote()))

    await coord._async_update_data()

    assert coord._history == [["2026-10-02", 225.87]]
    store.async_save.assert_called_once_with([["2026-10-02", 225.87]])


async def test_new_day_is_appended(hass):
    coord, store = _coord(hass, make_page(quote()), [["2026-10-01", 220.0]])

    await coord._async_update_data()

    assert coord._history == [["2026-10-01", 220.0], ["2026-10-02", 225.87]]
    store.async_save.assert_called_once()


async def test_same_day_correction_replaces_the_price(hass):
    coord, store = _coord(hass, make_page(quote(price=226.0)), [["2026-10-02", 225.87]])

    await coord._async_update_data()

    assert coord._history == [["2026-10-02", 226.0]]
    store.async_save.assert_called_once()


async def test_unchanged_price_is_not_saved_again(hass):
    coord, store = _coord(hass, make_page(quote()), [["2026-10-02", 225.87]])

    await coord._async_update_data()

    store.async_save.assert_not_called()


async def test_older_date_is_not_recorded(hass):
    coord, store = _coord(hass, make_page(quote(date="2026-10-01")), [["2026-10-02", 225.87]])

    await coord._async_update_data()

    assert coord._history == [["2026-10-02", 225.87]]
    store.async_save.assert_not_called()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


async def test_page_error_raises_update_failed(hass):
    coord, _ = _coord(hass, make_page(error=FondsenPageError("Zwitserleven returned HTTP 429")))

    with pytest.raises(UpdateFailed, match="HTTP 429"):
        await coord._async_update_data()


async def test_missing_fund_raises_update_failed(hass):
    coord, _ = _coord(hass, make_page(quote(symbol="LTAOB")))

    with pytest.raises(UpdateFailed, match=f"{SYMBOL} not found"):
        await coord._async_update_data()
