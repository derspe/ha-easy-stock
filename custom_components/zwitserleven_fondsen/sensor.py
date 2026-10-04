from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_SYMBOL, CONF_NAME
from .coordinator import ZwitserlevenDataCoordinator

if TYPE_CHECKING:
    from . import ZwitserlevenConfigEntry

# Every update comes from the coordinator, so entities never poll on their own.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZwitserlevenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ZwitserlevenSensor(entry.runtime_data, entry)])


class ZwitserlevenSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line"
    _attr_native_unit_of_measurement = "EUR"
    # The fund is the device and the price its only sensor, so the sensor
    # takes the device's name.
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self, coordinator: ZwitserlevenDataCoordinator, entry: ZwitserlevenConfigEntry
    ) -> None:
        super().__init__(coordinator)
        symbol = self._symbol = entry.data[CONF_SYMBOL]
        self._attr_unique_id = f"zwitserleven_fondsen_{symbol}"
        name = (
            entry.options.get(CONF_NAME)
            or entry.data.get(CONF_NAME)
            or entry.title
            or symbol
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, symbol)},
            name=name.strip(),
            manufacturer="Zwitserleven",
            model=symbol,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _fund(self) -> dict | None:
        return (self.coordinator.data or {}).get(self._symbol)

    @property
    def available(self) -> bool:
        return super().available and self._fund is not None

    @property
    def native_value(self) -> float | None:
        return self._fund["current_price"] if self._fund else None

    @property
    def extra_state_attributes(self) -> dict:
        d = self._fund
        if not d:
            return {}
        return {
            "symbol": d["symbol"],
            "long_name": d["long_name"],
            "price_date": d["price_date"],
            "change": d["change"],
            "change_pct": d["change_pct"],
            "previous_close": d["previous_close"],
        }
