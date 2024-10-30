"""Platform for sensor integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
import time
import requests
from requests import HTTPError, Timeout
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle

from .const import (
    CONF_ALERT_FOR,
    CONF_DOUBLESTATIONNUMBER,
    CONF_GLOBALID,
    CONF_GLOBALID2,
    CONF_HIDEDESTINATION,
    CONF_ONLYDESTINATION,
    CONF_HIDENAME,
    CONF_LIMIT,
    CONF_ONLYLINE,
    CONF_TIMEZONE_FROM,
    CONF_TIMEZONE_TO,
    CONF_TRANSPORTTYPES,
    CONF_SHOW_CLOCK,
    URL,
    USER_AGENT,
    MVGException,
    DEFAULT_ONLYLINE,
    DEFAULT_HIDEDESTINATION,
    DEFAULT_ONLYDESTINATION,
    DEFAULT_LIMIT,
    DEFAULT_CONF_DOUBLESTATIONNUMBER,
    DEFAULT_CONF_TRANSPORTTYPES,
    DEFAULT_CONF_GLOBALID2,
    DEFAULT_HIDENAME,
    DEFAULT_TIMEZONE_FROM,
    DEFAULT_TIMEZONE_TO,
    DEFAULT_ALERT_FOR,
    DEFAULT_SHOW_CLOCK,
)

# integration imports end

_LOGGER = logging.getLogger(__name__)

# Zeitintervall zwischen den Updates
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_GLOBALID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_ONLYLINE, default=DEFAULT_ONLYLINE): cv.string,
        vol.Optional(CONF_HIDEDESTINATION, default=DEFAULT_HIDEDESTINATION): cv.string,
        vol.Optional(CONF_ONLYDESTINATION, default=DEFAULT_ONLYDESTINATION): cv.string,
        vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): cv.positive_int,
        vol.Optional(CONF_DOUBLESTATIONNUMBER, default=DEFAULT_CONF_DOUBLESTATIONNUMBER): cv.string,
        vol.Optional(CONF_TRANSPORTTYPES, default=DEFAULT_CONF_TRANSPORTTYPES): cv.string,
        vol.Optional(CONF_GLOBALID2, default=DEFAULT_CONF_GLOBALID2): cv.string,
        vol.Optional(CONF_HIDENAME, default=DEFAULT_HIDENAME): cv.boolean,
        vol.Optional(CONF_TIMEZONE_FROM, default=DEFAULT_TIMEZONE_FROM): cv.string,
        vol.Optional(CONF_TIMEZONE_TO, default=DEFAULT_TIMEZONE_TO): cv.string,
        vol.Optional(CONF_ALERT_FOR, default=DEFAULT_ALERT_FOR): cv.string,
        vol.Optional(CONF_SHOW_CLOCK, default=DEFAULT_SHOW_CLOCK): cv.boolean,
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.warning(
        "Setting up Another MVG sensor using YAML configuration is deprecated. Please remove the YAML configuration and use the integration through the Home Assistant UI."
    )
    
    if discovery_info is None:
        # Konfiguration über YAML
        add_entities([ConnectionInfo(hass, config)], True)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Another MVG sensor from a config entry."""
    # Konfiguration über GUI
    async_add_entities([ConnectionInfo(hass, config_entry.data)])
    
@dataclass
class Departure:
    """Class to hold departure data."""
    
    transport_type: str
    label: str
    destination: str
    track: str
    planned_departure: str
    expected_departure: str
    cancelled: bool
    delay: int

@dataclass
class DepartureAlarms:
    """Class to hold departure alarm data."""
    
    label: str
    number: str
    delayInMinutes: int

