"""another_mvg Frontend"""
# thx to @msp1974 for providing the layout for this code
# https://github.com/asantaga/wiserHomeAssistantPlatform/blob/master/custom_components/wiser/frontend/__init__.py
import logging
import os
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.event import async_call_later

from ..const import URL_BASE, ANOTHER_MVG_CARDS

_LOGGER = logging.getLogger(__name__)

class AnotherMvgCardRegistration:
    def __init__(self, hass):
        self.hass = hass

    async def async_register(self):
        await self.async_register_another_mvg_path()
        if self.hass.data["lovelace"].mode == "storage":
            await self.async_wait_for_lovelace_resources()

    # install card resources
    async def async_register_another_mvg_path(self):
        # Register custom cards path if not already registered
        await self.hass.http.async_register_static_paths([
            StaticPathConfig(
                URL_BASE,
                self.hass.config.path("custom_components/another_mvg/frontend"),
                False
            )
        ])

    async def async_wait_for_lovelace_resources(self) -> None:
        async def check_lovelace_resources_loaded(now):
            if self.hass.data["lovelace"].resources.loaded:
                await self.async_register_another_mvg_cards()
            else:
                _LOGGER.debug(
                    "Unable to install another_mvg card resources because Lovelace resources not yet loaded. Trying again in 5 seconds."
                )
                async_call_later(self.hass, 5, check_lovelace_resources_loaded)

        await check_lovelace_resources_loaded(0)

    async def async_register_another_mvg_cards(self):
        _LOGGER.debug("Installing Lovelace resources for another_mvg cards")

        # Get resources already registered
        another_mvg_resources = [
            resource
            for resource in self.hass.data["lovelace"].resources.async_items()
            if resource["url"].startswith(URL_BASE)
        ]

        for card in ANOTHER_MVG_CARDS:
            url = f"{URL_BASE}/{card.get('filename')}"

            card_registered = False

            for res in another_mvg_resources:
                if self.get_resource_path(res["url"]) == url:
                    card_registered = True
                    # check version
                    if self.get_resource_version(res["url"]) != card.get("version"):
                        # Update card version
                        _LOGGER.debug(
                            "Updating %s to version %s",
                            card.get("name"),
                            card.get("version"),
                        )
                        await self.hass.data["lovelace"]["resources"].async_update_item(
                            res.get("id"),
                            {
                                "res_type": "module",
                                "url": url + "?v=" + card.get("version"),
                            },
                        )
                        # Remove old gzipped files
                        await self.async_remove_gzip_files()
                    else:
                        _LOGGER.debug(
                            "%s already registered as version %s",
                            card.get("name"),
                            card.get("version"),
                        )

            if not card_registered:
                _LOGGER.debug(
                    "Registering %s as version %s",
                    card.get("name"),
                    card.get("version"),
                )
                await self.hass.data["lovelace"]["resources"].async_create_item(
                    {"res_type": "module", "url": url + "?v=" + card.get("version")}
                )

    def get_resource_path(self, url: str):
        return url.split("?")[0]

    def get_resource_version(self, url: str):
        try:
            return url.split("?")[1].replace("v=", "")
        except Exception:
            return 0

    async def async_unregister(self):
        # Unload lovelace module resource
        if self.hass.data["lovelace"]["mode"] == "storage":
            for card in ANOTHER_MVG_CARDS:
                url = f"{URL_BASE}/{card.get('filename')}"
                another_mvg_resources = [
                    resource
                    for resource in self.hass.data["lovelace"][
                        "resources"
                    ].async_items()
                    if str(resource["url"]).startswith(url)
                ]
                for resource in another_mvg_resources:
                    await self.hass.data["lovelace"]["resources"].async_delete_item(
                        resource.get("id")
                    )

    async def async_remove_gzip_files(self):
        path = self.hass.config.path("custom_components/another_mvg/frontend")
        gzip_files = [
            filename for filename in os.listdir(path) if filename.endswith(".gz")
        ]

        for file in gzip_files:
            try:
                if os.path.getmtime(f"{path}/{file}") < os.path.getmtime(
                    f"{path}/{file.replace('.gz','')}"
                ):
                    _LOGGER.debug(f"Removing older gzip file - {file}")
                    os.remove(f"{path}/{file}")
            except Exception:
                pass
