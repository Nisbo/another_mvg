import logging
import aiohttp
import voluptuous as vol
import uuid
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.selector import selector, SelectSelector, SelectSelectorConfig, SelectSelectorMode
from homeassistant import data_entry_flow
from typing import Any
from homeassistant.const import CONF_NAME
from .const import (
    DOMAIN,
    CONF_GLOBALID,
    CONF_ONLYLINE,
    CONF_HIDEDESTINATION,
    CONF_ONLYDESTINATION,
    CONF_LIMIT,
    CONF_DOUBLESTATIONNUMBER, # this is deprecated, however we have to keep it in the code for the yaml import / convert to GUI
    CONF_TRANSPORTTYPES,
    CONF_GLOBALID2,
    CONF_HIDENAME,
    CONF_TIMEZONE_FROM,
    CONF_TIMEZONE_TO,
    CONF_ALERT_FOR,
    CONF_STATS_TEMPLATE,
    CONF_SHOW_CLOCK,
    CONF_DEPARTURE_FORMAT,
    CONF_INCREASED_LIMIT,
    CONF_SORT_BY_REAL_DEPARTURE,
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

_LOGGER = logging.getLogger(__name__)

class AnotherMVGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Another MVG integration."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return AnotherMVGOptionsFlowHandler(config_entry)

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import entry from configuration.yaml."""
        return await self.async_step_user(
            {
                CONF_GLOBALID: import_data.get(CONF_GLOBALID),
                CONF_NAME: import_data.get(CONF_NAME),
                CONF_ONLYLINE: import_data.get(CONF_ONLYLINE, DEFAULT_ONLYLINE),
                CONF_HIDEDESTINATION: import_data.get(CONF_HIDEDESTINATION, DEFAULT_HIDEDESTINATION),
                CONF_ONLYDESTINATION: import_data.get(CONF_ONLYDESTINATION, DEFAULT_ONLYDESTINATION),
                CONF_LIMIT: import_data.get(CONF_LIMIT, DEFAULT_LIMIT),
                CONF_DOUBLESTATIONNUMBER: import_data.get(CONF_DOUBLESTATIONNUMBER, ""),
                CONF_TRANSPORTTYPES: import_data.get(CONF_TRANSPORTTYPES, DEFAULT_CONF_TRANSPORTTYPES).split(','),
                CONF_GLOBALID2: import_data.get(CONF_GLOBALID2, DEFAULT_CONF_GLOBALID2),
                CONF_HIDENAME: import_data.get(CONF_HIDENAME, DEFAULT_HIDENAME),
                CONF_INCREASED_LIMIT: import_data.get(CONF_INCREASED_LIMIT, DEFAULT_INCREASED_LIMIT),
                CONF_TIMEZONE_FROM: import_data.get(CONF_TIMEZONE_FROM, DEFAULT_TIMEZONE_FROM),
                CONF_TIMEZONE_TO: import_data.get(CONF_TIMEZONE_TO, DEFAULT_TIMEZONE_TO),
                CONF_ALERT_FOR: import_data.get(CONF_ALERT_FOR, DEFAULT_ALERT_FOR),
                CONF_STATS_TEMPLATE: import_data.get(CONF_STATS_TEMPLATE, DEFAULT_STATS_TEMPLATE),
                CONF_SHOW_CLOCK: import_data.get(CONF_SHOW_CLOCK, DEFAULT_SHOW_CLOCK),
                CONF_DEPARTURE_FORMAT: import_data.get(CONF_DEPARTURE_FORMAT, DEFAULT_DEPARTURE_FORMAT),
                CONF_SORT_BY_REAL_DEPARTURE: import_data.get(CONF_SORT_BY_REAL_DEPARTURE, DEFAULT_SORT_BY_REAL_DEPARTURE),
            }
        )


    async def async_step_user(self, user_input=None):
        """Handle the initial step and configuration."""
        #_LOGGER.warning("async_step_user called with user_input: %s", user_input)

        if user_input is not None:
            if "station_name" in user_input:
                # Handle station search
                station_name = user_input.get("station_name")
                stations = await self._fetch_stations(station_name)

                if stations:
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._user_config_schema(stations, station_name)
                    )
                else:
                    errors = {}
                    errors["base"] = "station_not_found"
                    
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._station_search_schema(),
                        errors=errors
                    )
            
            # If the user_input contains configuration, validate and create entry
            if self._is_valid(user_input):
                # check advanced_options and filter_options
                advanced_options = user_input.get("advanced_options", {})
                filter_options   = user_input.get("filter_options", {})
                unique_id = str(uuid.uuid4())  # Generate unique_id
                #_LOGGER.warning("AnotherMVG: UUID prepared: %s", unique_id)

                # and convert the input
                # this is because the section function creates an dictionary and I dont want this
                # I only want an optical "collapsing"
                if CONF_SHOW_CLOCK in advanced_options:
                    user_input[CONF_SHOW_CLOCK] = advanced_options[CONF_SHOW_CLOCK]
                    
                if CONF_ALERT_FOR in advanced_options:
                    user_input[CONF_ALERT_FOR] = advanced_options[CONF_ALERT_FOR]
                    
                if CONF_STATS_TEMPLATE in advanced_options:
                    user_input[CONF_STATS_TEMPLATE] = advanced_options[CONF_STATS_TEMPLATE]
          
                if CONF_TIMEZONE_FROM in advanced_options:
                    user_input[CONF_TIMEZONE_FROM] = advanced_options[CONF_TIMEZONE_FROM]
        
                if CONF_TIMEZONE_TO in advanced_options:
                    user_input[CONF_TIMEZONE_TO] = advanced_options[CONF_TIMEZONE_TO]
        
                if CONF_GLOBALID2 in advanced_options:
                    user_input[CONF_GLOBALID2] = advanced_options[CONF_GLOBALID2]
        
                if CONF_HIDENAME in advanced_options:
                    user_input[CONF_HIDENAME] = advanced_options[CONF_HIDENAME]

                if CONF_INCREASED_LIMIT in advanced_options:
                    user_input[CONF_INCREASED_LIMIT] = advanced_options[CONF_INCREASED_LIMIT]


                if CONF_ONLYLINE in filter_options:
                    user_input[CONF_ONLYLINE] = filter_options[CONF_ONLYLINE]
        
                if CONF_HIDEDESTINATION in filter_options:
                    user_input[CONF_HIDEDESTINATION] = filter_options[CONF_HIDEDESTINATION]
        
                if CONF_ONLYDESTINATION in filter_options:
                    user_input[CONF_ONLYDESTINATION] = filter_options[CONF_ONLYDESTINATION]


                if CONF_TRANSPORTTYPES in user_input:
                    user_input[CONF_TRANSPORTTYPES] = ','.join(user_input[CONF_TRANSPORTTYPES])

                # if the request is from the YAML import, 
                # means there is a CONF_DOUBLESTATIONNUMBER,
                # use the old unique_id format to keep the old relations and avoid double import from YAML
                if CONF_DOUBLESTATIONNUMBER in user_input:
                    unique_id = user_input[CONF_GLOBALID].replace(":", "") + user_input[CONF_DOUBLESTATIONNUMBER]
                    _LOGGER.warning("AnotherMVG: Old UUID used: %s", unique_id)

                await self.async_set_unique_id(unique_id)

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input
                )

            return self.async_show_form(
                step_id="user",
                data_schema=self._user_config_schema(None),
                errors={"base": "invalid_input"}
            )

        # Show station search form initially
        return self.async_show_form(
            step_id="user",
            data_schema=self._station_search_schema()
        )

    def _is_valid(self, user_input):
        """Validate user input."""
        return True

    async def _fetch_stations(self, station_name):
        """Fetch and filter stations for the given station name."""
        # _LOGGER.warning("Fetching stations for station name: %s", station_name)
        url = f"https://www.mvg.de/api/bgw-pt/v3/locations?query={station_name}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        #_LOGGER.warning("API response: %s", data)
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
                        #_LOGGER.warning("Filtered stations: %s", filtered_stations)
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

    def _user_config_schema(self, stations, station_name):
        """Return the schema for the user configuration form with station options."""
        options = [
            {"label": f"{station['name']} - {station['transportTypes']} ({station['globalId']})", "value": station['globalId']}
            for station in stations
        ] if stations else []

        return vol.Schema({
            vol.Required(CONF_NAME, default=station_name): str,
            vol.Required(CONF_GLOBALID): selector({
                "select": {
                    "options": options
                }
            }),
            vol.Optional(CONF_TRANSPORTTYPES, default=DEFAULT_CONF_TRANSPORTTYPES.split(',')): selector({
                "select": {
                    "options": DEFAULT_CONF_TRANSPORTTYPES.split(','),
                    "multiple": True,
                    "custom_value": True
                }
            }),
            vol.Optional(CONF_LIMIT,               default=DEFAULT_LIMIT): int,

            vol.Required(CONF_DEPARTURE_FORMAT, default=DEFAULT_DEPARTURE_FORMAT): SelectSelector(
                SelectSelectorConfig(
                    options = [
                        {"label": "16:27 +2 (16:29)", "value": "1"},
                        {"label": "16:27 +2",         "value": "2"},
                        {"label": "16:29",            "value": "3"}
                    ], mode = SelectSelectorMode.DROPDOWN,
                )
            ),

            vol.Optional(CONF_SORT_BY_REAL_DEPARTURE, default=DEFAULT_SORT_BY_REAL_DEPARTURE): bool,

            # Filter
            vol.Required("filter_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_ONLYLINE,            default=DEFAULT_ONLYLINE): str,
                        vol.Optional(CONF_HIDEDESTINATION,     default=DEFAULT_HIDEDESTINATION): str,
                        vol.Optional(CONF_ONLYDESTINATION,     default=DEFAULT_ONLYDESTINATION): str,
                    }
                ),
                # Whether or not the section is initially collapsed (default = False)
                {"collapsed": True},
            ),
            # Advanced Options
            vol.Required("advanced_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_SHOW_CLOCK,          default=DEFAULT_SHOW_CLOCK): bool,
                        vol.Optional(CONF_HIDENAME,            default=DEFAULT_HIDENAME): bool,
                        vol.Optional(CONF_INCREASED_LIMIT,     default=DEFAULT_INCREASED_LIMIT): int,
                        vol.Optional(CONF_GLOBALID2,           default=DEFAULT_CONF_GLOBALID2): str,
                        vol.Optional(CONF_TIMEZONE_FROM,       default=DEFAULT_TIMEZONE_FROM): str,
                        vol.Optional(CONF_TIMEZONE_TO,         default=DEFAULT_TIMEZONE_TO): str,
                        vol.Optional(CONF_ALERT_FOR,           default=DEFAULT_ALERT_FOR): str,
                        vol.Optional(CONF_STATS_TEMPLATE,      default=DEFAULT_STATS_TEMPLATE): str,
                    }
                ),
                # Whether or not the section is initially collapsed (default = False)
                {"collapsed": True},
            )
        })

class AnotherMVGOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Another MVG."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Another MVG options flow."""
        self._config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Display an options menu"""
        return self.async_show_menu(
            step_id="init",
            menu_options=["edit", "globalid1search", "globalid2search"],
        )

    async def async_step_globalid1search(self, user_input=None):
        if user_input is not None:
            if "station_name" in user_input:
                # Handle station search
                station_name = user_input.get("station_name")
                stations = await self._fetch_stations(station_name)

                if stations:
                    return self.async_show_form(
                        step_id="globalid1save",
                        data_schema=self._search_schema_globalid1(stations, station_name)
                    )
                else:
                    errors = {}
                    errors["base"] = "station_not_found"
                    
                    return self.async_show_form(
                        step_id="globalid1search",
                        data_schema=self._station_search_schema(),
                        errors=errors
                    )

        return self.async_show_form(step_id="globalid1search", data_schema=self._station_search_schema())

    async def async_step_globalid2search(self, user_input=None):
        if user_input is not None:
            if "station_name" in user_input:
                # Handle station search
                station_name = user_input.get("station_name")
                stations = await self._fetch_stations(station_name)

                if stations:
                    return self.async_show_form(
                        step_id="globalid2save",
                        data_schema=self._search_schema_globalid2(stations, station_name)
                    )
                else:
                    errors = {}
                    errors["base"] = "station_not_found"
                    
                    return self.async_show_form(
                        step_id="globalid2search",
                        data_schema=self._station_search_schema(),
                        errors=errors
                    )

        return self.async_show_form(step_id="globalid2search", data_schema=self._station_search_schema())

    async def async_step_globalid2save(self, user_input=None):
        if user_input is not None:
            existing_data = self._config_entry.data
            updated_data  = {**existing_data, **user_input}

            self.hass.config_entries.async_update_entry(
                self._config_entry, data=updated_data
            )
            
            await self.hass.config_entries.async_reload(self._config_entry.entry_id)

            return self.async_create_entry(title="", data={})

    async def async_step_globalid1save(self, user_input=None):
        if user_input is not None:
            existing_data = self._config_entry.data
            updated_data  = {**existing_data, **user_input}

            self.hass.config_entries.async_update_entry(
                self._config_entry, data=updated_data
            )
            
            await self.hass.config_entries.async_reload(self._config_entry.entry_id)

            return self.async_create_entry(title="", data={})

    def _search_schema_globalid1(self, stations, station_name):
        """Return the schema for the user configuration form with station options."""
        options = [
            {"label": f"{station['name']} - {station['transportTypes']} ({station['globalId']})", "value": station['globalId']}
            for station in stations
        ] if stations else []

        return vol.Schema({
            vol.Required(CONF_GLOBALID): selector({
                "select": {
                    "options": options
                }
            })
        })

    def _search_schema_globalid2(self, stations, station_name):
        """Return the schema for the user configuration form with station options."""
        options = [
            {"label": f"{station['name']} - {station['transportTypes']} ({station['globalId']})", "value": station['globalId']}
            for station in stations
        ] if stations else []

        return vol.Schema({
            vol.Required(CONF_GLOBALID2): selector({
                "select": {
                    "options": options
                }
            })
        })


    async def _fetch_stations(self, station_name):
        """Fetch and filter stations for the given station name."""
        # _LOGGER.warning("Fetching stations for station name: %s", station_name)
        url = f"https://www.mvg.de/api/bgw-pt/v3/locations?query={station_name}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        #_LOGGER.warning("API response: %s", data)
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
                        #_LOGGER.warning("Filtered stations: %s", filtered_stations)
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


    async def async_step_edit(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Log submitted user_input
            # for key, value in user_input.items():
            #    _LOGGER.error(f"Field: {key}, Value: {value}")

            # check advanced_options and filter_options
            advanced_options = user_input.get("advanced_options", {})
            filter_options   = user_input.get("filter_options", {})
        
            # and convert the input
            # this is because the section function creates a dictionary and I dont want this
            # I only want an optical "collapsing"
            if CONF_SHOW_CLOCK in advanced_options:
                user_input[CONF_SHOW_CLOCK] = advanced_options[CONF_SHOW_CLOCK]
                
            if CONF_ALERT_FOR in advanced_options:
                user_input[CONF_ALERT_FOR] = advanced_options[CONF_ALERT_FOR]
            
            if CONF_STATS_TEMPLATE in advanced_options:
                user_input[CONF_STATS_TEMPLATE] = advanced_options[CONF_STATS_TEMPLATE]
          
            if CONF_TIMEZONE_FROM in advanced_options:
                user_input[CONF_TIMEZONE_FROM] = advanced_options[CONF_TIMEZONE_FROM]
        
            if CONF_TIMEZONE_TO in advanced_options:
                user_input[CONF_TIMEZONE_TO] = advanced_options[CONF_TIMEZONE_TO]
        
            if CONF_GLOBALID2 in advanced_options:
                user_input[CONF_GLOBALID2] = advanced_options[CONF_GLOBALID2]
        
            if CONF_HIDENAME in advanced_options:
                user_input[CONF_HIDENAME] = advanced_options[CONF_HIDENAME]

            if CONF_INCREASED_LIMIT in advanced_options:
                user_input[CONF_INCREASED_LIMIT] = advanced_options[CONF_INCREASED_LIMIT]


            if CONF_ONLYLINE in filter_options:
                user_input[CONF_ONLYLINE] = filter_options[CONF_ONLYLINE]
        
            if CONF_HIDEDESTINATION in filter_options:
                user_input[CONF_HIDEDESTINATION] = filter_options[CONF_HIDEDESTINATION]
        
            if CONF_ONLYDESTINATION in filter_options:
                user_input[CONF_ONLYDESTINATION] = filter_options[CONF_ONLYDESTINATION]


            # Ensure that empty fields are stored as empty strings
            for key in [CONF_ONLYLINE, CONF_HIDEDESTINATION, CONF_ONLYDESTINATION, 
                        CONF_TIMEZONE_FROM, CONF_TIMEZONE_TO, CONF_ALERT_FOR, CONF_GLOBALID2, CONF_STATS_TEMPLATE]:
                if key not in user_input:
                    user_input[key] = ""  # Explicitly set the field to an empty string if it's not in the user_input
            
            # Convert selected transport types to a comma-separated string
            if CONF_TRANSPORTTYPES in user_input:
                user_input[CONF_TRANSPORTTYPES] = ','.join(user_input[CONF_TRANSPORTTYPES])
            
            # Save the updated data
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=user_input
            )
            
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self._config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        # Prepare the default values based on current configuration data
        current_data = self._config_entry.data
        transport_types = DEFAULT_CONF_TRANSPORTTYPES.split(',')
        selected_transport_types = current_data.get(CONF_TRANSPORTTYPES, '').split(',')

        self.options_schema = vol.Schema({
            vol.Required(CONF_NAME,           default=current_data.get(CONF_NAME)): str,
            vol.Required(CONF_GLOBALID,       default=current_data.get(CONF_GLOBALID)): str,
            vol.Optional(CONF_TRANSPORTTYPES, default=selected_transport_types): selector({
                "select": {
                    "options": transport_types,
                    "multiple": True,
                    "custom_value": True
                }
            }),
            vol.Optional(CONF_LIMIT,            default=current_data.get(CONF_LIMIT, DEFAULT_LIMIT)): int,
            vol.Required(CONF_DEPARTURE_FORMAT, default=current_data.get(CONF_DEPARTURE_FORMAT, "1")): SelectSelector(
                SelectSelectorConfig(
                    options = [
                        {"label": "16:27 +2 (16:29)", "value": "1"},
                        {"label": "16:27 +2",         "value": "2"},
                        {"label": "16:29",            "value": "3"}
                    ], mode = SelectSelectorMode.DROPDOWN,
                )
            ),

            vol.Optional(CONF_SORT_BY_REAL_DEPARTURE, description={"suggested_value": current_data.get(CONF_SORT_BY_REAL_DEPARTURE, "")}): bool,

            # Filter
            vol.Required("filter_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_ONLYLINE,            description={"suggested_value": current_data.get(CONF_ONLYLINE, "")}): str,
                        vol.Optional(CONF_HIDEDESTINATION,     description={"suggested_value": current_data.get(CONF_HIDEDESTINATION, "")}): str,
                        vol.Optional(CONF_ONLYDESTINATION,     description={"suggested_value": current_data.get(CONF_ONLYDESTINATION, "")}): str,
                    }
                ),
                # Whether or not the section is initially collapsed (default = False)
                {"collapsed": True},
            ),
            # Advanced Options
            vol.Required("advanced_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_SHOW_CLOCK,          description={"suggested_value": current_data.get(CONF_SHOW_CLOCK, "")}): bool,
                        vol.Optional(CONF_HIDENAME,            description={"suggested_value": current_data.get(CONF_HIDENAME, "")}): bool,
                        vol.Optional(CONF_INCREASED_LIMIT,     description={"suggested_value": current_data.get(CONF_INCREASED_LIMIT, DEFAULT_INCREASED_LIMIT)}): int,
                        vol.Optional(CONF_GLOBALID2,           description={"suggested_value": current_data.get(CONF_GLOBALID2, "")}): str,
                        vol.Optional(CONF_TIMEZONE_FROM,       description={"suggested_value": current_data.get(CONF_TIMEZONE_FROM, "")}): str,
                        vol.Optional(CONF_TIMEZONE_TO,         description={"suggested_value": current_data.get(CONF_TIMEZONE_TO, "")}): str,
                        vol.Optional(CONF_ALERT_FOR,           description={"suggested_value": current_data.get(CONF_ALERT_FOR, "")}): str,
                        vol.Optional(CONF_STATS_TEMPLATE,      description={"suggested_value": current_data.get(CONF_STATS_TEMPLATE, "")}): str,
                    }
                ),
                # Whether or not the section is initially collapsed (default = False)
                {"collapsed": True},
            )
        })

        return self.async_show_form(
            step_id="edit",
            data_schema=self.options_schema
        )
