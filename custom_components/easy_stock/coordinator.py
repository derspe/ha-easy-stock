import logging
from datetime import datetime, timedelta, timezone

import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import YAHOO_CHART_URL

_LOGGER = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class StockDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, symbol: str, update_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"easy_stock_{symbol}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.symbol = symbol

    async def _async_update_data(self) -> dict:
        url = YAHOO_CHART_URL.format(symbol=self.symbol)
        try:
            async with aiohttp.ClientSession(headers=_HEADERS) as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(
                            f"Yahoo Finance returned HTTP {resp.status} for {self.symbol}"
                        )
                    data = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching {self.symbol}: {err}") from err

        try:
            result = data["chart"]["result"][0]
            meta = result["meta"]
            timestamps = result.get("timestamp", [])
            closes = result["indicators"]["quote"][0].get("close", [])

            # Build [[date_str, price], ...] — only complete pairs
            history: list[list] = []
            for ts, c in zip(timestamps, closes):
                if ts is not None and c is not None:
                    date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                    history.append([date_str, round(c, 4)])

            history = history[-252:]  # max 1 year of trading days

            # meta.previousClose can be wrong for some symbols (adjusted prices, splits, etc.).
            # Use history entries as the authoritative source for previous_close.
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            meta_price = meta.get("regularMarketPrice") or 0

            price_is_live = False
            if len(history) >= 2:
                last_date, last_price = history[-1]
                prev_price = history[-2][1]

                if last_date == today_str:
                    # Today's session close is already in history → completed session.
                    current_price = meta_price or last_price
                    previous_close = prev_price
                    price_is_live = True
                else:
                    # Today not yet in history → either market is open or it's a non-trading day.
                    # Distinguish by comparing meta_price against the last historical close:
                    # if they differ by > 0.01 % the market is in session (live price ≠ yesterday).
                    if meta_price and abs(meta_price - last_price) / last_price > 0.0001:
                        # Market open: live price vs. previous (last history close = yesterday)
                        current_price = meta_price
                        previous_close = last_price
                        price_is_live = True
                    else:
                        # Weekend / holiday: show last completed session's change
                        current_price = last_price
                        previous_close = prev_price
                        price_is_live = False
            else:
                current_price = meta_price or (history[-1][1] if history else 0)
                previous_close = meta.get("previousClose") or meta.get("chartPreviousClose") or 0
                price_is_live = bool(meta_price)

            change = current_price - previous_close
            change_pct = (change / previous_close * 100) if previous_close else 0

            return {
                "symbol": self.symbol,
                "long_name": meta.get("longName") or meta.get("shortName") or self.symbol,
                "currency": meta.get("currency", ""),
                "market_state": meta.get("marketState", "CLOSED"),
                "current_price": round(current_price, 4),
                "previous_close": round(previous_close, 4),
                "change": round(change, 4),
                "change_pct": round(change_pct, 2),
                "history": history,
                "price_is_live": price_is_live,
            }
        except (KeyError, IndexError, TypeError) as err:
            raise UpdateFailed(
                f"Error parsing Yahoo Finance response for {self.symbol}: {err}"
            ) from err
