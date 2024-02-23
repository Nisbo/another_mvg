"""Platform for sensor integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
import time
from zoneinfo import ZoneInfo

import requests
from requests import HTTPError, Timeout
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_DOUBLESTATIONNUMBER,
    CONF_GLOBALID,
    CONF_GLOBALID2,
    CONF_HIDEDESTINATION,
    CONF_HIDENAME,
    CONF_LIMIT,
    CONF_ONLYLINE,
    CONF_TIMEZONE_FROM,
    CONF_TIMEZONE_TO,
    CONF_TRANSPORTTYPES,
    URL,
    USER_AGENT,
    MVGException,
)

# integration imports end

DEFAULT_HIDEDESTINATION = ""
DEFAULT_ONLYLINE = ""
DEFAULT_LIMIT = 6
DEFAULT_CONF_DOUBLESTATIONNUMBER = ""
DEFAULT_CONF_TRANSPORTTYPES = "SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS"
DEFAULT_CONF_GLOBALID2 = ""
DEFAULT_TIMEZONE_FROM = "Europe/Berlin"  # or UTC
DEFAULT_TIMEZONE_TO = "Europe/Berlin"
DEFAULT_HIDENAME = False

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_GLOBALID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_ONLYLINE, default=DEFAULT_ONLYLINE): cv.string,
        vol.Optional(CONF_HIDEDESTINATION, default=DEFAULT_HIDEDESTINATION): cv.string,
        vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): cv.positive_int,
        vol.Optional(
            CONF_DOUBLESTATIONNUMBER, default=DEFAULT_CONF_DOUBLESTATIONNUMBER
        ): cv.string,
        vol.Optional(
            CONF_TRANSPORTTYPES, default=DEFAULT_CONF_TRANSPORTTYPES
        ): cv.string,
        vol.Optional(CONF_GLOBALID2, default=DEFAULT_CONF_GLOBALID2): cv.string,
        vol.Optional(CONF_HIDENAME, default=DEFAULT_HIDENAME): cv.boolean,
        vol.Optional(CONF_TIMEZONE_FROM, default=DEFAULT_TIMEZONE_FROM): cv.string,
        vol.Optional(CONF_TIMEZONE_TO, default=DEFAULT_TIMEZONE_TO): cv.string,
    }
)


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


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    add_entities([ConnectionInfo(hass, config)], True)


class ConnectionInfo(SensorEntity):
    """Class for MVG info."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialise."""
        self._onlyline = config[CONF_ONLYLINE]
        self._limit = config[CONF_LIMIT]
        self._hidedestination = config[CONF_HIDEDESTINATION]
        self._globalid = config[CONF_GLOBALID]
        self._globalid2 = config[CONF_GLOBALID2]
        self._name = config[CONF_NAME]
        self._hass = hass
        self._doublestationnumber = config[CONF_DOUBLESTATIONNUMBER]
        self._transporttypes = config[CONF_TRANSPORTTYPES]
        self._hidename = config[CONF_HIDENAME]
        self._timezoneFrom = config[CONF_TIMEZONE_FROM]
        self._timezoneTo = config[CONF_TIMEZONE_TO]
        self._custom_attributes = {
            "config": {"name": self._name, "hide_name": self._hidename}
        }

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        _LOGGER.warning(self._custom_attributes)
        return self._custom_attributes

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._globalid.replace(":", "") + self._doublestationnumber

    @property
    def native_value(self):
        """Return native value."""
        return "Please use the project lovelace card"

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        self._custom_attributes["departures"] = self.get_departures()

    def convert_timestamp_timezone(
        self,
        timestamp: int,
        from_timezone: str,
        to_timezone: str,
        output_format: str = "",
    ) -> datetime:
        """Convert epoch to timezone datetime."""
        dt = datetime.fromtimestamp(timestamp).replace(tzinfo=ZoneInfo(from_timezone))
        if output_format:
            return dt.replace(tzinfo=ZoneInfo(to_timezone)).strftime(format)
        return dt.replace(tzinfo=ZoneInfo(to_timezone))

    def get_departures(self) -> str:
        """Get departure data."""

        # check if self._hass.custom_attributes is set to avoid undefined messages if the API is down
        if not self._custom_attributes:
            self._custom_attributes = "Try to connect to the MVG API. If this message remains longer, maybe mvg.de is down."

        # 1st API call for globalid1
        try:
            data = self.get_api_for_globalid(
                self._name, self._globalid, self._transporttypes
            )
        except MVGException as ex:
            return ex

        # 2nd API call for globalid2
        if self._globalid2:
            # wait 1 second because of 509 error
            time.sleep(1)
            try:
                data2 = self.get_api_for_globalid(
                    self._name, self._globalid2, self._transporttypes
                )
            except MVGException as ex:
                return ex
            if data:
                data.extend(data2)

        sorted_data = sorted(data, key=lambda x: x["plannedDepartureTime"])
        return self.pre_process_output(sorted_data)

    def pre_process_output(self, data: dict) -> dict:
        """Preformat necessary values into list of Departure."""
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

            # Format platform
            if departure["transportType"] in ["BUS", "REGIONAL_BUS"]:
                track = "Bus"
            elif "platform" in departure:
                track = str(departure["platform"])
            else:
                # Der Schlüssel 'platform' existiert nicht im Dictionary user
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

            if len(departures) >= self._limit:
                break
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
                "Timeout beim Verbinden mit der URL für globalid %s - %s",
                global_id,
                name,
            )
            raise MVGException(
                f"Timeout beim Verbinden mit der URL für globalid - {name}"
            ) from ex
        except HTTPError as ex:
            _LOGGER.error(
                "Connection Problem globalid %s - %s - %s", global_id, name, str(ex)
            )
            raise MVGException(
                f"Connection Problem globalid {global_id} - {name}"
            ) from ex
        except Exception as ex:
            _LOGGER.error(
                "Anderes Problem bei der Verbindung mit globalid %s - %s - %s",
                global_id,
                name,
                str(ex),
            )
            raise MVGException(
                f"Anderes Problem bei der Verbindung mit globalid {global_id} - {name}"
            ) from ex
