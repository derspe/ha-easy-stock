"""Unit tests for the ISIN helpers."""
import aiohttp
import pytest

from custom_components.easy_stock import isin
from custom_components.easy_stock.isin import isin_checksum_valid, looks_like_isin
from tests.conftest import mock_http


@pytest.mark.parametrize("isin", ["US0378331005", "DE0007164600", "IE00B4L5Y983"])
def test_valid_isins(isin):
    assert looks_like_isin(isin)
    assert isin_checksum_valid(isin)


@pytest.mark.parametrize("value", ["AAPL", "SAP.DE", "BTC-USD", "US037833100", "1E0007164600", "de0007164600"])
def test_non_isins_are_not_matched(value):
    assert not looks_like_isin(value)


def test_wrong_check_digit_rejected():
    assert not isin_checksum_valid("US0378331006")


async def test_search_prefers_openfigi():
    from unittest.mock import patch

    found = [{"symbol": "EUNL.DE", "exchange": "XETRA", "name": "ISHARES", "currency": "EUR"}]
    with patch.object(isin, "find_listings", return_value=found) as figi, \
            patch.object(isin, "_search_yahoo") as yahoo:
        result = await isin.search_isin("IE00B4L5Y983", "EUR", "DE")

    assert result == found
    figi.assert_awaited_once_with("ID_ISIN", "IE00B4L5Y983", "EUR", "DE")
    yahoo.assert_not_called()


async def test_search_falls_back_to_yahoo_when_openfigi_knows_nothing():
    from unittest.mock import patch

    found = [{"symbol": "IWDA.L", "exchange": "London", "name": "ISHARES", "currency": "USD"}]
    with patch.object(isin, "find_listings", return_value=[]), \
            patch.object(isin, "_search_yahoo", return_value=found) as yahoo:
        result = await isin.search_isin("IE00B4L5Y983", "EUR", "DE")

    assert result == found
    yahoo.assert_awaited_once_with("IE00B4L5Y983", "EUR", "DE")


async def test_search_falls_back_to_yahoo_when_openfigi_is_unreachable():
    from unittest.mock import patch

    found = [{"symbol": "IWDA.L", "exchange": "London", "name": "ISHARES", "currency": "USD"}]
    with patch.object(isin, "find_listings", side_effect=aiohttp.ClientError("boom")), \
            patch.object(isin, "_search_yahoo", return_value=found):
        assert await isin.search_isin("IE00B4L5Y983") == found


async def test_search_raises_when_both_sources_fail():
    from unittest.mock import patch

    with patch.object(isin, "find_listings", side_effect=aiohttp.ClientError("boom")), \
            patch.object(isin, "_search_yahoo", side_effect=aiohttp.ClientError("down")), \
            pytest.raises(aiohttp.ClientError):
        await isin.search_isin("IE00B4L5Y983")


async def test_yahoo_search_maps_quotes():
    payload = {"quotes": [
        {"symbol": "SAP.DE", "exchDisp": "XETRA", "shortname": "SAP SE   I"},
        {"symbol": "SAP", "exchange": "NYQ", "longname": "SAP SE"},
        {"exchDisp": "nothing"},
    ]}
    from unittest.mock import patch
    from custom_components.easy_stock import listings
    import time

    patcher, _ = mock_http(payload)
    with patcher, patch.object(listings, "chart_stats", return_value=listings.ChartStats(250, int(time.time()), "EUR")):
        result = await isin._search_yahoo("DE0007164600", "", None)

    assert result == [
        {"symbol": "SAP.DE", "exchange": "XETRA", "name": "SAP SE   I", "currency": "EUR"},
        {"symbol": "SAP", "exchange": "NYQ", "name": "SAP SE", "currency": "EUR"},
    ]


async def test_yahoo_search_vets_listings_and_puts_the_users_own_first():
    from unittest.mock import patch
    from custom_components.easy_stock import listings
    import time

    payload = {"quotes": [
        {"symbol": "IWDA.L", "exchDisp": "London", "shortname": "ISHARES"},
        {"symbol": "EUNL.DE", "exchDisp": "XETRA", "shortname": "ISHARES"},
        {"symbol": "IWDA.MU", "exchDisp": "Munich", "shortname": "ISHARES"},
    ]}
    now = int(time.time())
    charts = {"IWDA.L": (250, now, "USD"), "EUNL.DE": (250, now, "EUR"), "IWDA.MU": (1, now, "EUR")}

    async def chart_stats(symbol):
        return listings.ChartStats(*charts[symbol])

    patcher, _ = mock_http(payload)
    with patcher, patch.object(listings, "chart_stats", side_effect=chart_stats):
        result = await isin._search_yahoo("IE00B4L5Y983", "EUR", "DE")

    assert [(r["symbol"], r["currency"]) for r in result] == [("EUNL.DE", "EUR"), ("IWDA.L", "USD")]


async def test_yahoo_search_empty():
    patcher, _ = mock_http({"quotes": []})
    with patcher:
        assert await isin._search_yahoo("DE0007164600", "", None) == []


async def test_yahoo_search_http_error_raises():
    patcher, _ = mock_http({}, status=429)
    with patcher, pytest.raises(aiohttp.ClientError):
        await isin._search_yahoo("DE0007164600", "", None)


@pytest.mark.parametrize("payload", [[], "nope", {"quotes": 5}, {"quotes": [5]}])
async def test_yahoo_search_rejects_a_malformed_payload(payload):
    patcher, _ = mock_http(payload)
    with patcher, pytest.raises(ValueError):
        await isin._search_yahoo("DE0007164600", "", None)


@pytest.mark.parametrize("stats", [None, (1, 0, "EUR"), (250, 1, "EUR")])
async def test_yahoo_fallback_does_not_restore_unusable_listings(stats):
    from unittest.mock import patch
    from custom_components.easy_stock import listings

    patcher, _ = mock_http({"quotes": [{"symbol": "DEAD.L", "exchDisp": "London"}]})
    chart = listings.ChartStats(*stats) if stats else None
    with patcher, patch.object(listings, "chart_stats", return_value=chart):
        assert await isin._search_yahoo("US0378331005", "EUR", "DE") == []


async def test_empty_fallback_does_not_hide_an_openfigi_outage():
    from unittest.mock import patch

    with patch.object(isin, "find_listings", side_effect=aiohttp.ClientError("down")), \
            patch.object(isin, "_search_yahoo", return_value=[]), pytest.raises(aiohttp.ClientError):
        await isin.search_isin("US0378331005")
