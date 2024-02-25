"""Platform for sensor integration."""

from __future__ import annotations
import voluptuous as vol
import logging
import time

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,  # noqa
    SCAN_INTERVAL,  # noqa
    CONF_GLOBALID,
    CONF_GLOBALID2,
    CONF_ONLYLINE,
    CONF_LIMIT,
    CONF_HIDEDESTINATION,
    CONF_DOUBLESTATIONNUMBER,
    CONF_TRANSPORTTYPES,
    CONF_HIDENAME,
    CONF_TIMEZONE_FROM,
    CONF_TIMEZONE_TO,
)

# integration imports start
import socket
import urllib.request, json
import urllib.error
import pytz
from datetime import datetime
from datetime import date
# integration imports end

DEFAULT_HIDEDESTINATION = ""
DEFAULT_ONLYLINE = ""
DEFAULT_LIMIT = 6
DEFAULT_CONF_DOUBLESTATIONNUMBER = ""
DEFAULT_CONF_TRANSPORTTYPES = "SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS"
DEFAULT_CONF_GLOBALID2 = ""
DEFAULT_TIMEZONE_FROM = "Europe/Berlin" # or UTC
DEFAULT_TIMEZONE_TO   = "Europe/Berlin"
DEFAULT_HIDENAME = False

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_GLOBALID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_ONLYLINE, default=DEFAULT_ONLYLINE): cv.string,
        vol.Optional(CONF_HIDEDESTINATION, default=DEFAULT_HIDEDESTINATION): cv.string,
        vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): cv.positive_int,
        vol.Optional(CONF_DOUBLESTATIONNUMBER, default=DEFAULT_CONF_DOUBLESTATIONNUMBER): cv.string,
        vol.Optional(CONF_TRANSPORTTYPES, default=DEFAULT_CONF_TRANSPORTTYPES): cv.string,
        vol.Optional(CONF_GLOBALID2, default=DEFAULT_CONF_GLOBALID2): cv.string,
        vol.Optional(CONF_HIDENAME, default=DEFAULT_HIDENAME): cv.boolean,
        vol.Optional(CONF_TIMEZONE_FROM, default=DEFAULT_TIMEZONE_FROM): cv.string,
        vol.Optional(CONF_TIMEZONE_TO, default=DEFAULT_TIMEZONE_TO): cv.string,
    }
)

