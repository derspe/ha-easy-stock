import asyncio
import logging
import re

import aiohttp

from .const import YAHOO_SEARCH_URL
from .listings import vet_listings
from .openfigi import find_listings

_LOGGER = logging.getLogger(__name__)

_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def looks_like_isin(value: str) -> bool:
    return bool(_ISIN_RE.match(value))


def isin_checksum_valid(isin: str) -> bool:
    """Luhn check over the ISIN with letters expanded to two digits (A=10 ... Z=35)."""
    digits = "".join(str(int(c, 36)) for c in isin)
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


async def search_isin(isin: str, currency: str = "", country: str | None = None) -> list[dict]:
    """Resolve an ISIN to the Yahoo listings that trade it, the user's own first.

    OpenFIGI lists every exchange a security trades on, so a German user gets the
    XETRA line of an ETF that Yahoo's own search only knows in London. Yahoo's search
    is the fallback for when OpenFIGI is unreachable or does not know the ISIN.
    Raises aiohttp.ClientError on network trouble and ValueError on a bad payload.
    """
    lookup_error = None
    try:
        listings = await find_listings("ID_ISIN", isin, currency, country)
        if listings:
            return listings
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
        lookup_error = err
        _LOGGER.debug("easy_stock: OpenFIGI lookup of %s failed (%s), asking Yahoo", isin, err)

    listings = await _search_yahoo(isin, currency, country)
    if not listings and lookup_error is not None:
        raise lookup_error
    return listings


async def _search_yahoo(isin: str, currency: str, country: str | None) -> list[dict]:
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(
            YAHOO_SEARCH_URL.format(query=isin),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                raise aiohttp.ClientError(f"Yahoo search returned HTTP {resp.status}")
            data = await resp.json()

    try:
        quotes = data.get("quotes") or []
        candidates = [
            {
                "symbol": q["symbol"],
                "exchange": q.get("exchDisp") or q.get("exchange") or "",
                "name": (q.get("shortname") or q.get("longname") or "").strip(),
            }
            for q in quotes
            if q.get("symbol")
        ]
    except (AttributeError, TypeError) as err:
        raise ValueError(f"Unexpected Yahoo search payload: {err}") from err

    return await vet_listings(candidates, currency, country)
