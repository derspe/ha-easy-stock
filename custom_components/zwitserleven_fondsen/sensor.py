from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_SYMBOL, CONF_NAME
from .coordinator import ZwitserleverDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ZwitserleverDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZwitserleverSensor(coordinator, entry)])


class ZwitserleverSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator: ZwitserleverDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"zwitserleven_fondsen_{entry.data[CONF_SYMBOL]}"
        name = entry.options.get(CONF_NAME) or entry.data.get(CONF_NAME) or entry.title or entry.data[CONF_SYMBOL]
        self._attr_name = name.strip()

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data["current_price"] if self.coordinator.data else None

    @property
    def native_unit_of_measurement(self) -> str:
        return "EUR"

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data
        return {
            "symbol": d["symbol"],
            "long_name": d["long_name"],
            "market_state": d["market_state"],
            "change": d["change"],
            "change_pct": d["change_pct"],
            "previous_close": d["previous_close"],
            "price_is_live": d["price_is_live"],
            "traded_today": d["traded_today"],
        }
