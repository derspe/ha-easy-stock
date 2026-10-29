"""Unit tests for the listing vetting shared by the ISIN and WKN lookups."""
import time
from unittest.mock import patch

import aiohttp
import pytest

from custom_components.easy_stock import listings
from tests.conftest import mock_http

FRESH = int(time.time())
STALE = FRESH - 3 * 365 * 86400


def _listing(symbol, exchange="", name=""):
    return {"symbol": symbol, "exchange": exchange, "name": name}


async def _vet(candidates, charts, **kw):
    async def chart_stats(symbol):
        stats = charts.get(symbol)
        return listings.ChartStats(*stats) if stats is not None else None

    with patch.object(listings, "chart_stats", side_effect=chart_stats):
        return await listings.vet_listings(candidates, **kw)


async def test_keeps_listings_with_history_and_a_recent_trade():
    result = await _vet([_listing("A.DE", "XETRA")], {"A.DE": (250, FRESH, "EUR")})

    assert result == [{"symbol": "A.DE", "exchange": "XETRA", "name": "", "currency": "EUR"}]


async def test_drops_a_listing_with_a_single_day_of_data():
    result = await _vet([_listing("A.MU")], {"A.MU": (1, FRESH, "EUR")})

    assert result == []


async def test_drops_a_dead_listing_with_a_stale_last_trade():
    result = await _vet([_listing("A.F")], {"A.F": (252, STALE, "EUR")})

    assert result == []


async def test_drops_a_listing_without_a_chart():
    assert await _vet([_listing("A.XX")], {}) == []


_VWRL = [
    _listing("VWRL.L", "London"),
    _listing("VWRL.AS", "Amsterdam"),
    _listing("VGWL.DE", "XETRA"),
    _listing("VWRL.MI", "Milan"),
]
_VWRL_CHARTS = {
    "VWRL.L": (250, FRESH, "GBp"),
    "VWRL.AS": (250, FRESH, "EUR"),
    "VGWL.DE": (250, FRESH, "EUR"),
    "VWRL.MI": (250, FRESH, "EUR"),
}


async def test_a_german_setup_gets_xetra_in_euro_first():
    result = await _vet(_VWRL, _VWRL_CHARTS, currency="EUR", country="DE")

    assert [r["symbol"] for r in result] == ["VGWL.DE", "VWRL.AS", "VWRL.MI", "VWRL.L"]


async def test_a_uk_setup_gets_london_in_pounds_first_and_no_german_venue_ahead():
    result = await _vet(_VWRL, _VWRL_CHARTS, currency="GBP", country="GB")

    # London quotes in pence; it still counts as the user's pound listing.
    assert [r["symbol"] for r in result][0] == "VWRL.L"


async def test_a_dutch_setup_gets_amsterdam_ahead_of_xetra():
    result = await _vet(_VWRL, _VWRL_CHARTS, currency="EUR", country="NL")

    assert [r["symbol"] for r in result][0] == "VWRL.AS"


async def test_currency_outranks_the_home_exchange():
    candidates = [_listing("X.L", "London"), _listing("X.DE", "XETRA")]
    charts = {"X.L": (250, FRESH, "USD"), "X.DE": (250, FRESH, "EUR")}
    result = await _vet(candidates, charts, currency="EUR", country="GB")

    assert [r["symbol"] for r in result] == ["X.DE", "X.L"]


async def test_us_symbols_without_a_suffix_are_the_us_home_exchange():
    candidates = [_listing("SAP.DE", "XETRA"), _listing("SAP", "NYSE")]
    charts = {"SAP.DE": (250, FRESH, "EUR"), "SAP": (250, FRESH, "USD")}
    result = await _vet(candidates, charts, currency="USD", country="US")

    assert [r["symbol"] for r in result] == ["SAP", "SAP.DE"]


async def test_unknown_country_and_currency_keep_the_callers_order():
    result = await _vet(_VWRL, _VWRL_CHARTS)

    assert [r["symbol"] for r in result] == ["VWRL.L", "VWRL.AS", "VGWL.DE", "VWRL.MI"]


