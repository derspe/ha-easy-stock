from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_SYMBOL, CONF_NAME, CONF_PURCHASE_PRICE, CONF_QUANTITY
from .coordinator import StockDataCoordinator
from .portfolio import position_attributes


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: StockDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StockSensor(coordinator, entry)])


class StockSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator: StockDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"easy_stock_{entry.data[CONF_SYMBOL]}"
        name = entry.options.get(CONF_NAME) or entry.data.get(CONF_NAME) or entry.title or entry.data[CONF_SYMBOL]
        self._attr_name = name.strip()

    def _option(self, key, default=None):
        """Read a setting, letting the options flow override the initial value.

        Options only hold what the user has saved through the options dialog,
        so an entry that was created before a setting existed has it in
        ``data`` alone -- or nowhere at all.
        """
        return self._entry.options.get(key, self._entry.data.get(key, default))

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data["current_price"] if self.coordinator.data else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.coordinator.data["currency"] if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data
        return {
            "symbol": d["symbol"],
            "long_name": d["long_name"],
            "currency": d["currency"],
            "market_state": d["market_state"],
            "change": d["change"],
            "change_pct": d["change_pct"],
            "previous_close": d["previous_close"],
            "price_is_live": d["price_is_live"],
            "traded_today": d["traded_today"],
            # Static, user-entered figures. Empty unless a purchase price is
            # configured, so sensors without a position stay untouched.
            **position_attributes(
                d["current_price"],
                self._option(CONF_PURCHASE_PRICE),
                self._option(CONF_QUANTITY),
            ),
        }
