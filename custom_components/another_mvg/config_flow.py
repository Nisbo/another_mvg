import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
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
        errors = {}
        if user_input is not None:
            if not self._is_valid(user_input):
                errors["base"] = "invalid_input"
            else:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_GLOBALID): str,
            vol.Required(CONF_NAME): str,
            vol.Optional(CONF_ONLYLINE, default=DEFAULT_ONLYLINE): str,
            vol.Optional(CONF_HIDEDESTINATION, default=DEFAULT_HIDEDESTINATION): str,
            vol.Optional(CONF_LIMIT, default=DEFAULT_LIMIT): int,
            vol.Optional(CONF_DOUBLESTATIONNUMBER, default=DEFAULT_CONF_DOUBLESTATIONNUMBER): str,
            vol.Optional(CONF_TRANSPORTTYPES, default=DEFAULT_CONF_TRANSPORTTYPES): str,
            vol.Optional(CONF_GLOBALID2, default=DEFAULT_CONF_GLOBALID2): str,
            vol.Optional(CONF_HIDENAME, default=DEFAULT_HIDENAME): bool,
            vol.Optional(CONF_TIMEZONE_FROM, default=DEFAULT_TIMEZONE_FROM): str,
            vol.Optional(CONF_TIMEZONE_TO, default=DEFAULT_TIMEZONE_TO): str,
            vol.Optional(CONF_ALERT_FOR, default=DEFAULT_ALERT_FOR): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    def _is_valid(self, user_input):
        """Validate user input."""
        return True

class AnotherMVGOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Another MVG."""

    def __init__(self, config_entry):
        """Initialize Another MVG options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required(CONF_GLOBALID): str,
            vol.Required(CONF_NAME): str,
            vol.Optional(CONF_ONLYLINE, default=self.config_entry.options.get(CONF_ONLYLINE, DEFAULT_ONLYLINE)): str,
            vol.Optional(CONF_HIDEDESTINATION, default=self.config_entry.options.get(CONF_HIDEDESTINATION, DEFAULT_HIDEDESTINATION)): str,
            vol.Optional(CONF_LIMIT, default=self.config_entry.options.get(CONF_LIMIT, DEFAULT_LIMIT)): int,
            vol.Optional(CONF_DOUBLESTATIONNUMBER, default=self.config_entry.options.get(CONF_DOUBLESTATIONNUMBER, DEFAULT_CONF_DOUBLESTATIONNUMBER)): str,
            vol.Optional(CONF_TRANSPORTTYPES, default=self.config_entry.options.get(CONF_TRANSPORTTYPES, DEFAULT_CONF_TRANSPORTTYPES)): str,
            vol.Optional(CONF_GLOBALID2, default=self.config_entry.options.get(CONF_GLOBALID2, DEFAULT_CONF_GLOBALID2)): str,
            vol.Optional(CONF_HIDENAME, default=self.config_entry.options.get(CONF_HIDENAME, DEFAULT_HIDENAME)): bool,
            vol.Optional(CONF_TIMEZONE_FROM, default=self.config_entry.options.get(CONF_TIMEZONE_FROM, DEFAULT_TIMEZONE_FROM)): str,
            vol.Optional(CONF_TIMEZONE_TO, default=self.config_entry.options.get(CONF_TIMEZONE_TO, DEFAULT_TIMEZONE_TO)): str,
            vol.Optional(CONF_ALERT_FOR, default=self.config_entry.options.get(CONF_ALERT_FOR, DEFAULT_ALERT_FOR)): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema
        )
