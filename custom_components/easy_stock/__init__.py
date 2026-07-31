import logging

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, CONF_SYMBOL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import StockDataCoordinator
from .frontend import (
    CARD_URL_BASE,
    DATA_FRONTEND,
    async_register_card,
    async_unregister_card,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


class EasyStockHistoryView(HomeAssistantView):
    """REST endpoint: GET /api/easy_stock/history?symbol=AAPL"""

    url = "/api/easy_stock/history"
    name = "api:easy_stock:history"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]
        symbol = request.query.get("symbol", "").upper().strip()
        if not symbol:
            return self.json_message("symbol parameter required", status_code=400)

        for coordinator in hass.data.get(DOMAIN, {}).values():
            if hasattr(coordinator, "symbol") and coordinator.symbol == symbol:
                return self.json({"symbol": symbol, "history": coordinator._history or []})

        return self.json_message(f"No sensor for symbol {symbol}", status_code=404)


async def _async_register_card_safely(hass: HomeAssistant) -> None:
    """Register the card without ever letting a card problem break setup.

    An exception raised out of a component's async_setup makes
    _async_setup_component log it and return False. The domain then never
    enters hass.config.components and *every* config entry fails, so a
    frontend detail would cost the user all of their sensors. Card
    registration reads and validates the Lovelace resource store, writes to
    it, and hashes a file that a truncated HACS download can leave missing --
    plenty of ways to raise for something the sensors do not depend on.
    """
    try:
        await async_register_card(hass)
    except Exception:  # noqa: BLE001 - deliberately broad, see docstring
        _LOGGER.exception(
            "Easy Stock could not register its Lovelace card. Your sensors are "
            "unaffected and keep updating normally; only the custom card may "
            "be missing from dashboards. As a workaround, add %s as a "
            "dashboard resource of type 'module' under Settings > Dashboards > "
            "Resources",
            CARD_URL_BASE,
        )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the card, the shared data store and the history endpoint."""
    await _async_register_card_safely(hass)
    hass.data.setdefault(DOMAIN, {})
    hass.http.register_view(EasyStockHistoryView())
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # Removing the last config entry unregisters the card but does not unload
    # the component: ConfigEntries._async_remove never touches
    # hass.config.components, so adding an entry back afterwards takes
    # ConfigEntries.async_setup's `entry.domain in components` branch and only
    # runs entry.async_setup. The module-level async_setup above never runs
    # again, so without this the card would stay gone until a restart.
    # The guard matters: hass.http.async_register_static_paths appends to the
    # aiohttp route table on every call, so an unconditional call here would
    # add litter for every entry.
    if DATA_FRONTEND not in hass.data:
        await _async_register_card_safely(hass)

    symbol = entry.data[CONF_SYMBOL]
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    store = Store(hass, version=1, key=f"easy_stock.{symbol.lower()}.history")
    coordinator = StockDataCoordinator(
        hass,
        symbol=symbol,
        update_interval=scan_interval,
        store=store,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop the card registration once the last entry is gone."""
    if hass.config_entries.async_entries(DOMAIN):
        return
    await async_unregister_card(hass)