class ConnectionInfo(SensorEntity):
    """Class for MVG info."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialise."""
        self._onlyline = config[CONF_ONLYLINE]
        self._limit = config[CONF_LIMIT]
        self._hidedestination = config[CONF_HIDEDESTINATION]
        self._onlydestination = config[CONF_ONLYDESTINATION]
        self._globalid = config[CONF_GLOBALID]
        self._globalid2 = config[CONF_GLOBALID2]
        self._name = config[CONF_NAME]
        self._hass = hass
        self._doublestationnumber = config[CONF_DOUBLESTATIONNUMBER]
        self._transporttypes = config[CONF_TRANSPORTTYPES]
        self._hidename = config[CONF_HIDENAME]
        self._show_clock = config.get(CONF_SHOW_CLOCK, DEFAULT_SHOW_CLOCK)
        self._timezoneFrom = config[CONF_TIMEZONE_FROM]
        self._timezoneTo = config[CONF_TIMEZONE_TO]
        self._alert_for = config[CONF_ALERT_FOR]
        self._custom_attributes = {
            "config": {"name": self._name, "hide_name": self._hidename, "show_clock": self._show_clock}
        }
        self._lateConnections = ""
        self._dataOutdated = ""

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        # _LOGGER.warning(self._custom_attributes)
        return self._custom_attributes

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._globalid.replace(":", "") + self._doublestationnumber

    @property
    def native_value(self):
        """Return native value."""
        return "Please use the project lovelace card to show your stop: " + self._name

    @property
    def dataOutdated(self):
        """Getter-Method"""
        return self._dataOutdated

    @dataOutdated.setter
    def dataOutdated(self, value):
        """Setter-Method"""
        self._dataOutdated = value

    @property
    def lateConnections(self):
        """Getter-Method"""
        return self._lateConnections

    @lateConnections.setter
    def lateConnections(self, value):
        """Setter-Method"""
        self._lateConnections = value

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._custom_attributes["departures"] = self.get_departures()
        self._custom_attributes["dataOutdated"] = self._dataOutdated
        self.process_late_connections()

    def process_late_connections(self):
        """Method to update the lateConnections"""
        for departure_alarm in self.lateConnections:
            label = departure_alarm.label
            number = departure_alarm.number
            delay_in_minutes = departure_alarm.delayInMinutes
            self._custom_attributes[f'notifyLateMvgConnection{label}_{number}'] = delay_in_minutes
        
    def convert_timestamp_timezone(
        self,
        timestamp: int,
        from_timezone: str,
        to_timezone: str,
        output_format: str = "",
    ) -> str:
        """Convert epoch timestamp to timezone-aware datetime and format it."""
        # First, create a timezone-aware datetime object from the timestamp and the from_timezone
        dt = datetime.fromtimestamp(timestamp, tz=ZoneInfo(from_timezone))
        
        # Convert to the target timezone
        dt_converted = dt.astimezone(ZoneInfo(to_timezone))
        
        # Return the formatted datetime string if output_format is specified
        if output_format:
            return dt_converted.strftime(output_format)
        
        return dt_converted
        
    def get_departures(self) -> str:
        """Get departure data."""

        # check if self._custom_attributes is set to avoid undefined messages if the API is down or if there is an error
        # or for the first call by the frontend when there is no data available in departures
        # normally you should never see this message
        if not self._custom_attributes:
            # Add a dummy connection
            departures = []
            departures.append(
                Departure(
                    transport_type="BUS",
                    label="ERROR",
                    destination="Try to connect to the MVG API. If this message remains longer, maybe mvg.de is down.",
                    track="---",
                    planned_departure="---",
                    expected_departure="---",
                    cancelled=False,
                    delay=0,
                )
            )
            self._custom_attributes["departures"] = departures

        # 1st API call for globalid1
        try:
            data = self.get_api_for_globalid(
                self._name, self._globalid, self._transporttypes
            )
        except MVGException as ex:
            # return the old departures self._custom_attributes["departures"] and set a variable with the info that the departures are outdated
            # because returning an ex leads to an error: Unable to serialize to JSON. Bad data found
            self._dataOutdated = " - nicht aktuell"
            if not self._custom_attributes["departures"]:
                # Add a dummy connection
                departures = []
                departures.append(
                    Departure(
                        transport_type="BUS",
                        label="ERROR",
                        destination="Try to connect to the MVG API. If this message remains longer, maybe mvg.de is down.",
                        track="---",
                        planned_departure="---",
                        expected_departure="---",
                        cancelled=False,
                        delay=0,
                    )
                )
                self._custom_attributes["departures"] = departures
            
            return self._custom_attributes["departures"]

        # 2nd API call for globalid2
        if self._globalid2:
            # wait 1 second because of 509 error
            time.sleep(1)
            try:
                data2 = self.get_api_for_globalid(
                    self._name, self._globalid2, self._transporttypes
                )
            except MVGException as ex:
                # return the old departures self._custom_attributes["departures"] and set a variable with the info that the departures are outdated
                # because returning an ex leads to an error: Unable to serialize to JSON. Bad data found
                self._dataOutdated = " - nicht aktuell"
                if not self._custom_attributes["departures"]:
                    # Add a dummy connection
                    departures = []
                    departures.append(
                        Departure(
                            transport_type="BUS",
                            label="ERROR",
                            destination="Try to connect to the MVG API. If this message remains longer, maybe mvg.de is down.",
                            track="---",
                            planned_departure="---",
                            expected_departure="---",
                            cancelled=False,
                            delay=0,
                        )
                    )
                    self._custom_attributes["departures"] = departures
                    
                return self._custom_attributes["departures"]
            if data:
                try:
                    data.extend(data2)
                except Exception as ex:
                    _LOGGER.error(
                         "AnotherMVG: Unable to combine data from globalid1 with globalid2 for %s - %s - This usually happens if the data from the API for globalid1 and/or globalid2 is malformated or not available. We can do nothing. Normally it will be fixed by its own.",
                          self._name,
                          str(ex),
                    )
                    # return the old departures self._custom_attributes["departures"]
                    # and set a variable with the info that the departures are outdated
                    self._dataOutdated = " - nicht aktuell"
                    return self._custom_attributes["departures"]
        
        try:
            sorted_data = sorted(data, key=lambda x: x["plannedDepartureTime"])
        except Exception as ex:
            _LOGGER.error(
                 "AnotherMVG: Unable to sort the result for %s - %s - This usually happens if the data from the API is malformated or not available. We can do nothing. Normally it will be fixed by its own.",
                  self._name,
                  str(ex),
            )
            # return the old departures self._custom_attributes["departures"]
            # and set a variable with the info that the departures are outdated
            self._dataOutdated = " - nicht aktuell"
            return self._custom_attributes["departures"]
        
        self._dataOutdated = ""
        return self.pre_process_output(sorted_data)

    def pre_process_output(self, data: dict) -> dict:
        """Preformat necessary values into list of Departure."""
        
        connectioninfos = []
        verbindungen_list = self._alert_for.split(",")
        counter_dict = {wert: 0 for wert in verbindungen_list}
        
        departures = []
        for departure in data:
            # if self._onlyline is set, check if it is the correct line
            if self._onlyline != "" and departure["label"] not in self._onlyline.split(
                ","
            ):
                continue
            
            # if self._hidedestination is set, check if it is the "NOT correct" destination
            if (
                self._hidedestination != ""
                and departure["destination"].lower() in self._hidedestination.lower()
            ):
                continue
            
            # if self._onlydestination is set, check if it is the correct destination
            if (
                self._onlydestination != ""
                and departure["destination"].lower() not in self._onlydestination.lower()
            ):
                continue
            
            # Format platform
            if departure["transportType"] in ["BUS", "REGIONAL_BUS"]:
                track = "Bus"
            elif "platform" in departure:
                track = str(departure["platform"])
            elif self._globalid == "de:09175:4070" or self._globalid2 == "de:09175:4070":
                # Work Around for missing track 2a in Ebersberg
                # If there is no platform available, assume that the departure is from Gleis 2a
                track = "2a"
            else:
                # the key 'platform' doesnt exist in Dictionary user
                track = "---"
            
            departures.append(
                Departure(
                    transport_type=departure["transportType"],
                    label=departure["label"],
                    destination=departure["destination"],
                    track=track,
                    planned_departure=self.convert_timestamp_timezone(
                        departure["plannedDepartureTime"] / 1000,
                        self._timezoneFrom,
                        self._timezoneTo,
                        "%H:%M",
                    ),
                    expected_departure=self.convert_timestamp_timezone(
                        departure["realtimeDepartureTime"] / 1000,
                        self._timezoneFrom,
                        self._timezoneTo,
                        "%H:%M",
                    ),
                    cancelled=departure["cancelled"],
                    delay=departure.get("delayInMinutes", 0),
                )
            )

            if departure['label'] in counter_dict:
              counter_dict[departure['label']] += 1
              label = departure['label']

              # alarm 1, 2, 3
              if counter_dict[label] in (1, 2, 3):
                  # in time
                  #connectioninfos[f'notifyLateMvgConnection{counter_dict[label]}_{label}'] = 0
                  alarmStatus = 0

                  # Delay
                  if 'delayInMinutes' in departure and departure['delayInMinutes'] is not None and departure['delayInMinutes'] > 0:
                      #connectioninfos[f'notifyLateMvgConnection{counter_dict[label]}_{label}'] = departure['delayInMinutes']
                      alarmStatus = departure.get("delayInMinutes", 0)

                  # Cancelled
                  if not departure['cancelled']:
                      # not cancelled
                      pass
                  else:
                      # connectioninfos[f'notifyLateMvgConnection{counter_dict[label]}_{label}'] = -1
                      alarmStatus = -1
                  
                  connectioninfos.append(
                    DepartureAlarms(
                      # notifyLateMvgConnectionS4_1
                      label=departure["label"],
                      number=counter_dict[label],
                      delayInMinutes=alarmStatus,
                    )
                  )
            
            if len(departures) >= self._limit:
                break
        
        self.lateConnections = connectioninfos
        
        # if there was an empty result from the API, return the old value
        if "departures" in self._custom_attributes and len(departures) == 0:
            self._dataOutdated = " - nicht aktuell"
            return self._custom_attributes["departures"]
        
        return departures

    def get_api_for_globalid(
        self, name: str, global_id: str, transport_types: str
    ) -> dict:
        """Get departure data from api."""
        url = URL.format(global_id, transport_types)
        headers = {}
        headers["User-Agent"] = USER_AGENT

        try:
            # Use requests library to simplify http request
            req = requests.get(url, headers=headers, timeout=10)
            if req.ok:
                return req.json()
            else:
                pass
        except Timeout as ex:
            _LOGGER.error(
                "AnotherMVG: Timeout while connecting to the MVG API for globalid %s - %s - This usually happens if MVG API not available or your internet connection is down. We can do nothing. Normally it will be fixed by its own.",
                global_id,
                name,
            )
            raise MVGException(
                f"AnotherMVG: Timeout while connecting to the MVG API for globalid {global_id} - {name} - This usually happens if MVG API not available or your internet connection is down. We can do nothing. Normally it will be fixed by its own."
            ) from ex
        except HTTPError as ex:
            _LOGGER.error(
                "AnotherMVG: HTTP Connection Problem for globalid %s - %s - %s - This usually happens if MVG API is rejecting the request. We can do nothing. Normally it will be fixed by its own.", global_id, name, str(ex)
            )
            raise MVGException(
                f"AnotherMVG: HTTP Connection Problem for globalid {global_id} - {name} - This usually happens if MVG API is rejecting your request. We can do nothing. Normally it will be fixed by its own."
            ) from ex
        except Exception as ex:
            _LOGGER.error(
                "AnotherMVG: Other problem while connecting to the MVG API for %s - %s - %s",
                global_id,
                name,
                str(ex),
            )
            raise MVGException(
                f"AnotherMVG: Other problem while connecting to the MVG API for {global_id} - {name}"
            ) from ex

