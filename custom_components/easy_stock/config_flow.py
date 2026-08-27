import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_SYMBOL,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_PURCHASE_PRICE,
    CONF_QUANTITY,
    DEFAULT_SCAN_INTERVAL,
)

# 0 is the "not set" value for both position fields. voluptuous has no way to
# leave an optional number blank in the UI form, so the flow needs a value that
# means "no position configured"; a purchase price of zero cannot occur for a
# real holding, which makes it a safe sentinel.
POSITION_UNSET = 0.0

_POSITION_NUMBER = vol.All(vol.Coerce(float), vol.Range(min=0))


class EasyStockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EasyStockOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict | None = None):
        errors = {}

        if user_input is not None:
            symbol = user_input[CONF_SYMBOL].upper().strip()
            await self.async_set_unique_id(f"easy_stock_{symbol}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get(CONF_NAME) or symbol,
                data={
                    CONF_SYMBOL: symbol,
                    CONF_NAME: user_input.get(CONF_NAME, ""),
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    CONF_PURCHASE_PRICE: user_input.get(CONF_PURCHASE_PRICE, POSITION_UNSET),
                    CONF_QUANTITY: user_input.get(CONF_QUANTITY, POSITION_UNSET),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_SYMBOL): str,
                vol.Optional(CONF_NAME, default=""): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    int, vol.Range(min=60, max=86400)
                ),
                vol.Optional(CONF_PURCHASE_PRICE, default=POSITION_UNSET): _POSITION_NUMBER,
                vol.Optional(CONF_QUANTITY, default=POSITION_UNSET): _POSITION_NUMBER,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class EasyStockOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_name = self._config_entry.options.get(
            CONF_NAME, self._config_entry.data.get(CONF_NAME, "")
        )
        current_interval = self._config_entry.options.get(
            CONF_SCAN_INTERVAL, self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        current_purchase_price = self._config_entry.options.get(
            CONF_PURCHASE_PRICE,
            self._config_entry.data.get(CONF_PURCHASE_PRICE, POSITION_UNSET),
        )
        current_quantity = self._config_entry.options.get(
            CONF_QUANTITY, self._config_entry.data.get(CONF_QUANTITY, POSITION_UNSET)
        )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=current_name): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    int, vol.Range(min=60, max=86400)
                ),
                vol.Optional(
                    CONF_PURCHASE_PRICE, default=current_purchase_price
                ): _POSITION_NUMBER,
                vol.Optional(CONF_QUANTITY, default=current_quantity): _POSITION_NUMBER,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
