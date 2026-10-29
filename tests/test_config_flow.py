"""Unit tests for EasyStockConfigFlow and EasyStockOptionsFlow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.easy_stock.const import (
    DOMAIN,
    CONF_SYMBOL,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)


# Patch out the actual HA setup so no coordinator/network calls are made
_SETUP_PATCHES = (
    patch("custom_components.easy_stock.async_setup", return_value=True),
    patch("custom_components.easy_stock.async_setup_entry", return_value=True),
)


@pytest.fixture(autouse=True)
def yahoo_lookup():
    """The flow asks Yahoo whether a symbol exists (and what it is called); no test may reach the network."""
    with patch("custom_components.easy_stock.config_flow.lookup_symbol", return_value="") as fetch:
        yield fetch


async def _init_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


# ---------------------------------------------------------------------------
# Config flow
# ---------------------------------------------------------------------------


async def test_user_step_shows_form(hass):
    """Initial step returns a form."""
    result = await _init_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_config_flow_creates_entry(hass):
    """Submitting valid data creates a config entry."""
    result = await _init_flow(hass)

    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SYMBOL: "AAPL", CONF_NAME: "Apple", CONF_SCAN_INTERVAL: 900},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SYMBOL] == "AAPL"
    assert result["data"][CONF_NAME] == "Apple"
    assert result["data"][CONF_SCAN_INTERVAL] == 900


async def test_symbol_normalized_to_uppercase(hass):
    """Lowercase ticker input is stored as uppercase."""
    result = await _init_flow(hass)

    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SYMBOL: "aapl", CONF_NAME: "", CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
        )

    assert result["data"][CONF_SYMBOL] == "AAPL"


async def test_duplicate_symbol_aborts(hass):
    """Configuring the same symbol twice triggers an abort."""
    for _ in range(2):
        result = await _init_flow(hass)
        with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_SYMBOL: "TSLA", CONF_NAME: "", CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
            )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# ISIN lookup
# ---------------------------------------------------------------------------

SAP_ISIN = "DE0007164600"
IWDA_ISIN = "IE00B4L5Y983"


def _search_patch(result=None, raises=None):
    if raises is not None:
        return patch("custom_components.easy_stock.config_flow.search_isin", side_effect=raises)
    return patch("custom_components.easy_stock.config_flow.search_isin", return_value=result)


def _listing(symbol, exchange="", name=""):
    return {"symbol": symbol, "exchange": exchange, "name": name}


async def _submit(hass, symbol, **kw):
    result = await _init_flow(hass)
    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SYMBOL: symbol, CONF_NAME: "", CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
    )


async def test_isin_single_listing_creates_entry(hass):
    with _search_patch([_listing("AAPL", "NASDAQ")]) as search, \
            _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "US0378331005")

    search.assert_awaited_once()
    assert search.await_args.args[0] == "US0378331005"
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SYMBOL] == "AAPL"


async def test_isin_lowercase_is_normalised(hass):
    with _search_patch([_listing("SAP.DE", "XETRA")]) as search, \
            _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, " de0007164600 ")

    search.assert_awaited_once()
    assert search.await_args.args[0] == SAP_ISIN
    assert result["data"][CONF_SYMBOL] == "SAP.DE"


async def test_isin_lookup_is_given_the_home_assistant_currency_and_country(hass):
    hass.config.currency = "GBP"
    hass.config.country = "GB"
    with _search_patch([_listing("AAPL", "NASDAQ")]) as search, \
            _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        await _submit(hass, "US0378331005")

    assert search.await_args.args[1:] == ("GBP", "GB")


async def test_isin_multiple_listings_shows_selection_preselecting_the_first(hass):
    # The lookup sorts the user's own listing first; the form preselects it.
    listings = [_listing("EUNL.DE", "XETRA"), _listing("IWDA.L", "London")]
    with _search_patch(listings), _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, IWDA_ISIN)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "select_listing"
        key = next(k for k in result["data_schema"].schema if k == CONF_SYMBOL)
        assert key.default() == "EUNL.DE"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_SYMBOL: "IWDA.L"}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SYMBOL] == "IWDA.L"
    assert result["data"][CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL


async def test_isin_selection_keeps_name_and_interval(hass):
    listings = [_listing("IWDA.L", "London"), _listing("IWDA.AS", "Amsterdam")]
    with _search_patch(listings), _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _init_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SYMBOL: IWDA_ISIN, CONF_NAME: "World", CONF_SCAN_INTERVAL: 600},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_SYMBOL: "IWDA.AS"}
        )

    assert result["title"] == "World"
    assert result["data"][CONF_NAME] == "World"
    assert result["data"][CONF_SCAN_INTERVAL] == 600


async def test_isin_not_found_shows_error(hass):
    with _search_patch([]):
        result = await _submit(hass, SAP_ISIN)

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_SYMBOL: "isin_not_found"}


async def test_isin_bad_checksum_shows_error_without_lookup(hass):
    with _search_patch([_listing("X")]) as search:
        result = await _submit(hass, "DE0007164601")

    search.assert_not_awaited()
    assert result["errors"] == {CONF_SYMBOL: "invalid_isin"}


async def test_isin_network_error_shows_error(hass):
    import aiohttp

    with _search_patch(raises=aiohttp.ClientError("boom")):
        result = await _submit(hass, SAP_ISIN)

    assert result["errors"] == {"base": "cannot_connect"}


async def test_plain_symbol_skips_lookup(hass):
    with _search_patch([]) as search, _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "SAP.DE")

    search.assert_not_awaited()
    assert result["data"][CONF_SYMBOL] == "SAP.DE"


async def test_listing_picker_shows_the_currency(hass):
    listings = [
        {"symbol": "IWDA.L", "exchange": "London", "name": "ISHARES", "currency": "USD"},
        {"symbol": "EUNL.DE", "exchange": "XETRA", "name": "ISHARES", "currency": "EUR"},
    ]
    with _search_patch(listings):
        result = await _submit(hass, IWDA_ISIN)

    options = next(iter(result["data_schema"].schema.values())).container
    assert options["EUNL.DE"] == "EUNL.DE · XETRA · EUR · ISHARES"


# ---------------------------------------------------------------------------
# WKN lookup
# ---------------------------------------------------------------------------


def _wkn_patch(result=None, raises=None):
    if raises is not None:
        return patch("custom_components.easy_stock.config_flow.search_wkn", side_effect=raises)
    return patch("custom_components.easy_stock.config_flow.search_wkn", return_value=result)


async def test_wkn_single_listing_creates_entry(hass):
    with _wkn_patch([_listing("SAP.DE", "XETRA")]) as search, \
            _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "716460")

    search.assert_awaited_once()
    assert search.await_args.args[0] == "716460"
    assert result["data"][CONF_SYMBOL] == "SAP.DE"


async def test_wkn_multiple_listings_shows_selection_preselecting_the_first(hass):
    # The lookup sorts the user's own listing first; the form preselects it.
    listings = [_listing("VGWL.DE", "XETRA"), _listing("VWRL.L", "London")]
    with _wkn_patch(listings), _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "a1jx52")
        assert result["step_id"] == "select_listing"
        key = next(k for k in result["data_schema"].schema if k == CONF_SYMBOL)
        assert key.default() == "VGWL.DE"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_SYMBOL: "VWRL.L"}
        )

    assert result["data"][CONF_SYMBOL] == "VWRL.L"


async def test_unresolved_wkn_shaped_input_is_kept_as_symbol(hass):
    """A six-character ticker that is no WKN must keep working."""
    with _wkn_patch([]), _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "NVDAUS")

    assert result["data"][CONF_SYMBOL] == "NVDAUS"


async def test_wkn_lookup_failure_falls_back_to_symbol(hass):
    import aiohttp

    with _wkn_patch(raises=aiohttp.ClientError("boom")), _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "A1JX52")

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SYMBOL] == "A1JX52"


async def test_wkn_lookup_is_given_the_home_assistant_currency_and_country(hass):
    hass.config.currency = "GBP"
    hass.config.country = "GB"
    with _wkn_patch([_listing("VWRL.L", "London")]) as search, \
            _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        await _submit(hass, "A1JX52")

    assert search.await_args.args[1:] == ("GBP", "GB")


async def test_symbol_with_dot_skips_wkn_lookup(hass):
    with _wkn_patch([]) as search, _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        await _submit(hass, "SAP.DE")

    search.assert_not_awaited()


async def test_the_symbol_stays_in_the_form_after_an_error(hass):
    with _search_patch([]):
        result = await _submit(hass, SAP_ISIN)

    assert result["errors"] == {CONF_SYMBOL: "isin_not_found"}
    suggested = {
        str(k): k.description["suggested_value"]
        for k in result["data_schema"].schema
        if k.description and "suggested_value" in k.description
    }
    assert suggested[CONF_SYMBOL] == SAP_ISIN


# ---------------------------------------------------------------------------
# Naming a new entry
# ---------------------------------------------------------------------------


async def test_an_empty_name_becomes_yahoos_long_name(hass, yahoo_lookup):
    yahoo_lookup.return_value = "Vanguard FTSE All-World UCITS ETF"
    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "VGWL.DE")

    yahoo_lookup.assert_awaited_once_with("VGWL.DE")
    assert result["title"] == "Vanguard FTSE All-World UCITS ETF"
    assert result["data"][CONF_NAME] == "Vanguard FTSE All-World UCITS ETF"
    assert result["data"][CONF_SYMBOL] == "VGWL.DE"


async def test_a_typed_name_wins_over_yahoos(hass, yahoo_lookup):
    yahoo_lookup.return_value = "Vanguard FTSE All-World UCITS ETF"
    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _init_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SYMBOL: "VGWL.DE", CONF_NAME: " My World ETF ", CONF_SCAN_INTERVAL: 900},
        )

    assert result["title"] == "My World ETF"
    assert result["data"][CONF_NAME] == "My World ETF"


async def test_no_long_name_keeps_the_symbol_as_the_title(hass):
    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "VGWL.DE")

    assert result["title"] == "VGWL.DE"
    assert result["data"][CONF_NAME] == ""


async def test_the_listing_picked_from_an_isin_is_named_too(hass, yahoo_lookup):
    yahoo_lookup.return_value = "iShares Core MSCI World UCITS ETF"
    listings = [_listing("EUNL.DE", "XETRA"), _listing("IWDA.L", "London")]
    with _search_patch(listings), _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, IWDA_ISIN)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_SYMBOL: "IWDA.L"}
        )

    yahoo_lookup.assert_awaited_once_with("IWDA.L")
    assert result["title"] == "iShares Core MSCI World UCITS ETF"


async def test_a_duplicate_aborts_before_yahoo_is_asked(hass, yahoo_lookup):
    for _ in range(2):
        with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
            result = await _submit(hass, "TSLA")

    assert result["reason"] == "already_configured"
    assert yahoo_lookup.await_count == 1


# ---------------------------------------------------------------------------
# A plain symbol has to exist
# ---------------------------------------------------------------------------


async def test_an_unknown_symbol_is_refused(hass, yahoo_lookup):
    """A1JX is not an ISIN, not a WKN and not a Yahoo symbol: no entry for it."""
    yahoo_lookup.return_value = None
    result = await _submit(hass, "A1JX")

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_SYMBOL: "symbol_not_found"}
    assert hass.config_entries.async_entries(DOMAIN) == []


async def test_an_unknown_symbol_keeps_what_was_typed_and_can_be_corrected(hass, yahoo_lookup):
    yahoo_lookup.return_value = None
    result = await _init_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SYMBOL: "A1JX", CONF_NAME: "World", CONF_SCAN_INTERVAL: 600}
    )
    assert result["errors"] == {CONF_SYMBOL: "symbol_not_found"}

    yahoo_lookup.return_value = "Vanguard FTSE All-World UCITS ETF"
    with _wkn_patch([]), _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_SYMBOL: "VWRL.AS", CONF_NAME: "World", CONF_SCAN_INTERVAL: 600}
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SYMBOL] == "VWRL.AS"


async def test_a_mistyped_wkn_is_refused_too(hass, yahoo_lookup):
    """A six-character WKN that OpenFIGI does not know and Yahoo does not either."""
    yahoo_lookup.return_value = None
    with _wkn_patch([]):
        result = await _submit(hass, "A1JX53")

    assert result["errors"] == {CONF_SYMBOL: "symbol_not_found"}


async def test_yahoo_being_down_is_not_called_an_unknown_symbol(hass, yahoo_lookup):
    import aiohttp

    yahoo_lookup.side_effect = aiohttp.ClientError("429")
    result = await _submit(hass, "SAP.DE")

    assert result["errors"] == {"base": "cannot_connect"}
    assert hass.config_entries.async_entries(DOMAIN) == []


async def test_an_unreachable_wkn_lookup_is_not_blamed_on_the_symbol(hass, yahoo_lookup):
    import aiohttp

    yahoo_lookup.return_value = None
    with _wkn_patch(raises=aiohttp.ClientError("429")):
        result = await _submit(hass, "A1JX52")

    assert result["errors"] == {"base": "cannot_connect"}


async def test_a_typed_name_does_not_skip_the_check(hass, yahoo_lookup):
    yahoo_lookup.return_value = None
    result = await _init_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SYMBOL: "A1JX", CONF_NAME: "My ETF", CONF_SCAN_INTERVAL: 900}
    )

    yahoo_lookup.assert_awaited_once_with("A1JX")
    assert result["errors"] == {CONF_SYMBOL: "symbol_not_found"}


async def test_a_symbol_without_a_yahoo_name_is_still_accepted(hass, yahoo_lookup):
    yahoo_lookup.return_value = ""
    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "SOMETHING.DE")

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "SOMETHING.DE"


async def test_a_resolved_listing_is_not_blocked_when_its_name_cannot_be_fetched(hass, yahoo_lookup):
    """ISIN/WKN lookups already vetted the listing; a missing name only costs the nicer title."""
    import aiohttp

    yahoo_lookup.side_effect = aiohttp.ClientError("429")
    with _search_patch([_listing("AAPL", "NASDAQ")]), _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await _submit(hass, "US0378331005")

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "AAPL"


async def test_a_known_duplicate_aborts_before_yahoo_is_asked(hass, yahoo_lookup):
    for _ in range(2):
        with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
            result = await _submit(hass, "MSFT")

    assert result["reason"] == "already_configured"
    assert yahoo_lookup.await_count == 1


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------


async def test_options_flow_shows_form(hass):
    """Options flow init step shows a form pre-filled with current values."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SYMBOL: "MSFT", CONF_NAME: "Microsoft", CONF_SCAN_INTERVAL: 900},
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_saves_new_values(hass):
    """Submitting options form saves updated name and interval."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SYMBOL: "MSFT", CONF_NAME: "Microsoft", CONF_SCAN_INTERVAL: 900},
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_NAME: "MSFT Stock", CONF_SCAN_INTERVAL: 1800},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_NAME] == "MSFT Stock"
    assert entry.options[CONF_SCAN_INTERVAL] == 1800


async def test_wkn_listing_picker_shows_the_currency(hass):
    listings = [
        {"symbol": "VWRL.L", "exchange": "London", "name": "VANG", "currency": "GBp"},
        {"symbol": "VGWL.DE", "exchange": "XETRA", "name": "VANG", "currency": "EUR"},
    ]
    with _wkn_patch(listings):
        result = await _submit(hass, "A1JX52")

    options = next(iter(result["data_schema"].schema.values())).container
    assert options["VGWL.DE"] == "VGWL.DE · XETRA · EUR · VANG"


async def test_a_disappeared_listing_is_not_created_and_can_be_reselected(hass, yahoo_lookup):
    yahoo_lookup.return_value = None
    with _search_patch([_listing("EUNL.DE", "XETRA"), _listing("IWDA.L", "London")]):
        result = await _submit(hass, IWDA_ISIN)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_SYMBOL: "EUNL.DE"})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_SYMBOL: "symbol_not_found"}
    assert hass.config_entries.async_entries(DOMAIN) == []
    yahoo_lookup.return_value = "World ETF"
    with _SETUP_PATCHES[0], _SETUP_PATCHES[1]:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_SYMBOL: "IWDA.L"})
    assert result["data"][CONF_SYMBOL] == "IWDA.L"


async def test_wkn_chart_outage_is_reported_as_cannot_connect(hass, yahoo_lookup):
    from tests.conftest import mock_http
    from custom_components.easy_stock import openfigi

    yahoo_lookup.return_value = None
    patcher, _ = mock_http({}, status=503)
    with patcher, patch.object(openfigi, "_figi_lookup", return_value=[{"ticker": "VGWL", "exchCode": "GR"}]):
        result = await _submit(hass, "A1JX52")
    assert result["errors"] == {"base": "cannot_connect"}
    assert hass.config_entries.async_entries(DOMAIN) == []
