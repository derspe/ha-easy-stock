DOMAIN = "zwitserleven_fondsen"

CONF_SYMBOL = "symbol"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 3600  # 1 hour; Zwitserleven publishes one price per day

PRICE_DECIMALS = 4

# The fund page shared by every config entry and the config flow, see fondsen_page.
DATA_PAGE = f"{DOMAIN}_page"

ZWITSERLEVEN_FONDSEN_URL = (
    "https://www.zwitserleven.nl/over-zwitserleven/verantwoord-beleggen/fondsen/"
)
