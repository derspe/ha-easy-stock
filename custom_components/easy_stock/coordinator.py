import logging
from datetime import datetime, timedelta, timezone

import aiohttp
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import YAHOO_CHART_URL, YAHOO_CHART_URL_MINI

_LOGGER = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class StockDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, symbol: str, update_interval: int, store: Store) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"easy_stock_{symbol}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.symbol = symbol
        self._store = store
        # None = not yet loaded from store (populated on first _async_update_data call)
        self._history: list | None = None

    async def _async_update_data(self) -> dict:
        # Load persistent history on first call
        if self._history is None:
            stored = await self._store.async_load()
            self._history = stored if isinstance(stored, list) else []

        # Migration: old versions capped history at 252 entries (stock trading days), which
        # silently truncated crypto data to ~8 months (crypto trades 7 days/week = 365/year).
        # Detect truncated history: ≥250 entries stored but oldest entry is newer than 355 days
        # ago. Stocks/ETFs are unaffected (their oldest entry is always ~361–365 days old).
        cutoff_355 = (datetime.now(timezone.utc) - timedelta(days=355)).strftime("%Y-%m-%d")
        history_needs_backfill = not self._history or (
            len(self._history) >= 250 and self._history[0][0] > cutoff_355
        )
        if history_needs_backfill and self._history:
            _LOGGER.info(
                "easy_stock: %s — history starts %s (<355 days), triggering full re-fetch",
                self.symbol,
                self._history[0][0],
            )

        # Choose URL: full 1y backfill when history is empty or truncated, mini 5d otherwise
        url = (
            YAHOO_CHART_URL.format(symbol=self.symbol)
            if history_needs_backfill
            else YAHOO_CHART_URL_MINI.format(symbol=self.symbol)
        )

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

            # Parse fetched closes into [[date_str, price], ...]
            fetched: list[list] = []
            for ts, c in zip(timestamps, closes):
                if ts is not None and c is not None:
                    date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                    fetched.append([date_str, round(c, 4)])

            # Update persistent history
            if history_needs_backfill:
                # Initial backfill or migration: 365 days covers crypto (7-day trading week)
                # as well as stocks/ETFs (~252 trading days ≤ 365).
                self._history = fetched[-365:]
                await self._store.async_save(self._history)
            elif fetched:
                last_fetched_date = fetched[-1][0]
                last_stored_date = self._history[-1][0]
                if last_fetched_date > last_stored_date:
                    self._history.append([last_fetched_date, fetched[-1][1]])
                    await self._store.async_save(self._history)

            # Price logic — same as before, based on fetched (recent) data
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            meta_price = meta.get("regularMarketPrice") or 0

            price_is_live = False
            if len(fetched) >= 2:
                last_date, last_price = fetched[-1]
                prev_price = fetched[-2][1]

                if last_date == today_str:
                    current_price = meta_price or last_price
                    previous_close = prev_price
                    price_is_live = True
                else:
                    if meta_price and abs(meta_price - last_price) / last_price > 0.0001:
                        current_price = meta_price
                        previous_close = last_price
                        price_is_live = True
                    else:
                        current_price = last_price
                        previous_close = prev_price
                        price_is_live = False
            else:
                current_price = meta_price or (fetched[-1][1] if fetched else 0)
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
                "price_is_live": price_is_live,
                # NOTE: "history" intentionally omitted — served via /api/easy_stock/history
            }
        except (KeyError, IndexError, TypeError) as err:
            raise UpdateFailed(
                f"Error parsing Yahoo Finance response for {self.symbol}: {err}"
            ) from err
