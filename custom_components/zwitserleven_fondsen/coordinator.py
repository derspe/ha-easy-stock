"""One coordinator for the whole integration.

Every fund is on the same Zwitserleven page, so one download updates all
configured funds, however many there are and whenever they were added. The
page is fetched when the funds set up and then every day at
DAILY_UPDATE_HOUR_UTC:00 UTC; a failed daily fetch is retried every
RETRY_INTERVAL until it succeeds.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.event import async_call_later, async_track_utc_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DAILY_UPDATE_HOUR_UTC,
    DATA_COORDINATOR,
    DOMAIN,
    PRICE_DECIMALS,
    RETRY_INTERVAL,
)
from .fondsen_page import FondsenPage, FondsenPageError, get_page

_LOGGER = logging.getLogger(__name__)


class FundHistory:
    """The stored daily prices of one fund, as [["YYYY-MM-DD", price], ...]."""

    def __init__(self, store: Store) -> None:
        self._store = store
        self.days: list = []

    async def async_load(self) -> None:
        stored = await self._store.async_load()
        self.days = stored if isinstance(stored, list) else []

    async def async_record(self, date: str, price: float) -> None:
        """Store the price as the daily value for `date`; older dates are ignored."""
        if self.days:
            last_date, last_price = self.days[-1]
            if date < last_date or (date == last_date and price == last_price):
                return
            if date == last_date:
                self.days[-1] = [date, price]
            else:
                self.days.append([date, price])
        else:
            self.days.append([date, price])
        await self._store.async_save(self.days)

    def previous_price(self, date: str, fallback: float) -> float:
        """Price of the last stored day before `date`, or `fallback` if there is none."""
        for day, price in reversed(self.days):
            if day < date:
                return price
        return fallback


class ZwitserlevenDataCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Fetches the fund page and keeps the data of every configured fund.

    `data` maps each configured fund ID to its sensor data. A fund that is
    missing from the page is left out, which makes its sensor unavailable.
    """

    def __init__(self, hass: HomeAssistant, page: FondsenPage) -> None:
        super().__init__(
            hass,
            _LOGGER,
            # Shared by every config entry, so it belongs to none of them.
            config_entry=None,
            name=DOMAIN,
            # No interval: refreshes follow the daily schedule below.
            update_interval=None,
        )
        self._page = page
        self._funds: dict[str, FundHistory] = {}
        self._missing: set[str] = set()
        self._unsub_daily: Callable[[], None] | None = None
        self._unsub_retry: Callable[[], None] | None = None
        self._unsub_stop: Callable[[], None] | None = None

    async def async_add_fund(self, symbol: str, store: Store) -> None:
        history = FundHistory(store)
        await history.async_load()
        self._funds[symbol] = history
        self._start_schedule()

    def remove_fund(self, symbol: str) -> None:
        self._funds.pop(symbol, None)
        self._missing.discard(symbol)
        if not self._funds:
            self._stop_schedule()

    def _start_schedule(self) -> None:
        if self._unsub_daily is not None:
            return
        self._unsub_daily = async_track_utc_time_change(
            self.hass,
            self._async_scheduled_refresh,
            hour=DAILY_UPDATE_HOUR_UTC,
            minute=0,
            second=0,
        )
        self._unsub_stop = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, self._async_on_stop
        )

    def _stop_schedule(self) -> None:
        self._cancel_retry()
        if self._unsub_daily is not None:
            self._unsub_daily()
            self._unsub_daily = None
        if self._unsub_stop is not None:
            self._unsub_stop()
            self._unsub_stop = None

    def _cancel_retry(self) -> None:
        if self._unsub_retry is not None:
            self._unsub_retry()
            self._unsub_retry = None

    async def _async_on_stop(self, _event: Event) -> None:
        # The listener is removed by firing it; don't unsubscribe it again.
        self._unsub_stop = None
        self._stop_schedule()

    async def _async_scheduled_refresh(self, _now: datetime | None = None) -> None:
        """The daily refresh, also used for the retries after a failed one."""
        # A pending retry is superseded by this refresh; cancelling one that
        # has just fired is a no-op.
        self._cancel_retry()
        await self.async_refresh()
        if not self.last_update_success and self._funds:
            self._unsub_retry = async_call_later(
                self.hass, RETRY_INTERVAL, self._async_scheduled_refresh
            )

    def history(self, symbol: str) -> list | None:
        """Stored daily prices of a configured fund, or None if it is not configured."""
        fund = self._funds.get(symbol)
        return None if fund is None else fund.days

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            quotes = await self._page.async_get_funds()
        except FondsenPageError as err:
            raise UpdateFailed(str(err)) from err

        data: dict[str, dict] = {}
        for symbol, history in list(self._funds.items()):
            quote = quotes.get(symbol)
            if quote is None:
                if symbol not in self._missing:
                    _LOGGER.warning("Fund %s is no longer listed on the Zwitserleven page", symbol)
                    self._missing.add(symbol)
                continue
            if symbol in self._missing:
                _LOGGER.info("Fund %s is listed on the Zwitserleven page again", symbol)
                self._missing.discard(symbol)

            await history.async_record(quote.price_date, quote.price)
            price = quote.price
            previous_close = history.previous_price(quote.price_date, price)
            change = price - previous_close
            change_pct = (change / previous_close * 100) if previous_close else 0
            data[symbol] = {
                "symbol": symbol,
                "long_name": quote.name,
                "price_date": quote.price_date,
                "current_price": round(price, PRICE_DECIMALS),
                "previous_close": round(previous_close, PRICE_DECIMALS),
                "change": round(change, PRICE_DECIMALS),
                "change_pct": round(change_pct, 2),
            }
        return data


def get_coordinator(hass: HomeAssistant) -> ZwitserlevenDataCoordinator:
    """Return the coordinator shared by all config entries, creating it once."""
    coordinator = hass.data.get(DATA_COORDINATOR)
    if coordinator is None:
        coordinator = hass.data[DATA_COORDINATOR] = ZwitserlevenDataCoordinator(
            hass, get_page(hass)
        )
    return coordinator
