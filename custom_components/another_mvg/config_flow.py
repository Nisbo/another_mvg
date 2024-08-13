import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
from homeassistant.const import CONF_NAME
from .const import (
    DOMAIN,
    CONF_GLOBALID,
    CONF_ONLYLINE,
    CONF_HIDEDESTINATION,
    CONF_LIMIT,
    CONF_DOUBLESTATIONNUMBER,
    CONF_TRANSPORTTYPES,
    CONF_GLOBALID2,
    CONF_HIDENAME,
    CONF_TIMEZONE_FROM,
    CONF_TIMEZONE_TO,
    CONF_ALERT_FOR,
    DEFAULT_ONLYLINE,
    DEFAULT_HIDEDESTINATION,
    DEFAULT_LIMIT,
    DEFAULT_CONF_DOUBLESTATIONNUMBER,
    DEFAULT_CONF_TRANSPORTTYPES,
    DEFAULT_CONF_GLOBALID2,
    DEFAULT_HIDENAME,
    DEFAULT_TIMEZONE_FROM,
    DEFAULT_TIMEZONE_TO,
    DEFAULT_ALERT_FOR,
)

_LOGGER = logging.getLogger(__name__)

class AnotherMVGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Another MVG integration."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return AnotherMVGOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.warning("async_step_user called with user_input: %s", user_input)

        if user_input is not None:
            # Handle the search if user_input is provided
            return await self.async_step_station_search(user_input)

        # Show the search form if no user input is provided
        return self.async_show_form(
            step_id="station_search",
            data_schema=self._station_search_schema()
        )

    async def async_step_user_config(self, user_input=None):
        """Handle the user configuration step after station search."""
        _LOGGER.warning("async_step_user_config called with user_input: %s", user_input)

        if user_input is not None:
            if not self._is_valid(user_input):
                _LOGGER.warning("Invalid user_input: %s", user_input)
                return self.async_show_form(
                    step_id="user_config",
                    data_schema=self._user_config_schema(user_input),
                    errors={"base": "invalid_input"}
                )
            
            # Convert selected transport types to a comma-separated string
            if CONF_TRANSPORTTYPES in user_input:
                user_input[CONF_TRANSPORTTYPES] = ','.join(user_input[CONF_TRANSPORTTYPES])
            
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input
            )

        # Prepare the schema for user configuration
        return self.async_show_form(
            step_id="user_config",
            data_schema=self._user_config_schema(None)
        )

    def _is_valid(self, user_input):
        """Validate user input."""
        return True

    async def async_step_station_search(self, user_input=None):
        """Handle the station search step."""
        _LOGGER.warning("async_step_station_search called with user_input: %s", user_input)
        
        if user_input is not None:
            station_name = user_input.get("station_name")
            _LOGGER.warning("Searching for station with name: %s", station_name)

            try:
                stations = await self._fetch_stations(station_name)
                _LOGGER.warning("Fetched stations: %s", stations)

                if stations:
                    return self.async_show_form(
                        step_id="user_config",
                        data_schema=self._user_config_schema(stations)
                    )
                else:
                    _LOGGER.warning("No valid stations found for station name: %s", station_name)
                    return self.async_show_form(
                        step_id="station_search",
                        data_schema=self._station_search_schema(),
                        errors={"base": "station_not_found"}
                    )
            except Exception as e:
                _LOGGER.error("Error fetching stations: %s", e)
                return self.async_show_form(
                    step_id="station_search",
                    data_schema=self._station_search_schema(),
                    errors={"base": "api_error"}
                )

        return self.async_show_form(
            step_id="station_search",
            data_schema=self._station_search_schema()
        )

    async def _fetch_stations(self, station_name):
        """Fetch and filter stations for the given station name."""
        _LOGGER.warning("Fetching stations for station name: %s", station_name)
        url = f"https://www.mvg.de/api/fib/v2/location?query={station_name}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.warning("API response: %s", data)
                        # Filter out only entries with transportTypes
                        filtered_stations = [
                            {
                                "name": entry["name"],
                                "transportTypes": ', '.join(entry["transportTypes"]),
                                "globalId": entry["globalId"]
                            }
                            for entry in data
                            if "transportTypes" in entry and entry["type"] == "STATION"
                        ]
                        _LOGGER.warning("Filtered stations: %s", filtered_stations)
                        return filtered_stations
                    else:
                        _LOGGER.error("API request failed with status: %s", response.status)
        except aiohttp.ClientError as e:
            _LOGGER.error("HTTP request error: %s", e)
        except Exception as e:
            _LOGGER.error("Error processing API response: %s", e)

        return []

    def _station_search_schema(self):
        """Return the schema for the station search form."""
        return vol.Schema({
            vol.Required("station_name"): str,
        })

    def _user_config_schema(self, stations):
        """Return the schema for the user configuration form with station options."""
        options = [
            {"label": f"{station['name']} - {station['transportTypes']} ({station['globalId']})", "value": station['globalId']}
            for station in stations
        ]

        return vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_GLOBALID): selector({
                "select": {
                    "options": options
                }
            }),
            vol.Optional(CONF_GLOBALID2, default=DEFAULT_CONF_GLOBALID2): str,
            vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): int,
            vol.Optional(CONF_TRANSPORTTYPES, default=DEFAULT_CONF_TRANSPORTTYPES.split(',')): selector({
                "select": {
                    "options": DEFAULT_CONF_TRANSPORTTYPES.split(','),
                    "multiple": True,
                    "custom_value": True
                }
            }),
            vol.Optional(CONF_ONLYLINE, default=DEFAULT_ONLYLINE): str,
            vol.Optional(CONF_HIDEDESTINATION, default=DEFAULT_HIDEDESTINATION): str,
            vol.Optional(CONF_HIDENAME, default=DEFAULT_HIDENAME): bool,
            vol.Optional(CONF_DOUBLESTATIONNUMBER, default=DEFAULT_CONF_DOUBLESTATIONNUMBER): str,
            vol.Optional(CONF_TIMEZONE_FROM, default=DEFAULT_TIMEZONE_FROM): str,
            vol.Optional(CONF_TIMEZONE_TO, default=DEFAULT_TIMEZONE_TO): str,
            vol.Optional(CONF_ALERT_FOR, default=DEFAULT_ALERT_FOR): str,
        })

class AnotherMVGOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Another MVG."""

    def __init__(self, config_entry):
        """Initialize Another MVG options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Convert selected transport types to a comma-separated string
            if CONF_TRANSPORTTYPES in user_input:
                user_input[CONF_TRANSPORTTYPES] = ','.join(user_input[CONF_TRANSPORTTYPES])

            # Save the updated data
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        # Prepare the default values based on current configuration data
        current_data = self.config_entry.data
        transport_types = DEFAULT_CONF_TRANSPORTTYPES.split(',')
        selected_transport_types = current_data.get(CONF_TRANSPORTTYPES, '').split(',')

        self.options_schema = vol.Schema({
            vol.Required(CONF_NAME, default=current_data.get(CONF_NAME)): str,
            vol.Required(CONF_GLOBALID, default=current_data.get(CONF_GLOBALID)): str,
            vol.Optional(CONF_GLOBALID2, default=current_data.get(CONF_GLOBALID2, DEFAULT_CONF_GLOBALID2)): str,
            vol.Optional(CONF_LIMIT, default=current_data.get(CONF_LIMIT, DEFAULT_LIMIT)): int,
            vol.Optional(CONF_TRANSPORTTYPES, default=selected_transport_types): selector({
                "select": {
                    "options": transport_types,
                    "multiple": True,
                    "custom_value": True
                }
            }),
            vol.Optional(CONF_ONLYLINE, default=current_data.get(CONF_ONLYLINE, DEFAULT_ONLYLINE)): str,
            vol.Optional(CONF_HIDEDESTINATION, default=current_data.get(CONF_HIDEDESTINATION, DEFAULT_HIDEDESTINATION)): str,
            vol.Optional(CONF_HIDENAME, default=current_data.get(CONF_HIDENAME, DEFAULT_HIDENAME)): bool,
            vol.Optional(CONF_DOUBLESTATIONNUMBER, default=current_data.get(CONF_DOUBLESTATIONNUMBER, DEFAULT_CONF_DOUBLESTATIONNUMBER)): str,
            vol.Optional(CONF_TIMEZONE_FROM, default=current_data.get(CONF_TIMEZONE_FROM, DEFAULT_TIMEZONE_FROM)): str,
            vol.Optional(CONF_TIMEZONE_TO, default=current_data.get(CONF_TIMEZONE_TO, DEFAULT_TIMEZONE_TO)): str,
            vol.Optional(CONF_ALERT_FOR, default=current_data.get(CONF_ALERT_FOR, DEFAULT_ALERT_FOR)): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=self.options_schema
        )
