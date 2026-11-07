"""Constants for the Euribor rates integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "euribor_rates"

ATTRIBUTION: Final = "Data provided by Banco de España"

# Banco de España's file of daily money market rates, Euribor's among them.
CSV_URL: Final = "https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/ti_1_7.csv"

# The maturities Euribor is published for, and the code of each one's series in the file.
SERIES_BY_MATURITY: Final[dict[str, str]] = {
    "1 week": "D_DNBAS172",
    "1 month": "D_DNBAC172",
    "3 months": "D_DNBAD172",
    "6 months": "D_DNBAE172",
    "12 months": "D_DNBAF172",
}
MATURITIES: Final = list(SERIES_BY_MATURITY)

# Config entry data. The keys are those of earlier versions, so existing entries keep working.
CONF_MATURITY: Final = "maturity"
CONF_DAYS: Final = "days"

DEFAULT_DAYS: Final = 365
MIN_DAYS: Final = 7
# Euribor's series in the file start on 30 December 1998.
MAX_DAYS: Final = 10950

# Every maturity being followed is a subentry of the one Euribor entry.
SUBENTRY_MATURITY: Final = "maturity"
TITLE: Final = "Euribor"

# The file gets the previous working day's rates once a day, at about ten in the morning Madrid time.
UPDATE_INTERVAL: Final = timedelta(hours=1)

# Sensor attributes.
ATTR_MATURITY: Final = "maturity"
ATTR_LATEST_DATE: Final = "latest_date"
ATTR_LATEST_RATE: Final = "latest_rate"
