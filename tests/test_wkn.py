"""Unit tests for the WKN lookup."""
from unittest.mock import patch

import pytest

from custom_components.easy_stock import wkn

@pytest.mark.parametrize("value", ["A1JX52", "716460", "A0D9PT", "ENER6Y"])
def test_wkn_shapes(value):
    assert wkn.looks_like_wkn(value)


@pytest.mark.parametrize("value", ["AAPL", "SAP.DE", "BTC-USD", "DE0007164600", "a1jx52", "A1IX52", "A1JX5O"])
def test_non_wkn_shapes(value):
    assert not wkn.looks_like_wkn(value)


async def test_search_goes_through_openfigi_with_the_wkn_id_type():
    with patch.object(wkn, "find_listings", return_value=["x"]) as find:
        assert await wkn.search_wkn("A1JX52", "EUR", "DE") == ["x"]

    find.assert_awaited_once_with("ID_WERTPAPIER", "A1JX52", "EUR", "DE")
