from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .frontend import AnotherMvgCardRegistration

# This file is not used at the moment, because the integration works direct with the sensor
# The domain of your component. Should be equal to the name of your component.
from .const import DOMAIN

# def setup(hass: HomeAssistant, config: ConfigType) -> bool:
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up a skeleton component."""
    # States are in the format DOMAIN.OBJECT_ID.
    # hass.states.set('another_mvg.connections', 'Not used at the moment')
    # Register custom cards
    cards = AnotherMvgCardRegistration(hass)
    await cards.async_register()
    
    # Return boolean to indicate that initialization was successfully.
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Another MVG from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Speichere die Daten aus dem ConfigEntry
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Starte die Sensor-Integration mit den neuen Daten
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])  # Update hier

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)

    return True
