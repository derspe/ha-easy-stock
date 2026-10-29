DOMAIN = "easy_stock"

CONF_SYMBOL = "symbol"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 900  # 15 minutes

# Yahoo refuses requests without a browser-like User-Agent.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

YAHOO_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?range=1y&interval=1d&includePrePost=false"
)

YAHOO_CHART_URL_MINI = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?range=5d&interval=1d&includePrePost=false"
)

YAHOO_CHART_URL_INTRADAY = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?range=5d&interval=1h&includePrePost=false"
)

YAHOO_SEARCH_URL = (
    "https://query1.finance.yahoo.com/v1/finance/search"
    "?q={query}&quotesCount=10&newsCount=0"
)

OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"
