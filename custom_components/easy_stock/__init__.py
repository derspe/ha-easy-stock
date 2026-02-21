from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig

from .const import DOMAIN, CONF_SYMBOL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import StockDataCoordinator

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register static path and Lovelace resource once per domain load."""
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            f"/{DOMAIN}",
            str(Path(__file__).parent / "www"),
            cache_headers=False,
        )
    ])
    add_extra_js_url(hass, f"/{DOMAIN}/easy-stock-card.js")
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    coordinator = StockDataCoordinator(
        hass,
        symbol=entry.data[CONF_SYMBOL],
        update_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
