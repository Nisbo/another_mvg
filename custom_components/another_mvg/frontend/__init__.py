"""another_mvg Frontend"""
# thx to @msp1974 for providing the layout for this code
# https://github.com/asantaga/wiserHomeAssistantPlatform/blob/master/custom_components/wiser/frontend/__init__.py

import logging
import os
from pathlib import Path

import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.components.lovelace import MODE_STORAGE, LovelaceData
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later

from ..const import ANOTHER_MVG_CARDS, URL_BASE

_LOGGER = logging.getLogger(__name__)

LIVE_MAP_ORIGIN      = "https://s-bahn-muenchen-live.de"
LIVE_MAP_PROXY_BASE  = "/another_mvg_livemap"
GEOPS_API_ORIGIN     = "https://api.geops.io"
GEOPS_API_PROXY_BASE = "/another_mvg_geops_api"

class AnotherMvgLiveMapProxyView(HomeAssistantView):
    """Proxy S-Bahn live map and hide disruption info if requested."""

    url = LIVE_MAP_PROXY_BASE
    extra_urls = [f"{LIVE_MAP_PROXY_BASE}/{{path:.*}}"]
    name = "api:another_mvg:livemap_proxy"
    requires_auth = False

    async def get(self, request, path=""):
        hass = request.app["hass"]
        session = async_get_clientsession(hass)

        target_url = f"{LIVE_MAP_ORIGIN}/{path or ''}"
        if request.query_string:
            target_url = f"{target_url}?{request.query_string}"

        async with session.get(
            target_url,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            body = await resp.read()
            content_type = resp.headers.get(
                "Content-Type",
                "application/octet-stream",
            )

        if "text/html" in content_type:
            text = body.decode("utf-8", errors="replace")

            text = text.replace('src="/', f'src="{LIVE_MAP_PROXY_BASE}/')
            text = text.replace('href="/', f'href="{LIVE_MAP_PROXY_BASE}/')

            route_fix = f"""
<script>
(() => {{
  if (window.location.pathname.startsWith("{LIVE_MAP_PROXY_BASE}")) {{
    window.history.replaceState(null, "", "/" + window.location.search + window.location.hash);
  }}
}})();
</script>
"""
            text = text.replace("</head>", f"{route_fix}</head>")

            inject = """
<script>
(() => {
  if (new URLSearchParams(window.location.search).get("disruption") !== "false") return;

  const hide = () => {
    document.querySelectorAll("#platform-info, #disruption-info").forEach((el) => el.remove());
  };

  hide();

  new MutationObserver(hide).observe(document.documentElement, {
    childList: true,
    subtree: true
  });
})();
</script>
"""
            text = text.replace("</body>", f"{inject}</body>")
            return web.Response(text=text, content_type="text/html")

        if "javascript" in content_type:
            text = body.decode("utf-8", errors="replace")
            proxy_origin = f"{request.scheme}://{request.host}"
            text = text.replace(GEOPS_API_ORIGIN, f"{proxy_origin}{GEOPS_API_PROXY_BASE}")
            return web.Response(text=text, content_type=content_type)

        return web.Response(body=body, headers={"Content-Type": content_type})

class AnotherMvgGeopsApiProxyView(HomeAssistantView):
    """Proxy geops API requests used by the proxied S-Bahn live map."""

    url = GEOPS_API_PROXY_BASE
    extra_urls = [f"{GEOPS_API_PROXY_BASE}/{{path:.*}}"]
    name = "api:another_mvg:geops_api_proxy"
    requires_auth = False

    async def get(self, request, path=""):
        hass = request.app["hass"]
        session = async_get_clientsession(hass)

        target_url = f"{GEOPS_API_ORIGIN}/{path or ''}"
        if request.query_string:
            target_url = f"{target_url}?{request.query_string}"
            
        if path.startswith("moco3/v1/") and "/export" in path:
            return web.json_response({
                "paginatedSituations": {
                    "results": []
                }
            })
            
        async with session.get(
            target_url,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            body = await resp.read()
            content_type = resp.headers.get(
                "Content-Type",
                "application/octet-stream",
            )

        return web.Response(body=body, headers={"Content-Type": content_type})

class AnotherMvgCardRegistration:
    """Register Javascript modules."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise."""
        self.hass = hass
        self.lovelace: LovelaceData = self.hass.data.get("lovelace")

        # Fix for change to name of mode to reousrce_mode in 2026.2
        if MAJOR_VERSION >= 2026 and MINOR_VERSION >= 2:
            self.resource_mode = self.lovelace.resource_mode
        else:
            self.resource_mode = self.lovelace.mode

    async def async_register(self):
        """Register view_assist path."""
        await self._async_register_path()
        
        self.hass.http.register_view(AnotherMvgLiveMapProxyView)
        self.hass.http.register_view(AnotherMvgGeopsApiProxyView)
        
        if self.lovelace and self.resource_mode == MODE_STORAGE:
            await self._async_wait_for_lovelace_resources()

    # install card resources
    async def _async_register_path(self):
        """Register resource path if not already registered."""
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, Path(__file__).parent, False)]
            )
            _LOGGER.debug("Registered resource path from %s", Path(__file__).parent)
        except RuntimeError:
            # Runtime error is likley this is already registered.
            _LOGGER.debug("Resource path already registered")

    async def _async_wait_for_lovelace_resources(self) -> None:
        """Wait for lovelace resources to have loaded."""

        async def _check_lovelace_resources_loaded(now):
            if self.lovelace.resources.loaded:
                await self._async_register_modules()
            else:
                _LOGGER.debug(
                    "Unable to install resources because Lovelace resources have not yet loaded.  Trying again in 5 seconds"
                )
                async_call_later(self.hass, 5, _check_lovelace_resources_loaded)

        await _check_lovelace_resources_loaded(0)

    async def _async_register_modules(self):
        """Register modules if not already registered."""
        _LOGGER.debug("Installing javascript modules")

        # Get resources already registered
        resources = [
            resource
            for resource in self.lovelace.resources.async_items()
            if resource["url"].startswith(URL_BASE)
        ]

        for module in ANOTHER_MVG_CARDS:
            url = f"{URL_BASE}/{module.get('filename')}"

            card_registered = False

            for resource in resources:
                if self._get_resource_path(resource["url"]) == url:
                    card_registered = True
                    # check version
                    if self._get_resource_version(resource["url"]) != module.get(
                        "version"
                    ):
                        # Update card version
                        _LOGGER.debug(
                            "Updating %s to version %s",
                            module.get("name"),
                            module.get("version"),
                        )
                        await self.lovelace.resources.async_update_item(
                            resource.get("id"),
                            {
                                "res_type": "module",
                                "url": url + "?v=" + module.get("version"),
                            },
                        )
                        # Remove old gzipped files
                        await self.async_remove_gzip_files()
                    else:
                        _LOGGER.debug(
                            "%s already registered as version %s",
                            module.get("name"),
                            module.get("version"),
                        )

            if not card_registered:
                _LOGGER.debug(
                    "Registering %s as version %s",
                    module.get("name"),
                    module.get("version"),
                )
                await self.lovelace.resources.async_create_item(
                    {"res_type": "module", "url": url + "?v=" + module.get("version")}
                )

    def _get_resource_path(self, url: str):
        return url.split("?")[0]

    def _get_resource_version(self, url: str):
        if version := url.split("?")[1].replace("v=", ""):
            return version
        return 0

    async def async_unregister(self):
        """Unload lovelace module resource."""
        if self.resource_mode == MODE_STORAGE:
            for module in ANOTHER_MVG_CARDS:
                url = f"{URL_BASE}/{module.get('filename')}"
                wiser_resources = [
                    resource
                    for resource in self.lovelace.resources.async_items()
                    if str(resource["url"]).startswith(url)
                ]
                for resource in wiser_resources:
                    await self.lovelace.resources.async_delete_item(resource.get("id"))

    async def async_remove_gzip_files(self):
        """Remove cached gzip files."""
        await self.hass.async_add_executor_job(self.remove_gzip_files)

    def remove_gzip_files(self):
        """Remove cached gzip files."""
        path = self.hass.config.path("custom_components/another_mvg/frontend")

        gzip_files = [
            filename for filename in os.listdir(path) if filename.endswith(".gz")
        ]

        for file in gzip_files:
            try:
                if (
                    Path.stat(f"{path}/{file}").st_mtime
                    < Path.stat(f"{path}/{file.replace('.gz', '')}").st_mtime
                ):
                    _LOGGER.debug("Removing older gzip file - %s", file)
                    Path.unlink(f"{path}/{file}")
            except OSError:
                pass
