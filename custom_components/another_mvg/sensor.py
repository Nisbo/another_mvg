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
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry

from .const import (
    DOMAIN,
    CONF_ALERT_FOR,
    CONF_STATS_TEMPLATE,
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
    CONF_DEPARTURE_FORMAT,
    CONF_INCREASED_LIMIT,
    CONF_SORT_BY_REAL_DEPARTURE,
    URL,
    USER_AGENT,
    MVGException,
    DEFAULT_ONLYLINE,
    DEFAULT_HIDEDESTINATION,
    DEFAULT_ONLYDESTINATION,
    DEFAULT_LIMIT,
    DEFAULT_CONF_TRANSPORTTYPES,
    DEFAULT_CONF_GLOBALID2,
    DEFAULT_HIDENAME,
    DEFAULT_TIMEZONE_FROM,
    DEFAULT_TIMEZONE_TO,
    DEFAULT_ALERT_FOR,
    DEFAULT_STATS_TEMPLATE,
    DEFAULT_SHOW_CLOCK,
    DEFAULT_DEPARTURE_FORMAT,
    DEFAULT_INCREASED_LIMIT,
    DEFAULT_SORT_BY_REAL_DEPARTURE,
)

# integration imports end

_LOGGER = logging.getLogger(__name__)

# time intervall between the updates
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_GLOBALID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_DEPARTURE_FORMAT, default=DEFAULT_DEPARTURE_FORMAT): cv.string,
        vol.Optional(CONF_ONLYLINE, default=DEFAULT_ONLYLINE): cv.string,
        vol.Optional(CONF_HIDEDESTINATION, default=DEFAULT_HIDEDESTINATION): cv.string,
        vol.Optional(CONF_ONLYDESTINATION, default=DEFAULT_ONLYDESTINATION): cv.string,
        vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): cv.positive_int,
        vol.Optional(CONF_DOUBLESTATIONNUMBER, default=""): cv.string,
        vol.Optional(CONF_TRANSPORTTYPES, default=DEFAULT_CONF_TRANSPORTTYPES): cv.string,
        vol.Optional(CONF_GLOBALID2, default=DEFAULT_CONF_GLOBALID2): cv.string,
        vol.Optional(CONF_HIDENAME, default=DEFAULT_HIDENAME): cv.boolean,
        vol.Optional(CONF_TIMEZONE_FROM, default=DEFAULT_TIMEZONE_FROM): cv.string,
        vol.Optional(CONF_TIMEZONE_TO, default=DEFAULT_TIMEZONE_TO): cv.string,
        vol.Optional(CONF_ALERT_FOR, default=DEFAULT_ALERT_FOR): cv.string,
        vol.Optional(CONF_STATS_TEMPLATE, default=DEFAULT_STATS_TEMPLATE): cv.string,
        vol.Optional(CONF_SHOW_CLOCK, default=DEFAULT_SHOW_CLOCK): cv.boolean,
        vol.Optional(CONF_INCREASED_LIMIT, default=DEFAULT_INCREASED_LIMIT): cv.positive_int,
        vol.Optional(CONF_SORT_BY_REAL_DEPARTURE, default=DEFAULT_SORT_BY_REAL_DEPARTURE): cv.boolean,
    }
)

"""Configuration via YAML --> deprecated --> convert everything to GUI"""
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    _LOGGER.warning(
        "Setting up Another MVG sensor using YAML configuration is deprecated and has been removed. "
        "The configuration has been migrated to a config entry. Please remove the YAML configuration and use the integration through the Home Assistant UI."
    )

    # Check if no config entry exists and if configuration.yaml config exists, trigger the import flow.
    found_entry = None
    unique_id_2_check = config.get(CONF_GLOBALID).replace(":", "") + config.get(CONF_DOUBLESTATIONNUMBER)

    gui_entries = hass.config_entries.async_entries(DOMAIN)
    #_LOGGER.warning("AnotherMVG: Found GUI-Entities: %d", len(gui_entries))

    for entry in gui_entries:
        #_LOGGER.warning("AnotherMVG: GUI Entity: %s", entry)
        if entry.unique_id == unique_id_2_check:
            found_entry = entry
            _LOGGER.warning("AnotherMVG: Found already configured GUI-Sensor: %s - skip the import.", entry.title)
            break

            #_LOGGER.warning("AnotherMVG: Found other GUI-Sensor: %s - do nothing", entry.title)

    if found_entry is None:
        _LOGGER.warning("AnotherMVG: The YAML Sensor: %s was converted to a GUI Sensor.", config.get(CONF_NAME))
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_IMPORT}, data=config)
    else:
        _LOGGER.warning("AnotherMVG: nothing left to convert from YAML to GUI, please remove the related YAML code from your configuration.yaml")


