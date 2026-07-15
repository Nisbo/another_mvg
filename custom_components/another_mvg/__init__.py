from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol
from aiohttp import web
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.http import HomeAssistantView
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from .frontend import AnotherMvgCardRegistration

# The domain of your component. Should be equal to the name of your component.
from .const import (
    CONF_ALERT_FOR,
    CONF_CSS_CODE,
    CONF_CSS_CODE_DARKMODE_ONLY,
    CONF_DOUBLESTATIONNUMBER,
    CONF_FORCE_PROXY,
    CONF_GLOBALID,
    CONF_GLOBALID2,
    CONF_HIDEDESTINATION,
    CONF_INCREASED_LIMIT,
    CONF_LIMIT,
    CONF_MONITOR_TYPE,
    CONF_MQTT_ENABLED,
    CONF_MQTT_QOS,
    CONF_MQTT_RETAIN,
    CONF_MQTT_TOPIC_PREFIX,
    CONF_OFFSET_IN_MINUTES,
    CONF_ONLYDESTINATION,
    CONF_ONLYLINE,
    CONF_PROXY_URL,
    CONF_PROXY_USETIME,
    CONF_SORT_BY_REAL_DEPARTURE,
    CONF_STATS_TEMPLATE,
    CONF_TIMEZONE_FROM,
    CONF_TIMEZONE_TO,
    CONF_TRANSPORTTYPES,
    DEFAULT_ALERT_FOR,
    DEFAULT_CONF_GLOBALID2,
    DEFAULT_CONF_TRANSPORTTYPES,
    DEFAULT_CSS_CODE,
    DEFAULT_CSS_CODE_DARKMODE_ONLY,
    DEFAULT_FORCE_PROXY,
    DEFAULT_HIDEDESTINATION,
    DEFAULT_INCREASED_LIMIT,
    DEFAULT_LIMIT,
    DEFAULT_MONITOR_TYPE,
    DEFAULT_MQTT_QOS,
    DEFAULT_MQTT_RETAIN,
    DEFAULT_MQTT_TOPIC_PREFIX,
    DEFAULT_OFFSET_IN_MINUTES,
    DEFAULT_ONLYDESTINATION,
    DEFAULT_ONLYLINE,
    DEFAULT_PROXY_URL,
    DEFAULT_PROXY_USETIME,
    DEFAULT_SORT_BY_REAL_DEPARTURE,
    DEFAULT_STATS_TEMPLATE,
    DEFAULT_TIMEZONE_FROM,
    DEFAULT_TIMEZONE_TO,
    DOMAIN,
    MONITOR_TYPE_ARRIVAL,
    MONITOR_TYPE_DEPARTURE,
    MVGException,
    SERVICE_REFRESH,
)

_LOGGER = logging.getLogger(__name__)

REFRESH_SERVICE_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids})


