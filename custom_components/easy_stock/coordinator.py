import logging
from datetime import datetime, timedelta, timezone

import aiohttp
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import HEADERS, YAHOO_CHART_URL, YAHOO_CHART_URL_MINI, YAHOO_CHART_URL_INTRADAY
from .market_state import derive_market_state, last_trade_date
from .intraday import traded_on
from .precision import price_decimals, round_price

_LOGGER = logging.getLogger(__name__)


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
            async with aiohttp.ClientSession(headers=HEADERS) as session:
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

        # Second request: the hourly series, which is what decides whether the
        # asset traded today. Tolerated to fail -- a flaky request must not make
        # the sensor unavailable, so the older signals stand in for that update.
        intraday_today = None
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get(
                    YAHOO_CHART_URL_INTRADAY.format(symbol=self.symbol),
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        intraday = await resp.json()
                        now_local = dt_util.now()
                        intraday_today = traded_on(
                            intraday["chart"]["result"][0], now_local.date(), now_local.tzinfo
                        )
        except (aiohttp.ClientError, KeyError, IndexError, TypeError, ValueError) as err:
            _LOGGER.debug(
                "easy_stock: %s -- intraday request failed (%s), falling back to the quote",
                self.symbol,
                err,
            )

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
                    fetched.append([date_str, round_price(c)])

            # Update persistent history
            if history_needs_backfill:
                # Initial backfill or migration: 365 days covers crypto (7-day trading week)
                # as well as stocks/ETFs (~252 trading days ≤ 365).
                self._history = fetched[-365:]
                await self._store.async_save(self._history)
            elif fetched:
                last_fetched_date, last_fetched_price = fetched[-1]
                last_stored_date, last_stored_price = self._history[-1]
                if last_fetched_date > last_stored_date:
                    self._history.append([last_fetched_date, last_fetched_price])
                    await self._store.async_save(self._history)
                elif (
                    last_fetched_date == last_stored_date
                    and last_fetched_price != last_stored_price
                ):
                    # Yahoo keeps rewriting the running day's candle until the
                    # close. Appending only on a new date froze the entry at the
                    # first intraday sample of that day, so the stored series was
                    # a set of arbitrary intraday prices rather than closes.
                    self._history[-1] = [last_fetched_date, last_fetched_price]
                    await self._store.async_save(self._history)

            # Price logic — same as before, based on fetched (recent) data
            # Home Assistant's own timezone, not UTC. The card cuts its 1T series
            # at local midnight, so a UTC "today" made the hours between local and
            # UTC midnight belong to the previous session: east of Greenwich the
            # first hours of a Saturday still counted as Friday, and Yahoo's
            # post-close revisions were written into the weekend chart (#17).
            today_str = dt_util.now().strftime("%Y-%m-%d")
            meta_price = meta.get("regularMarketPrice") or 0

            # traded_today: the asset produced a price today, so an intraday view
            # has something to show. Stays true once the exchange has shut.
            # "Did it trade today" is answered by the intraday bars when we have
            # them -- see ./intraday for why the quote cannot be trusted for that.
            # The older signals stay as fallbacks for when that request fails.
            last_trade_on = last_trade_date(meta, dt_util.now().tzinfo)

            traded_today = False
            if len(fetched) >= 2:
                last_date, last_price = fetched[-1]
                prev_price = fetched[-2][1]

                if intraday_today is not None:
                    session_today = intraday_today
                elif last_date == today_str:
                    session_today = True
                elif last_trade_on is not None:
                    session_today = last_trade_on == today_str
                else:
                    session_today = bool(meta_price) and (
                        abs(meta_price - last_price) / last_price > 0.0001
                    )

                if session_today and last_date == today_str:
                    current_price = meta_price or last_price
                    previous_close = prev_price
                    traded_today = True
                elif session_today:
                    # A session is running that Yahoo has no candle for yet.
                    current_price = meta_price
                    previous_close = last_price
                    traded_today = True
                else:
                    # Nothing traded today: keep the last price anyone paid,
                    # and measure the change against the session before it.
                    current_price = meta_price or last_price
                    previous_close = prev_price
                    traded_today = False
            else:
                current_price = meta_price or (fetched[-1][1] if fetched else 0)
                previous_close = meta.get("previousClose") or meta.get("chartPreviousClose") or 0
                if intraday_today is not None:
                    traded_today = intraday_today
                elif last_trade_on is not None:
                    traded_today = last_trade_on == today_str
                else:
                    traded_today = bool(meta_price)

            # price_is_live: the exchange is in session right now, so the price
            # still moves. Derived from currentTradingPeriod because a candle
            # dated today keeps its date for hours after the close — which used
            # to report Tokyo as live all through the European afternoon. Only
            # when Yahoo ships no trading windows at all does the date-based
            # heuristic stand in for it.
            state = derive_market_state(meta, traded_today=intraday_today)
            price_is_live = traded_today if state is None else state == "REGULAR"

            change = current_price - previous_close
            change_pct = (change / previous_close * 100) if previous_close else 0

            # One decimal place for all three, taken from the price they describe,
            # so the change stays exactly current_price - previous_close.
            decimals = price_decimals(current_price)

            return {
                "symbol": self.symbol,
                "long_name": meta.get("longName") or meta.get("shortName") or self.symbol,
                "currency": meta.get("currency", ""),
                "market_state": state or "CLOSED",
                "current_price": round(current_price, decimals),
                "previous_close": round(previous_close, decimals),
                "change": round(change, decimals),
                "change_pct": round(change_pct, 2),
                "price_is_live": price_is_live,
                "traded_today": traded_today,
                # NOTE: "history" intentionally omitted — served via /api/easy_stock/history
            }
        except (KeyError, IndexError, TypeError) as err:
            raise UpdateFailed(
                f"Error parsing Yahoo Finance response for {self.symbol}: {err}"
            ) from err
