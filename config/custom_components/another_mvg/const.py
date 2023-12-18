from datetime import timedelta

DOMAIN = "another_mvg"                           # name of the integration, dont change
SCAN_INTERVAL = timedelta(seconds=60)            # updateinterval in seconds

CONF_GLOBALID            = "globalid"            # required
CONF_GLOBALID2           = "globalid2"           # optional but not recommened because of 2 API calls
CONF_ONLYLINE            = "onlyline"            # optional
CONF_LIMIT               = "limit"               # optional --> max 80
CONF_HIDEDESTINATION     = "hidedestination"     # optional
CONF_DOUBLESTATIONNUMBER = "doublestationnumber" # optional --> any String, if you want the globalid more than 1 times
CONF_TRANSPORTTYPES      = "transporttypes"      # SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS (SCHIFF - There is a parameter in the MVG API, but dont know if it will return data, at the moment not supported)
