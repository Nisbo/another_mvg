from datetime import timedelta


class MVGException(Exception):
    """Exception class for MVG."""


DOMAIN = "another_mvg"  # name of the integration, dont change
SCAN_INTERVAL = timedelta(seconds=60)  # updateinterval in seconds

URL = "https://www.mvg.de/api/bgw-pt/v3/departures?globalId={}&limit={}&offsetInMinutes={}&transportTypes={}"
URL_EFA_ARRIVALS = "https://m.mvv-muenchen.de/efa/XML_DM_REQUEST"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.10 Safari/605.1.1"

CONF_MONITOR_TYPE = "monitor_type"  # departure or arrival
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
CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER = "exclude_attributes_from_recorder" # optional
CONF_MQTT_ENABLED = "mqtt_enabled" # optional
CONF_MQTT_TOPIC_PREFIX = "mqtt_topic_prefix" # optional
CONF_MQTT_RETAIN = "mqtt_retain" # optional
CONF_MQTT_QOS = "mqtt_qos" # optional
CONF_UPDATE_MODE = "update_mode" # optional
CONF_ALERT_ENABLED = "alert{}_enabled" # optional
CONF_ALERT_NAME = "alert{}_name" # optional
CONF_ALERT_WEEKDAYS = "alert{}_weekdays" # optional
CONF_ALERT_LINE = "alert{}_line" # optional
CONF_ALERT_PLANNED_TIME = "alert{}_planned_time" # optional
CONF_ALERT_DIRECTION = "alert{}_direction" # optional
CONF_ALERT_ACTIVE_FROM = "alert{}_active_from" # optional
CONF_ALERT_ACTIVE_TO = "alert{}_active_to" # optional
CONF_ALERT_DELAY_MINUTES = "alert{}_delay_minutes" # optional
CONF_ALERT_CANCELLED = "alert{}_cancelled" # optional
CONF_ALERT_NOTIFY_MODE = "alert{}_notify_mode" # optional

DEFAULT_HIDEDESTINATION = ""
DEFAULT_ONLYDESTINATION = ""
DEFAULT_ONLYLINE = ""
DEFAULT_LIMIT = 40
DEFAULT_CONF_TRANSPORTTYPES = "SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS"
DEFAULT_MONITOR_TYPE = "departure"
MONITOR_TYPE_DEPARTURE = "departure"
MONITOR_TYPE_ARRIVAL = "arrival"
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
DEFAULT_EXCLUDE_ATTRIBUTES_FROM_RECORDER = False
DEFAULT_MQTT_ENABLED = False
DEFAULT_MQTT_TOPIC_PREFIX = "another_mvg"
DEFAULT_MQTT_RETAIN = False
DEFAULT_MQTT_QOS = 0
DEFAULT_UPDATE_MODE = "auto"
UPDATE_MODE_AUTO = "auto"
UPDATE_MODE_MANUAL = "manual"
SERVICE_REFRESH = "refresh"
ALERT_COUNT = 5
ALERT_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
ALERT_NOTIFY_ONCE = "once"
ALERT_NOTIFY_WORSENING = "worsening"
DEFAULT_ALERT_ENABLED = False
DEFAULT_ALERT_NAME = ""
DEFAULT_ALERT_WEEKDAYS = []
DEFAULT_ALERT_LINE = ""
DEFAULT_ALERT_PLANNED_TIME = ""
DEFAULT_ALERT_DIRECTION = ""
DEFAULT_ALERT_ACTIVE_FROM = ""
DEFAULT_ALERT_ACTIVE_TO = ""
DEFAULT_ALERT_DELAY_MINUTES = 0
DEFAULT_ALERT_CANCELLED = False
DEFAULT_ALERT_NOTIFY_MODE = ALERT_NOTIFY_ONCE
EVENT_ANOTHER_MVG_ALERT = "another_mvg_alert"

URL_BASE = "/another_mvg"
ANOTHER_MVG_CARDS = [
    {
        "name": "Another MVG Card",
        "filename": "content-card-another-mvg.js",
        "version": "3.0.0-BETA-11.0",
    },
    {
        "name": "Another MVG Big Card",
        "filename": "content-card-another-mvg-big.js",
        "version": "3.0.0-BETA-11.0",
    },
    {
        "name": "Another MVG Search Card",
        "filename": "content-card-another-mvg-search.js",
        "version": "3.0.0-BETA-11.0",
    },
    {
        "name": "Another MVG Route Card",
        "filename": "content-card-another-mvg-route.js",
        "version": "3.0.0-BETA-11.0",
    },
    {
        "name": "Another MVG LiveMap Card",
        "filename": "content-card-another-mvg-livemap.js",
        "version": "3.0.0-BETA-11.0",
    },
]
