from datetime import timedelta


class MVGException(Exception):
    """Exception class for MVG."""


DOMAIN = "another_mvg"  # name of the integration, dont change
SCAN_INTERVAL = timedelta(seconds=60)  # updateinterval in seconds

URL = "https://www.mvg.de/api/bgw-pt/v3/departures?globalId={}&limit=80&offsetInMinutes={}&transportTypes={}"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.10 Safari/605.1.1"

CONF_GLOBALID = "globalid"  # required
CONF_GLOBALID2 = "globalid2"  # optional but not recommened because of 2 API calls
CONF_ONLYLINE = "onlyline"  # optional
CONF_LIMIT = "limit"  # optional --> max 80
CONF_HIDEDESTINATION = "hidedestination"  # optional
CONF_ONLYDESTINATION = "onlydestination"  # optional
CONF_DOUBLESTATIONNUMBER = "doublestationnumber"  # deprecated - but has to stay in the code because of converting to GUI - optional --> any String, if you want the globalid more than 1 times
CONF_TRANSPORTTYPES = "transporttypes"  # SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS (SCHIFF - There is a parameter in the MVG API, but dont know if it will return data, at the moment not supported) BAHN is also possible but not enabled by default
CONF_TIMEZONE_FROM = "timezone_from"  # like "Europe/Berlin" or "UTC" if your system is running with UTC settings
CONF_TIMEZONE_TO = "timezone_to"  # like "Europe/Berlin"
CONF_ALERT_FOR = "alert_for"  # optional
CONF_STATS_TEMPLATE = "stats_template" # optional
CONF_INCREASED_LIMIT = "increased_limit" # optional
CONF_SORT_BY_REAL_DEPARTURE = "sort_by_real_departure" # optional
CONF_OFFSET_IN_MINUTES = "offset_in_minutes" # optional
CONF_PROXY_URL = "proxy_url" # optional
CONF_PROXY_USETIME = "proxy_usetime" # optionalo
CONF_FORCE_PROXY = "force_proxy" # optional
CONF_CSS_CODE = "css_code" # optional
CONF_CSS_CODE_DARKMODE_ONLY = "css_code_darkmode_only" # optional

DEFAULT_HIDEDESTINATION = ""
DEFAULT_ONLYDESTINATION = ""
DEFAULT_ONLYLINE = ""
DEFAULT_LIMIT = 6
DEFAULT_CONF_TRANSPORTTYPES = "SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS"
DEFAULT_CONF_GLOBALID2 = ""
DEFAULT_TIMEZONE_FROM = "Europe/Berlin"  # or UTC
DEFAULT_TIMEZONE_TO = "Europe/Berlin"
DEFAULT_ALERT_FOR = ""
DEFAULT_STATS_TEMPLATE = ""
DEFAULT_INCREASED_LIMIT = 0
DEFAULT_SORT_BY_REAL_DEPARTURE = False
DEFAULT_OFFSET_IN_MINUTES = 0
DEFAULT_PROXY_URL = ""
DEFAULT_PROXY_USETIME = 600
DEFAULT_FORCE_PROXY = False
DEFAULT_CSS_CODE = ""
DEFAULT_CSS_CODE_DARKMODE_ONLY = False

URL_BASE = "/another_mvg"
ANOTHER_MVG_CARDS = [
    {
        "name": "Another MVG Card",
        "filename": "content-card-another-mvg.js",
        "version": "2.2.0-BETA.3",
    },
    {
        "name": "Another MVG Big Card",
        "filename": "content-card-another-mvg-big.js",
        "version": "2.2.0-BETA.3",
    },
    {
        "name": "Another MVG LiveMap Card",
        "filename": "content-card-another-mvg-livemap.js",
        "version": "2.2.0-BETA.3",
    },
]
