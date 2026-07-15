"""Platform for sensor integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import logging
import re
import time
import requests
import asyncio
import aiohttp
from requests import HTTPError, Timeout
import urllib.parse
import voluptuous as vol
from homeassistant.components import mqtt
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry

from .const import (
    DOMAIN,
    CONF_MONITOR_TYPE,
    CONF_ALERT_FOR,
    CONF_STATS_TEMPLATE,
    CONF_DOUBLESTATIONNUMBER,
    CONF_GLOBALID,
    CONF_GLOBALID2,
    CONF_HIDEDESTINATION,
    CONF_ONLYDESTINATION,
    CONF_LIMIT,
    CONF_ONLYLINE,
    CONF_TIMEZONE_FROM,
    CONF_TIMEZONE_TO,
    CONF_TRANSPORTTYPES,
    CONF_INCREASED_LIMIT,
    CONF_SORT_BY_REAL_DEPARTURE,
    CONF_OFFSET_IN_MINUTES,
    CONF_PROXY_URL,
    CONF_PROXY_USETIME,
    CONF_FORCE_PROXY,
    CONF_CSS_CODE,
    CONF_CSS_CODE_DARKMODE_ONLY,
    CONF_MQTT_ENABLED,
    CONF_MQTT_TOPIC_PREFIX,
    CONF_MQTT_RETAIN,
    CONF_MQTT_QOS,
    CONF_UPDATE_MODE,
    URL,
    URL_EFA_ARRIVALS,
    USER_AGENT,
    MVGException,
    DEFAULT_MONITOR_TYPE,
    MONITOR_TYPE_ARRIVAL,
    DEFAULT_ONLYLINE,
    DEFAULT_HIDEDESTINATION,
    DEFAULT_ONLYDESTINATION,
    DEFAULT_LIMIT,
    DEFAULT_CONF_TRANSPORTTYPES,
    DEFAULT_CONF_GLOBALID2,
    DEFAULT_TIMEZONE_FROM,
    DEFAULT_TIMEZONE_TO,
    DEFAULT_ALERT_FOR,
    DEFAULT_STATS_TEMPLATE,
    DEFAULT_INCREASED_LIMIT,
    DEFAULT_SORT_BY_REAL_DEPARTURE,
    DEFAULT_OFFSET_IN_MINUTES,
    DEFAULT_PROXY_URL,
    DEFAULT_PROXY_USETIME,
    DEFAULT_FORCE_PROXY,
    DEFAULT_CSS_CODE,
    DEFAULT_CSS_CODE_DARKMODE_ONLY,
    DEFAULT_MQTT_ENABLED,
    DEFAULT_MQTT_TOPIC_PREFIX,
    DEFAULT_MQTT_RETAIN,
    DEFAULT_MQTT_QOS,
    DEFAULT_UPDATE_MODE,
    UPDATE_MODE_AUTO,
    UPDATE_MODE_MANUAL,
)

# integration imports end

_LOGGER = logging.getLogger(__name__)

# time intervall between the updates
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_GLOBALID): cv.string,
        vol.Optional(CONF_MONITOR_TYPE, default=DEFAULT_MONITOR_TYPE): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_ONLYLINE, default=DEFAULT_ONLYLINE): cv.string,
        vol.Optional(CONF_HIDEDESTINATION, default=DEFAULT_HIDEDESTINATION): cv.string,
        vol.Optional(CONF_ONLYDESTINATION, default=DEFAULT_ONLYDESTINATION): cv.string,
        vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): cv.positive_int,
        vol.Optional(CONF_DOUBLESTATIONNUMBER, default=""): cv.string,
        vol.Optional(CONF_TRANSPORTTYPES, default=DEFAULT_CONF_TRANSPORTTYPES): cv.string,
        vol.Optional(CONF_GLOBALID2, default=DEFAULT_CONF_GLOBALID2): cv.string,
        vol.Optional(CONF_TIMEZONE_FROM, default=DEFAULT_TIMEZONE_FROM): cv.string,
        vol.Optional(CONF_TIMEZONE_TO, default=DEFAULT_TIMEZONE_TO): cv.string,
        vol.Optional(CONF_ALERT_FOR, default=DEFAULT_ALERT_FOR): cv.string,
        vol.Optional(CONF_STATS_TEMPLATE, default=DEFAULT_STATS_TEMPLATE): cv.string,
        vol.Optional(CONF_INCREASED_LIMIT, default=DEFAULT_INCREASED_LIMIT): cv.positive_int,
        vol.Optional(CONF_SORT_BY_REAL_DEPARTURE, default=DEFAULT_SORT_BY_REAL_DEPARTURE): cv.boolean,
        vol.Optional(CONF_OFFSET_IN_MINUTES, default=DEFAULT_OFFSET_IN_MINUTES): cv.positive_int,
        vol.Optional(CONF_PROXY_URL, default=DEFAULT_PROXY_URL): cv.string,
        vol.Optional(CONF_PROXY_USETIME, default=DEFAULT_PROXY_USETIME): cv.positive_int,
        vol.Optional(CONF_FORCE_PROXY, default=DEFAULT_FORCE_PROXY): cv.boolean,
        vol.Optional(CONF_CSS_CODE, default=DEFAULT_CSS_CODE): cv.string,
        vol.Optional(CONF_CSS_CODE_DARKMODE_ONLY, default=DEFAULT_CSS_CODE_DARKMODE_ONLY): cv.boolean,
        vol.Optional(CONF_MQTT_ENABLED, default=DEFAULT_MQTT_ENABLED): cv.boolean,
        vol.Optional(CONF_MQTT_TOPIC_PREFIX, default=DEFAULT_MQTT_TOPIC_PREFIX): cv.string,
        vol.Optional(CONF_MQTT_RETAIN, default=DEFAULT_MQTT_RETAIN): cv.boolean,
        vol.Optional(CONF_MQTT_QOS, default=DEFAULT_MQTT_QOS): vol.All(vol.Coerce(int), vol.Range(min=0, max=2)),
        vol.Optional(CONF_UPDATE_MODE, default=DEFAULT_UPDATE_MODE): cv.string,
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
    
    entity = ConnectionInfo(hass, config_entry)
    hass.data.setdefault(DOMAIN, {}).setdefault("entities", {})[config_entry.entry_id] = entity
    async_add_entities([entity])


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
    time_diff: int

    def to_dict(self):
        """Convert Departure object to a dictionary for JSON serialization."""
        return {
            "transport_type": self.transport_type,
            "label": self.label,
            "destination": self.destination,
            "track": self.track,
            "planned_departure": self.planned_departure,
            "expected_departure": self.expected_departure,
            "cancelled": self.cancelled,
            "delay": self.delay,
            "trainType": self.trainType,
            "time_diff": self.time_diff,
        }


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
        self._monitor_type = config_data.get(CONF_MONITOR_TYPE, DEFAULT_MONITOR_TYPE)
        self._update_mode = config_data.get(CONF_UPDATE_MODE, DEFAULT_UPDATE_MODE)
        self._limit = self.normalize_api_limit(config_data.get(CONF_LIMIT, DEFAULT_LIMIT))
        self._hidedestination = config_data.get(CONF_HIDEDESTINATION)
        self._onlydestination = config_data.get(CONF_ONLYDESTINATION)
        self._globalid = config_data.get(CONF_GLOBALID)
        self._globalid2 = config_data.get(CONF_GLOBALID2)
        self._name = config_data.get(CONF_NAME)
        self._transporttypes = config_data.get(CONF_TRANSPORTTYPES)
        self._css_code = config_data.get(CONF_CSS_CODE, DEFAULT_CSS_CODE)
        self._css_code_darkmode_only = config_data.get(CONF_CSS_CODE_DARKMODE_ONLY, DEFAULT_CSS_CODE_DARKMODE_ONLY)
        self._mqtt_enabled = config_data.get(CONF_MQTT_ENABLED, DEFAULT_MQTT_ENABLED)
        self._mqtt_topic_prefix = self.normalize_mqtt_topic_prefix(
            config_data.get(CONF_MQTT_TOPIC_PREFIX, DEFAULT_MQTT_TOPIC_PREFIX)
        )
        self._mqtt_retain = config_data.get(CONF_MQTT_RETAIN, DEFAULT_MQTT_RETAIN)
        self._mqtt_qos = min(2, max(0, self.normalize_non_negative_int(
            config_data.get(CONF_MQTT_QOS, DEFAULT_MQTT_QOS),
            DEFAULT_MQTT_QOS,
        )))
        self._mqtt_publish_warning_logged = False
        self._sort_by_real_departure = config_data.get(CONF_SORT_BY_REAL_DEPARTURE, DEFAULT_SORT_BY_REAL_DEPARTURE)
        self._stats_template = config_data.get(CONF_STATS_TEMPLATE, DEFAULT_STATS_TEMPLATE)
        self._timezoneFrom = config_data.get(CONF_TIMEZONE_FROM)
        self._timezoneTo = config_data.get(CONF_TIMEZONE_TO)
        self._alert_for = config_data.get(CONF_ALERT_FOR)
        self._lateConnections = []
        self._nextDeparture = ""
        self._dataOutdated = ""
        self._maxConnectionErrorTime = 0
        self._offsetInMinutes = config_data.get(CONF_OFFSET_IN_MINUTES, DEFAULT_OFFSET_IN_MINUTES)
        self._proxyURL = config_data.get(CONF_PROXY_URL, DEFAULT_PROXY_URL)
        self._proxyUsetime = config_data.get(CONF_PROXY_USETIME, DEFAULT_PROXY_USETIME)
        self._forceProxy = config_data.get(CONF_FORCE_PROXY, DEFAULT_FORCE_PROXY)
        self._increased_limit = self.normalize_non_negative_int(
            config_data.get(CONF_INCREASED_LIMIT, DEFAULT_INCREASED_LIMIT),
            DEFAULT_INCREASED_LIMIT,
        )
        self._custom_attributes = {
            "config": {
                "name": self._name, 
                "unique_id": self._unique_id,
                "monitor_type": self._monitor_type,
                "update_mode": self._update_mode,
                "mqtt_enabled": self._mqtt_enabled,
                "mqtt_topic_prefix": self._mqtt_topic_prefix,
                "mqtt_retain": self._mqtt_retain,
                "mqtt_qos": self._mqtt_qos,
                "css_code": self._css_code,
                "css_code_darkmode_only": self._css_code_darkmode_only
            }
        }
        self._custom_attributes["monitor_type"] = self._monitor_type
        self._custom_attributes["update_mode"] = self._update_mode

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def should_poll(self) -> bool:
        """Return true if Home Assistant should poll this sensor automatically."""
        return self._update_mode == UPDATE_MODE_AUTO

    @staticmethod
    def normalize_api_limit(value, default: int = DEFAULT_LIMIT) -> int:
        """Return an API request limit clamped to the supported range."""
        try:
            limit = int(value)
        except (TypeError, ValueError):
            limit = default
        return max(1, min(80, limit))

    @staticmethod
    def normalize_non_negative_int(value, default: int = 0) -> int:
        """Return a non-negative integer from config values."""
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = default
        return max(0, number)

    @staticmethod
    def normalize_mqtt_topic_prefix(value) -> str:
        """Return a publishable MQTT topic prefix."""
        topic = str(value or "").strip()
        if (
            not topic
            or topic.startswith("/")
            or topic.endswith("/")
            or "//" in topic
            or not all(
                char.isascii() and (char.isalnum() or char in "._-/")
                for char in topic
            )
        ):
            return DEFAULT_MQTT_TOPIC_PREFIX
        return topic

    @staticmethod
    def sanitize_mqtt_topic_part(value: str) -> str:
        """Return a safe MQTT topic segment based on a Home Assistant entity id."""
        raw_value = str(value or "").strip()
        object_id = raw_value.split(".", 1)[1] if "." in raw_value else raw_value
        topic_part = re.sub(r"[^A-Za-z0-9_-]+", "_", object_id)
        return topic_part.strip("_") or "unknown"

    @property
    def mqtt_topic(self) -> str:
        """Return the MQTT topic for this sensor."""
        entity_part = self.sanitize_mqtt_topic_part(
            self.entity_id or self._unique_id or self._name
        )
        return f"{self._mqtt_topic_prefix}/{entity_part}/state"

    def get_request_limit(self) -> int:
        """Return the effective API request limit, including the optional buffer."""
        return self.normalize_api_limit(self._limit + self._increased_limit, self._limit)

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
    def maxConnectionErrorTime(self):
        """Getter-Method"""
        return self._maxConnectionErrorTime

    @maxConnectionErrorTime.setter
    def maxConnectionErrorTime(self, value):
        """Setter-Method"""
        self._maxConnectionErrorTime = value

    @property
    def lateConnections(self):
        """Getter for lateConnections"""
        return self._lateConnections

    @lateConnections.setter
    def lateConnections(self, value):
        if not isinstance(value, list):
            _LOGGER.error(
                "AnotherMVG: Unable to set lateConnections for %s - Value must be a list. Received: %s ",
                self._name,
                repr(value),
            )
            return  
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
        
        # defice transport_type
        transport_type_text = ""
        if transport_type not in ["SBAHN", "UBAHN"]:
            transport_type_text = f"{readable_transport_type} "
        
        # check if transport_type = "BAHN" and label contains only digits
        if transport_type == "BAHN" and label.replace(" ", "").isdigit():
            transport_type_text = trainType
        
        if transport_type == "BAHN" and not label.replace(" ", "").isdigit():
            transport_type_text = ""
        
        # accouncements
        announcement = ""
        
        # check if cancelled
        if cancelled:
            value   = f"{transport_type_text}{label} nach {destination}, planmäßige Abfahrt um {planned_departure} entfällt."
            valueEN = f"{transport_type_text}{label} to {destination}, scheduled departure at {planned_departure} is cancelled."
        else:
            if planned_departure != expected_departure:
                # singular or plural
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
  
    async def async_update(self) -> None:
        self._custom_attributes["monitor_type"] = self._monitor_type
        self._custom_attributes["config"]["monitor_type"] = self._monitor_type
        self._custom_attributes["update_mode"] = self._update_mode
        self._custom_attributes["config"]["update_mode"] = self._update_mode
        self._custom_attributes["departures"] = [
            departure.to_dict() if isinstance(departure, Departure) else departure
            for departure in await self.get_departures()
        ]
        
        self._custom_attributes["dataOutdated"] = self._dataOutdated
        self._custom_attributes["maxConnectionErrorTime"] = self._maxConnectionErrorTime
        self.process_late_connections()
        await self.async_publish_mqtt()

    async def async_manual_refresh(self) -> None:
        """Refresh this sensor when it is configured for manual updates."""
        if self._update_mode != UPDATE_MODE_MANUAL:
            _LOGGER.warning(
                "AnotherMVG: Manual refresh requested for %s, but the sensor is in automatic update mode.",
                self._name,
            )
            return

        await self.async_update()
        self.async_write_ha_state()

    async def async_publish_mqtt(self) -> None:
        """Publish the current monitor data through Home Assistant MQTT."""
        if not self._mqtt_enabled:
            return

        payload = {
            "name": self._name,
            "entity_id": self.entity_id,
            "unique_id": self._unique_id,
            "topic": self.mqtt_topic,
            "monitor_type": self._monitor_type,
            "state": self.native_value,
            "dataOutdated": self._dataOutdated,
            "maxConnectionErrorTime": self._maxConnectionErrorTime,
            "departures": self._custom_attributes.get("departures", []),
        }

        try:
            await mqtt.async_publish(
                self._hass,
                self.mqtt_topic,
                json.dumps(payload, ensure_ascii=False),
                qos=self._mqtt_qos,
                retain=self._mqtt_retain,
            )
            self._mqtt_publish_warning_logged = False
        except Exception as err:
            if not self._mqtt_publish_warning_logged:
                _LOGGER.warning(
                    "AnotherMVG: MQTT publish for %s failed. Is the Home Assistant MQTT integration configured? Error: %s",
                    self._name,
                    err,
                )
                self._mqtt_publish_warning_logged = True

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
        
    async def get_departures(self) -> str:
        """Get departure data."""
        if self._monitor_type == MONITOR_TYPE_ARRIVAL:
            return await self.get_arrivals()

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
                    time_diff=0,
                )
            )
            self._custom_attributes["departures"] = departures

        # 1st API call for globalid1
        try:
            request_limit = self.get_request_limit()
            data = await self.get_api_for_globalid(
                self._name, self._globalid, self._offsetInMinutes, self._transporttypes, request_limit
            )

            # If data is empty, check if there are results for the next day
            if not data or len(data) < request_limit:
                data = await self.fetch_additional_data_for_next_day(data, self._name, self._globalid, self._transporttypes, request_limit)

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
                        time_diff=0,
                    )
                )
                self._custom_attributes["departures"] = departures
            
            return self._custom_attributes["departures"]

        # 2nd API call for globalid2
        if self._globalid2:
            # wait 1 second because of 509 error
            await asyncio.sleep(1)
            try:
                request_limit = self.get_request_limit()
                data2 = await self.get_api_for_globalid(
                    self._name, self._globalid2, self._offsetInMinutes, self._transporttypes, request_limit
                )

                # If data2 is empty, check if there are results for the next day
                if not data2 or len(data2) < request_limit:  # Überprüft, ob die Liste leer ist
                    data2 = await self.fetch_additional_data_for_next_day(data2, self._name, self._globalid2, self._transporttypes, request_limit)

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
                            time_diff=0,
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
            elif data2:
                data = list(data2)
        
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

    async def fetch_additional_data_for_next_day(self, data, name, globalid, transporttypes, request_limit):
        # wait 1 second because of 509 error
        await asyncio.sleep(1)

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
        additional_data = await self.get_api_for_globalid(name, globalid, minutes_to_midnight, transporttypes, request_limit)

        # merge it
        if additional_data:
            data.extend(additional_data)

        return data

    def pre_process_output(self, data: list) -> list:
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
        final_departure = None  # Variable for next departure
        
        for departure in sorted_data:
            # if self._onlyline is set, check if it is the correct line
            if self._onlyline != "" and departure["label"] not in self._onlyline.split(","):
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
                track = "---"
            
            planned_departure = self.convert_timestamp_timezone(
                departure["plannedDepartureTime"] / 1000,
                self._timezoneFrom,
                self._timezoneTo,
                "%H:%M",
            )
    
            expected_departure = self.convert_timestamp_timezone(
                departure["realtimeDepartureTime"] / 1000,
                self._timezoneFrom,
                self._timezoneTo,
                "%H:%M",
            )
            
            transport_type = departure["transportType"]
            label = departure["label"]
            destination = departure["destination"]
            cancelled = departure["cancelled"]
            delay = departure.get("delayInMinutes", 0)
            trainType = departure["trainType"]
            
            current_time = datetime.utcnow()
            time_diff = datetime.utcfromtimestamp(departure["realtimeDepartureTime"] / 1000) - current_time
            
            # already departed
            if time_diff.total_seconds() < 0:
                continue
            
            if (
                (lastRealtimeDepartureTime == 0 and time_diff.total_seconds() > 0) or
                (departure["realtimeDepartureTime"] < lastRealtimeDepartureTime and time_diff.total_seconds() > 0)
            ):
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
                    time_diff=round(time_diff.total_seconds()),
                )
            )
    
            if departure["label"] in counter_dict:
                counter_dict[departure["label"]] += 1
                label = departure["label"]
    
                # alarm 1, 2, 3
                if counter_dict[label] in (1, 2, 3):
                    alarmStatus = 0
    
                    # Delay
                    if "delayInMinutes" in departure and departure["delayInMinutes"] is not None and departure["delayInMinutes"] > 0:
                        alarmStatus = departure.get("delayInMinutes", 0)
    
                    # Cancelled
                    if not departure["cancelled"]:
                        pass
                    else:
                        alarmStatus = -1
                    
                    connectioninfos.append(
                        DepartureAlarms(
                            label=departure["label"],
                            number=counter_dict[label],
                            delayInMinutes=alarmStatus,
                        )
                    )
            
            if len(departures) >= self._limit:
                break
        
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

    async def get_arrivals(self) -> list:
        """Get arrival data from the MVV/EFA API and normalize it for the cards."""
        if not self._custom_attributes or not self._custom_attributes.get("departures"):
            self._custom_attributes["departures"] = [
                Departure(
                    transport_type="BUS",
                    label="ERROR",
                    destination="Try to connect to the MVV/EFA API. If this message remains longer, maybe mvv-muenchen.de is down.",
                    track="---",
                    planned_departure="---",
                    expected_departure="---",
                    cancelled=False,
                    delay=0,
                    trainType="",
                    time_diff=0,
                )
            ]

        try:
            request_limit = self.get_request_limit()
            data = await self.get_efa_arrivals_for_globalid(
                self._name,
                self._globalid,
                request_limit,
            )
        except MVGException:
            self._dataOutdated = " - nicht aktuell"
            _LOGGER.debug("AnotherMVG: Reusing previous arrival data for %s after EFA request failed", self._name)
            return self._custom_attributes["departures"]

        if self._globalid2:
            await asyncio.sleep(1)
            try:
                data2 = await self.get_efa_arrivals_for_globalid(
                    self._name,
                    self._globalid2,
                    request_limit,
                )
            except MVGException:
                self._dataOutdated = " - nicht aktuell"
                _LOGGER.debug(
                    "AnotherMVG: Reusing previous arrival data for %s after second EFA request failed",
                    self._name,
                )
                return self._custom_attributes["departures"]

            if data:
                try:
                    data.extend(data2)
                    _LOGGER.debug(
                        "AnotherMVG: Combined EFA arrivals for %s from globalid1 %s and globalid2 %s",
                        self._name,
                        self._globalid,
                        self._globalid2,
                    )
                except Exception as ex:
                    _LOGGER.error(
                        "AnotherMVG: Unable to combine EFA arrival data from globalid1 with globalid2 for %s - %s",
                        self._name,
                        str(ex),
                    )
                    self._dataOutdated = " - nicht aktuell"
                    return self._custom_attributes["departures"]
            elif data2:
                data = list(data2)

        try:
            sorted_data = sorted(
                data,
                key=lambda x: x.get("arrivalTimeEstimated") or x.get("arrivalTimePlanned") or "",
            )
        except Exception as ex:
            _LOGGER.error(
                "AnotherMVG: Unable to sort EFA arrivals for %s - %s",
                self._name,
                str(ex),
            )
            self._dataOutdated = " - nicht aktuell"
            return self._custom_attributes["departures"]

        self._dataOutdated = ""
        return self.pre_process_arrival_output(sorted_data)

    def pre_process_arrival_output(self, data: list) -> list:
        """Normalize EFA stopEvents into the existing departure card payload."""
        departures = []
        connectioninfos = []
        verbindungen_list = self._alert_for.split(",") if self._alert_for else []
        counter_dict = {wert: 0 for wert in verbindungen_list}
        final_departure = None

        transport_types = [
            item.strip().upper()
            for item in (self._transporttypes or DEFAULT_CONF_TRANSPORTTYPES).split(",")
            if item.strip()
        ]

        for event in data:
            transportation = event.get("transportation") or {}
            location = event.get("location") or {}
            product = transportation.get("product") or {}

            transport_type = self.map_efa_transport_type(product, transportation)
            label = transportation.get("number") or transportation.get("name") or ""
            origin = self.get_efa_origin(event, transportation)
            display_destination = origin or "---"
            track = self.get_efa_track(location, transport_type)

            if transport_types and transport_type not in transport_types:
                continue

            if self._onlyline != "" and label not in self._onlyline.split(","):
                continue

            if (
                self._hidedestination != ""
                and display_destination.lower() in self._hidedestination.lower()
            ):
                continue

            if (
                self._onlydestination != ""
                and display_destination.lower() not in self._onlydestination.lower()
            ):
                continue

            planned_ms = self.efa_time_to_ms(event.get("arrivalTimePlanned"))
            expected_ms = self.efa_time_to_ms(
                event.get("arrivalTimeEstimated") or event.get("arrivalTimePlanned")
            )

            if not planned_ms or not expected_ms:
                _LOGGER.debug(
                    "AnotherMVG: Skipping EFA arrival for %s because planned/expected time is missing: %s",
                    self._name,
                    event,
                )
                continue

            planned_departure = self.convert_timestamp_timezone(
                planned_ms / 1000,
                "UTC",
                self._timezoneTo,
                "%H:%M",
            )
            expected_departure = self.convert_timestamp_timezone(
                expected_ms / 1000,
                "UTC",
                self._timezoneTo,
                "%H:%M",
            )

            current_time = datetime.utcnow()
            time_diff = datetime.utcfromtimestamp(expected_ms / 1000) - current_time
            if time_diff.total_seconds() < 0:
                continue

            delay = max(0, round((expected_ms - planned_ms) / 60000))
            realtime_status = event.get("realtimeStatus") or []
            if isinstance(realtime_status, str):
                realtime_status = [realtime_status]
            cancelled = "TRIP_CANCELLED" in realtime_status or "ARRIVAL_CANCELLED" in realtime_status
            trainType = ""

            if final_departure is None:
                final_departure = {
                    "planned_departure": planned_departure,
                    "expected_departure": expected_departure,
                    "track": track,
                    "transport_type": transport_type,
                    "label": label,
                    "destination": display_destination,
                    "cancelled": cancelled,
                    "delay": delay,
                    "trainType": trainType,
                    "plannedDepartureTime": planned_ms,
                    "realtimeDepartureTime": expected_ms,
                }

            departures.append(
                Departure(
                    transport_type=transport_type,
                    label=label,
                    destination=display_destination,
                    track=track,
                    planned_departure=planned_departure,
                    expected_departure=expected_departure,
                    cancelled=cancelled,
                    delay=delay,
                    trainType=trainType,
                    time_diff=round(time_diff.total_seconds()),
                )
            )

            if label in counter_dict:
                counter_dict[label] += 1
                if counter_dict[label] in (1, 2, 3):
                    alarm_status = -1 if cancelled else delay
                    connectioninfos.append(
                        DepartureAlarms(
                            label=label,
                            number=counter_dict[label],
                            delayInMinutes=alarm_status,
                        )
                    )

            if len(departures) >= self._limit:
                break

        if final_departure:
            self.set_next_departure(
                final_departure["planned_departure"],
                final_departure["expected_departure"],
                final_departure["track"],
                final_departure["transport_type"],
                final_departure["label"],
                final_departure["destination"],
                final_departure["cancelled"],
                final_departure["delay"],
                final_departure["trainType"],
                final_departure["plannedDepartureTime"],
                final_departure["realtimeDepartureTime"],
            )

        self.lateConnections = connectioninfos

        if "departures" in self._custom_attributes and len(departures) == 0:
            self._dataOutdated = " - nicht aktuell"
            return self._custom_attributes["departures"]

        _LOGGER.debug("AnotherMVG: Normalized %s EFA arrivals for %s", len(departures), self._name)
        return departures

    def efa_time_to_ms(self, value: str | None) -> int | None:
        """Convert an EFA ISO timestamp to epoch milliseconds."""
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return round(dt.timestamp() * 1000)
        except ValueError:
            _LOGGER.debug("AnotherMVG: Unable to parse EFA timestamp %s", value)
            return None

    def get_efa_track(self, location: dict, transport_type: str) -> str:
        """Return platform information from an EFA location."""
        properties = location.get("properties") or {}
        track = (
            properties.get("platformName")
            or properties.get("plannedPlatformName")
            or properties.get("platform")
            or ""
        )
        if isinstance(track, str):
            normalized_track = track.strip()
            track_match = re.search(r"(?:^|\s)(?:Gleis|Gl\.?|Bstg\.?|Steig|Pos\.?|Position)\s*([0-9]+[a-zA-Z]?)\b", normalized_track, re.IGNORECASE)
            if track_match:
                return track_match.group(1)

            normalized_track = re.sub(r"\b(?:Bstg\.?|Steig|Pos\.?|Position)\b", "", normalized_track, flags=re.IGNORECASE).strip()
            if normalized_track:
                return normalized_track
        elif track:
            return str(track)

        if transport_type in ["BUS", "REGIONAL_BUS"]:
            return "Bus"

        return "---"

    def get_efa_origin(self, event: dict, transportation: dict | None = None) -> str:
        """Return the first known stop of an EFA journey."""
        origin = (transportation or {}).get("origin") or {}
        if isinstance(origin, dict) and origin.get("name"):
            return origin.get("name", "")

        previous_locations = event.get("previousLocations") or []
        if previous_locations:
            return previous_locations[0].get("name", "")
        return ""

    def map_efa_transport_type(self, product: dict, transportation: dict) -> str:
        """Map EFA product information to the existing Another MVG transport types."""
        product_name = (product.get("name") or "").lower()
        line_name = (transportation.get("name") or "").lower()
        product_class = product.get("class")
        label = (
            transportation.get("number")
            or transportation.get("disassembledName")
            or transportation.get("name")
            or ""
        ).upper()

        if product_class == 17 or "sev" in product_name or "sev" in line_name:
            if label.startswith("S"):
                return "SBAHN"
            if label.startswith("U"):
                return "UBAHN"
            return "BUS"
        if product_class == 1:
            return "SBAHN"
        if product_class == 2:
            return "UBAHN"
        if product_class == 4:
            return "TRAM"
        if product_class == 5:
            return "BUS"
        if product_class == 6:
            return "REGIONAL_BUS"
        if product_class in [7, 10]:
            return "BUS"
        if product_class in [0, 13, 14, 16]:
            return "BAHN"
        if "s-bahn" in product_name or "s-bahn" in line_name:
            return "SBAHN"
        if "u-bahn" in product_name or "u-bahn" in line_name:
            return "UBAHN"
        if "tram" in product_name or "tram" in line_name:
            return "TRAM"
        if "regional" in product_name and "bus" in product_name:
            return "REGIONAL_BUS"
        if "bus" in product_name or "bus" in line_name:
            return "BUS"
        return "BAHN"

    def get_efa_mot_params(self) -> dict:
        """Build EFA inclMOT parameters from the configured transport types."""
        mot_by_transport_type = {
            "SBAHN": ["1", "17"],
            "UBAHN": ["2", "17"],
            "TRAM": ["4"],
            "BUS": ["5", "7", "10"],
            "REGIONAL_BUS": ["6"],
            "BAHN": ["0", "13"],
        }
        configured_transport_types = [
            item.strip().upper()
            for item in (self._transporttypes or DEFAULT_CONF_TRANSPORTTYPES).split(",")
            if item.strip()
        ]
        mot_values = []
        for transport_type in configured_transport_types:
            mot_values.extend(mot_by_transport_type.get(transport_type, []))

        if not mot_values:
            mot_values = ["0", "1", "2", "4", "5", "6", "7", "10", "13", "17"]

        return {f"inclMOT_{mot}": "true" for mot in sorted(set(mot_values), key=int)}

    async def get_efa_arrivals_for_globalid(self, name: str, global_id: str, limit: int) -> list:
        """Get arrival stopEvents from the MVV/EFA API."""
        headers = {"User-Agent": USER_AGENT}
        dep_sequence = max(1, min(80, limit or DEFAULT_LIMIT))
        params = {
            "calcOneDirection": "1",
            "coordOutputFormat": "WGS84[dd.ddddd]",
            "deleteAssignedStops_dm": "1",
            "depSequence": str(dep_sequence),
            "depType": "stopEvents",
            "doNotSearchForStops": "1",
            "genMaps": "0",
            "imparedOptionsActive": "1",
            "includeCompleteStopSeq": "0",
            "includedMeans": "checkbox",
            "itOptionsActive": "1",
            "itdDateTimeDepArr": "arr",
            "language": "de",
            "locationServerActive": "1",
            "maxTimeLoop": "1",
            "mode": "direct",
            "name_dm": global_id,
            "outputFormat": "rapidJSON",
            "ptOptionsActive": "1",
            "serverInfo": "1",
            "sl3plusDMMacro": "1",
            "type_dm": "any",
            "useAllStops": "1",
            "useProxFootSearch": "0",
            "useRealtime": "1",
            "version": "10.5.17.3",
        }
        params.update(self.get_efa_mot_params())

        _LOGGER.debug(
            "AnotherMVG: Requesting EFA arrivals for %s - %s with limit %s and MOTs %s",
            global_id,
            name,
            dep_sequence,
            {key: value for key, value in params.items() if key.startswith("inclMOT_")},
        )
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(URL_EFA_ARRIVALS, params=params, headers=headers, timeout=10) as req:
                    if req.ok:
                        data = await req.json()
                        events = data.get("stopEvents") or []
                        _LOGGER.debug(
                            "AnotherMVG: EFA returned %s arrivals for %s - %s",
                            len(events),
                            global_id,
                            name,
                        )
                        return events
                    raise MVGException(f"AnotherMVG: EFA request failed with status {req.status} for {global_id} - {name}")
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError as ex:
            _LOGGER.error("AnotherMVG: Timeout while connecting to the MVV/EFA API for globalid %s - %s", global_id, name)
            raise MVGException(f"AnotherMVG: Timeout while connecting to the MVV/EFA API for {global_id} - {name}") from ex
        except aiohttp.ClientError as ex:
            _LOGGER.error("AnotherMVG: HTTP problem while connecting to the MVV/EFA API for globalid %s - %s - %s", global_id, name, str(ex))
            raise MVGException(f"AnotherMVG: HTTP problem while connecting to the MVV/EFA API for {global_id} - {name}") from ex


    async def get_api_for_globalid(self, name: str, global_id: str, offsetInMinutes: int, transport_types: str, limit: int) -> dict:
        """Get departure data from API, fallback to proxy server if needed."""
        request_limit = self.normalize_api_limit(limit)
        url = URL.format(global_id, request_limit, offsetInMinutes, transport_types)
        headers = {"User-Agent": USER_AGENT}

        if self._proxyURL:
            proxy_url = f"{self._proxyURL}?urlToOpen={urllib.parse.quote(url, safe='')}"

        #_LOGGER.error("AnotherMVG: Test for %s - %s value: %s", global_id, name, self._proxyUsetime)
    
        # check if _maxConnectionErrorTime 0 or older than 10 minutes (default)
        #if self._maxConnectionErrorTime == 0 or (time.time() - self._maxConnectionErrorTime) > self._proxyUsetime:
        if not self._forceProxy and (self._maxConnectionErrorTime == 0 or (time.time() - self._maxConnectionErrorTime) > self._proxyUsetime):
            self._maxConnectionErrorTime = 0 # reset
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=10) as req:
                        if req.ok:
                            return await req.json()

            except asyncio.CancelledError:
                raise

            except asyncio.TimeoutError as ex:
                _LOGGER.error("AnotherMVG: Timeout while connecting to the MVG API for globalid %s - %s - This usually happens if MVG API not available or your internet connection is down. This can also happens if MVG API is rejecting your request. We can do nothing. Normally it will be fixed by its own.", global_id, name)
                raise MVGException(f"AnotherMVG: Timeout while connecting to the MVG API for globalid {global_id} - {name} - This usually happens if MVG API not available or your internet connection is down. This can also happens if MVG API is rejecting your request. We can do nothing. Normally it will be fixed by its own.") from ex

            except aiohttp.ClientError as ex:
                _LOGGER.error("AnotherMVG: HTTP Connection Problem (ClientError) for globalid %s - %s - %s - This usually happens if MVG API is rejecting the request. We can do nothing. Normally it will be fixed by its own.", global_id, name, str(ex))
                raise MVGException(f"AnotherMVG: HTTP Connection Problem (ClientError) for globalid {global_id} - {name} - This usually happens if MVG API is rejecting your request. We can do nothing. Normally it will be fixed by its own.") from ex

            except Exception as ex:
                _LOGGER.exception("AnotherMVG: 2. Other problem while connecting to the MVG API for %s - %s", global_id, name)
                if not self._proxyURL:
                    raise MVGException(f"AnotherMVG: Other problem while connecting to the MVG API for {global_id} - {name}") from ex
                # no `raise`, to use the fallback via `mvg.php`
    
        # Fallback to own "Proxy"
        if self._proxyURL:
            try:
                if not self._forceProxy:
                    _LOGGER.warning("AnotherMVG: Proxy as fallback used for %s - %s", global_id, name)
                else:
                    _LOGGER.warning("AnotherMVG: Proxy due to settings as fallback used for %s - %s", global_id, name)

                async with aiohttp.ClientSession() as session:
                    async with session.get(proxy_url, headers=headers, timeout=10) as proxy_req:
                        if not self._forceProxy and self._maxConnectionErrorTime == 0:
                            self._maxConnectionErrorTime = int(time.time())  # set UNIX-Timestamp
                        if proxy_req.ok:
                            return await proxy_req.json()

            except asyncio.CancelledError:
                raise

            except Exception as ex:
                _LOGGER.exception("AnotherMVG: Proxy request failed for %s - %s - %s - Looks like also the Proxy can not reach the API. Maybe the API or the Proxy is down.", global_id, name, str(ex))
                raise MVGException(f"API and proxy failed for {global_id} - {name}") from ex
    
            raise MVGException(f"AnotherMVG: API and proxy failed for {global_id} - {name}")
