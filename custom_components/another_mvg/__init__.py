from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

# This file is not used at the moment, because the integration works direct with the sensor
# The domain of your component. Should be equal to the name of your component.
from .const import DOMAIN

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up a skeleton component."""
    # States are in the format DOMAIN.OBJECT_ID.
    # hass.states.set('another_mvg.connections', 'Not used at the moment')

    # Return boolean to indicate that initialization was successfully.
    return True
