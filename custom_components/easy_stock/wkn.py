import re

from .openfigi import find_listings

# WKNs are six characters and never use the letters I and O.
_WKN_RE = re.compile(r"^[A-HJ-NP-Z0-9]{6}$")


def looks_like_wkn(value: str) -> bool:
    return bool(_WKN_RE.match(value))


async def search_wkn(wkn: str, currency: str = "", country: str | None = None) -> list[dict]:
    """Resolve a WKN to the Yahoo listings that trade it, the user's own first.

    Yahoo's search does not know WKNs, so this goes through OpenFIGI only.
    Raises aiohttp.ClientError on network trouble and ValueError on a bad payload.
    """
    return await find_listings("ID_WERTPAPIER", wkn, currency, country)