class AnotherMvgStationSearchView(HomeAssistantView):
    """Search MVG stations for the search card."""

    url = "/api/another_mvg/search_stations"
    name = "api:another_mvg:search_stations"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]
        query = request.query.get("query", "").strip()
        include_non_stations = request.query.get("includeNonStations", "").lower() in ("1", "true", "yes")

        if len(query) < 2:
            return web.json_response({"stations": []})

        session = async_get_clientsession(hass)
        try:
            async with session.get(
                "https://www.mvg.de/api/bgw-pt/v3/locations",
                params={"query": query},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    return web.json_response(
                        {"stations": [], "error": "station_search_failed"},
                        status=response.status,
                    )
                data = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("AnotherMVG: Search card station search failed: %s", err)
            return web.json_response(
                {"stations": [], "error": "station_search_failed"},
                status=502,
            )

        stations = []
        for entry in data:
            location_type = entry.get("type", "")
            is_station = location_type == "STATION" and entry.get("globalId") and entry.get("transportTypes")
            is_coordinate_location = (
                include_non_stations
                and location_type in ("ADDRESS", "POI")
                and entry.get("latitude") is not None
                and entry.get("longitude") is not None
            )
            if not is_station and not is_coordinate_location:
                continue
            stations.append(
                {
                    "name": entry.get("name", ""),
                    "globalId": entry.get("globalId", ""),
                    "transportTypes": entry.get("transportTypes", []),
                    "type": location_type or "STATION",
                    "latitude": entry.get("latitude"),
                    "longitude": entry.get("longitude"),
                    "place": entry.get("place", ""),
                    "postCode": entry.get("postCode", ""),
                    "street": entry.get("street", ""),
                    "houseNumber": entry.get("houseNumber", ""),
                }
            )

        return web.json_response({"stations": stations})


class AnotherMvgNearbyStationSearchView(HomeAssistantView):
    """Search MVG stations near browser coordinates for the search card."""

    url = "/api/another_mvg/search_nearby_stations"
    name = "api:another_mvg:search_nearby_stations"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]

        try:
            latitude = float(request.query.get("latitude", ""))
            longitude = float(request.query.get("longitude", ""))
        except (TypeError, ValueError):
            return web.json_response(
                {"stations": [], "error": "invalid_coordinates"},
                status=400,
            )

        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            return web.json_response(
                {"stations": [], "error": "invalid_coordinates"},
                status=400,
            )

        params = {"latitude": latitude, "longitude": longitude}
        try:
            radius = int(request.query.get("radiusInMeter", "1000"))
        except (TypeError, ValueError):
            radius = 1000
        if radius > 0:
            params["radiusInMeter"] = max(50, min(5000, radius))

        session = async_get_clientsession(hass)
        try:
            async with session.get(
                "https://www.mvg.de/api/bgw-pt/v3/stations/nearby",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    return web.json_response(
                        {"stations": [], "error": "nearby_station_search_failed"},
                        status=response.status,
                    )
                data = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("AnotherMVG: Search card nearby station search failed: %s", err)
            return web.json_response(
                {"stations": [], "error": "nearby_station_search_failed"},
                status=502,
            )

        stations = [
            {
                "name": entry.get("name", ""),
                "globalId": entry.get("globalId", ""),
                "transportTypes": entry.get("transportTypes", []),
                "distanceInMeters": entry.get("distanceInMeters"),
            }
            for entry in data
            if entry.get("globalId") and entry.get("transportTypes")
        ]

        return web.json_response({"stations": stations})


class AnotherMvgSearchMonitorView(HomeAssistantView):
    """Return normalized departures or arrivals for the search card."""

    url = "/api/another_mvg/search_monitor"
    name = "api:another_mvg:search_monitor"
    requires_auth = True

    async def post(self, request):
        try:
            payload = await request.json()
        except ValueError:
            return web.json_response({"error": "invalid_json"}, status=400)

        global_id = str(payload.get("globalId", "")).strip()
        if not global_id:
            return web.json_response({"error": "missing_global_id"}, status=400)

        monitor_type = payload.get(CONF_MONITOR_TYPE, DEFAULT_MONITOR_TYPE)
        if monitor_type not in (MONITOR_TYPE_DEPARTURE, MONITOR_TYPE_ARRIVAL):
            monitor_type = DEFAULT_MONITOR_TYPE

        transport_types = payload.get(
            CONF_TRANSPORTTYPES,
            payload.get("transportTypes", DEFAULT_CONF_TRANSPORTTYPES),
        )
        if isinstance(transport_types, list):
            transport_types = ",".join(str(item).strip() for item in transport_types if str(item).strip())
        transport_types = transport_types or DEFAULT_CONF_TRANSPORTTYPES

        try:
            limit = max(1, min(80, int(payload.get(CONF_LIMIT, DEFAULT_LIMIT))))
        except (TypeError, ValueError):
            limit = DEFAULT_LIMIT

        try:
            offset = max(0, int(payload.get(CONF_OFFSET_IN_MINUTES, DEFAULT_OFFSET_IN_MINUTES)))
        except (TypeError, ValueError):
            offset = DEFAULT_OFFSET_IN_MINUTES

        station_name = str(payload.get("name") or global_id)

        config = {
            CONF_GLOBALID: global_id,
            CONF_GLOBALID2: DEFAULT_CONF_GLOBALID2,
            CONF_DOUBLESTATIONNUMBER: "",
            CONF_MONITOR_TYPE: monitor_type,
            "name": station_name,
            CONF_LIMIT: limit,
            CONF_TRANSPORTTYPES: transport_types,
            CONF_OFFSET_IN_MINUTES: offset,
            CONF_ONLYLINE: DEFAULT_ONLYLINE,
            CONF_HIDEDESTINATION: DEFAULT_HIDEDESTINATION,
            CONF_ONLYDESTINATION: DEFAULT_ONLYDESTINATION,
            CONF_TIMEZONE_FROM: DEFAULT_TIMEZONE_FROM,
            CONF_TIMEZONE_TO: DEFAULT_TIMEZONE_TO,
            CONF_ALERT_FOR: DEFAULT_ALERT_FOR,
            CONF_STATS_TEMPLATE: DEFAULT_STATS_TEMPLATE,
            CONF_INCREASED_LIMIT: DEFAULT_INCREASED_LIMIT,
            CONF_SORT_BY_REAL_DEPARTURE: DEFAULT_SORT_BY_REAL_DEPARTURE,
            CONF_PROXY_URL: DEFAULT_PROXY_URL,
            CONF_PROXY_USETIME: DEFAULT_PROXY_USETIME,
            CONF_FORCE_PROXY: DEFAULT_FORCE_PROXY,
            CONF_CSS_CODE: DEFAULT_CSS_CODE,
            CONF_CSS_CODE_DARKMODE_ONLY: DEFAULT_CSS_CODE_DARKMODE_ONLY,
            CONF_MQTT_ENABLED: False,
            CONF_MQTT_TOPIC_PREFIX: DEFAULT_MQTT_TOPIC_PREFIX,
            CONF_MQTT_RETAIN: DEFAULT_MQTT_RETAIN,
            CONF_MQTT_QOS: DEFAULT_MQTT_QOS,
        }

        from .sensor import ConnectionInfo, Departure

        monitor = ConnectionInfo(request.app["hass"], config)
        try:
            departures = await monitor.get_departures()
        except MVGException as err:
            _LOGGER.warning("AnotherMVG: Search card monitor request failed: %s", err)
            return web.json_response({"departures": [], "error": "monitor_request_failed"}, status=502)

        return web.json_response(
            {
                "name": station_name,
                "globalId": global_id,
                "monitor_type": monitor_type,
                "departures": [
                    departure.to_dict() if isinstance(departure, Departure) else departure
                    for departure in departures
                ],
                "dataOutdated": monitor.dataOutdated,
                "maxConnectionErrorTime": monitor.maxConnectionErrorTime,
            }
        )


class AnotherMvgRouteSearchView(HomeAssistantView):
    """Return normalized route suggestions for the route card."""

    url = "/api/another_mvg/search_routes"
    name = "api:another_mvg:search_routes"
    requires_auth = True

    async def post(self, request):
        try:
            payload = await request.json()
        except ValueError:
            return web.json_response({"routes": [], "error": "invalid_json"}, status=400)

        origin_location = payload.get("origin") if isinstance(payload.get("origin"), dict) else {}
        destination_location = payload.get("destination") if isinstance(payload.get("destination"), dict) else {}
        origin_global_id = str(origin_location.get("globalId") or payload.get("originGlobalId", "")).strip()
        destination_global_id = str(destination_location.get("globalId") or payload.get("destinationGlobalId", "")).strip()

        def valid_coordinate_location(location):
            try:
                latitude = float(location.get("latitude"))
                longitude = float(location.get("longitude"))
            except (TypeError, ValueError):
                return False
            return -90 <= latitude <= 90 and -180 <= longitude <= 180

        if (
            not origin_global_id
            and not valid_coordinate_location(origin_location)
        ) or (
            not destination_global_id
            and not valid_coordinate_location(destination_location)
        ):
            return web.json_response(
                {"routes": [], "error": "missing_route_stations"},
                status=400,
            )

        transport_types = payload.get(
            CONF_TRANSPORTTYPES,
            payload.get("transportTypes", DEFAULT_CONF_TRANSPORTTYPES),
        )
        if isinstance(transport_types, str):
            transport_type_list = [
                item.strip()
                for item in transport_types.split(",")
                if item.strip()
            ]
        elif isinstance(transport_types, list):
            transport_type_list = [
                str(item).strip()
                for item in transport_types
                if str(item).strip()
            ]
        else:
            transport_type_list = [
                item.strip()
                for item in DEFAULT_CONF_TRANSPORTTYPES.split(",")
                if item.strip()
            ]
        transport_types = ",".join(transport_type_list) or DEFAULT_CONF_TRANSPORTTYPES

        params = {
            "transportTypes": transport_types,
            "routeType": str(payload.get("routeType") or "LEAST_TIME"),
            "changeSpeed": str(payload.get("changeSpeed") or "NORMAL"),
        }

        def add_route_location_params(prefix: str, location: dict, global_id: str) -> None:
            location_type = str(location.get("type") or "STATION").upper()
            if global_id and location_type == "STATION":
                params[f"{prefix}StationGlobalId"] = global_id
                return
            if valid_coordinate_location(location):
                params[f"{prefix}Latitude"] = str(float(location.get("latitude")))
                params[f"{prefix}Longitude"] = str(float(location.get("longitude")))
                return
            if global_id:
                params[f"{prefix}StationGlobalId"] = global_id

        add_route_location_params("origin", origin_location, origin_global_id)
        add_route_location_params("destination", destination_location, destination_global_id)

        routing_datetime = str(payload.get("routingDateTime", "")).strip()
        if routing_datetime:
            params["routingDateTime"] = routing_datetime
            params["routingDateTimeIsArrival"] = str(bool(payload.get("routingDateTimeIsArrival", False))).lower()

        session = async_get_clientsession(request.app["hass"])
        try:
            async with session.get(
                "https://www.mvg.de/api/bgw-pt/v3/routes",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status != 200:
                    return web.json_response(
                        {"routes": [], "error": "route_search_failed"},
                        status=response.status,
                    )
                data = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("AnotherMVG: Route card request failed: %s", err)
            return web.json_response(
                {"routes": [], "error": "route_search_failed"},
                status=502,
            )

        def station_departure_time(station):
            return (
                station.get("plannedDeparture")
                or station.get("realtimeDeparture")
                or station.get("plannedArrival")
                or station.get("realtimeArrival")
                or ""
            )

        def station_arrival_time(station):
            return (
                station.get("plannedArrival")
                or station.get("realtimeArrival")
                or station.get("plannedDeparture")
                or station.get("realtimeDeparture")
                or ""
            )

        def station_name(station):
            return station.get("name") or station.get("stationGlobalId") or ""

        def normalize_intermediate_stop(station):
            return {
                "name": station_name(station),
                "departureTime": station_departure_time(station),
                "arrivalTime": station_arrival_time(station),
                "plannedDepartureTime": station.get("plannedDeparture"),
                "realtimeDepartureTime": station.get("realtimeDeparture"),
                "plannedArrivalTime": station.get("plannedArrival"),
                "realtimeArrivalTime": station.get("realtimeArrival"),
                "departureDelayInMinutes": station.get("departureDelayInMinutes"),
                "arrivalDelayInMinutes": station.get("arrivalDelayInMinutes"),
                "platform": station.get("platform"),
                "platformChanged": station.get("platformChanged", False),
            }

        def normalize_part(part):
            line = part.get("line") or {}
            from_station = part.get("from") or {}
            to_station = part.get("to") or {}
            infos = part.get("infos") or []
            messages = part.get("messages") or []

            return {
                "fromName": station_name(from_station),
                "toName": station_name(to_station),
                "departureTime": station_departure_time(from_station),
                "arrivalTime": station_arrival_time(to_station),
                "plannedDepartureTime": from_station.get("plannedDeparture"),
                "realtimeDepartureTime": from_station.get("realtimeDeparture"),
                "plannedArrivalTime": to_station.get("plannedArrival"),
                "realtimeArrivalTime": to_station.get("realtimeArrival"),
                "departureDelayInMinutes": from_station.get("departureDelayInMinutes"),
                "arrivalDelayInMinutes": to_station.get("arrivalDelayInMinutes"),
                "platform": from_station.get("platform"),
                "platformChanged": from_station.get("platformChanged", False),
                "lineLabel": line.get("label", ""),
                "transportType": line.get("transportType", ""),
                "sev": line.get("sev", False),
                "destination": line.get("destination", ""),
                "distance": part.get("distance"),
                "interchangePathDistance": part.get("interchangePathDistance"),
                "interchangePathDurationInMinutes": part.get("interchangePathDurationInMinutes"),
                "intermediateStopCount": len(part.get("intermediateStops") or []),
                "intermediateStops": [
                    normalize_intermediate_stop(stop)
                    for stop in part.get("intermediateStops") or []
                ],
                "changeStatus": part.get("changeStatus", ""),
                "realTime": part.get("realTime", False),
                "infos": [
                    info.get("message", "")
                    for info in infos
                    if info.get("message")
                ],
                "messages": [
                    message if isinstance(message, str) else message.get("message", "")
                    for message in messages
                    if message
                ],
                "infoDetails": [
                    {
                        "title": info.get("message", ""),
                        "description": info.get("sourceMessage") or info.get("description") or "",
                        "type": info.get("type", ""),
                        "network": info.get("network", ""),
                    }
                    for info in infos
                    if info.get("message") or info.get("sourceMessage")
                ],
            }

        try:
            limit = max(1, min(10, int(payload.get("limit", 5) or 5)))
        except (TypeError, ValueError):
            limit = 5

        def route_sort_time(route):
            parts = route.get("parts") or []
            first_part = parts[0] if parts else {}
            from_station = first_part.get("from") or {}
            return station_departure_time(from_station)

        def route_signature(route):
            signature_parts = []
            for part in route.get("parts") or []:
                line = part.get("line") or {}
                from_station = part.get("from") or {}
                to_station = part.get("to") or {}
                signature_parts.append(
                    "|".join(
                        [
                            line.get("transportType", ""),
                            line.get("label", ""),
                            station_name(from_station),
                            station_name(to_station),
                            station_departure_time(from_station),
                            station_arrival_time(to_station),
                        ]
                    )
                )
            return "||".join(signature_parts)

        unique_routes = []
        seen_routes = set()
        for route in sorted(data, key=route_sort_time):
            route_key = route.get("uniqueId") or route_signature(route)
            if route_key in seen_routes:
                continue
            seen_routes.add(route_key)
            unique_routes.append(route)

        routes = []
        for route in unique_routes[:limit]:
            parts = [normalize_part(part) for part in route.get("parts", [])]
            if not parts:
                continue
            public_parts = [
                part
                for part in parts
                if part["transportType"] not in ("PEDESTRIAN", "WALK")
            ]
            routes.append(
                {
                    "uniqueId": route.get("uniqueId"),
                    "departureTime": parts[0]["departureTime"],
                    "arrivalTime": parts[-1]["arrivalTime"],
                    "distance": route.get("distance"),
                    "transfers": max(0, len(public_parts) - 1),
                    "parts": parts,
                }
            )

        return web.json_response({"routes": routes})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up a skeleton component."""
    # States are in the format DOMAIN.OBJECT_ID.
    # hass.states.set('another_mvg.connections', 'Not used at the moment')
    # Register custom cards
    cards = AnotherMvgCardRegistration(hass)
    await cards.async_register()
    hass.http.register_view(AnotherMvgStationSearchView)
    hass.http.register_view(AnotherMvgNearbyStationSearchView)
    hass.http.register_view(AnotherMvgSearchMonitorView)
    hass.http.register_view(AnotherMvgRouteSearchView)

    async def async_handle_refresh(call) -> None:
        """Refresh a manual Another MVG sensor."""
        entity_ids = call.data[ATTR_ENTITY_ID]
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
        entities = hass.data.get(DOMAIN, {}).get("entities", {})

        for entity_id in entity_ids:
            entity = next(
                (
                    entity
                    for entity in entities.values()
                    if getattr(entity, "entity_id", None) == entity_id
                ),
                None,
            )

            if entity is None:
                _LOGGER.warning(
                    "AnotherMVG: Manual refresh requested for unknown entity %s",
                    entity_id,
                )
                continue

            await entity.async_manual_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH,
            async_handle_refresh,
            schema=REFRESH_SERVICE_SCHEMA,
        )
    
    # Return boolean to indicate that initialization was successfully.
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Another MVG from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("entries", {})
    hass.data[DOMAIN].setdefault("entities", {})

    # Speichere die Daten aus dem ConfigEntry
    hass.data[DOMAIN]["entries"][entry.entry_id] = entry.data

    # Starte die Sensor-Integration mit den neuen Daten
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])  # Update hier

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].get("entries", {}).pop(entry.entry_id, None)
    hass.data[DOMAIN].get("entities", {}).pop(entry.entry_id, None)

    return True
