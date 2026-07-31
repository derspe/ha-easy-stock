"""Unit tests for the frontend registration module."""
from unittest.mock import patch

from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.setup import async_setup_component

from custom_components.easy_stock.frontend import (
    CARD_URL_BASE,
    DATA_FRONTEND,
    async_register_card,
    async_unregister_card,
)


async def _setup_storage_mode(hass):
    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, "lovelace", {})
    return hass.data[LOVELACE_DATA].resources


def _card_items(resources):
    return [i for i in resources.async_items() if i["url"].startswith(CARD_URL_BASE)]


async def test_creates_resource_in_storage_mode(hass):
    """Storage mode gets exactly one module resource for the card."""
    resources = await _setup_storage_mode(hass)

    await async_register_card(hass)

    await resources.async_get_info()
    items = _card_items(resources)
    assert len(items) == 1
    assert items[0]["type"] == "module"
    assert items[0]["url"].startswith(f"{CARD_URL_BASE}?v=")


async def test_adopts_and_updates_a_stale_entry(hass):
    """An existing entry with an old version is updated, never duplicated."""
    resources = await _setup_storage_mode(hass)
    await resources.async_create_item(
        {"res_type": "module", "url": f"{CARD_URL_BASE}?v=deadbeef"}
    )

    await async_register_card(hass)

    await resources.async_get_info()
    items = _card_items(resources)
    assert len(items) == 1
    assert items[0]["url"] != f"{CARD_URL_BASE}?v=deadbeef"


async def test_second_call_is_a_no_op(hass):
    """Registering twice leaves a single entry with an unchanged URL."""
    resources = await _setup_storage_mode(hass)

    await async_register_card(hass)
    await resources.async_get_info()
    first_url = _card_items(resources)[0]["url"]

    await async_register_card(hass)
    await resources.async_get_info()
    items = _card_items(resources)

    assert len(items) == 1
    assert items[0]["url"] == first_url


async def test_yaml_resource_mode_falls_back_to_extra_js(hass):
    """YAML resource mode cannot be written, so use add_extra_js_url."""
    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(
        hass, "lovelace", {"lovelace": {"mode": "yaml", "resources": []}}
    )

    with patch(
        "custom_components.easy_stock.frontend.add_extra_js_url"
    ) as mock_add:
        await async_register_card(hass)

    assert mock_add.call_count == 1
    assert mock_add.call_args.args[1].startswith(f"{CARD_URL_BASE}?v=")


async def test_missing_lovelace_falls_back_to_extra_js(hass):
    """Without Lovelace data at all, fall back rather than raise."""
    assert await async_setup_component(hass, "http", {})

    with patch(
        "custom_components.easy_stock.frontend.add_extra_js_url"
    ) as mock_add:
        await async_register_card(hass)

    assert mock_add.call_count == 1


async def test_missing_frontend_does_not_raise(hass):
    """A KeyError from add_extra_js_url must not break integration setup."""
    assert await async_setup_component(hass, "http", {})

    with patch(
        "custom_components.easy_stock.frontend.add_extra_js_url",
        side_effect=KeyError("frontend_extra_module_url"),
    ):
        await async_register_card(hass)  # must not raise


async def test_unregister_missing_frontend_does_not_raise(hass):
    """An exception from remove_extra_js_url during unregister must not propagate."""
    assert await async_setup_component(hass, "http", {})

    with patch("custom_components.easy_stock.frontend.add_extra_js_url"):
        await async_register_card(hass)

    with patch(
        "custom_components.easy_stock.frontend.remove_extra_js_url",
        side_effect=KeyError("frontend_extra_module_url"),
    ):
        await async_unregister_card(hass)  # must not raise

    assert DATA_FRONTEND not in hass.data


async def test_unregister_removes_the_resource(hass):
    """Unregistering deletes the entry it created."""
    resources = await _setup_storage_mode(hass)
    await async_register_card(hass)

    await async_unregister_card(hass)

    await resources.async_get_info()
    assert _card_items(resources) == []
    assert DATA_FRONTEND not in hass.data
