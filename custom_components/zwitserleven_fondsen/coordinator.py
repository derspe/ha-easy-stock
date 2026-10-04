import logging
from datetime import timedelta

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import PRICE_DECIMALS
from .fondsen_page import FondsenPage, FondsenPageError

_LOGGER = logging.getLogger(__name__)


def previous_price(history: list, date: str, fallback: float) -> float:
    """Price of the last stored day before `date`, or `fallback` if there is none."""
    for day, price in reversed(history):
        if day < date:
            return price
    return fallback


class ZwitserlevenDataCoordinator(DataUpdateCoordinator):
    def __init__(
        self, hass, symbol: str, update_interval: int, store: Store, page: FondsenPage
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"zwitserleven_fonds_{symbol}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.symbol = symbol
        self._store = store
        self._page = page
        # None = not yet loaded from store (populated on first _async_update_data call)
        self._history: list | None = None

    async def _async_update_data(self) -> dict:
        try:
            funds = await self._page.async_get_funds()
        except FondsenPageError as err:
            raise UpdateFailed(str(err)) from err

        quote = funds.get(self.symbol)
        if quote is None:
            raise UpdateFailed(f"Fund {self.symbol} not found on the Zwitserleven page")

        if self._history is None:
            stored = await self._store.async_load()
            self._history = stored if isinstance(stored, list) else []

        await self._async_record(quote.price_date, quote.price)

        price = quote.price
        previous_close = previous_price(self._history, quote.price_date, price)
        change = price - previous_close
        change_pct = (change / previous_close * 100) if previous_close else 0

        return {
            "symbol": self.symbol,
            "long_name": quote.name,
            "price_date": quote.price_date,
            "current_price": round(price, PRICE_DECIMALS),
            "previous_close": round(previous_close, PRICE_DECIMALS),
            "change": round(change, PRICE_DECIMALS),
            "change_pct": round(change_pct, 2),
        }

    async def _async_record(self, date: str, price: float) -> None:
        """Store the price as the daily value for `date`; older dates are ignored."""
        if self._history:
            last_date, last_price = self._history[-1]
            if date < last_date or (date == last_date and price == last_price):
                return
            if date == last_date:
                self._history[-1] = [date, price]
            else:
                self._history.append([date, price])
        else:
            self._history.append([date, price])
        await self._store.async_save(self._history)