"""Configuration via GUI"""
"""Set up Another MVG sensor from a config entry."""   
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Check if there is an unique_id and if not create an unique_id with the old unique_id format to keep the old relations"""
    """From 2.1.0 BETA-3 a new UUID format is used for unique_id and this unique_id will be set during the configuration flow via GUI."""
    """Due to this also CONF_DOUBLESTATIONNUMBER and DEFAULT_CONF_DOUBLESTATIONNUMBER were be removed from the schema, however we have to keep it in the code for compatibility reasons."""
    if not config_entry.unique_id:
        unique_id = config_entry.data[CONF_GLOBALID].replace(":", "") + config_entry.data[CONF_DOUBLESTATIONNUMBER]
        hass.config_entries.async_update_entry(config_entry, unique_id=unique_id)
    
    async_add_entities([ConnectionInfo(hass, config_entry)])


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
    trainType: str

@dataclass
class DepartureAlarms:
    """Class to hold departure alarm data."""
    
    label: str
    number: str
    delayInMinutes: int

class ConnectionInfo(SensorEntity):
    """Class for MVG info."""

    def __init__(self, hass: HomeAssistant, config) -> None:
        """Initialize the MVG sensor."""
        self._hass = hass

        # check if `config` a `config_entry` or a `dict` is
        if hasattr(config, 'data'):
            # GUI-Configuration
            config_data = config.data
            self._unique_id = config.unique_id
        else:
            # YAML-Configuration --> this is deprecated and will be removed soon
            config_data = config
            self._unique_id = config_data[CONF_GLOBALID].replace(":", "") + config_data[CONF_DOUBLESTATIONNUMBER]

        # Log-Configuration (for Debugging)
        #_LOGGER.warning("Config Entry Data: %s", config_data)
        #_LOGGER.warning("Config Entry Options: %s", getattr(config, 'options', None))
        #_LOGGER.warning("Config Entry Unique ID: %s", getattr(config, 'unique_id', None))
        #_LOGGER.warning("Complete Config Entry: %s", config)

        self._onlyline = config_data.get(CONF_ONLYLINE)
        self._limit = config_data.get(CONF_LIMIT)
        self._hidedestination = config_data.get(CONF_HIDEDESTINATION)
        self._onlydestination = config_data.get(CONF_ONLYDESTINATION)
        self._globalid = config_data.get(CONF_GLOBALID)
        self._globalid2 = config_data.get(CONF_GLOBALID2)
        self._name = config_data.get(CONF_NAME)
        self._transporttypes = config_data.get(CONF_TRANSPORTTYPES)
        self._hidename = config_data.get(CONF_HIDENAME)
        self._show_clock = config_data.get(CONF_SHOW_CLOCK, DEFAULT_SHOW_CLOCK)
        self._sort_by_real_departure = config_data.get(CONF_SORT_BY_REAL_DEPARTURE, DEFAULT_SORT_BY_REAL_DEPARTURE)
        self._departure_format = config_data.get(CONF_DEPARTURE_FORMAT, DEFAULT_DEPARTURE_FORMAT)
        self._stats_template = config_data.get(CONF_STATS_TEMPLATE, DEFAULT_STATS_TEMPLATE)
        self._timezoneFrom = config_data.get(CONF_TIMEZONE_FROM)
        self._timezoneTo = config_data.get(CONF_TIMEZONE_TO)
        self._alert_for = config_data.get(CONF_ALERT_FOR)
        self._lateConnections = ""
        self._nextDeparture = ""
        self._dataOutdated = ""
        self._offsetInMinutes = 0
        self._increased_limit = config_data.get(CONF_INCREASED_LIMIT, DEFAULT_INCREASED_LIMIT)
        self._custom_attributes = {
            "config": {
                "name": self._name, 
                "hide_name": self._hidename, 
                "show_clock": self._show_clock, 
                "departure_format": self._departure_format,
                "unique_id": self._unique_id
            }
        }


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
        return self._unique_id

    @property
    def native_value(self):
        """Return native value."""
        return self.nextDeparture #"Please use the project lovelace card to show your stop: " + self._name

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

    @property
    def nextDeparture(self):
        """Getter-Method"""
        return self._nextDeparture

    @nextDeparture.setter
    def nextDeparture(self, value):
        """Setter-Method"""
        self._nextDeparture = value
        

    def set_next_departure(self, planned_departure, expected_departure, track, transport_type, label, destination, cancelled, delay, trainType, plannedDepartureTime, realtimeDepartureTime):
        template = self._stats_template
        
        transport_map = {
            "SBAHN": "S-Bahn",
            "BAHN": "Bahn",
            "UBAHN": "U-Bahn",
            "TRAM": "Tram",
            "BUS": "Bus",
            "REGIONAL_BUS": "Bus"
        }
        
        # realtimeDepartureTime < plannedDepartureTime use plannedDepartureTime
        if realtimeDepartureTime < plannedDepartureTime:
            realtimeDepartureTime = plannedDepartureTime
        
        # if transport_type is not in the map above, use transport_type as value
        readable_transport_type = transport_map.get(transport_type, transport_type)
        
        # make date objects
        planned_departure_datetime = datetime.utcfromtimestamp(plannedDepartureTime / 1000)
        realtime_departure_datetime = datetime.utcfromtimestamp(realtimeDepartureTime / 1000)

        # calculate time diff in minues
        current_time = datetime.utcnow()
        time_diff =  realtime_departure_datetime - current_time
        realtime_departure_diff_minutes = time_diff.total_seconds() / 60  # minutes with decimals
        minutes_difference = int(realtime_departure_diff_minutes)         # round, "cut" the decimals with int

        if track != "Bus" and track != "---":
            trackCheck   = " von Gleis " + track
            trackCheckEN = " from track " + track
        else:
            trackCheck   = ""
            trackCheckEN = ""
        
        # Bestimmen, ob der transport_type angezeigt werden soll
        transport_type_text = ""  # Standardmäßig nichts anzeigen
        if transport_type not in ["SBAHN", "UBAHN"]:
            transport_type_text = f"{readable_transport_type} "
        
        # Überprüfe, ob transport_type = "BAHN" und label nur Zahlen enthält
        if transport_type == "BAHN" and label.replace(" ", "").isdigit():
            transport_type_text = trainType
        
        if transport_type == "BAHN" and not label.replace(" ", "").isdigit():
            transport_type_text = ""
        
        announcement = ""
        
        # check if cancelled
        if cancelled:
            value   = f"{transport_type_text}{label} nach {destination}, planmäßige Abfahrt um {planned_departure} entfällt."
            valueEN = f"{transport_type_text}{label} to {destination}, scheduled departure at {planned_departure} is cancelled."
        else:
            if planned_departure != expected_departure:
                # Bestimmen, ob "Minute" oder "Minuten" angezeigt werden soll
                delay_text   = f"{delay} Minute" if delay == 1 else f"{delay} Minuten"
                delay_textEN = f"{delay} minute" if delay == 1 else f"{delay} minutes"

                value   = f"{transport_type_text}{label} nach {destination}, planmäßige Abfahrt um {planned_departure}, Abfahrt {delay_text} später um {expected_departure}{trackCheck}."
                valueEN = f"{transport_type_text}{label} to {destination}, scheduled departure at {planned_departure}, departure {delay_textEN} later at {expected_departure}{trackCheckEN}."
            else:
                value   = f"{transport_type_text}{label} nach {destination}, planmäßige Abfahrt um {planned_departure}{trackCheck}"
                valueEN = f"{transport_type_text}{label} to {destination}, scheduled departure at {planned_departure}{trackCheckEN}"

        # fill the template with the vaules
        departure_info = template.format(
            planned_departure=planned_departure,
            expected_departure=expected_departure,
            track=track,
            transport_type=readable_transport_type,  # use real name of transport_type 
            label=label,
            destination=destination,
            cancelled=cancelled,
            delay=delay,
            trainType=trainType,
            plannedDepartureTime=planned_departure_datetime.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            realtimeDepartureTime=realtime_departure_datetime.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            realtime_departure_diff_minutes=realtime_departure_diff_minutes,
            minutes_difference=minutes_difference,
            announcement=value,
            announcementEN=valueEN
        )
        
        #_LOGGER.error(
        #         "AnotherMVG: %s --> Template: %s",
        #          self._name,
        #          message,
        #)
        
        self.nextDeparture = departure_info
  
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
        if not self._custom_attributes or not self._custom_attributes.get("departures"):
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
                    trainType="",
                )
            )
            self._custom_attributes["departures"] = departures

        # 1st API call for globalid1
        try:
            data = self.get_api_for_globalid(
                self._name, self._globalid, self._offsetInMinutes, self._transporttypes
            )

            # If data is empty, check if there are results for the next day
            if not data or len(data) < (self._limit + self._increased_limit): 
                data = self.fetch_additional_data_for_next_day(data, self._name, self._globalid, self._transporttypes)


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
                        trainType="",
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
                    self._name, self._globalid2, self._offsetInMinutes, self._transporttypes
                )

                # If data2 is empty, check if there are results for the next day
                if not data2 or len(data2) < (self._limit + self._increased_limit):  # Überprüft, ob die Liste leer ist
                    data2 = self.fetch_additional_data_for_next_day(data2, self._name, self._globalid2, self._transporttypes)

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
                            trainType="",
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




    def fetch_additional_data_for_next_day(self, data, name, globalid, transporttypes):
        # wait 1 second because of 509 error
        time.sleep(1)

        # calculate minutes till midnight
        now = datetime.now()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_to_midnight = (midnight - now).total_seconds()
        minutes_to_midnight = int((seconds_to_midnight + 59) // 60)  # Rundet auf die nächste volle Minute

        if data is None:
            _LOGGER.debug(
                "AnotherMVG: For %s, no data was returned for this day. Current time is %s. Minutes to midnight: %s",
                name,
                now.strftime("%H:%M:%S"),
                minutes_to_midnight,
            )
            data = []  # Initialise `data` as empty list
        else:
            _LOGGER.debug(
                "AnotherMVG: For %s there were only %s results for this day, trying to get results for the next day. Current time is %s. Minutes to midnight: %s",
                name,
                len(data),
                now.strftime("%H:%M:%S"),
                minutes_to_midnight,
            )

        # get additional data from API
        additional_data = self.get_api_for_globalid(name, globalid, minutes_to_midnight, transporttypes)

        # merge it
        if additional_data:
            data.extend(additional_data)

        return data


    def pre_process_output(self, data: dict) -> dict:
        """Preformat necessary values into list of Departure."""
        
        # sort by 'realtimeDepartureTime' asc
        if self._sort_by_real_departure:
            sorted_data = sorted(data, key=lambda x: x["realtimeDepartureTime"], reverse=False)
        else:
            sorted_data = data

        connectioninfos = []
        verbindungen_list = self._alert_for.split(",")
        counter_dict = {wert: 0 for wert in verbindungen_list}
        
        departures = []
        counter = 0
        lastRealtimeDepartureTime = 0
        final_departure = None  # Variable zum Zwischenspeichern der aktuellen Abfahrt
        
        for departure in sorted_data:
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
            
            counter += 1
            
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
                
            planned_departure = self.convert_timestamp_timezone(
                        departure["plannedDepartureTime"] / 1000,
                        self._timezoneFrom,
                        self._timezoneTo,
                        "%H:%M",
                    )

            expected_departure=self.convert_timestamp_timezone(
                        departure["realtimeDepartureTime"] / 1000,
                        self._timezoneFrom,
                        self._timezoneTo,
                        "%H:%M",
                    )
            
            transport_type = departure["transportType"]
            label          = departure["label"]
            destination    = departure["destination"]
            cancelled      = departure["cancelled"]
            delay          = departure.get("delayInMinutes", 0)
            trainType      = departure["trainType"]
            
            #if counter == 1:
                
            current_time = datetime.utcnow()
            time_diff    = datetime.utcfromtimestamp(departure["realtimeDepartureTime"] / 1000) - current_time
            
            # already departured
            if time_diff.total_seconds() < 0:
                continue
            
            #if lastRealtimeDepartureTime == 0 or departure["realtimeDepartureTime"] < lastRealtimeDepartureTime:
            if ((lastRealtimeDepartureTime == 0 and time_diff.total_seconds() > 0) or (departure["realtimeDepartureTime"] < lastRealtimeDepartureTime and time_diff.total_seconds() > 0)):
                # Setze die Abfahrtsdaten in die Zwischenspeicher-Variable
                lastRealtimeDepartureTime = departure["realtimeDepartureTime"]
                final_departure = {
                    'planned_departure': planned_departure,
                    'expected_departure': expected_departure,
                    'track': track,
                    'transport_type': transport_type,
                    'label': label,
                    'destination': destination,
                    'cancelled': cancelled,
                    'delay': delay,
                    'trainType': trainType,
                    'plannedDepartureTime': departure["plannedDepartureTime"],
                    'realtimeDepartureTime': departure["realtimeDepartureTime"]
                }
            
            departures.append(
                Departure(
                    transport_type=transport_type,
                    label=label,
                    destination=destination,
                    track=track,
                    planned_departure=planned_departure,
                    expected_departure=expected_departure,
                    cancelled=cancelled,
                    delay=delay,
                    trainType=trainType,
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
        # Wenn nach der Schleife final_departure gesetzt wurde, dann setze es in Home Assistant
        if final_departure:
            self.set_next_departure(
                final_departure['planned_departure'],
                final_departure['expected_departure'],
                final_departure['track'],
                final_departure['transport_type'],
                final_departure['label'],
                final_departure['destination'],
                final_departure['cancelled'],
                final_departure['delay'],
                final_departure['trainType'],
                final_departure['plannedDepartureTime'],
                final_departure['realtimeDepartureTime']
            )
        self.lateConnections = connectioninfos
        
        # if there was an empty result from the API, return the old value
        if "departures" in self._custom_attributes and len(departures) == 0:
            self._dataOutdated = " - nicht aktuell"
            return self._custom_attributes["departures"]
        
        return departures

    def get_api_for_globalid(
        self, name: str, global_id: str, offsetInMinutes: int, transport_types: str
    ) -> dict:
        """Get departure data from api."""
        url = URL.format(global_id, offsetInMinutes, transport_types)
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

