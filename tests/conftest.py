"""Shared fixtures for zwitserleven_fondsen tests."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this package."""
    return


SYMBOL = "LTAAF"

# Five consecutive trading days, safely in the past
SAMPLE_DAYS = [
    ("2024-01-02", 225.87),
    ("2024-01-03", 224.10),
    ("2024-01-04", 226.50),
    ("2024-01-05", 228.00),
    ("2024-01-08", 229.30),
]


def make_zwitserleven_html():
    """Build a minimal Zwitserleven fondsen HTML response with fund table."""
    html = f"""
    <html>
    <body>
        <table class="fundoverview">
            <tr class="fundoverview__item">
                <td>
                    <button id="{SYMBOL}">Test Fund</button>
                </td>
                <td>02-01-2024</td>
                <td>€ 225,87</td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html


def make_store(history=None):
    """Return a mocked Store with optional pre-loaded history."""
    store = AsyncMock()
    store.async_load.return_value = history
    return store


def mock_http(html_or_json, status=200):
    """Return a context manager that patches aiohttp.ClientSession."""
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.text = AsyncMock(return_value=html_or_json)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.get.return_value = mock_resp

    return patch("aiohttp.ClientSession", MagicMock(return_value=mock_session)), mock_session
