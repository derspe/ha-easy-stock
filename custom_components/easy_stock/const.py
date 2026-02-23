DOMAIN = "easy_stock"

CONF_SYMBOL = "symbol"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 900  # 15 minutes

YAHOO_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?range=1y&interval=1d&includePrePost=false"
)

YAHOO_CHART_URL_MINI = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?range=5d&interval=1d&includePrePost=false"
)
