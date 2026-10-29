import aiohttp

from .const import OPENFIGI_URL
from .listings import vet_listings

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# OpenFIGI exchange code -> (Yahoo ticker suffix, label shown in the picker).
# OpenFIGI lists every venue and currency line a security trades on; only the
# exchanges Yahoo has a quote for are mapped, the rest is dropped.
_EXCHANGES = {
    "GY": (".DE", "XETRA"),
    # The German composite. For some securities (the Vanguard FTSE All-World, A1JX52)
    # OpenFIGI carries the XETRA line only under this code and has no GY entry.
    "GR": (".DE", "XETRA"),
    "GF": (".F", "Frankfurt"),
    "GS": (".SG", "Stuttgart"),
    "GD": (".DU", "Düsseldorf"),
    "GH": (".HM", "Hamburg"),
    "GM": (".MU", "München"),
    "GB": (".BE", "Berlin"),
    "LN": (".L", "London"),
    "NA": (".AS", "Amsterdam"),
    "FP": (".PA", "Paris"),
    "IM": (".MI", "Milan"),
    "SW": (".SW", "Swiss"),
    "AV": (".VI", "Vienna"),
    "SM": (".MC", "Madrid"),
    "UN": ("", "NYSE"),
    "UW": ("", "Nasdaq"),
    "UQ": ("", "Nasdaq"),
    "UA": ("", "NYSE American"),
    "UP": ("", "NYSE Arca"),
}


async def _figi_lookup(id_type: str, value: str) -> list[dict]:
    """Every listing OpenFIGI knows for an identifier (ID_ISIN, ID_WERTPAPIER = WKN). Raises aiohttp.ClientError / ValueError."""
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.post(
            OPENFIGI_URL,
            json=[{"idType": id_type, "idValue": value}],
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                raise aiohttp.ClientError(f"OpenFIGI returned HTTP {resp.status}")
            payload = await resp.json()

    try:
        job = payload[0]
        if job.get("error"):
            raise ValueError(f"OpenFIGI mapping failed: {job['error']}")
        return job.get("data") or []
    except (KeyError, IndexError, AttributeError, TypeError) as err:
        raise ValueError(f"Unexpected OpenFIGI payload: {err}") from err


async def find_listings(
    id_type: str, value: str, currency: str = "", country: str | None = None
) -> list[dict]:
    """Resolve a security identifier to the Yahoo listings that trade it.

    Returns [{"symbol", "exchange", "name", "currency"}, ...] with the listings that
    suit `currency` / `country` first; empty when it resolves to nothing Yahoo quotes.
    OpenFIGI gives a ticker and an exchange per listing, not Yahoo's symbol, so the
    symbol is built from the exchange's suffix and then checked: it has to trade
    currently and carry a daily history.
    Raises aiohttp.ClientError on network trouble and ValueError on a bad payload.
    """
    candidates: dict[str, dict] = {}
    for listing in await _figi_lookup(id_type, value):
        mapped = _EXCHANGES.get(listing.get("exchCode"))
        ticker = (listing.get("ticker") or "").strip().upper()
        if mapped is None or not ticker:
            continue
        suffix, label = mapped
        symbol = ticker.replace("/", "-") + suffix
        candidates.setdefault(
            symbol,
            {"symbol": symbol, "exchange": label, "name": (listing.get("name") or "").strip()},
        )

    # The table's order is the tie-break once the user's own listings are first.
    labels = [label for _, label in _EXCHANGES.values()]
    ordered = sorted(candidates.values(), key=lambda c: labels.index(c["exchange"]))
    return await vet_listings(ordered, currency, country)
