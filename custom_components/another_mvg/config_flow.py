import logging
import aiohttp
import voluptuous as vol
import uuid
import json
from pathlib import Path
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.selector import selector, SelectSelector, SelectSelectorConfig, SelectSelectorMode, ObjectSelector, ObjectSelectorConfig, TextSelector
from homeassistant import data_entry_flow
from typing import Any
from homeassistant.const import CONF_NAME
from .const import (
    DOMAIN,
    CONF_MONITOR_TYPE,
    CONF_GLOBALID,
    CONF_ONLYLINE,
    CONF_HIDEDESTINATION,
    CONF_ONLYDESTINATION,
    CONF_LIMIT,
    CONF_DOUBLESTATIONNUMBER, # this is deprecated, however we have to keep it in the code for the yaml import / convert to GUI
    CONF_TRANSPORTTYPES,
    CONF_GLOBALID2,
    CONF_TIMEZONE_FROM,
    CONF_TIMEZONE_TO,
    CONF_ALERT_FOR,
    CONF_STATS_TEMPLATE,
    CONF_INCREASED_LIMIT,
    CONF_SORT_BY_REAL_DEPARTURE,
    CONF_OFFSET_IN_MINUTES,
    CONF_PROXY_URL,
    CONF_PROXY_USETIME,
    CONF_FORCE_PROXY,
    CONF_CSS_CODE,
    CONF_CSS_CODE_DARKMODE_ONLY,
    CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER,
    CONF_MQTT_ENABLED,
    CONF_MQTT_TOPIC_PREFIX,
    CONF_MQTT_RETAIN,
    CONF_MQTT_QOS,
    CONF_UPDATE_MODE,
    CONF_ALERT_ENABLED,
    CONF_ALERT_NAME,
    CONF_ALERT_WEEKDAYS,
    CONF_ALERT_LINE,
    CONF_ALERT_PLANNED_TIME,
    CONF_ALERT_DIRECTION,
    CONF_ALERT_ACTIVE_FROM,
    CONF_ALERT_ACTIVE_TO,
    CONF_ALERT_DELAY_MINUTES,
    CONF_ALERT_CANCELLED,
    CONF_ALERT_NOTIFY_MODE,
    ALERT_COUNT,
    ALERT_WEEKDAYS,
    ALERT_NOTIFY_ONCE,
    ALERT_NOTIFY_WORSENING,
    DEFAULT_ONLYLINE,
    DEFAULT_MONITOR_TYPE,
    MONITOR_TYPE_DEPARTURE,
    MONITOR_TYPE_ARRIVAL,
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
    DEFAULT_EXCLUDE_ATTRIBUTES_FROM_RECORDER,
    DEFAULT_MQTT_ENABLED,
    DEFAULT_MQTT_TOPIC_PREFIX,
    DEFAULT_MQTT_RETAIN,
    DEFAULT_MQTT_QOS,
    DEFAULT_UPDATE_MODE,
    DEFAULT_ALERT_ENABLED,
    DEFAULT_ALERT_NAME,
    DEFAULT_ALERT_WEEKDAYS,
    DEFAULT_ALERT_LINE,
    DEFAULT_ALERT_PLANNED_TIME,
    DEFAULT_ALERT_DIRECTION,
    DEFAULT_ALERT_ACTIVE_FROM,
    DEFAULT_ALERT_ACTIVE_TO,
    DEFAULT_ALERT_DELAY_MINUTES,
    DEFAULT_ALERT_CANCELLED,
    DEFAULT_ALERT_NOTIFY_MODE,
    UPDATE_MODE_AUTO,
    UPDATE_MODE_MANUAL,
)

_LOGGER = logging.getLogger(__name__)
_TRANSLATION_CACHE = {}

class AnotherMVGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Another MVG integration."""

    VERSION = 1

    @staticmethod
    def _normalize_limit(value) -> int:
        """Clamp API request limit to the supported range."""
        try:
            limit = int(value)
        except (TypeError, ValueError):
            limit = DEFAULT_LIMIT
        return max(1, min(80, limit))

    @staticmethod
    def _normalize_mqtt_topic_prefix(value) -> str:
        """Normalize an MQTT topic prefix."""
        topic = str(value or "").strip()
        return topic or DEFAULT_MQTT_TOPIC_PREFIX

    @staticmethod
    def _is_valid_mqtt_topic_prefix(value) -> bool:
        """Return true if the MQTT topic prefix can be published to."""
        topic = AnotherMVGConfigFlow._normalize_mqtt_topic_prefix(value)
        return (
            bool(topic)
            and all(
                char.isascii() and (char.isalnum() or char in "._-/")
                for char in topic
            )
            and not topic.startswith("/")
            and not topic.endswith("/")
            and "//" not in topic
        )

    @staticmethod
    def _alert_defaults(index: int) -> dict[str, Any]:
        """Return default values for one alert rule."""
        return {
            CONF_ALERT_ENABLED.format(index): DEFAULT_ALERT_ENABLED,
            CONF_ALERT_NAME.format(index): DEFAULT_ALERT_NAME,
            CONF_ALERT_WEEKDAYS.format(index): list(DEFAULT_ALERT_WEEKDAYS),
            CONF_ALERT_LINE.format(index): DEFAULT_ALERT_LINE,
            CONF_ALERT_PLANNED_TIME.format(index): DEFAULT_ALERT_PLANNED_TIME,
            CONF_ALERT_DIRECTION.format(index): DEFAULT_ALERT_DIRECTION,
            CONF_ALERT_ACTIVE_FROM.format(index): DEFAULT_ALERT_ACTIVE_FROM,
            CONF_ALERT_ACTIVE_TO.format(index): DEFAULT_ALERT_ACTIVE_TO,
            CONF_ALERT_DELAY_MINUTES.format(index): DEFAULT_ALERT_DELAY_MINUTES,
            CONF_ALERT_CANCELLED.format(index): DEFAULT_ALERT_CANCELLED,
            CONF_ALERT_NOTIFY_MODE.format(index): DEFAULT_ALERT_NOTIFY_MODE,
        }

    @classmethod
    def _flatten_alert_options(cls, user_input: dict, current_data=None) -> None:
        """Move nested alert section values to the flat config entry data."""
        field_map = {
            "enabled": CONF_ALERT_ENABLED,
            "name": CONF_ALERT_NAME,
            "weekdays": CONF_ALERT_WEEKDAYS,
            "line": CONF_ALERT_LINE,
            "planned_time": CONF_ALERT_PLANNED_TIME,
            "direction": CONF_ALERT_DIRECTION,
            "active_from": CONF_ALERT_ACTIVE_FROM,
            "active_to": CONF_ALERT_ACTIVE_TO,
            "delay_minutes": CONF_ALERT_DELAY_MINUTES,
            "cancelled": CONF_ALERT_CANCELLED,
            "notify_mode": CONF_ALERT_NOTIFY_MODE,
        }

        for index in range(1, ALERT_COUNT + 1):
            defaults = cls._alert_defaults(index)
            section_name = f"alert{index}_options"
            section = user_input.get(section_name, {}) or {}
            for section_field, config_key_template in field_map.items():
                config_key = config_key_template.format(index)
                default_value = defaults[config_key]
                if current_data is not None:
                    default_value = current_data.get(config_key, default_value)
                user_input[config_key] = section.get(section_field, default_value)

            try:
                user_input[CONF_ALERT_DELAY_MINUTES.format(index)] = max(
                    0,
                    int(user_input[CONF_ALERT_DELAY_MINUTES.format(index)]),
                )
            except (TypeError, ValueError):
                user_input[CONF_ALERT_DELAY_MINUTES.format(index)] = DEFAULT_ALERT_DELAY_MINUTES

            user_input.pop(section_name, None)

    @staticmethod
    def _load_translation(language: str | None) -> dict:
        """Load the integration translation file."""
        lang = "de" if (language or "").lower().startswith("de") else "en"
        if lang in _TRANSLATION_CACHE:
            return _TRANSLATION_CACHE[lang]

        translation_file = Path(__file__).with_name("translations") / f"{lang}.json"
        try:
            with translation_file.open(encoding="utf-8") as file:
                _TRANSLATION_CACHE[lang] = json.load(file)
        except (OSError, json.JSONDecodeError):
            _TRANSLATION_CACHE[lang] = {}
        return _TRANSLATION_CACHE[lang]

    @staticmethod
    def _translation(translations: dict, keys: list[str], fallback: str) -> str:
        """Return a translated string from the integration translation files."""
        value = translations
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return fallback
            value = value[key]
        return value if isinstance(value, str) else fallback

    @classmethod
    def _monitor_type_options(cls, translations: dict) -> list[dict[str, str]]:
        """Return monitor type labels for the active Home Assistant language."""
        return [
            {
                "label": cls._translation(
                    translations,
                    ["selector", "monitor_type", "options", MONITOR_TYPE_DEPARTURE],
                    "Departure monitor",
                ),
                "value": MONITOR_TYPE_DEPARTURE,
            },
            {
                "label": cls._translation(
                    translations,
                    ["selector", "monitor_type", "options", MONITOR_TYPE_ARRIVAL],
                    "Arrival monitor",
                ),
                "value": MONITOR_TYPE_ARRIVAL,
            },
        ]

    @classmethod
    def _update_mode_options(cls, translations: dict) -> list[dict[str, str]]:
        """Return update mode labels for the active Home Assistant language."""
        return [
            {
                "label": cls._translation(
                    translations,
                    ["selector", "update_mode", "options", UPDATE_MODE_AUTO],
                    "Automatic",
                ),
                "value": UPDATE_MODE_AUTO,
            },
            {
                "label": cls._translation(
                    translations,
                    ["selector", "update_mode", "options", UPDATE_MODE_MANUAL],
                    "Manual",
                ),
                "value": UPDATE_MODE_MANUAL,
            },
        ]

    @classmethod
    def _alert_weekday_options(cls, translations: dict) -> list[dict[str, str]]:
        """Return weekday labels for alert rules."""
        return [
            {
                "label": cls._translation(
                    translations,
                    ["selector", "alert_weekday", "options", weekday],
                    weekday,
                ),
                "value": weekday,
            }
            for weekday in ALERT_WEEKDAYS
        ]

    @classmethod
    def _alert_notify_mode_options(cls, translations: dict) -> list[dict[str, str]]:
        """Return alert notification mode labels."""
        return [
            {
                "label": cls._translation(
                    translations,
                    ["selector", "alert_notify_mode", "options", ALERT_NOTIFY_ONCE],
                    "Once per trip",
                ),
                "value": ALERT_NOTIFY_ONCE,
            },
            {
                "label": cls._translation(
                    translations,
                    ["selector", "alert_notify_mode", "options", ALERT_NOTIFY_WORSENING],
                    "Again when delay gets worse",
                ),
                "value": ALERT_NOTIFY_WORSENING,
            },
        ]

    async def _async_monitor_type_options(self) -> list[dict[str, str]]:
        """Return translated monitor type options without blocking the event loop."""
        translations = await self.hass.async_add_executor_job(
            self._load_translation,
            self.hass.config.language,
        )
        return self._monitor_type_options(translations)

    async def _async_update_mode_options(self) -> list[dict[str, str]]:
        """Return translated update mode options without blocking the event loop."""
        translations = await self.hass.async_add_executor_job(
            self._load_translation,
            self.hass.config.language,
        )
        return self._update_mode_options(translations)

    async def _async_alert_weekday_options(self) -> list[dict[str, str]]:
        """Return translated alert weekday options without blocking the event loop."""
        translations = await self.hass.async_add_executor_job(
            self._load_translation,
            self.hass.config.language,
        )
        return self._alert_weekday_options(translations)

    async def _async_alert_notify_mode_options(self) -> list[dict[str, str]]:
        """Return translated alert notify mode options without blocking the event loop."""
        translations = await self.hass.async_add_executor_job(
            self._load_translation,
            self.hass.config.language,
        )
        return self._alert_notify_mode_options(translations)

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
                CONF_MONITOR_TYPE: import_data.get(CONF_MONITOR_TYPE, DEFAULT_MONITOR_TYPE),
                CONF_NAME: import_data.get(CONF_NAME),
                CONF_ONLYLINE: import_data.get(CONF_ONLYLINE, DEFAULT_ONLYLINE),
                CONF_HIDEDESTINATION: import_data.get(CONF_HIDEDESTINATION, DEFAULT_HIDEDESTINATION),
                CONF_ONLYDESTINATION: import_data.get(CONF_ONLYDESTINATION, DEFAULT_ONLYDESTINATION),
                CONF_LIMIT: import_data.get(CONF_LIMIT, DEFAULT_LIMIT),
                CONF_DOUBLESTATIONNUMBER: import_data.get(CONF_DOUBLESTATIONNUMBER, ""),
                CONF_TRANSPORTTYPES: import_data.get(CONF_TRANSPORTTYPES, DEFAULT_CONF_TRANSPORTTYPES).split(','),
                CONF_GLOBALID2: import_data.get(CONF_GLOBALID2, DEFAULT_CONF_GLOBALID2),
                CONF_INCREASED_LIMIT: import_data.get(CONF_INCREASED_LIMIT, DEFAULT_INCREASED_LIMIT),
                CONF_TIMEZONE_FROM: import_data.get(CONF_TIMEZONE_FROM, DEFAULT_TIMEZONE_FROM),
                CONF_TIMEZONE_TO: import_data.get(CONF_TIMEZONE_TO, DEFAULT_TIMEZONE_TO),
                CONF_ALERT_FOR: import_data.get(CONF_ALERT_FOR, DEFAULT_ALERT_FOR),
                CONF_STATS_TEMPLATE: import_data.get(CONF_STATS_TEMPLATE, DEFAULT_STATS_TEMPLATE),
                CONF_SORT_BY_REAL_DEPARTURE: import_data.get(CONF_SORT_BY_REAL_DEPARTURE, DEFAULT_SORT_BY_REAL_DEPARTURE),
                CONF_OFFSET_IN_MINUTES: import_data.get(CONF_OFFSET_IN_MINUTES, DEFAULT_OFFSET_IN_MINUTES),
                CONF_PROXY_URL: import_data.get(CONF_PROXY_URL, DEFAULT_PROXY_URL),
                CONF_PROXY_USETIME: import_data.get(CONF_PROXY_USETIME, DEFAULT_PROXY_USETIME),
                CONF_FORCE_PROXY: import_data.get(CONF_FORCE_PROXY, DEFAULT_FORCE_PROXY),
                CONF_CSS_CODE: import_data.get(CONF_CSS_CODE, DEFAULT_CSS_CODE),
                CONF_CSS_CODE_DARKMODE_ONLY: import_data.get(CONF_CSS_CODE_DARKMODE_ONLY, DEFAULT_CSS_CODE_DARKMODE_ONLY),
                CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER: import_data.get(CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER, DEFAULT_EXCLUDE_ATTRIBUTES_FROM_RECORDER),
                CONF_MQTT_ENABLED: import_data.get(CONF_MQTT_ENABLED, DEFAULT_MQTT_ENABLED),
                CONF_MQTT_TOPIC_PREFIX: import_data.get(CONF_MQTT_TOPIC_PREFIX, DEFAULT_MQTT_TOPIC_PREFIX),
                CONF_MQTT_RETAIN: import_data.get(CONF_MQTT_RETAIN, DEFAULT_MQTT_RETAIN),
                CONF_MQTT_QOS: import_data.get(CONF_MQTT_QOS, DEFAULT_MQTT_QOS),
                CONF_UPDATE_MODE: import_data.get(CONF_UPDATE_MODE, DEFAULT_UPDATE_MODE),
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
                    monitor_type_options = await self._async_monitor_type_options()
                    update_mode_options = await self._async_update_mode_options()
                    weekday_options = await self._async_alert_weekday_options()
                    notify_mode_options = await self._async_alert_notify_mode_options()
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._user_config_schema(
                            stations,
                            station_name,
                            monitor_type_options,
                            update_mode_options,
                            weekday_options,
                            notify_mode_options,
                        )
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
                proxy_options    = user_input.get("proxy_options", {})
                mqtt_options     = user_input.get("mqtt_options", {})
                unique_id = str(uuid.uuid4())  # Generate unique_id
                #_LOGGER.warning("AnotherMVG: UUID prepared: %s", unique_id)

                # and convert the input
                # this is because the section function creates an dictionary and I dont want this
                # I only want an optical "collapsing"
                    
                if CONF_ALERT_FOR in advanced_options:
                    user_input[CONF_ALERT_FOR] = advanced_options[CONF_ALERT_FOR]
                    
                if CONF_STATS_TEMPLATE in advanced_options:
                    user_input[CONF_STATS_TEMPLATE] = advanced_options[CONF_STATS_TEMPLATE]
        
                if CONF_CSS_CODE in advanced_options:
                    user_input[CONF_CSS_CODE] = advanced_options[CONF_CSS_CODE]
        
                if CONF_CSS_CODE_DARKMODE_ONLY in advanced_options:
                    user_input[CONF_CSS_CODE_DARKMODE_ONLY] = advanced_options[CONF_CSS_CODE_DARKMODE_ONLY]

                if CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER in advanced_options:
                    user_input[CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER] = advanced_options[CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER]
        
                if CONF_TIMEZONE_FROM in advanced_options:
                    user_input[CONF_TIMEZONE_FROM] = advanced_options[CONF_TIMEZONE_FROM]
        
                if CONF_TIMEZONE_TO in advanced_options:
                    user_input[CONF_TIMEZONE_TO] = advanced_options[CONF_TIMEZONE_TO]
        
                if CONF_GLOBALID2 in advanced_options:
                    user_input[CONF_GLOBALID2] = advanced_options[CONF_GLOBALID2]
        

                if CONF_INCREASED_LIMIT in advanced_options:
                    user_input[CONF_INCREASED_LIMIT] = advanced_options[CONF_INCREASED_LIMIT]


                if CONF_ONLYLINE in filter_options:
                    user_input[CONF_ONLYLINE] = filter_options[CONF_ONLYLINE]
        
                if CONF_HIDEDESTINATION in filter_options:
                    user_input[CONF_HIDEDESTINATION] = filter_options[CONF_HIDEDESTINATION]
        
                if CONF_ONLYDESTINATION in filter_options:
                    user_input[CONF_ONLYDESTINATION] = filter_options[CONF_ONLYDESTINATION]


                if CONF_PROXY_URL in proxy_options:
                    user_input[CONF_PROXY_URL] = proxy_options[CONF_PROXY_URL]
        
                if CONF_PROXY_USETIME in proxy_options:
                    user_input[CONF_PROXY_USETIME] = proxy_options[CONF_PROXY_USETIME]
        
                if CONF_FORCE_PROXY in proxy_options:
                    user_input[CONF_FORCE_PROXY] = proxy_options[CONF_FORCE_PROXY]

                self._flatten_alert_options(user_input)

                if CONF_MQTT_ENABLED in mqtt_options:
                    user_input[CONF_MQTT_ENABLED] = mqtt_options[CONF_MQTT_ENABLED]

                user_input[CONF_MQTT_TOPIC_PREFIX] = self._normalize_mqtt_topic_prefix(
                    mqtt_options.get(CONF_MQTT_TOPIC_PREFIX, DEFAULT_MQTT_TOPIC_PREFIX)
                )

                if CONF_MQTT_RETAIN in mqtt_options:
                    user_input[CONF_MQTT_RETAIN] = mqtt_options[CONF_MQTT_RETAIN]

                user_input[CONF_MQTT_QOS] = int(
                    mqtt_options.get(CONF_MQTT_QOS, DEFAULT_MQTT_QOS)
                )

                if not self._is_valid_mqtt_topic_prefix(user_input[CONF_MQTT_TOPIC_PREFIX]):
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._user_config_schema(
                            None,
                            None,
                            await self._async_monitor_type_options(),
                            await self._async_update_mode_options(),
                            await self._async_alert_weekday_options(),
                            await self._async_alert_notify_mode_options(),
                        ),
                        errors={"base": "invalid_mqtt_topic"},
                    )

                if CONF_TRANSPORTTYPES in user_input:
                    user_input[CONF_TRANSPORTTYPES] = ','.join(user_input[CONF_TRANSPORTTYPES])

                if CONF_LIMIT in user_input:
                    user_input[CONF_LIMIT] = self._normalize_limit(user_input[CONF_LIMIT])

                if CONF_UPDATE_MODE not in user_input:
                    user_input[CONF_UPDATE_MODE] = DEFAULT_UPDATE_MODE

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
                data_schema=self._user_config_schema(
                    None,
                    None,
                    await self._async_monitor_type_options(),
                    await self._async_update_mode_options(),
                    await self._async_alert_weekday_options(),
                    await self._async_alert_notify_mode_options(),
                ),
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

    @classmethod
    def _alert_rule_schema(cls, index, current_data, weekday_options, notify_mode_options):
        """Return one collapsible alert rule section."""
        current_data = current_data or {}
        defaults = cls._alert_defaults(index)

        def value(config_key):
            return current_data.get(config_key, defaults[config_key])

        weekdays = value(CONF_ALERT_WEEKDAYS.format(index))
        if isinstance(weekdays, str):
            weekdays = [item.strip() for item in weekdays.split(",") if item.strip()]

        return data_entry_flow.section(
            vol.Schema(
                {
                    vol.Optional("enabled", default=value(CONF_ALERT_ENABLED.format(index))): bool,
                    vol.Optional("name", default=value(CONF_ALERT_NAME.format(index))): str,
                    vol.Optional("weekdays", default=weekdays): selector({
                        "select": {
                            "options": weekday_options,
                            "multiple": True,
                            "mode": "list",
                        }
                    }),
                    vol.Optional("line", default=value(CONF_ALERT_LINE.format(index))): str,
                    vol.Optional("planned_time", default=value(CONF_ALERT_PLANNED_TIME.format(index))): str,
                    vol.Optional("direction", default=value(CONF_ALERT_DIRECTION.format(index))): str,
                    vol.Optional("active_from", default=value(CONF_ALERT_ACTIVE_FROM.format(index))): str,
                    vol.Optional("active_to", default=value(CONF_ALERT_ACTIVE_TO.format(index))): str,
                    vol.Optional("delay_minutes", default=value(CONF_ALERT_DELAY_MINUTES.format(index))): selector({
                        "number": {
                            "min": 0,
                            "max": 180,
                            "step": 1,
                            "mode": "box",
                        }
                    }),
                    vol.Optional("cancelled", default=value(CONF_ALERT_CANCELLED.format(index))): bool,
                    vol.Optional("notify_mode", default=value(CONF_ALERT_NOTIFY_MODE.format(index))): selector({
                        "select": {
                            "options": notify_mode_options,
                            "mode": "dropdown",
                        }
                    }),
                }
            ),
            {"collapsed": True},
        )

    @classmethod
    def _alert_options_schema(cls, current_data, weekday_options, notify_mode_options):
        """Return alert rule sections."""
        return {
            vol.Required(f"alert{index}_options"): cls._alert_rule_schema(
                index,
                current_data,
                weekday_options,
                notify_mode_options,
            )
            for index in range(1, ALERT_COUNT + 1)
        }

    def _user_config_schema(self, stations, station_name, monitor_type_options, update_mode_options, weekday_options, notify_mode_options):
        """Return the schema for the user configuration form with station options."""
        options = [
            {"label": f"{station['name']} - {station['transportTypes']} ({station['globalId']})", "value": station['globalId']}
            for station in stations
        ] if stations else []

        return vol.Schema({
            vol.Required(CONF_NAME, default=station_name): str,
            vol.Optional(CONF_MONITOR_TYPE, default=DEFAULT_MONITOR_TYPE): selector({
                "select": {
                    "options": monitor_type_options,
                    "mode": "dropdown"
                }
            }),
            vol.Optional(CONF_UPDATE_MODE, default=DEFAULT_UPDATE_MODE): selector({
                "select": {
                    "options": update_mode_options,
                    "mode": "dropdown"
                }
            }),
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
            vol.Optional(CONF_LIMIT,               default=self._normalize_limit(DEFAULT_LIMIT)): selector({
                "number": {
                    "min": 1,
                    "max": 80,
                    "step": 1,
                    "mode": "box"
                }
            }),
            vol.Optional(CONF_SORT_BY_REAL_DEPARTURE, default=DEFAULT_SORT_BY_REAL_DEPARTURE): bool,
            vol.Optional(CONF_OFFSET_IN_MINUTES, default=DEFAULT_OFFSET_IN_MINUTES): int,

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
            # Alerts
            **self._alert_options_schema(None, weekday_options, notify_mode_options),
            # Advanced Options
            vol.Required("advanced_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_INCREASED_LIMIT,     default=DEFAULT_INCREASED_LIMIT): int,
                        vol.Optional(CONF_GLOBALID2,           default=DEFAULT_CONF_GLOBALID2): str,
                        vol.Optional(CONF_TIMEZONE_FROM,       default=DEFAULT_TIMEZONE_FROM): str,
                        vol.Optional(CONF_TIMEZONE_TO,         default=DEFAULT_TIMEZONE_TO): str,
                        vol.Optional(CONF_ALERT_FOR,           default=DEFAULT_ALERT_FOR): str,
                        #vol.Optional(CONF_STATS_TEMPLATE,      default=DEFAULT_STATS_TEMPLATE): str,
                        vol.Optional(CONF_STATS_TEMPLATE,      default=DEFAULT_STATS_TEMPLATE): TextSelector({"type": "text", "multiline": True}),
                        vol.Optional(CONF_CSS_CODE,            default=DEFAULT_CSS_CODE): TextSelector({"type": "text", "multiline": True}),
                        vol.Optional(CONF_CSS_CODE_DARKMODE_ONLY, default=DEFAULT_CSS_CODE_DARKMODE_ONLY): bool,
                        vol.Optional(CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER, default=DEFAULT_EXCLUDE_ATTRIBUTES_FROM_RECORDER): bool,
                    }
                ),
                # Whether or not the section is initially collapsed (default = False)
                {"collapsed": True},
            ),
            # Proxy
            vol.Required("proxy_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_PROXY_URL,            default=DEFAULT_PROXY_URL): str,
                        vol.Required(CONF_PROXY_USETIME,        default=DEFAULT_PROXY_USETIME): int,
                        vol.Optional(CONF_FORCE_PROXY,          default=DEFAULT_FORCE_PROXY): bool,
                    }
                ),
                # Whether or not the section is initially collapsed (default = False)
                {"collapsed": True},
            ),
            # MQTT
            vol.Required("mqtt_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_MQTT_ENABLED, default=DEFAULT_MQTT_ENABLED): bool,
                        vol.Optional(CONF_MQTT_TOPIC_PREFIX, default=DEFAULT_MQTT_TOPIC_PREFIX): str,
                        vol.Optional(CONF_MQTT_QOS, default=str(DEFAULT_MQTT_QOS)): selector({
                            "select": {
                                "options": ["0", "1", "2"],
                                "mode": "dropdown"
                            }
                        }),
                        vol.Optional(CONF_MQTT_RETAIN, default=DEFAULT_MQTT_RETAIN): bool,
                    }
                ),
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
        current_data = self._config_entry.data

        if user_input is not None:
            # Log submitted user_input
            # for key, value in user_input.items():
            #    _LOGGER.error(f"Field: {key}, Value: {value}")

            # check advanced_options and filter_options
            advanced_options = user_input.get("advanced_options", {})
            filter_options   = user_input.get("filter_options", {})
            proxy_options    = user_input.get("proxy_options", {})
            mqtt_options     = user_input.get("mqtt_options", {})
        
            # and convert the input
            # this is because the section function creates a dictionary and I dont want this
            # I only want an optical "collapsing"
            if CONF_ALERT_FOR in advanced_options:
                user_input[CONF_ALERT_FOR] = advanced_options[CONF_ALERT_FOR]
            
            if CONF_STATS_TEMPLATE in advanced_options:
                user_input[CONF_STATS_TEMPLATE] = advanced_options[CONF_STATS_TEMPLATE]
                
            if CONF_CSS_CODE in advanced_options:
                user_input[CONF_CSS_CODE] = advanced_options[CONF_CSS_CODE]               
            
            if CONF_CSS_CODE_DARKMODE_ONLY in advanced_options:
                user_input[CONF_CSS_CODE_DARKMODE_ONLY] = advanced_options[CONF_CSS_CODE_DARKMODE_ONLY]

            if CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER in advanced_options:
                user_input[CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER] = advanced_options[CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER]
            
            if CONF_TIMEZONE_FROM in advanced_options:
                user_input[CONF_TIMEZONE_FROM] = advanced_options[CONF_TIMEZONE_FROM]
        
            if CONF_TIMEZONE_TO in advanced_options:
                user_input[CONF_TIMEZONE_TO] = advanced_options[CONF_TIMEZONE_TO]
        
            if CONF_GLOBALID2 in advanced_options:
                user_input[CONF_GLOBALID2] = advanced_options[CONF_GLOBALID2]

            if CONF_INCREASED_LIMIT in advanced_options:
                user_input[CONF_INCREASED_LIMIT] = advanced_options[CONF_INCREASED_LIMIT]

            if CONF_ONLYLINE in filter_options:
                user_input[CONF_ONLYLINE] = filter_options[CONF_ONLYLINE]
        
            if CONF_HIDEDESTINATION in filter_options:
                user_input[CONF_HIDEDESTINATION] = filter_options[CONF_HIDEDESTINATION]
        
            if CONF_ONLYDESTINATION in filter_options:
                user_input[CONF_ONLYDESTINATION] = filter_options[CONF_ONLYDESTINATION]


            if CONF_PROXY_URL in proxy_options:
                user_input[CONF_PROXY_URL] = proxy_options[CONF_PROXY_URL]
        
            if CONF_PROXY_USETIME in proxy_options:
                user_input[CONF_PROXY_USETIME] = proxy_options[CONF_PROXY_USETIME]
        
            if CONF_FORCE_PROXY in proxy_options:
                user_input[CONF_FORCE_PROXY] = proxy_options[CONF_FORCE_PROXY]

            AnotherMVGConfigFlow._flatten_alert_options(user_input, current_data)

            if CONF_MQTT_ENABLED in mqtt_options:
                user_input[CONF_MQTT_ENABLED] = mqtt_options[CONF_MQTT_ENABLED]

            user_input[CONF_MQTT_TOPIC_PREFIX] = AnotherMVGConfigFlow._normalize_mqtt_topic_prefix(
                mqtt_options.get(CONF_MQTT_TOPIC_PREFIX, DEFAULT_MQTT_TOPIC_PREFIX)
            )

            if CONF_MQTT_RETAIN in mqtt_options:
                user_input[CONF_MQTT_RETAIN] = mqtt_options[CONF_MQTT_RETAIN]

            user_input[CONF_MQTT_QOS] = int(
                mqtt_options.get(CONF_MQTT_QOS, DEFAULT_MQTT_QOS)
            )

            if not AnotherMVGConfigFlow._is_valid_mqtt_topic_prefix(user_input[CONF_MQTT_TOPIC_PREFIX]):
                return self.async_show_form(
                    step_id="edit",
                    data_schema=self.options_schema,
                    errors={"base": "invalid_mqtt_topic"},
                )

            # Ensure that empty fields are stored as empty strings
            for key in [CONF_ONLYLINE, CONF_HIDEDESTINATION, CONF_ONLYDESTINATION, 
                        CONF_TIMEZONE_FROM, CONF_TIMEZONE_TO, CONF_ALERT_FOR, CONF_GLOBALID2, CONF_STATS_TEMPLATE, CONF_PROXY_USETIME, CONF_PROXY_URL, CONF_CSS_CODE]:
                if key not in user_input:
                    user_input[key] = ""  # Explicitly set the field to an empty string if it's not in the user_input

            if CONF_MONITOR_TYPE not in user_input:
                user_input[CONF_MONITOR_TYPE] = current_data.get(CONF_MONITOR_TYPE, DEFAULT_MONITOR_TYPE)

            if CONF_UPDATE_MODE not in user_input:
                user_input[CONF_UPDATE_MODE] = current_data.get(CONF_UPDATE_MODE, DEFAULT_UPDATE_MODE)
            
            # Convert selected transport types to a comma-separated string
            if CONF_TRANSPORTTYPES in user_input:
                user_input[CONF_TRANSPORTTYPES] = ','.join(user_input[CONF_TRANSPORTTYPES])

            if CONF_LIMIT in user_input:
                user_input[CONF_LIMIT] = AnotherMVGConfigFlow._normalize_limit(user_input[CONF_LIMIT])
            
            # Save the updated data
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=user_input
            )
            
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self._config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        # Prepare the default values based on current configuration data
        transport_types = DEFAULT_CONF_TRANSPORTTYPES.split(',')
        selected_transport_types = current_data.get(CONF_TRANSPORTTYPES, '').split(',')
        translations = await self.hass.async_add_executor_job(
            AnotherMVGConfigFlow._load_translation,
            self.hass.config.language,
        )
        monitor_type_options = AnotherMVGConfigFlow._monitor_type_options(translations)
        update_mode_options = AnotherMVGConfigFlow._update_mode_options(translations)
        weekday_options = AnotherMVGConfigFlow._alert_weekday_options(translations)
        notify_mode_options = AnotherMVGConfigFlow._alert_notify_mode_options(translations)

        self.options_schema = vol.Schema({
            vol.Required(CONF_NAME,           default=current_data.get(CONF_NAME)): str,
            vol.Optional(CONF_MONITOR_TYPE,   default=current_data.get(CONF_MONITOR_TYPE, DEFAULT_MONITOR_TYPE)): selector({
                "select": {
                    "options": monitor_type_options,
                    "mode": "dropdown"
                }
            }),
            vol.Optional(CONF_UPDATE_MODE,   default=current_data.get(CONF_UPDATE_MODE, DEFAULT_UPDATE_MODE)): selector({
                "select": {
                    "options": update_mode_options,
                    "mode": "dropdown"
                }
            }),
            vol.Required(CONF_GLOBALID,       default=current_data.get(CONF_GLOBALID)): str,
            vol.Optional(CONF_TRANSPORTTYPES, default=selected_transport_types): selector({
                "select": {
                    "options": transport_types,
                    "multiple": True,
                    "custom_value": True
                }
            }),
            vol.Optional(CONF_LIMIT,            default=AnotherMVGConfigFlow._normalize_limit(current_data.get(CONF_LIMIT, DEFAULT_LIMIT))): selector({
                "number": {
                    "min": 1,
                    "max": 80,
                    "step": 1,
                    "mode": "box"
                }
            }),
            vol.Optional(CONF_SORT_BY_REAL_DEPARTURE, description={"suggested_value": current_data.get(CONF_SORT_BY_REAL_DEPARTURE, "")}): bool,
            vol.Optional(CONF_OFFSET_IN_MINUTES, default=current_data.get(CONF_OFFSET_IN_MINUTES, DEFAULT_OFFSET_IN_MINUTES)): int,

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
            # Alerts
            **AnotherMVGConfigFlow._alert_options_schema(current_data, weekday_options, notify_mode_options),
            # Advanced Options
            vol.Required("advanced_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_INCREASED_LIMIT,     description={"suggested_value": current_data.get(CONF_INCREASED_LIMIT, DEFAULT_INCREASED_LIMIT)}): int,
                        vol.Optional(CONF_GLOBALID2,           description={"suggested_value": current_data.get(CONF_GLOBALID2, "")}): str,
                        vol.Optional(CONF_TIMEZONE_FROM,       description={"suggested_value": current_data.get(CONF_TIMEZONE_FROM, "")}): str,
                        vol.Optional(CONF_TIMEZONE_TO,         description={"suggested_value": current_data.get(CONF_TIMEZONE_TO, "")}): str,
                        vol.Optional(CONF_ALERT_FOR,           description={"suggested_value": current_data.get(CONF_ALERT_FOR, "")}): str,
                        #vol.Optional(CONF_STATS_TEMPLATE,      description={"suggested_value": current_data.get(CONF_STATS_TEMPLATE, "")}): str,
                        vol.Optional(CONF_STATS_TEMPLATE,      description={"suggested_value": current_data.get(CONF_STATS_TEMPLATE, "")}): TextSelector({"type": "text", "multiline": True}),
                        vol.Optional(CONF_CSS_CODE,            description={"suggested_value": current_data.get(CONF_CSS_CODE, DEFAULT_CSS_CODE)}): TextSelector({"type": "text", "multiline": True}),
                        vol.Optional(CONF_CSS_CODE_DARKMODE_ONLY, description={"suggested_value": current_data.get(CONF_CSS_CODE_DARKMODE_ONLY, DEFAULT_CSS_CODE_DARKMODE_ONLY)}): bool,
                        vol.Optional(CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER, default=current_data.get(CONF_EXCLUDE_ATTRIBUTES_FROM_RECORDER, DEFAULT_EXCLUDE_ATTRIBUTES_FROM_RECORDER)): bool,
                    }
                ),
                # Whether or not the section is initially collapsed (default = False)
                {"collapsed": True},
            ),
            # Proxy
            vol.Required("proxy_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_PROXY_URL,           description={"suggested_value": current_data.get(CONF_PROXY_URL, "")}): str,
                        vol.Required(CONF_PROXY_USETIME,       description={"suggested_value": current_data.get(CONF_PROXY_USETIME, DEFAULT_PROXY_USETIME)}): int,
                        vol.Optional(CONF_FORCE_PROXY,         description={"suggested_value": current_data.get(CONF_FORCE_PROXY, DEFAULT_FORCE_PROXY)}): bool,
                    }
                ),
                # Whether or not the section is initially collapsed (default = False)
                {"collapsed": True},
            ),
            # MQTT
            vol.Required("mqtt_options"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(CONF_MQTT_ENABLED, default=current_data.get(CONF_MQTT_ENABLED, DEFAULT_MQTT_ENABLED)): bool,
                        vol.Optional(CONF_MQTT_TOPIC_PREFIX, description={"suggested_value": current_data.get(CONF_MQTT_TOPIC_PREFIX, DEFAULT_MQTT_TOPIC_PREFIX)}): str,
                        vol.Optional(CONF_MQTT_QOS, default=str(current_data.get(CONF_MQTT_QOS, DEFAULT_MQTT_QOS))): selector({
                            "select": {
                                "options": ["0", "1", "2"],
                                "mode": "dropdown"
                            }
                        }),
                        vol.Optional(CONF_MQTT_RETAIN, default=current_data.get(CONF_MQTT_RETAIN, DEFAULT_MQTT_RETAIN)): bool,
                    }
                ),
                {"collapsed": True},
            )
        })

        return self.async_show_form(
            step_id="edit",
            data_schema=self.options_schema
        )