async def async_setup_platform(
    hass:           HomeAssistant,
    config:         ConfigType,
    add_entities:   AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    name                = config[CONF_NAME]
    globalid            = config[CONF_GLOBALID]
    globalid2           = config[CONF_GLOBALID2]
    onlyline            = config[CONF_ONLYLINE]
    limit               = config[CONF_LIMIT]
    hidedestination     = config[CONF_HIDEDESTINATION]
    doublestationnumber = config[CONF_DOUBLESTATIONNUMBER]
    transporttypes      = config[CONF_TRANSPORTTYPES]
    hidename            = config[CONF_HIDENAME]
    timezoneFrom        = config[CONF_TIMEZONE_FROM]
    timezoneTo          = config[CONF_TIMEZONE_TO]
    add_entities([ConnectionInfo(hass, globalid, globalid2, name, onlyline, limit, hidedestination, doublestationnumber, transporttypes, hidename, timezoneFrom, timezoneTo)], True)

class ConnectionInfo(SensorEntity):

    def __init__(self, hass, globalid, globalid2, name, onlyline, limit, hidedestination, doublestationnumber, transporttypes, hidename, timezoneFrom, timezoneTo) -> None:
        self._onlyline               = onlyline
        self._limit                  = limit
        self._hidedestination        = hidedestination
        self._globalid               = globalid
        self._globalid2              = globalid2
        self._name                   = name
        self._attr_name              = name
        self._hass                   = hass
        self._doublestationnumber    = doublestationnumber
        self._transporttypes         = transporttypes
        self._hidename               = hidename
        self._timezoneFrom           = timezoneFrom
        self._timezoneTo             = timezoneTo
        self._hass.custom_attributes = {}

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._hass.custom_attributes

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._hass.custom_attributes

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._globalid.replace(":", "") + self._doublestationnumber

    def convert_datetime_timezone(self, dt, tz1, tz2):
       tz1 = pytz.timezone(tz1)
       tz2 = pytz.timezone(tz2)
       
       dt = tz1.localize(dt)
       dt = dt.astimezone(tz2)
       
       return dt

    def departure(self) -> str:
        limit = self._limit

        # check if self._hass.custom_attributes is set to avoid undefined messages if the API is down
        if not self._hass.custom_attributes:
           self._hass.custom_attributes = "Try to connect to the MVG API. If this message remains longer, maybe mvg.de is down."

        # 1st API call for globalid1
        try:
           url = "https://www.mvg.de/api/fib/v2/departure?globalId=" + self._globalid + "&limit=80&offsetInMinutes=0&transportTypes=" + self._transporttypes
           headers1 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
           req = urllib.request.Request(url, headers=headers1)
           
           # Setze das Timeout auf 10 Sekunden
           with urllib.request.urlopen(req, timeout=10) as resp:
               responsecode1 = resp.getcode()
               html = resp.read()
        
        except urllib.error.URLError as e:
           if isinstance(e.reason, socket.timeout):
               _LOGGER.error("Timeout beim Verbinden mit der URL für globalid1 - " + self._name)
               return "Timeout beim Verbinden mit der URL für globalid1 - " + self._name
           else:
               _LOGGER.error("Connection Problem globalid1 - " + self._name + " - " + str(e))
               return "Connection Problem globalid1 - " + self._name
        except Exception as e:
           _LOGGER.error("Anderes Problem bei der Verbindung mit globalid1 - " + self._name + " - " + str(e))
           return "Anderes Problem bei der Verbindung mit globalid1 - " + self._name
        
        
        # 2nd API call for globalid2
        if self._globalid2 != "" :
           # do the 2nd call
           # wait 1 second because of 509 error
           time.sleep(1)
           
           try:
              url2 = "https://www.mvg.de/api/fib/v2/departure?globalId=" + self._globalid2 + "&limit=80&offsetInMinutes=0&transportTypes=" + self._transporttypes
              headers2 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
              req2 = urllib.request.Request(url2, headers=headers2)
              
              # Setze das Timeout auf 10 Sekunden
              with urllib.request.urlopen(req2, timeout=10) as resp2:
                  responsecode2 = resp2.getcode()
                  html2 = resp2.read()
           
           except urllib.error.URLError as e:
              if isinstance(e.reason, socket.timeout):
                  _LOGGER.error("Timeout beim Verbinden mit der URL für globalid2 - " + self._name)
                  return "Timeout beim Verbinden mit der URL für globalid2 - " + self._name
              else:                   
                  _LOGGER.error("Connection Problem globalid2 - " + self._name + " - " + str(e))
                  return "Connection Problem globalid2 - " + self._name
           except Exception as e:
              _LOGGER.error("Anderes Problem bei der Verbindung mit globalid2 - " + self._name + " - " + str(e))
              return "Anderes Problem bei der Verbindung mit globalid2 - " + self._name
           
           data  = json.loads(html)
           data2 = json.loads(html2)

           data.extend(data2)
        else :
           data = json.loads(html)

        sorted_data = sorted(data, key=lambda x: x["plannedDepartureTime"])
        fahrtinfos = "Please use the project lovelace card"

        connectioninfos = {}
        ccc = 0

        tableContent = '<table>'

        if self._hidename == False:
          tableContent += '<tr><td colspan="4" class="cardname">' + self._name + '</td></tr>'
                          
        tableContent += '<tr>\
                            <td class="headline">Linie</td>\
                            <td class="headline">Ziel</td>\
                            <td class="headline">Gleis</td>\
                            <td class="headline">Abfahrt</td>\
                          </tr>'

        for user in sorted_data:
          delay = ""
          track = ""

          # if self._onlyline is set, check if it is the correct line
          if self._onlyline != "":
            splitted = self._onlyline.split(',')
            if user['label'] not in splitted: continue

          # if self._hidedestination is set, check if it is the "NOT correct" destination
          if self._hidedestination != "":
            if user['destination'].lower() in self._hidedestination.lower(): continue

          timestampPlannedDeparture = user['plannedDepartureTime'] / 1000
          dt_object = self.convert_datetime_timezone(datetime.fromtimestamp(timestampPlannedDeparture), self._timezoneFrom, self._timezoneTo)
          
          timestampRealDeparture = user['realtimeDepartureTime'] / 1000
          dt_objectReal = self.convert_datetime_timezone(datetime.fromtimestamp(timestampRealDeparture), self._timezoneFrom, self._timezoneTo)

          t = dt_object.strftime("%H:%M")
          d = dt_object.strftime("%d.%m.%Y")
          
          tReal = dt_objectReal.strftime("%H:%M")
          dReal = dt_objectReal.strftime("%d.%m.%Y")

          if 'delayInMinutes' in user:
             if user['delayInMinutes'] is not None: 
                if user['delayInMinutes'] > 0 : delay = ' <font color="red">+' + str(user['delayInMinutes']) + '</font> (' + tReal + ')'
                
          if user['transportType'] == "BUS"          : user['platform'] = 'Bus'
          if user['transportType'] == "REGIONAL_BUS" : user['platform'] = 'Bus'
          
          if 'platform' not in user:
             # Der Schlüssel 'platform' existiert nicht im Dictionary user
             user['platform'] = '---'
          
          if not user['cancelled'] : 
            track = "" + str(user['platform'])
          else:
            track = "" + str(user['platform'])
            delay = ' <font color="red">Entfällt</font>'

          tableContent += '\
             <tr>\
                <td><span class="line ' + user['transportType'] + ' ' + user['label'] + '">' + user['label'] + '</span></td>\
                <td>' + user['destination'] + '</td>\
                <td>' + track + '</td>\
                <td>' + t +''+ delay + '</td>\
             </tr>';

          ccc += 1
          if ccc == limit: break

        connectioninfos['connections'] = tableContent + '</table>'
        self._hass.custom_attributes = connectioninfos
        return fahrtinfos

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._attr_native_value = "" + self.departure()
