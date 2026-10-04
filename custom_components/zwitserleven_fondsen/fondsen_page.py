"""Fetch and parse the Zwitserleven fund overview page.

All funds are published on a single page. The coordinator and the config flow
share one FondsenPage, which keeps the parsed result for a short while so the
fund entries setting up together at startup cause a single download.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DATA_PAGE, ZWITSERLEVEN_FONDSEN_URL

# Long enough to cover the fund entries setting up together at startup.
PAGE_CACHE_SECONDS = 60

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
_TIMEOUT = aiohttp.ClientTimeout(total=15)


class FondsenPageError(Exception):
    """The page could not be fetched or did not contain the fund table."""


@dataclass(frozen=True)
class FundQuote:
    symbol: str
    name: str
    price_date: str  # YYYY-MM-DD
    price: float


def parse_price(text: str) -> float:
    """Parse a Dutch formatted price like '€ 1.225,87' to 1225.87."""
    cleaned = (
        text.replace("€", "")
        .replace("\xa0", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
    )
    try:
        return float(cleaned)
    except ValueError as err:
        raise ValueError(f"Could not parse price: {text!r}") from err


def parse_date(text: str) -> str:
    """Convert DD-MM-YYYY to YYYY-MM-DD."""
    try:
        return datetime.strptime(text.strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError as err:
        raise ValueError(f"Could not parse date: {text!r}") from err


def parse_funds(html: str) -> dict[str, FundQuote]:
    """Return every fund on the page, keyed by its button id (e.g. LTAAF).

    Rows that do not parse are skipped rather than failing the whole page, so
    one odd row cannot take down every fund.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="fundoverview")
    if table is None:
        raise FondsenPageError("Could not find the fund table on the page")

    funds: dict[str, FundQuote] = {}
    for row in table.find_all("tr", class_="fundoverview__item"):
        button = row.find("button", class_="icon-favorite")
        name = row.find("td", class_="fundoverview__fund")
        date = row.find("td", class_="fundoverview__date")
        rate = row.find("td", class_="fundoverview__rate")
        if not (button and button.get("id") and name and date and rate):
            continue
        try:
            quote = FundQuote(
                symbol=button["id"].strip().upper(),
                name=name.get_text(strip=True),
                price_date=parse_date(date.get_text(strip=True)),
                price=parse_price(rate.get_text(strip=True)),
            )
        except ValueError:
            continue
        funds[quote.symbol] = quote
    return funds


class FondsenPage:
    """The fund overview page, shared by all config entries."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._lock = asyncio.Lock()
        self._funds: dict[str, FundQuote] | None = None
        self._fetched_at = 0.0

    async def async_get_funds(self) -> dict[str, FundQuote]:
        async with self._lock:
            if (
                self._funds is not None
                and time.monotonic() - self._fetched_at < PAGE_CACHE_SECONDS
            ):
                return self._funds
            html = await self._async_fetch()
            self._funds = parse_funds(html)
            self._fetched_at = time.monotonic()
            return self._funds

    async def _async_fetch(self) -> str:
        session = async_get_clientsession(self._hass)
        try:
            async with session.get(
                ZWITSERLEVEN_FONDSEN_URL, headers=_HEADERS, timeout=_TIMEOUT
            ) as resp:
                if resp.status != 200:
                    raise FondsenPageError(f"Zwitserleven returned HTTP {resp.status}")
                return await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise FondsenPageError(f"Network error fetching the fund page: {err}") from err


def get_page(hass: HomeAssistant) -> FondsenPage:
    """Return the FondsenPage shared by all config entries, creating it once."""
    page = hass.data.get(DATA_PAGE)
    if page is None:
        page = hass.data[DATA_PAGE] = FondsenPage(hass)
    return page
