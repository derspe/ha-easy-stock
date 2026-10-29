"""Unit tests for the OpenFIGI lookup shared by the ISIN and WKN searches."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.easy_stock import listings, openfigi

FRESH = int(time.time())


def _figi(ticker, exch, name="VANG FTSE AW USDD"):
    return {"ticker": ticker, "exchCode": exch, "name": name}


def _live(*symbols, currency="EUR"):
    return {s: (250, FRESH, currency) for s in symbols}


async def _search(figi, charts, currency="", country=None):
    """`charts` maps a Yahoo symbol to (daily closes, last trade time, currency); absent = no chart."""
    async def chart_stats(symbol):
        stats = charts.get(symbol)
        return listings.ChartStats(*stats) if stats is not None else None

    with patch.object(openfigi, "_figi_lookup", return_value=figi), \
            patch.object(listings, "chart_stats", side_effect=chart_stats):
        return await openfigi.find_listings("ID_WERTPAPIER", "A1JX52", currency, country)


async def test_maps_exchange_codes_to_yahoo_symbols():
    figi = [_figi("VGWL", "GY"), _figi("VWRL", "LN"), _figi("VWRL", "NA")]
    charts = {**_live("VGWL.DE", "VWRL.AS"), "VWRL.L": (250, FRESH, "GBp")}
    result = await _search(figi, charts)

    assert [(r["symbol"], r["exchange"]) for r in result] == [
        ("VGWL.DE", "XETRA"), ("VWRL.L", "London"), ("VWRL.AS", "Amsterdam"),
    ]


async def test_drops_unmapped_exchanges_and_currency_lines():
    figi = [_figi("VGWL", "GY"), _figi("VWRDCHF", "E1"), _figi("VGWL", "XX"), _figi("", "LN")]
    result = await _search(figi, _live("VGWL.DE", "VGWL"))

    assert [r["symbol"] for r in result] == ["VGWL.DE"]


async def test_drops_symbols_yahoo_has_no_chart_for():
    figi = [_figi("VGWL", "GY"), _figi("VGWL", "GF")]
    result = await _search(figi, _live("VGWL.DE"))

    assert [r["symbol"] for r in result] == ["VGWL.DE"]


async def test_dedupes_listings_and_maps_us_share_classes():
    figi = [_figi("BRK/B", "UN", "BERKSHIRE"), _figi("BRK/B", "UN", "BERKSHIRE"), _figi("BRK/B", "UW")]
    result = await _search(figi, _live("BRK-B"))

    assert result == [{"symbol": "BRK-B", "exchange": "NYSE", "name": "BERKSHIRE", "currency": "EUR"}]


async def test_nothing_found_returns_empty():
    assert await _search([], {}) == []


async def test_german_composite_stands_in_for_a_missing_xetra_line():
    figi = [_figi("VGWL", "GR"), _figi("VWRL", "LN")]
    result = await _search(figi, {**_live("VGWL.DE"), "VWRL.L": (250, FRESH, "GBp")})

    assert [(r["symbol"], r["exchange"]) for r in result] == [("VGWL.DE", "XETRA"), ("VWRL.L", "London")]


async def test_xetra_listed_under_both_codes_is_offered_once():
    figi = [_figi("SAP", "GY"), _figi("SAP", "GR")]
    result = await _search(figi, _live("SAP.DE"))

    assert [r["symbol"] for r in result] == ["SAP.DE"]


async def test_the_users_currency_and_home_exchange_lead():
    figi = [_figi("VGWL", "GY"), _figi("VWRL", "LN"), _figi("VWRL", "NA")]
    charts = {**_live("VGWL.DE", "VWRL.AS"), "VWRL.L": (250, FRESH, "GBp")}

    german = await _search(figi, charts, "EUR", "DE")
    british = await _search(figi, charts, "GBP", "GB")

    assert [r["symbol"] for r in german] == ["VGWL.DE", "VWRL.AS", "VWRL.L"]
    assert [r["symbol"] for r in british] == ["VWRL.L", "VGWL.DE", "VWRL.AS"]


async def test_the_identifier_type_reaches_openfigi():
    async def chart_stats(symbol):
        return None

    with patch.object(openfigi, "_figi_lookup", return_value=[]) as lookup, \
            patch.object(listings, "chart_stats", side_effect=chart_stats):
        await openfigi.find_listings("ID_ISIN", "IE00B4L5Y983")

    lookup.assert_awaited_once_with("ID_ISIN", "IE00B4L5Y983")


# ---------------------------------------------------------------------------
# The HTTP layer: what goes to OpenFIGI and how its answer is read
# ---------------------------------------------------------------------------


def _post_session(payload=None, status=200, raises=None):
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=payload)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    if raises is not None:
        session.post.side_effect = raises
    else:
        session.post.return_value = resp
    return patch("aiohttp.ClientSession", MagicMock(return_value=session)), session


async def test_the_request_names_the_id_type_and_value():
    patcher, session = _post_session([{"data": []}])
    with patcher:
        await openfigi._figi_lookup("ID_WERTPAPIER", "A1JX52")

    args, kwargs = session.post.call_args
    assert args[0] == "https://api.openfigi.com/v3/mapping"
    assert kwargs["json"] == [{"idType": "ID_WERTPAPIER", "idValue": "A1JX52"}]


async def test_the_listings_come_out_of_the_first_job():
    data = [{"ticker": "VGWL", "exchCode": "GR", "name": "VANG"}]
    patcher, _ = _post_session([{"data": data}])
    with patcher:
        assert await openfigi._figi_lookup("ID_ISIN", "IE00B3RBWM25") == data


async def test_an_identifier_openfigi_does_not_know_gives_no_listings():
    """OpenFIGI answers an unknown identifier with a warning and no data key."""
    patcher, _ = _post_session([{"warning": "No identifier found."}])
    with patcher:
        assert await openfigi._figi_lookup("ID_ISIN", "XX0000000002") == []


@pytest.mark.parametrize("status", [429, 500, 503])
async def test_an_http_error_is_a_client_error(status):
    """429 is the rate limit (25 requests a minute without a key)."""
    patcher, _ = _post_session([], status=status)
    with patcher, pytest.raises(aiohttp.ClientError):
        await openfigi._figi_lookup("ID_ISIN", "IE00B3RBWM25")


@pytest.mark.parametrize("payload", [{}, [], None, "nope"])
async def test_an_unexpected_payload_is_a_value_error(payload):
    patcher, _ = _post_session(payload)
    with patcher, pytest.raises(ValueError):
        await openfigi._figi_lookup("ID_ISIN", "IE00B3RBWM25")


async def test_a_network_error_propagates():
    patcher, _ = _post_session(raises=aiohttp.ClientConnectionError("down"))
    with patcher, pytest.raises(aiohttp.ClientError):
        await openfigi._figi_lookup("ID_ISIN", "IE00B3RBWM25")


async def test_job_error_is_not_an_unknown_identifier():
    patcher, _ = _post_session([{"error": "There was an unexpected error when processing the request."}])
    with patcher, pytest.raises(ValueError, match="OpenFIGI mapping failed"):
        await openfigi._figi_lookup("ID_WERTPAPIER", "A1JX52")


async def test_us_listing_uses_yahoos_exchange_after_deduplication():
    figi = [_figi("AAPL", "UA", "APPLE"), _figi("AAPL", "UW", "APPLE")]
    result = await _search(figi, {"AAPL": (250, FRESH, "USD", "NasdaqGS")})
    assert len(result) == 1
    assert result[0]["exchange"] == "NasdaqGS"