async def test_nothing_vetted_gives_nothing_by_default():
    assert await _vet([_listing("A.DE")], {"A.DE": (1, FRESH, "EUR")}) == []


# ---------------------------------------------------------------------------
# Reading Yahoo's chart answer
# ---------------------------------------------------------------------------


def _chart(closes, market_time=FRESH, currency="EUR"):
    return {"chart": {"result": [{
        "meta": {"regularMarketTime": market_time, "currency": currency},
        "indicators": {"quote": [{"close": closes}]},
    }]}}


async def test_chart_stats_counts_the_closes_and_reads_time_and_currency():
    patcher, _ = mock_http(_chart([1.0, None, 2.0, 3.0], FRESH, "GBp"))
    with patcher:
        assert await listings.chart_stats("VWRL.L") == listings.ChartStats(3, FRESH, "GBp")


async def test_chart_stats_asks_for_the_year():
    patcher, session = mock_http(_chart([1.0]))
    with patcher:
        await listings.chart_stats("VWRL.L")

    assert "VWRL.L" in session.get.call_args.args[0]
    assert "range=1y" in session.get.call_args.args[0]


async def test_chart_stats_is_none_for_a_symbol_yahoo_does_not_have():
    patcher, _ = mock_http({}, status=404)
    with patcher:
        assert await listings.chart_stats("NOPE.DE") is None


@pytest.mark.parametrize("payload", [{"chart": {"result": None}}, {"chart": {"result": []}}])
async def test_chart_stats_is_none_for_an_empty_answer(payload):
    patcher, _ = mock_http(payload)
    with patcher:
        assert await listings.chart_stats("NOPE.DE") is None


async def test_chart_stats_propagates_a_network_error():
    patcher, session = mock_http({})
    session.get.side_effect = aiohttp.ClientConnectionError("down")
    with patcher, pytest.raises(aiohttp.ClientError):
        await listings.chart_stats("VWRL.L")


@pytest.mark.parametrize("status", [429, 500, 503])
async def test_chart_stats_propagates_an_outage(status):
    patcher, _ = mock_http({}, status=status)
    with patcher, pytest.raises(aiohttp.ClientError):
        await listings.chart_stats("VGWL.DE")


@pytest.mark.parametrize("payload", [{}, {"chart": {"error": {"code": "Internal Server Error"}, "result": None}}])
async def test_chart_stats_rejects_invalid_answers(payload):
    patcher, _ = mock_http(payload)
    with patcher, pytest.raises(ValueError):
        await listings.chart_stats("VGWL.DE")


async def test_chart_stats_propagates_a_timeout():
    patcher, session = mock_http({})
    session.get.side_effect = TimeoutError()
    with patcher, pytest.raises(TimeoutError):
        await listings.chart_stats("VGWL.DE")


async def test_a_failed_request_drops_only_that_listing():
    async def stats(symbol):
        if symbol == "VGWL.DE":
            raise aiohttp.ClientError("429")
        return listings.ChartStats(*_VWRL_CHARTS[symbol])

    with patch.object(listings, "chart_stats", side_effect=stats):
        result = await listings.vet_listings(_VWRL, "EUR", "DE")

    # The three that answered stay, in the usual order: euro lines before pounds.
    assert [r["symbol"] for r in result] == ["VWRL.AS", "VWRL.MI", "VWRL.L"]


async def test_every_request_failing_is_an_outage():
    async def stats(symbol):
        raise aiohttp.ClientError("503")

    with patch.object(listings, "chart_stats", side_effect=stats), pytest.raises(aiohttp.ClientError):
        await listings.vet_listings(_VWRL, "EUR", "DE")


async def test_yahoo_exchange_overrides_the_derived_exchange():
    payload = _chart([1.0] * 10)
    payload["chart"]["result"][0]["meta"]["fullExchangeName"] = "NasdaqGS"
    patcher, _ = mock_http(payload)
    with patcher:
        result = await listings.vet_listings([_listing("AAPL", "NYSE American")])
    assert result[0]["exchange"] == "NasdaqGS"
