from datetime import timedelta


class MVGException(Exception):
    """Exception class for MVG."""


DOMAIN = "another_mvg"  # name of the integration, dont change
SCAN_INTERVAL = timedelta(seconds=60)  # updateinterval in seconds

#URL = "https://www.mvg.de/api/fib/v2/departure?globalId={}&limit=80&offsetInMinutes=0&transportTypes={}" # the old API URL
URL = "https://www.mvg.de/api/bgw-pt/v3/departures?globalId={}&limit=80&offsetInMinutes=0&transportTypes={}"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

CONF_GLOBALID = "globalid"  # required
CONF_GLOBALID2 = "globalid2"  # optional but not recommened because of 2 API calls
CONF_ONLYLINE = "onlyline"  # optional
CONF_LIMIT = "limit"  # optional --> max 80
CONF_HIDEDESTINATION = "hidedestination"  # optional
CONF_ONLYDESTINATION = "onlydestination"  # optional
CONF_DOUBLESTATIONNUMBER = "doublestationnumber"  # optional --> any String, if you want the globalid more than 1 times
CONF_TRANSPORTTYPES = "transporttypes"  # SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS (SCHIFF - There is a parameter in the MVG API, but dont know if it will return data, at the moment not supported) BAHN is also possible but not enabled by default
CONF_HIDENAME = "hidename"  # Hide the name of the card
CONF_TIMEZONE_FROM = "timezone_from"  # like "Europe/Berlin" or "UTC" if your system is running with UTC settings
CONF_TIMEZONE_TO = "timezone_to"  # like "Europe/Berlin"
CONF_ALERT_FOR = "alert_for"  # optional

DEFAULT_HIDEDESTINATION = ""
DEFAULT_ONLYDESTINATION = ""
DEFAULT_ONLYLINE = ""
DEFAULT_LIMIT = 6
DEFAULT_CONF_DOUBLESTATIONNUMBER = ""
DEFAULT_CONF_TRANSPORTTYPES = "SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS"
DEFAULT_CONF_GLOBALID2 = ""
DEFAULT_TIMEZONE_FROM = "Europe/Berlin"  # or UTC
DEFAULT_TIMEZONE_TO = "Europe/Berlin"
DEFAULT_HIDENAME = False
DEFAULT_ALERT_FOR = ""

URL_BASE = "/another_mvg"
ANOTHER_MVG_CARDS = [
    {
        "name": "Another MVG Card",
        "filename": "content-card-another-mvg.js",
        "version": "1.6.0",
    },
    {
        "name": "Another MVG Big Card",
        "filename": "content-card-another-mvg-big.js",
        "version": "1.6.0",
    },
]
