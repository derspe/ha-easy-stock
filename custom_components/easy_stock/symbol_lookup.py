import aiohttp

from .const import YAHOO_CHART_URL_MINI

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


async def lookup_symbol(symbol: str) -> str | None:
    """Ask Yahoo whether a symbol exists, and what it calls it.

    Returns Yahoo's name for it ("Vanguard FTSE All-World UCITS ETF", "" when it has
    none), or None when Yahoo does not know the symbol. Yahoo answers an unknown one
    with a 404 "Not Found", which is told apart from an outage on purpose: only the
    first says the user mistyped. Raises aiohttp.ClientError when Yahoo cannot be
    reached or fails, and ValueError on an answer that makes no sense.
    """
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(
            YAHOO_CHART_URL_MINI.format(symbol=symbol),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 404:
                return None
            if resp.status != 200:
                raise aiohttp.ClientError(f"Yahoo Finance returned HTTP {resp.status}")
            data = await resp.json()

    try:
        result = data["chart"]["result"]
        if not result:
            return None
        meta = result[0]["meta"]
        return " ".join((meta.get("longName") or meta.get("shortName") or "").split())
    except (KeyError, IndexError, TypeError, AttributeError) as err:
        raise ValueError(f"Unexpected Yahoo chart payload: {err}") from err
