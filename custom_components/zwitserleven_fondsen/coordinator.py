import logging
import re
from datetime import datetime, timedelta, timezone

import aiohttp
from bs4 import BeautifulSoup
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import ZWITSERLEVEN_FONDSEN_URL
from .precision import price_decimals

_LOGGER = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class ZwitserleverDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, symbol: str, update_interval: int, store: Store) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"zwitserleven_fonds_{symbol}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.symbol = symbol
        self._store = store
        # None = not yet loaded from store (populated on first _async_update_data call)
        self._history: list | None = None

    def _parse_price(self, price_str: str) -> float:
        """Parse price string like '€ 225,87' to float."""
        # Remove € symbol and whitespace, replace comma with dot
        match = re.search(r"[\d,]+\.?\d*", price_str.replace("€", "").replace(".", "").replace(",", "."))
        if match:
            return float(match.group())
        raise ValueError(f"Could not parse price: {price_str}")

    def _parse_date(self, date_str: str) -> str:
        """Convert DD-MM-YYYY to YYYY-MM-DD."""
        try:
            dt = datetime.strptime(date_str.strip(), "%d-%m-%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Could not parse date: {date_str}") from e

    async def _async_update_data(self) -> dict:
        """Scrape Zwitserleven fondsen page to get fund data."""
        try:
            async with aiohttp.ClientSession(headers=_HEADERS) as session:
                async with session.get(
                    ZWITSERLEVEN_FONDSEN_URL, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(
                            f"Zwitserleven returned HTTP {resp.status} for {self.symbol}"
                        )
                    html_content = await resp.text()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching fondsen page: {err}") from err

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            table = soup.find("table", class_="fundoverview")
            if not table:
                raise UpdateFailed("Could not find fondsen table on page")

            # Find the fund row matching self.symbol
            fund_row = None
            for tr in table.find_all("tr", class_="fundoverview__item"):
                link = tr.find("a", class_=None)
                if link:
                    fund_name = link.get_text(strip=True)
                    button_id = tr.find("button", class_="icon-favorite")
                    if button_id and button_id.get("id") == self.symbol:
                        fund_row = tr
                        break

            if not fund_row:
                raise UpdateFailed(f"Fund {self.symbol} not found in Zwitserleven fondsen")

            # Extract data from row
            tds = fund_row.find_all("td")
            if len(tds) < 3:
                raise UpdateFailed(f"Invalid row structure for fund {self.symbol}")

            long_name = tds[0].get_text(strip=True)
            date_str = tds[1].get_text(strip=True)
            price_str = tds[2].get_text(strip=True)

            # Parse values
            today_str = self._parse_date(date_str)
            current_price = self._parse_price(price_str)

            # Load history
            if self._history is None:
                stored = await self._store.async_load()
                self._history = stored if isinstance(stored, list) else []

            # Update history
            if self._history:
                last_date, last_price = self._history[-1]
                if today_str > last_date:
                    self._history.append([today_str, current_price])
                    await self._store.async_save(self._history)
                elif today_str == last_date and last_price != current_price:
                    self._history[-1] = [today_str, current_price]
                    await self._store.async_save(self._history)
                previous_close = last_price
            else:
                self._history = [[today_str, current_price]]
                await self._store.async_save(self._history)
                previous_close = current_price

            change = current_price - previous_close
            change_pct = (change / previous_close * 100) if previous_close else 0
            decimals = price_decimals(current_price)

            return {
                "symbol": self.symbol,
                "long_name": long_name,
                "market_state": "CLOSED",
                "current_price": round(current_price, decimals),
                "previous_close": round(previous_close, decimals),
                "change": round(change, decimals),
                "change_pct": round(change_pct, 2),
                "price_is_live": False,
                "traded_today": True,
            }
        except (ValueError, AttributeError, IndexError) as err:
            raise UpdateFailed(f"Error parsing Zwitserleven page for {self.symbol}: {err}") from err
