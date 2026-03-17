import hashlib
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, CONF_SYMBOL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import StockDataCoordinator

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


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register static path, Lovelace resource, and history REST endpoint once per domain."""
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            f"/{DOMAIN}",
            str(Path(__file__).parent / "www"),
            cache_headers=False,
        )
    ])
    js_path = Path(__file__).parent / "www" / "easy-stock-card.js"
    file_hash = hashlib.md5(js_path.read_bytes()).hexdigest()[:8]
    add_extra_js_url(hass, f"/{DOMAIN}/easy-stock-card.js?v={file_hash}")
    hass.data.setdefault(DOMAIN, {})
    hass.http.register_view(EasyStockHistoryView())
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

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
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
