import asyncio

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_SYMBOL,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)
from .symbol_lookup import lookup_symbol
from .isin import isin_checksum_valid, looks_like_isin, search_isin
from .wkn import looks_like_wkn, search_wkn


class EasyStockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._user_input: dict = {}
        self._candidates: list[dict] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EasyStockOptionsFlow(config_entry)

    async def _abort_if_configured(self, symbol: str) -> None:
        await self.async_set_unique_id(f"easy_stock_{symbol}")
        self._abort_if_unique_id_configured()

    async def _create_entry(self, symbol: str, yahoo_name: str = ""):
        await self._abort_if_configured(symbol)

        # No name typed: take Yahoo's, so the entry and its sensor read "Vanguard FTSE
        # All-World UCITS ETF" rather than the ticker. Only new entries get this; the
        # entity id keeps coming from the symbol (see StockSensor).
        name = self._user_input.get(CONF_NAME, "").strip() or yahoo_name

        return self.async_create_entry(
            title=name or symbol,
            data={
                CONF_SYMBOL: symbol,
                CONF_NAME: name,
                CONF_SCAN_INTERVAL: self._user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            },
        )

    async def _create_resolved_entry(self, symbol: str):
        """Create the entry for a listing an ISIN or WKN lookup found and already vetted.

        Only the name is fetched; failing to get it is no reason to stop.
        """
        await self._abort_if_configured(symbol)
        try:
            yahoo_name = await lookup_symbol(symbol)
            if yahoo_name is None:
                return await self.async_step_select_listing(
                    errors={CONF_SYMBOL: "symbol_not_found"}
                )
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            yahoo_name = ""
        return await self._create_entry(symbol, yahoo_name)

    async def async_step_user(self, user_input: dict | None = None):
        errors = {}

        if user_input is not None:
            self._user_input = user_input
            symbol = user_input[CONF_SYMBOL].upper().strip()

            if looks_like_isin(symbol):
                if not isin_checksum_valid(symbol):
                    errors[CONF_SYMBOL] = "invalid_isin"
                else:
                    try:
                        self._candidates = await search_isin(
                            symbol, self.hass.config.currency, self.hass.config.country
                        )
                    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
                        errors["base"] = "cannot_connect"
                    else:
                        if not self._candidates:
                            errors[CONF_SYMBOL] = "isin_not_found"
                        elif len(self._candidates) == 1:
                            return await self._create_resolved_entry(self._candidates[0]["symbol"])
                        else:
                            return await self.async_step_select_listing()
            else:
                # Six plain characters are a WKN -- or a short ticker. Whatever
                # does not resolve is taken as the Yahoo symbol it was typed as.
                self._candidates = []
                wkn_unreachable = False
                if looks_like_wkn(symbol):
                    try:
                        self._candidates = await search_wkn(
                            symbol, self.hass.config.currency, self.hass.config.country
                        )
                    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
                        wkn_unreachable = True
                if len(self._candidates) == 1:
                    return await self._create_resolved_entry(self._candidates[0]["symbol"])
                if len(self._candidates) > 1:
                    return await self.async_step_select_listing()

                # Nothing resolved: it has to be a Yahoo symbol, so ask Yahoo whether
                # it is one. Creating an entry for a typo gave a sensor that never
                # had a value.
                await self._abort_if_configured(symbol)
                try:
                    yahoo_name = await lookup_symbol(symbol)
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
                    errors["base"] = "cannot_connect"
                else:
                    if yahoo_name is None and wkn_unreachable:
                        # The unanswered WKN lookup may be why it did not resolve.
                        errors["base"] = "cannot_connect"
                    elif yahoo_name is None:
                        errors[CONF_SYMBOL] = "symbol_not_found"
                    else:
                        return await self._create_entry(symbol, yahoo_name)

        schema = vol.Schema(
            {
                vol.Required(CONF_SYMBOL): str,
                vol.Optional(CONF_NAME, default=""): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    int, vol.Range(min=60, max=86400)
                ),
            }
        )

        # What was typed before stays in the form after an error, so nobody has to
        # type an ISIN twice.
        schema = self.add_suggested_values_to_schema(schema, self._user_input)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_select_listing(
        self, user_input: dict | None = None, *, errors: dict | None = None
    ):
        if user_input is not None:
            return await self._create_resolved_entry(user_input[CONF_SYMBOL])

        options = {
            c["symbol"]: " · ".join(
                p for p in (c["symbol"], c["exchange"], c.get("currency"), c["name"]) if p
            )
            for c in self._candidates
        }
        # The lookups sort the user's own listing first.
        default = self._candidates[0]["symbol"]

        return self.async_show_form(
            step_id="select_listing",
            errors=errors or {},
            data_schema=vol.Schema({vol.Required(CONF_SYMBOL, default=default): vol.In(options)}),
        )


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

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=current_name): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    int, vol.Range(min=60, max=86400)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
