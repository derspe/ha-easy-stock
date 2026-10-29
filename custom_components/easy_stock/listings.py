import asyncio
import time
from typing import NamedTuple

import aiohttp

from .const import YAHOO_CHART_URL

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# A listing is only worth offering when it trades and has a history to chart. Yahoo
# answers for plenty of symbols that do neither: the German regional exchanges come
# with a single day of data, and a dead listing keeps its last price from years ago.
MIN_POINTS = 5
MAX_QUOTE_AGE = 14 * 86400

# Yahoo ticker suffix of the home exchange of the countries Home Assistant knows a
# user by. "" is the US, whose symbols carry none.
HOME_SUFFIX = {
    "DE": ".DE",
    "GB": ".L",
    "FR": ".PA",
    "NL": ".AS",
    "IT": ".MI",
    "CH": ".SW",
    "AT": ".VI",
    "ES": ".MC",
    "US": "",
}


def _currency(code: str) -> str:
    """London quotes in pence (GBp / GBX); for matching it is the pound."""
    return "GBP" if code in ("GBp", "GBX") else code


def _suffix(symbol: str) -> str:
    return symbol[symbol.rfind("."):] if "." in symbol else ""


class ChartStats(NamedTuple):
    closes: int
    last_trade: int
    currency: str
    exchange: str = ""


async def chart_stats(symbol: str) -> ChartStats | None:
    """Read chart metadata; only a missing chart is None, outages raise."""
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(
            YAHOO_CHART_URL.format(symbol=symbol),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 404:
                return None
            if resp.status != 200:
                raise aiohttp.ClientError(f"Yahoo chart returned HTTP {resp.status}")
            data = await resp.json()
    try:
        chart = data["chart"]
        if chart.get("error"):
            raise ValueError(f"Yahoo chart error: {chart['error']}")
        if not chart["result"]:
            return None
        result = chart["result"][0]
        closes = [c for c in result["indicators"]["quote"][0].get("close", []) if c is not None]
        meta = result["meta"]
        return ChartStats(
            len(closes), int(meta.get("regularMarketTime") or 0),
            meta.get("currency") or "", meta.get("fullExchangeName") or meta.get("exchangeName") or "",
        )
    except (KeyError, IndexError, TypeError, AttributeError) as err:
        raise ValueError(f"Unexpected Yahoo chart payload: {err}") from err


async def vet_listings(
    candidates: list[dict],
    currency: str = "",
    country: str | None = None,
) -> list[dict]:
    """Keep the listings that trade and carry a history, the user's own first.

    Each kept listing gains a "currency". Listings in the user's currency lead, and
    within those the ones on the home exchange of their country; `currency` and
    `country` are Home Assistant's own settings. A listing whose request failed (Yahoo
    answers bursts with the odd 429) is dropped; only when every request failed is it
    an outage, which raises instead of passing for a "not found" result.
    """
    stats = await asyncio.gather(
        *(chart_stats(c["symbol"]) for c in candidates), return_exceptions=True
    )
    failures = [st for st in stats if isinstance(st, BaseException)]
    if failures and len(failures) == len(stats):
        raise failures[0]
    now = time.time()
    kept = [
        {**c, "currency": st.currency, "exchange": st.exchange or c["exchange"]}
        for c, st in zip(candidates, stats)
        if st is not None and not isinstance(st, BaseException) and st.closes >= MIN_POINTS and now - st.last_trade <= MAX_QUOTE_AGE
    ]

    home = HOME_SUFFIX.get(country or "")
    wanted = _currency(currency)

    def rank(c: dict) -> tuple[bool, bool]:
        return (
            bool(wanted) and _currency(c["currency"]) != wanted,
            home is not None and _suffix(c["symbol"]) != home,
        )

    # sorted() is stable: within a group the order the caller gave stays.
    return sorted(kept, key=rank)
