"""Shared fixtures for easy_stock tests."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this package."""
    return


SYMBOL = "AAPL"

# Five consecutive trading days, safely in the past
SAMPLE_DAYS = [
    ("2024-01-02", 185.20),
    ("2024-01-03", 184.10),
    ("2024-01-04", 186.50),
    ("2024-01-05", 188.00),
    ("2024-01-08", 189.30),
]


def make_yahoo_payload(days_prices=None, meta_price=None, market_state="REGULAR"):
    """Build a minimal Yahoo Finance chart API response."""
    if days_prices is None:
        days_prices = SAMPLE_DAYS
    timestamps = []
    closes = []
    for date_str, price in days_prices:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        timestamps.append(int(dt.timestamp()))
        closes.append(price)
    last_close = closes[-1]
    prev_close = closes[-2] if len(closes) >= 2 else last_close
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": SYMBOL,
                        "currency": "USD",
                        "longName": "Apple Inc.",
                        "marketState": market_state,
                        "regularMarketPrice": (
                            meta_price if meta_price is not None else last_close
                        ),
                        "previousClose": prev_close,
                        "chartPreviousClose": prev_close,
                    },
                    "timestamp": timestamps,
                    "indicators": {"quote": [{"close": closes}]},
                }
            ],
            "error": None,
        }
    }


def make_store(history=None):
    """Return a mocked Store with optional pre-loaded history."""
    store = AsyncMock()
    store.async_load.return_value = history
    return store


def mock_http(payload, status=200):
    """Return a context manager that patches aiohttp.ClientSession."""
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=payload)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get.return_value = mock_resp

    return patch("aiohttp.ClientSession", MagicMock(return_value=mock_session)), mock_session
