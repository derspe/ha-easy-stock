"""Tests for fetching and parsing the Zwitserleven fund overview page."""
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.zwitserleven_fondsen.const import ZWITSERLEVEN_FONDSEN_URL
from custom_components.zwitserleven_fondsen.fondsen_page import (
    FondsenPage,
    FondsenPageError,
    parse_date,
    parse_funds,
    parse_price,
)

from .conftest import FONDSEN_HTML

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parses_every_fund_on_the_real_page():
    funds = parse_funds(FONDSEN_HTML)

    assert len(funds) > 50
    assert {"LTAAF", "LTAOB"} <= funds.keys()


def test_parses_a_fund_row():
    fund = parse_funds(FONDSEN_HTML)["LTAAF"]

    assert fund.name == "ASN Duurzaam Aandelenfonds"
    assert fund.price_date == "2026-10-02"
    assert fund.price == 225.87


def test_decodes_html_entities_in_names():
    names = {f.name for f in parse_funds(FONDSEN_HTML).values()}

    assert "ASN Milieu & Waterfonds" in names


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("€\xa0225,87", 225.87),
        ("€ 24,56", 24.56),
        ("€ 1.225,87", 1225.87),
        ("7", 7.0),
    ],
)
def test_parse_price(text, expected):
    assert parse_price(text) == expected


def test_parse_price_rejects_garbage():
    with pytest.raises(ValueError):
        parse_price("n.v.t.")


def test_parse_date():
    assert parse_date("02-10-2026") == "2026-10-02"


def test_parse_date_rejects_garbage():
    with pytest.raises(ValueError):
        parse_date("vandaag")


def _row(symbol, date="02-10-2026", rate="€ 10,00", with_rate=True):
    rate_cell = f'<td class="fundoverview__rate">{rate}</td>' if with_rate else ""
    return f"""
      <tr class="fundoverview__item">
        <td class="fundoverview__fund"><a>{symbol} fund</a></td>
        <td class="fundoverview__date">{date}</td>
        {rate_cell}
        <td><button id="{symbol}" class="icon-favorite"></button></td>
      </tr>"""


def test_row_with_a_bad_date_is_skipped():
    html = f'<table class="fundoverview">{_row("GOOD")}{_row("BAD", date="n.v.t.")}</table>'
    assert set(parse_funds(html)) == {"GOOD"}


def test_row_with_a_missing_column_is_skipped():
    html = f'<table class="fundoverview">{_row("GOOD")}{_row("BAD", with_rate=False)}</table>'
    assert set(parse_funds(html)) == {"GOOD"}


def test_page_without_the_table_raises():
    with pytest.raises(FondsenPageError):
        parse_funds("<html><body></body></html>")


def test_unparseable_row_is_skipped():
    html = """
    <table class="fundoverview">
      <tr class="fundoverview__item">
        <td class="fundoverview__fund"><a>Good</a></td>
        <td class="fundoverview__date">02-10-2026</td>
        <td class="fundoverview__rate">€ 10,00</td>
        <td><button id="GOOD" class="icon-favorite"></button></td>
      </tr>
      <tr class="fundoverview__item">
        <td class="fundoverview__fund"><a>Bad</a></td>
        <td class="fundoverview__date">02-10-2026</td>
        <td class="fundoverview__rate">-</td>
        <td><button id="BAD" class="icon-favorite"></button></td>
      </tr>
    </table>
    """
    assert set(parse_funds(html)) == {"GOOD"}


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


def _session(text="", status=200, error=None):
    resp = AsyncMock()
    resp.status = status
    resp.text = AsyncMock(return_value=text)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    session = MagicMock()
    if error is not None:
        session.get.side_effect = error
    else:
        session.get.return_value = resp
    return patch(
        "custom_components.zwitserleven_fondsen.fondsen_page.async_get_clientsession",
        return_value=session,
    ), session


async def test_fetches_the_fund_page(hass):
    patcher, session = _session(FONDSEN_HTML)

    with patcher:
        funds = await FondsenPage(hass).async_get_funds()

    assert session.get.call_args[0][0] == ZWITSERLEVEN_FONDSEN_URL
    assert "LTAAF" in funds


async def test_one_request_serves_every_fund(hass):
    """Coordinators polling together share one download."""
    patcher, session = _session(FONDSEN_HTML)
    page = FondsenPage(hass)

    with patcher:
        await page.async_get_funds()
        await page.async_get_funds()

    assert session.get.call_count == 1


async def test_http_error_raises(hass):
    patcher, _ = _session(status=429)

    with patcher, pytest.raises(FondsenPageError, match="HTTP 429"):
        await FondsenPage(hass).async_get_funds()


async def test_network_error_raises(hass):
    patcher, _ = _session(error=aiohttp.ClientError("timeout"))

    with patcher, pytest.raises(FondsenPageError, match="Network error"):
        await FondsenPage(hass).async_get_funds()
