"""Constants for the Euribor rates integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "euribor_rates"

ATTRIBUTION: Final = "Data provided by euribor-rates.eu"

API_URL: Final = "https://www.euribor-rates.eu/umbraco/api/euriborpageapi/highchartsdata"
# The site serves this endpoint to its own charts, and checks that the request looks like one of them.
HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/106.0.5249.62 Safari/537.36"
    ),
    "Sec-Fetch-Mode": "cors",
    "Referer": "https://www.euribor-rates.eu/",
}

# The maturities the site publishes, and the number its API gives each one.
SERIES_BY_MATURITY: Final[dict[str, int]] = {
    "1 week": 5,
    "1 month": 1,
    "3 months": 2,
    "6 months": 3,
    "12 months": 4,
}
MATURITIES: Final = list(SERIES_BY_MATURITY)

# Config entry data. The keys are those of earlier versions, so existing entries keep working.
CONF_MATURITY: Final = "maturity"
CONF_DAYS: Final = "days"

DEFAULT_DAYS: Final = 30
MIN_DAYS: Final = 7
MAX_DAYS: Final = 3650

# Rates are published once a day, on working days.
UPDATE_INTERVAL: Final = timedelta(hours=3)

# Sensor attributes.
ATTR_HISTORY: Final = "history"
ATTR_DATE: Final = "date"
ATTR_RATE: Final = "rate"
ATTR_MATURITY: Final = "maturity"
ATTR_LATEST_DATE: Final = "latest_date"
ATTR_LATEST_RATE: Final = "latest_rate"
