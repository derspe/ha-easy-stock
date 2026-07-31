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


async def test_duplicate_entries_are_healed_to_one(hass):
    """Two pre-existing matching entries are healed down to a single, current one."""
    resources = await _setup_storage_mode(hass)
    await resources.async_create_item(
        {"res_type": "module", "url": f"{CARD_URL_BASE}?v=aaaaaaaa"}
    )
    await resources.async_create_item(
        {"res_type": "module", "url": f"{CARD_URL_BASE}?v=bbbbbbbb"}
    )

    await async_register_card(hass)

    await resources.async_get_info()
    items = _card_items(resources)
    assert len(items) == 1
    assert items[0]["url"] == hass.data[DATA_FRONTEND]["url"]
    assert items[0]["url"] not in (
        f"{CARD_URL_BASE}?v=aaaaaaaa",
        f"{CARD_URL_BASE}?v=bbbbbbbb",
    )


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


async def test_unregister_when_already_deleted_does_not_raise(hass):
    """If the resource was already removed (e.g. by the user), unregister must not raise."""
    resources = await _setup_storage_mode(hass)
    await async_register_card(hass)

    resource_id = hass.data[DATA_FRONTEND]["resource_id"]
    await resources.async_delete_item(resource_id)

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


async def test_removing_one_of_several_keeps_the_resource(hass):
    """The card must survive as long as any entry remains.

    Home Assistant deletes the entry from the registry *before* it calls
    async_remove_entry (`del self._entries[...]` then `await
    entry.async_remove(...)` in ConfigEntries._async_remove), so the entry
    being removed is already absent and only the survivors are visible here.
    The removed entry is therefore deliberately never added to hass.
    """
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.easy_stock import async_remove_entry
    from custom_components.easy_stock.const import DOMAIN as EASY_STOCK

    resources = await _setup_storage_mode(hass)
    await async_register_card(hass)

    remaining = MockConfigEntry(domain=EASY_STOCK, data={"symbol": "AAPL"})
    remaining.add_to_hass(hass)
    removed = MockConfigEntry(domain=EASY_STOCK, data={"symbol": "MSFT"})

    await async_remove_entry(hass, removed)

    await resources.async_get_info()
    assert len(_card_items(resources)) == 1


async def test_removing_the_last_entry_drops_the_resource(hass):
    """With no entries left in the registry, the resource is deleted."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.easy_stock import async_remove_entry
    from custom_components.easy_stock.const import DOMAIN as EASY_STOCK

    resources = await _setup_storage_mode(hass)
    await async_register_card(hass)

    removed = MockConfigEntry(domain=EASY_STOCK, data={"symbol": "AAPL"})

    await async_remove_entry(hass, removed)

    await resources.async_get_info()
    assert _card_items(resources) == []
