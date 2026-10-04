"""Shared fixtures for zwitserleven_fondsen tests."""
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from custom_components.zwitserleven_fondsen.fondsen_page import FundQuote

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this package."""
    return


# A saved copy of the real fund overview page (prices dated 02-10-2026).
FONDSEN_HTML = (Path(__file__).parent / "fixtures" / "fondsen.html").read_text(
    encoding="utf-8"
)

SYMBOL = "LTAAF"


def make_store(history=None):
    """Return a mocked Store with optional pre-loaded history."""
    store = AsyncMock()
    store.async_load.return_value = history
    return store


def make_page(*quotes, error=None):
    """Return a mocked FondsenPage serving `quotes`, or raising `error`."""
    page = AsyncMock()
    if error is not None:
        page.async_get_funds.side_effect = error
    else:
        page.async_get_funds.return_value = {q.symbol: q for q in quotes}
    return page


def quote(date="2026-10-02", price=225.87, symbol=SYMBOL, name="ASN Duurzaam Aandelenfonds"):
    return FundQuote(symbol=symbol, name=name, price_date=date, price=price)
