"""Unit tests for the Yahoo symbol lookup the setup form validates a symbol with."""
import aiohttp
import pytest

from custom_components.easy_stock.symbol_lookup import lookup_symbol
from tests.conftest import mock_http


def _payload(**meta):
    return {"chart": {"result": [{"meta": meta}]}}


async def test_returns_the_long_name():
    patcher, session = mock_http(_payload(longName="Vanguard FTSE All-World UCITS ETF", shortName="VANGUARD"))
    with patcher:
        assert await lookup_symbol("VGWL.DE") == "Vanguard FTSE All-World UCITS ETF"

    assert "VGWL.DE" in session.get.call_args.args[0]


async def test_falls_back_to_the_short_name():
    patcher, _ = mock_http(_payload(shortName="SAP SE"))
    with patcher:
        assert await lookup_symbol("SAP.DE") == "SAP SE"


async def test_collapses_whitespace():
    patcher, _ = mock_http(_payload(longName="  SAP   SE \n"))
    with patcher:
        assert await lookup_symbol("SAP.DE") == "SAP SE"


async def test_a_symbol_without_a_name_exists_but_has_none():
    """"" is not None: the symbol is real, Yahoo just has no name for it."""
    patcher, _ = mock_http(_payload(symbol="X"))
    with patcher:
        assert await lookup_symbol("X") == ""


async def test_an_unknown_symbol_is_none():
    """Yahoo answers a symbol it does not know with 404 "Not Found"."""
    patcher, _ = mock_http({"chart": {"result": None, "error": {"code": "Not Found"}}}, status=404)
    with patcher:
        assert await lookup_symbol("A1JX") is None


@pytest.mark.parametrize("payload", [{"chart": {"result": None}}, {"chart": {"result": []}}])
async def test_an_empty_result_is_none(payload):
    patcher, _ = mock_http(payload)
    with patcher:
        assert await lookup_symbol("A1JX") is None


@pytest.mark.parametrize("status", [429, 500, 503])
async def test_an_outage_is_an_error_not_an_unknown_symbol(status):
    """Telling the user their symbol is wrong when Yahoo is rate-limiting would mislead."""
    patcher, _ = mock_http({}, status=status)
    with patcher, pytest.raises(aiohttp.ClientError):
        await lookup_symbol("SAP.DE")


@pytest.mark.parametrize("payload", [{}, [], "nope", {"chart": {"result": [5]}}])
async def test_a_malformed_answer_is_a_value_error(payload):
    patcher, _ = mock_http(payload)
    with patcher, pytest.raises(ValueError):
        await lookup_symbol("SAP.DE")


async def test_a_network_error_propagates():
    patcher, session = mock_http({})
    session.get.side_effect = aiohttp.ClientConnectionError("down")
    with patcher, pytest.raises(aiohttp.ClientError):
        await lookup_symbol("SAP.DE")
