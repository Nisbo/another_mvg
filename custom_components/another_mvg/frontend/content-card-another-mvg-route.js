/* AnotherMVG Route */
const version = "3.0.0-BETA-11.0";
const routeFavoritesStorageKey = "another_mvg_route_favorites_v1";
const routeTransportTypes = ["SBAHN", "UBAHN", "TRAM", "BUS", "REGIONAL_BUS", "BAHN"];
const defaultRouteTransportTypes = ["SBAHN", "UBAHN", "TRAM", "BUS", "REGIONAL_BUS"];

class ContentAnotherMVGRoute extends HTMLElement {
    constructor() {
        super();

        console.log(
            "%cAnotherMVG-Route %cv" + version,
            "color:#fff;background:#2196f3;padding:2px 6px;border-radius:3px;",
            "color:#fff;background:#4caf50;padding:2px 6px;border-radius:3px;"
        );

        this._originQuery = "";
        this._destinationQuery = "";
        this._originResults = [];
        this._destinationResults = [];
        this._originStation = null;
        this._destinationStation = null;
        this._routes = [];
        this._loading = false;
        this._loadingEarlier = false;
        this._loadingLater = false;
        this._searchingOrigin = false;
        this._searchingDestination = false;
        this._locatingOrigin = false;
        this._locatingDestination = false;
        this._infoPopup = null;
        this._expandedStops = new Set();
        this._collapsedRoutes = new Set();
        this._expandedRoutes = new Set();
        this._showFavorites = false;
        this._showFilters = false;
        this._routeFilters = null;
        this._favoriteMessage = "";
        this._pendingDeleteFavorite = null;
        this._error = "";
        this._translationsRequested = false;
        this._translationsLoaded = false;
    }

    set hass(hass) {
        this._hass = hass;
        const translationsWereLoaded = this._translationsLoaded;

        if (!this._translationsRequested) {
            this._translationsRequested = true;
            this.loadTranslations(hass);
        }

        if (!this._translationsLoaded) {
            if (this.hasTranslation("frontend.column_line")) {
                this._translationsLoaded = true;
            }
        }

        if (!this.content || (!translationsWereLoaded && this._translationsLoaded)) {
            this.render();
        }
    }

    async loadTranslations(hass) {
        try {
            await Promise.all([
                hass.loadBackendTranslation("frontend", "another_mvg"),
                hass.loadBackendTranslation("cardeditor", "another_mvg")
            ]);
            this._translationsLoaded = this.hasTranslation("frontend.column_line");
            this.render();
        } catch (err) {
            console.warn("AnotherMVG-Route - translation load failed", err);
        }
    }

    hasTranslation(key) {
        const fullKey = `component.another_mvg.${key}`;
        const translated = this._hass?.localize(fullKey);
        return Boolean(translated && translated !== fullKey);
    }

    translateIfAvailable(key) {
        const fullKey = `component.another_mvg.${key}`;
        const translated = this._hass?.localize(fullKey);
        return translated && translated !== fullKey ? translated : "";
    }

    localize(key, fallback) {
        const translated = this._hass?.localize(`component.another_mvg.${key}`);
        return translated && translated !== `component.another_mvg.${key}` ? translated : fallback;
    }

    escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    formatTime(value) {
        if (!value) return "";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    formatDuration(route) {
        const start = new Date(route.departureTime);
        const end = new Date(route.arrivalTime);
        if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return "";
        const minutes = Math.max(0, Math.round((end.getTime() - start.getTime()) / 60000));
        return `${minutes} min`;
    }

    formatMinutes(minutes) {
        const value = Number(minutes);
        if (!Number.isFinite(value) || value < 0) return "";
        return `${Math.round(value)} min`;
    }

    formatDelay(minutes) {
        if (minutes === undefined || minutes === null || Number(minutes) === 0) return "";
        const value = Number(minutes);
        return value > 0 ? `+${value}` : `${value}`;
    }

    addMinutes(value, minutes) {
        if (!value || minutes === undefined || minutes === null || Number(minutes) === 0) return value || "";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value || "";
        date.setMinutes(date.getMinutes() + Number(minutes));
        return date.toISOString();
    }

    getDisplayTime(value, realtimeValue, delayMinutes) {
        const mode = this.config.timeDisplayMode || "delay";
        const planned = value || "";
        const delay = this.formatDelay(delayMinutes);
        const realtime = realtimeValue || this.addMinutes(planned, delayMinutes);

        if (mode === "planned") {
            return `<span>${this.escapeHtml(this.formatTime(planned))}</span>`;
        }

        if (mode === "realtime") {
            const time = this.formatTime(delay ? realtime : planned);
            return `<span class="${delay ? "delay" : ""}">${this.escapeHtml(time)}</span>`;
        }

        return `
            <span>
                ${this.escapeHtml(this.formatTime(planned))}
                ${delay ? `<span class="time-delay delay">${this.escapeHtml(delay)}</span>` : ""}
            </span>
        `;
    }

    getSummaryDisplayTime(value, realtimeValue, delayMinutes) {
        return this.getDisplayTime(value, realtimeValue, delayMinutes)
            .replace(/<span/g, "<span class=\"summary-time\"")
            .replace(/class="summary-time" class="/g, "class=\"summary-time ");
    }

    getEffectiveRouteDepartureTime(route) {
        const firstPart = (route.parts || [])[0] || {};
        const planned = firstPart.plannedDepartureTime || firstPart.departureTime || route.departureTime;
        const realtime = firstPart.realtimeDepartureTime || this.addMinutes(planned, firstPart.departureDelayInMinutes);
        return new Date(realtime || planned).getTime();
    }

    sortRoutes(routes) {
        if ((this.config.routeSortMode || "api") !== "realtime_departure") {
            return routes;
        }

        return [...routes].sort((left, right) => {
            const leftTime = this.getEffectiveRouteDepartureTime(left);
            const rightTime = this.getEffectiveRouteDepartureTime(right);
            if (Number.isNaN(leftTime) && Number.isNaN(rightTime)) return 0;
            if (Number.isNaN(leftTime)) return 1;
            if (Number.isNaN(rightTime)) return -1;
            return leftTime - rightTime;
        });
    }

    getTransferMinutes(previousPart, nextPart) {
        if (!previousPart || !nextPart || this.isWalkingPart(previousPart) || this.isWalkingPart(nextPart)) {
            return null;
        }

        const previousArrival = previousPart.realtimeArrivalTime
            || this.addMinutes(previousPart.plannedArrivalTime || previousPart.arrivalTime, previousPart.arrivalDelayInMinutes);
        const nextDeparture = nextPart.realtimeDepartureTime
            || this.addMinutes(nextPart.plannedDepartureTime || nextPart.departureTime, nextPart.departureDelayInMinutes);
        const previousDate = new Date(previousArrival || previousPart.arrivalTime);
        const nextDate = new Date(nextDeparture || nextPart.departureTime);

        if (Number.isNaN(previousDate.getTime()) || Number.isNaN(nextDate.getTime())) {
            return null;
        }

        return Math.max(0, Math.round((nextDate.getTime() - previousDate.getTime()) / 60000));
    }

    normalizeTransportTypes(value, fallback = defaultRouteTransportTypes) {
        const rawValues = Array.isArray(value)
            ? value
            : String(value || "").split(",");
        const normalized = rawValues
            .map(item => String(item || "").trim().toUpperCase())
            .filter(item => routeTransportTypes.includes(item));
        return normalized.length ? [...new Set(normalized)] : [...fallback];
    }

    getDefaultRouteFilters() {
        const configuredTransportTypes = this.config.transportType ?? this.config.transportTypes;
        return {
            transportTypes: configuredTransportTypes === undefined
                ? [...defaultRouteTransportTypes]
                : this.normalizeTransportTypes(configuredTransportTypes, []),
            timeMode: "now",
            dateTime: "",
            routeType: this.normalizeRouteType(this.config.routeType),
            changeSpeed: this.normalizeChangeSpeed(this.config.changeSpeed),
        };
    }

    getRouteFilters() {
        if (!this._routeFilters) {
            this._routeFilters = this.getDefaultRouteFilters();
        }
        return this._routeFilters;
    }

    normalizeRouteType(value) {
        return ["LEAST_TIME", "LEAST_INTERCHANGES", "LEAST_WALKING"].includes(value)
            ? value
            : "LEAST_TIME";
    }

    normalizeChangeSpeed(value) {
        return ["SLOW", "NORMAL", "FAST"].includes(value) ? value : "NORMAL";
    }

    getEffectiveRouteTransportTypes(filters = this.getRouteFilters()) {
        const selected = this.normalizeTransportTypes(filters.transportTypes, []);
        return selected.length ? selected : [...routeTransportTypes];
    }

    getFilterDateTimeIso(filters = this.getRouteFilters()) {
        if (!filters.dateTime) return "";
        const date = new Date(filters.dateTime);
        return Number.isNaN(date.getTime()) ? "" : date.toISOString();
    }

    getCurrentLocalDateTimeValue() {
        const date = new Date();
        date.setSeconds(0, 0);
        date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
        return date.toISOString().slice(0, 16);
    }

    getRouteFilterSummary() {
        const filters = this.getRouteFilters();
        const parts = [];
        const selectedTypes = this.getEffectiveRouteTransportTypes(filters);
        parts.push(selectedTypes.length === routeTransportTypes.length
            ? this.localize("frontend.route_filter_all_transport", "All transport types")
            : selectedTypes.map(type => this.getTransportTypeLabel(type)).join(", "));

        if (filters.timeMode === "departure") {
            parts.push(this.localize("frontend.route_time_departure_at", "Departure at"));
        } else if (filters.timeMode === "arrival") {
            parts.push(this.localize("frontend.route_time_arrival_at", "Arrival at"));
        } else {
            parts.push(this.localize("frontend.route_time_now", "Now"));
        }

        return parts.filter(Boolean).join(" · ");
    }

    getTransportTypeLabel(type) {
        const labels = {
            SBAHN: "S-Bahn",
            UBAHN: "U-Bahn",
            TRAM: "Tram",
            BUS: "Bus",
            REGIONAL_BUS: this.localize("frontend.route_transport_regional_bus", "Regional bus"),
            BAHN: this.localize("frontend.route_transport_train", "Train"),
        };
        return labels[type] || type;
    }

    formatMeters(value) {
        const meters = Number(value);
        if (!Number.isFinite(meters) || meters <= 0) return "";
        return meters >= 1000 ? `${(meters / 1000).toFixed(1)} km` : `${Math.round(meters)} m`;
    }

    getPartDuration(part) {
        const directDuration = Number(part.interchangePathDurationInMinutes);
        if (Number.isFinite(directDuration) && directDuration > 0) return Math.round(directDuration);

        const start = new Date(part.departureTime);
        const end = new Date(part.arrivalTime);
        if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
        return Math.max(0, Math.round((end.getTime() - start.getTime()) / 60000));
    }

    isWalkingPart(part) {
        const transportType = String(part.transportType || "").toUpperCase();
        const label = String(part.lineLabel || "").toUpperCase();
        return transportType === "PEDESTRIAN" || transportType === "WALK" || label === "FUSSWEG" || label === "FOOTPATH";
    }

    isSevPart(part) {
        return part.sev === true || String(part.sev).toLowerCase() === "true";
    }

    getDisplayLineLabel(part) {
        const label = String(part.lineLabel || "");
        if (this.isWalkingPart(part)) return this.localize("frontend.route_walk", "Fuss");
        if (label.toUpperCase() === "LUFTHANSA EXPRESS BUS") return "LEB";
        return label || part.transportType || "";
    }

    getInfoItems(part, routeIndex, partIndex) {
        const details = part.infoDetails || [];
        if (details.length) {
            return details
                .filter(info => info?.title || info?.description)
                .map((info, infoIndex) => ({
                    key: `${routeIndex}-${partIndex}-${infoIndex}`,
                    title: info.title || info.description || "",
                    description: info.description || "",
                    type: info.type || "",
                    network: info.network || "",
                }));
        }

        return [...(part.infos || []), ...(part.messages || [])]
            .filter(Boolean)
            .map((info, infoIndex) => ({
                key: `${routeIndex}-${partIndex}-${infoIndex}`,
                title: String(info),
                description: "",
                type: "",
                network: "",
            }));
    }

    findInfoItem(key) {
        for (let routeIndex = 0; routeIndex < this._routes.length; routeIndex += 1) {
            const route = this._routes[routeIndex];
            for (let partIndex = 0; partIndex < (route.parts || []).length; partIndex += 1) {
                const item = this.getInfoItems(route.parts[partIndex], routeIndex, partIndex)
                    .find(info => info.key === key);
                if (item) return item;
            }
        }
        return null;
    }

    keepScrollAnchor(anchor, fallbackScrollTop = null) {
        const scrollElement = this.content?.querySelector(".route-scroll");
        const scrollTop = fallbackScrollTop ?? scrollElement?.scrollTop ?? 0;
        const anchorTop = anchor && scrollElement
            ? anchor.getBoundingClientRect().top - scrollElement.getBoundingClientRect().top
            : null;

        this.render();

        const nextScrollElement = this.content?.querySelector(".route-scroll");
        if (!nextScrollElement) return;

        const anchorSelector = anchor?.dataset?.stopsKey
            ? "[data-stops-key]"
            : anchor?.dataset?.routeToggle
                ? "[data-route-toggle]"
                : "";
        const anchorValue = anchor?.dataset?.stopsKey || anchor?.dataset?.routeToggle || "";
        const nextAnchor = anchorSelector
            ? [...this.content.querySelectorAll(anchorSelector)].find(element => (
                element.dataset.stopsKey === anchorValue || element.dataset.routeToggle === anchorValue
            ))
            : null;

        if (nextAnchor && anchorTop !== null) {
            const nextAnchorTop = nextAnchor.getBoundingClientRect().top - nextScrollElement.getBoundingClientRect().top;
            nextScrollElement.scrollTop += nextAnchorTop - anchorTop;
        } else {
            nextScrollElement.scrollTop = scrollTop;
        }
    }

    toggleIntermediateStops(key, anchor = null) {
        if (this._expandedStops.has(key)) {
            this._expandedStops.delete(key);
        } else {
            this._expandedStops.add(key);
        }
        this.keepScrollAnchor(anchor);
    }

    getLineCssClass(part) {
        return this.getDisplayLineLabel(part).replace(/[^a-zA-Z0-9_-]/g, "");
    }

    getRouteKey(route, index) {
        return this.getRouteIdentity(route) || String(index);
    }

    getRouteIdentity(route) {
        if (route?.uniqueId) return String(route.uniqueId);

        return (route?.parts || [])
            .map(part => [
                part.transportType || "",
                part.lineLabel || "",
                part.fromName || "",
                part.toName || "",
                part.plannedDepartureTime || part.departureTime || "",
                part.plannedArrivalTime || part.arrivalTime || "",
            ].join("|"))
            .join("||") || `${route?.departureTime || ""}-${route?.arrivalTime || ""}`;
    }

    mergeRoutes(existingRoutes, newRoutes, direction = "replace") {
        const orderedRoutes = direction === "prepend"
            ? [...newRoutes, ...existingRoutes]
            : direction === "append"
                ? [...existingRoutes, ...newRoutes]
                : [...newRoutes];
        const seen = new Set();
        const merged = [];

        for (const route of orderedRoutes) {
            const key = this.getRouteIdentity(route);
            if (seen.has(key)) continue;
            seen.add(key);
            merged.push(route);
        }

        return this.sortRoutes(merged);
    }

    getRouteBoundaryTime(direction) {
        if (!this._routes.length) return "";

        const route = direction === "earlier" ? this._routes[0] : this._routes[this._routes.length - 1];
        const parts = route.parts || [];
        const firstPart = parts[0] || {};
        const lastPart = parts[Math.max(0, parts.length - 1)] || {};
        const value = direction === "earlier"
            ? lastPart.plannedArrivalTime || lastPart.arrivalTime || route.arrivalTime
            : firstPart.plannedDepartureTime || firstPart.departureTime || route.departureTime;
        const date = new Date(value);

        return Number.isNaN(date.getTime()) ? "" : date.toISOString();
    }

    routeIsCollapsed(route, index) {
        if (this.config.routesCollapsible !== true) return false;

        const key = this.getRouteKey(route, index);
        if (this.config.routesDefaultCollapsed === true) {
            return !this._expandedRoutes.has(key);
        }
        return this._collapsedRoutes.has(key);
    }

    toggleRouteCollapsed(route, index, anchor = null) {
        const key = this.getRouteKey(route, index);
        if (this.config.routesDefaultCollapsed === true) {
            if (this._expandedRoutes.has(key)) {
                this._expandedRoutes.delete(key);
            } else {
                this._expandedRoutes.add(key);
            }
        } else if (this._collapsedRoutes.has(key)) {
            this._collapsedRoutes.delete(key);
        } else {
            this._collapsedRoutes.add(key);
        }

        this.keepScrollAnchor(anchor);
    }

    enableDragScroll(element) {
        if (!element) return;

        let active = false;
        let moved = false;
        let startY = 0;
        let startScrollTop = 0;

        const stop = () => {
            if (!active) return;
            active = false;
            element.classList.remove("dragging");
        };

        element.addEventListener("pointerdown", (event) => {
            if (event.button !== 0 || event.target.closest("button, input, textarea, select, a, [role='button']")) return;
            active = true;
            moved = false;
            startY = event.clientY;
            startScrollTop = element.scrollTop;
            element.setPointerCapture?.(event.pointerId);
        });

        element.addEventListener("pointermove", (event) => {
            if (!active) return;
            const deltaY = event.clientY - startY;
            if (Math.abs(deltaY) > 3) {
                moved = true;
                element.classList.add("dragging");
            }
            if (!moved) return;
            event.preventDefault();
            element.scrollTop = startScrollTop - deltaY;
        });

        element.addEventListener("pointerup", stop);
        element.addEventListener("pointercancel", stop);
        element.addEventListener("lostpointercapture", stop);
    }

    getRouteLineParts(route) {
        return (route.parts || [])
            .filter(part => !this.isWalkingPart(part))
            .map(part => ({
                label: this.getDisplayLineLabel(part),
                transportType: part.transportType || "",
                cssClass: this.getLineCssClass(part),
                sev: this.isSevPart(part),
            }))
            .filter(part => part.label);
    }

    renderCollapsedLineChain(route) {
        const lineParts = this.getRouteLineParts(route);
        if (!lineParts.length) return "";

        return `
            <div class="route-line-chain">
                ${lineParts.map((part, index) => `
                    ${index > 0 ? `<span class="route-line-separator">→</span>` : ""}
                    <span class="line mini ${this.escapeHtml(part.transportType)} ${this.escapeHtml(part.cssClass)}">${this.escapeHtml(part.label)}</span>
                    ${part.sev ? `<span class="sev-badge mini">SEV</span>` : ""}
                `).join("")}
            </div>
        `;
    }

    renderIntermediateStops(stops) {
        if (!stops?.length) return "";

        return `
            <div class="intermediate-list">
                ${stops.map(stop => {
                    const timeHtml = this.getDisplayTime(
                        stop.plannedDepartureTime || stop.plannedArrivalTime || stop.departureTime || stop.arrivalTime,
                        stop.realtimeDepartureTime || stop.realtimeArrivalTime,
                        stop.departureDelayInMinutes ?? stop.arrivalDelayInMinutes
                    );
                    const platform = stop.platform ? `${this.localize("frontend.column_track", "Track")} ${stop.platform}` : "";
                    return `
                        <div class="intermediate-stop">
                            <span class="intermediate-time">${timeHtml}</span>
                            <span class="intermediate-name">${this.escapeHtml(stop.name)}</span>
                            ${platform ? `<span class="intermediate-platform">${this.escapeHtml(platform)}</span>` : ""}
                        </div>
                    `;
                }).join("")}
            </div>
        `;
    }

    normalizeLocationType(type) {
        return String(type || "STATION").toUpperCase();
    }

    isCoordinateLocation(location) {
        return Number.isFinite(Number(location?.latitude)) && Number.isFinite(Number(location?.longitude));
    }

    getLocationId(location) {
        if (location?.globalId) return String(location.globalId).trim();
        if (this.isCoordinateLocation(location)) {
            return `${this.normalizeLocationType(location.type)}:${Number(location.latitude).toFixed(6)},${Number(location.longitude).toFixed(6)}`;
        }
        return "";
    }

    getLocationKindLabel(location) {
        const type = this.normalizeLocationType(location?.type);
        if (type === "ADDRESS") return this.localize("frontend.route_location_address", "Address");
        if (type === "POI") return this.localize("frontend.route_location_poi", "POI");
        return this.localize("frontend.route_location_station", "Station");
    }

    getLocationMeta(location) {
        const label = this.getLocationKindLabel(location);
        const place = location?.place ? ` · ${location.place}` : "";
        const id = location?.globalId ? ` · ${location.globalId}` : "";
        return `${label}${place}${id}`;
    }

    serializeRouteLocation(location, prefix) {
        return {
            [`${prefix}Name`]: String(location?.name || "").trim(),
            [`${prefix}GlobalId`]: String(location?.globalId || "").trim(),
            [`${prefix}Type`]: this.normalizeLocationType(location?.type),
            [`${prefix}Latitude`]: this.isCoordinateLocation(location) ? Number(location.latitude) : null,
            [`${prefix}Longitude`]: this.isCoordinateLocation(location) ? Number(location.longitude) : null,
            [`${prefix}Place`]: String(location?.place || "").trim(),
            [`${prefix}TransportTypes`]: Array.isArray(location?.transportTypes) ? location.transportTypes : [],
        };
    }

    deserializeRouteLocation(favorite, prefix) {
        const name = String(favorite?.[`${prefix}Name`] || "").trim();
        const globalId = String(favorite?.[`${prefix}GlobalId`] || "").trim();
        const latitude = favorite?.[`${prefix}Latitude`];
        const longitude = favorite?.[`${prefix}Longitude`];
        const type = this.normalizeLocationType(favorite?.[`${prefix}Type`] || (globalId ? "STATION" : ""));
        if (!name || (!globalId && !this.isCoordinateLocation({ latitude, longitude }))) return null;
        return {
            name,
            globalId,
            type,
            latitude,
            longitude,
            place: String(favorite?.[`${prefix}Place`] || "").trim(),
            transportTypes: Array.isArray(favorite?.[`${prefix}TransportTypes`]) ? favorite[`${prefix}TransportTypes`] : [],
        };
    }

    getStationFavoriteKey(favorite) {
        return this.getLocationId(favorite);
    }

    getRouteFavoriteKey(favorite) {
        const origin = this.deserializeRouteLocation(favorite, "origin") || { globalId: favorite.originGlobalId };
        const destination = this.deserializeRouteLocation(favorite, "destination") || { globalId: favorite.destinationGlobalId };
        return `${this.getLocationId(origin)}|${this.getLocationId(destination)}`;
    }

    formatStationFavoriteForConfig(favorite) {
        if (!favorite.globalId) return "";
        return `${favorite.name}|${favorite.globalId}`;
    }

    formatRouteFavoriteForConfig(favorite) {
        if (!favorite.originGlobalId || !favorite.destinationGlobalId) return "";
        return `${favorite.name}|${favorite.originName}|${favorite.originGlobalId}|${favorite.destinationName}|${favorite.destinationGlobalId}`;
    }

    getStationFavoriteFromStation(station) {
        if (!station?.globalId && !this.isCoordinateLocation(station)) return null;
        return {
            name: String(station.name || station.globalId || "").trim(),
            globalId: String(station.globalId || "").trim(),
            type: this.normalizeLocationType(station.type),
            latitude: this.isCoordinateLocation(station) ? Number(station.latitude) : null,
            longitude: this.isCoordinateLocation(station) ? Number(station.longitude) : null,
            place: String(station.place || "").trim(),
            transportTypes: Array.isArray(station.transportTypes) ? station.transportTypes : [],
        };
    }

    getRouteFavoriteFromCurrent() {
        if (!this.getLocationId(this._originStation) || !this.getLocationId(this._destinationStation)) return null;
        const originName = String(this._originStation.name || this._originStation.globalId || "").trim();
        const destinationName = String(this._destinationStation.name || this._destinationStation.globalId || "").trim();
        return {
            name: `${originName} → ${destinationName}`,
            ...this.serializeRouteLocation(this._originStation, "origin"),
            ...this.serializeRouteLocation(this._destinationStation, "destination"),
        };
    }

    normalizeRouteFavoritesStorage(value) {
        const stations = Array.isArray(value?.stations) ? value.stations : [];
        const routes = Array.isArray(value?.routes) ? value.routes : [];

        return {
            stations: stations
                .map((favorite) => ({
                    source: "local",
                    name: String(favorite.name || "").trim(),
                    globalId: String(favorite.globalId || favorite.globalid || "").trim(),
                    type: this.normalizeLocationType(favorite.type),
                    latitude: favorite.latitude ?? null,
                    longitude: favorite.longitude ?? null,
                    place: String(favorite.place || "").trim(),
                    transportTypes: Array.isArray(favorite.transportTypes) ? favorite.transportTypes : [],
                    createdAt: favorite.createdAt || "",
                }))
                .filter((favorite) => favorite.name && this.getLocationId(favorite)),
            routes: routes
                .map((favorite) => ({
                    source: "local",
                    name: String(favorite.name || "").trim(),
                    originName: String(favorite.originName || "").trim(),
                    originGlobalId: String(favorite.originGlobalId || "").trim(),
                    originType: this.normalizeLocationType(favorite.originType),
                    originLatitude: favorite.originLatitude ?? null,
                    originLongitude: favorite.originLongitude ?? null,
                    originPlace: String(favorite.originPlace || "").trim(),
                    originTransportTypes: Array.isArray(favorite.originTransportTypes) ? favorite.originTransportTypes : [],
                    destinationName: String(favorite.destinationName || "").trim(),
                    destinationGlobalId: String(favorite.destinationGlobalId || "").trim(),
                    destinationType: this.normalizeLocationType(favorite.destinationType),
                    destinationLatitude: favorite.destinationLatitude ?? null,
                    destinationLongitude: favorite.destinationLongitude ?? null,
                    destinationPlace: String(favorite.destinationPlace || "").trim(),
                    destinationTransportTypes: Array.isArray(favorite.destinationTransportTypes) ? favorite.destinationTransportTypes : [],
                    createdAt: favorite.createdAt || "",
                }))
                .filter((favorite) => favorite.name && this.getRouteFavoriteKey(favorite) !== "|"),
        };
    }

    getLocalFavorites() {
        try {
            return this.normalizeRouteFavoritesStorage(JSON.parse(localStorage.getItem(routeFavoritesStorageKey) || "{}"));
        } catch (err) {
            console.warn("AnotherMVG-Route - failed to read favorites", err);
            return { stations: [], routes: [] };
        }
    }

    saveLocalFavorites(favorites) {
        try {
            localStorage.setItem(routeFavoritesStorageKey, JSON.stringify(this.normalizeRouteFavoritesStorage(favorites)));
        } catch (err) {
            console.warn("AnotherMVG-Route - failed to save favorites", err);
        }
    }

    getConfiguredStationFavorites() {
        return String(this.config.favoriteStations || "")
            .split(/\r?\n/)
            .map(line => line.trim())
            .filter(Boolean)
            .map((line) => {
                const [name, globalId] = line.split("|").map(part => part.trim());
                if (!name || !globalId) return null;
                return { source: "config", name, globalId, transportTypes: [] };
            })
            .filter(Boolean);
    }

    getConfiguredRouteFavorites() {
        return String(this.config.favoriteRoutes || "")
            .split(/\r?\n/)
            .map(line => line.trim())
            .filter(Boolean)
            .map((line) => {
                const [name, originName, originGlobalId, destinationName, destinationGlobalId] = line.split("|").map(part => part.trim());
                if (!name || !originName || !originGlobalId || !destinationName || !destinationGlobalId) return null;
                return { source: "config", name, originName, originGlobalId, destinationName, destinationGlobalId };
            })
            .filter(Boolean);
    }

    getVisibleLocalStationFavorites() {
        const configuredKeys = new Set(this.getConfiguredStationFavorites().map(favorite => this.getStationFavoriteKey(favorite)));
        return this.getLocalFavorites().stations.filter(favorite => !configuredKeys.has(this.getStationFavoriteKey(favorite)));
    }

    getVisibleLocalRouteFavorites() {
        const configuredKeys = new Set(this.getConfiguredRouteFavorites().map(favorite => this.getRouteFavoriteKey(favorite)));
        return this.getLocalFavorites().routes.filter(favorite => !configuredKeys.has(this.getRouteFavoriteKey(favorite)));
    }

    getStationFavoriteByRef(ref) {
        const [source, index] = String(ref || "").split(":");
        const favorites = source === "config" ? this.getConfiguredStationFavorites() : this.getVisibleLocalStationFavorites();
        return favorites[Number(index)] || null;
    }

    getRouteFavoriteByRef(ref) {
        const [source, index] = String(ref || "").split(":");
        const favorites = source === "config" ? this.getConfiguredRouteFavorites() : this.getVisibleLocalRouteFavorites();
        return favorites[Number(index)] || null;
    }

    getStartRouteFavorites() {
        return [
            ...this.getConfiguredRouteFavorites().map((favorite, index) => ({ favorite, ref: `config:${index}` })),
            ...this.getVisibleLocalRouteFavorites().map((favorite, index) => ({ favorite, ref: `local:${index}` })),
        ];
    }

    showFavoriteMessage(messageKey, fallback) {
        this._favoriteMessage = this.localize(messageKey, fallback);
        this._showFavorites = true;
        this.render();

        window.clearTimeout(this._favoriteMessageTimer);
        this._favoriteMessageTimer = window.setTimeout(() => {
            this._favoriteMessage = "";
            if (this._showFavorites) {
                this.render();
            }
        }, 2200);
    }

    saveStationFavorite(station) {
        const favorite = this.getStationFavoriteFromStation(station);
        if (!favorite) return;

        const localFavorites = this.getLocalFavorites();
        const key = this.getStationFavoriteKey(favorite);
        localFavorites.stations = [
            { ...favorite, source: "local", createdAt: new Date().toISOString() },
            ...localFavorites.stations.filter(item => this.getStationFavoriteKey(item) !== key),
        ];
        this.saveLocalFavorites(localFavorites);
        this._showFavorites = true;
        this._pendingDeleteFavorite = null;
        this.render();
    }

    saveCurrentRouteFavorite() {
        const favorite = this.getRouteFavoriteFromCurrent();
        if (!favorite) return;

        const localFavorites = this.getLocalFavorites();
        const key = this.getRouteFavoriteKey(favorite);
        localFavorites.routes = [
            { ...favorite, source: "local", createdAt: new Date().toISOString() },
            ...localFavorites.routes.filter(item => this.getRouteFavoriteKey(item) !== key),
        ];
        this.saveLocalFavorites(localFavorites);
        this._showFavorites = true;
        this._pendingDeleteFavorite = null;
        this.render();
    }

    async copyText(text) {
        if (!text) return false;

        try {
            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(text);
                return true;
            }
        } catch (err) {
            console.warn("AnotherMVG-Route - clipboard API failed, using fallback", err);
        }

        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.setAttribute("readonly", "");
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.select();
        const copied = document.execCommand("copy");
        document.body.removeChild(textArea);
        return copied;
    }

    async copyFavoriteText(text) {
        const copied = await this.copyText(text);
        if (copied) {
            this.showFavoriteMessage("frontend.favorite_copied", "Copied to clipboard");
        }
    }

    setStationFavorite(kind, favorite) {
        if (!this.getLocationId(favorite)) return;

        const station = {
            name: favorite.name,
            globalId: favorite.globalId || "",
            type: this.normalizeLocationType(favorite.type),
            latitude: favorite.latitude ?? null,
            longitude: favorite.longitude ?? null,
            place: favorite.place || "",
            transportTypes: favorite.transportTypes || [],
        };

        if (kind === "origin") {
            this._originStation = station;
            this._originQuery = station.name;
            this._originResults = [];
        } else {
            this._destinationStation = station;
            this._destinationQuery = station.name;
            this._destinationResults = [];
        }

        this._routes = [];
        this._showFavorites = false;
        this.render();
    }

    loadRouteFavorite(favorite) {
        const origin = this.deserializeRouteLocation(favorite, "origin");
        const destination = this.deserializeRouteLocation(favorite, "destination");
        if (!origin || !destination) return;

        this._originStation = origin;
        this._destinationStation = destination;
        this._originQuery = origin.name;
        this._destinationQuery = destination.name;
        this._originResults = [];
        this._destinationResults = [];
        this._routes = [];
        this._showFavorites = false;
        this.fetchRoutes();
    }

    requestDeleteLocalFavorite(type, key) {
        this._pendingDeleteFavorite = { type, key };
        this._favoriteMessage = "";
        this.render();
    }

    deleteLocalFavorite(type, key) {
        const localFavorites = this.getLocalFavorites();

        if (type === "route") {
            localFavorites.routes = localFavorites.routes.filter(favorite => this.getRouteFavoriteKey(favorite) !== key);
        } else {
            localFavorites.stations = localFavorites.stations.filter(favorite => this.getStationFavoriteKey(favorite) !== key);
        }

        this.saveLocalFavorites(localFavorites);
        this._pendingDeleteFavorite = null;
        this.showFavoriteMessage("frontend.favorite_deleted", "Favorite deleted");
    }

    async searchStations(kind) {
        const isOrigin = kind === "origin";
        const query = (isOrigin ? this._originQuery : this._destinationQuery).trim();

        if (query.length < 2) {
            if (isOrigin) this._originResults = [];
            else this._destinationResults = [];
            this.render();
            return;
        }

        if (isOrigin) this._searchingOrigin = true;
        else this._searchingDestination = true;
        this._error = "";
        this.render();

        try {
            const result = await this._hass.callApi(
                "GET",
                `another_mvg/search_stations?query=${encodeURIComponent(query)}&includeNonStations=1`
            );
            if (isOrigin) this._originResults = result.stations || [];
            else this._destinationResults = result.stations || [];
        } catch (err) {
            if (isOrigin) this._originResults = [];
            else this._destinationResults = [];
            this._error = this.localize("frontend.route_station_search_failed", "Station search failed");
            console.warn("AnotherMVG-Route - station search failed", err);
        } finally {
            if (isOrigin) this._searchingOrigin = false;
            else this._searchingDestination = false;
            this.render();
        }
    }

    getLocationErrorMessage(err) {
        if (window.isSecureContext === false) {
            return this.localize("frontend.location_requires_https", "Location lookup requires HTTPS");
        }
        if (err?.code === 1) {
            return this.localize("frontend.location_permission_denied", "Location permission was denied");
        }
        if (err?.code === 2) {
            return this.localize("frontend.location_unavailable", "Current location is unavailable");
        }
        if (err?.code === 3) {
            return this.localize("frontend.location_timeout", "Location lookup timed out");
        }
        return this.localize("frontend.location_failed", "Could not load nearby stations");
    }

    async searchNearbyStations(kind) {
        if (!navigator.geolocation) {
            this._error = this.localize("frontend.location_not_supported", "This browser does not support location lookup");
            this.render();
            return;
        }

        const isOrigin = kind === "origin";
        if (isOrigin) this._locatingOrigin = true;
        else this._locatingDestination = true;
        this._error = "";
        this._originResults = isOrigin ? [] : this._originResults;
        this._destinationResults = isOrigin ? this._destinationResults : [];
        this.render();

        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    maximumAge: 60000,
                    timeout: 12000,
                });
            });
            const { latitude, longitude } = position.coords;
            const result = await this._hass.callApi(
                "GET",
                `another_mvg/search_nearby_stations?latitude=${encodeURIComponent(latitude)}&longitude=${encodeURIComponent(longitude)}`
            );
            if (isOrigin) {
                this._originResults = result.stations || [];
                this._originQuery = this.localize("frontend.nearby_stations", "Nearby stations");
            } else {
                this._destinationResults = result.stations || [];
                this._destinationQuery = this.localize("frontend.nearby_stations", "Nearby stations");
            }
            if (!(result.stations || []).length) {
                this._error = this.localize("frontend.location_no_stations", "No nearby stations found");
            }
        } catch (err) {
            this._error = this.getLocationErrorMessage(err);
            console.warn("AnotherMVG-Route - nearby station search failed", err);
        } finally {
            if (isOrigin) this._locatingOrigin = false;
            else this._locatingDestination = false;
            this.render();
        }
    }

    selectStation(kind, index) {
        const isOrigin = kind === "origin";
        const results = isOrigin ? this._originResults : this._destinationResults;
        const station = results[Number(index)];
        if (!station) return;

        if (isOrigin) {
            this._originStation = station;
            this._originQuery = station.name;
            this._originResults = [];
        } else {
            this._destinationStation = station;
            this._destinationQuery = station.name;
            this._destinationResults = [];
        }
        this._routes = [];
        this.render();
    }

    swapStations() {
        const originStation = this._originStation;
        const originQuery = this._originQuery;
        this._originStation = this._destinationStation;
        this._originQuery = this._destinationQuery;
        this._destinationStation = originStation;
        this._destinationQuery = originQuery;
        this._originResults = [];
        this._destinationResults = [];
        this._routes = [];
        this.render();
    }

    async fetchRoutes(direction = "replace") {
        if (!this.getLocationId(this._originStation) || !this.getLocationId(this._destinationStation)) {
            this._error = this.localize("frontend.route_missing_stations", "Select origin and destination first");
            this.render();
            return;
        }

        const filters = this.getRouteFilters();
        const routingDateTime = direction === "replace" ? "" : this.getRouteBoundaryTime(direction);
        if (direction !== "replace" && !routingDateTime) return;

        if (direction === "earlier") this._loadingEarlier = true;
        else if (direction === "later") this._loadingLater = true;
        else this._loading = true;
        this._showFavorites = false;
        this._showFilters = false;
        this._favoriteMessage = "";
        this._pendingDeleteFavorite = null;
        this._error = "";
        this.render();

        try {
            const payload = {
                origin: this._originStation,
                destination: this._destinationStation,
                originGlobalId: this._originStation.globalId || "",
                destinationGlobalId: this._destinationStation.globalId || "",
                transportTypes: this.getEffectiveRouteTransportTypes(filters),
                routeType: this.normalizeRouteType(filters.routeType),
                changeSpeed: this.normalizeChangeSpeed(filters.changeSpeed),
            };
            if (routingDateTime) {
                payload.routingDateTime = routingDateTime;
                payload.routingDateTimeIsArrival = direction === "earlier";
            } else if (filters.timeMode === "departure" || filters.timeMode === "arrival") {
                const filterDateTime = this.getFilterDateTimeIso(filters);
                if (filterDateTime) {
                    payload.routingDateTime = filterDateTime;
                    payload.routingDateTimeIsArrival = filters.timeMode === "arrival";
                }
            }

            const result = await this._hass.callApi("POST", "another_mvg/search_routes", payload);
            this._routes = this.mergeRoutes(
                this._routes,
                result.routes || [],
                direction === "earlier" ? "prepend" : direction === "later" ? "append" : "replace"
            );
            if (direction === "replace") {
                this._collapsedRoutes = new Set();
                this._expandedRoutes = new Set();
            }
            if (!this._routes.length) {
                this._error = this.localize("frontend.route_no_routes", "No routes found");
            }
        } catch (err) {
            if (direction === "replace") this._routes = [];
            this._error = this.localize("frontend.route_search_failed", "Route search failed");
            console.warn("AnotherMVG-Route - route search failed", err);
        } finally {
            this._loading = false;
            this._loadingEarlier = false;
            this._loadingLater = false;
            this.render();
        }
    }

    renderStationResults(kind, results) {
        if (!results.length) return "";

        return `
            <div class="station-list">
                ${results.map((station, index) => `
                    <button class="station" data-select-${kind}="${index}">
                        <span>${this.escapeHtml(station.name)}</span>
                        <small>
                            ${this.escapeHtml(this.getLocationMeta(station))}
                            ${(station.transportTypes || []).length ? ` · ${this.escapeHtml((station.transportTypes || []).join(", "))}` : ""}
                            ${station.distanceInMeters !== undefined ? ` · ${this.escapeHtml(this.formatMeters(station.distanceInMeters))}` : ""}
                        </small>
                    </button>
                `).join("")}
            </div>
        `;
    }

    renderRoute(route, index) {
        const duration = this.formatDuration(route);
        const transfers = route.transfers ?? 0;
        const collapsed = this.routeIsCollapsed(route, index);
        const collapsible = this.config.routesCollapsible === true;
        const firstPart = (route.parts || [])[0] || {};
        const lastPart = (route.parts || [])[Math.max(0, (route.parts || []).length - 1)] || {};
        const routeStart = this.getSummaryDisplayTime(firstPart.plannedDepartureTime || firstPart.departureTime || route.departureTime, firstPart.realtimeDepartureTime, firstPart.departureDelayInMinutes);
        const routeEnd = this.getSummaryDisplayTime(lastPart.plannedArrivalTime || lastPart.arrivalTime || route.arrivalTime, lastPart.realtimeArrivalTime, lastPart.arrivalDelayInMinutes);
        return `
            <div class="route ${collapsed ? "collapsed" : ""}">
                <div class="route-summary ${collapsible ? "collapsible" : ""}" ${collapsible ? `role="button" tabindex="0" data-route-toggle="${this.escapeHtml(this.getRouteKey(route, index))}"` : ""}>
                    <div class="route-summary-main">
                        <strong class="route-summary-time">${routeStart} - ${routeEnd}</strong>
                        <span class="route-summary-meta">${duration}${duration ? " · " : ""}${transfers} ${this.localize("frontend.route_transfers", "changes")}</span>
                    </div>
                    <div class="route-summary-side">
                        <span class="route-number">#${index + 1}</span>
                        ${collapsed ? this.renderCollapsedLineChain(route) : ""}
                    </div>
                </div>
                <div class="parts ${collapsed ? "hidden" : ""}">
                    ${route.parts.map((part, partIndex) => `
                        ${partIndex > 0 ? this.renderTransferTime(route.parts[partIndex - 1], part) : ""}
                        ${this.renderRoutePart(part, index, partIndex)}
                    `).join("")}
                </div>
            </div>
        `;
    }

    renderTransferTime(previousPart, nextPart) {
        if (this.config.showTransferTime !== true) return "";

        const minutes = this.getTransferMinutes(previousPart, nextPart);
        if (minutes === null) return "";

        return `
            <div class="transfer-time">
                <span></span>
                <span></span>
                <span>${this.localize("frontend.route_transfer_time", "Transfer time")}: ${this.escapeHtml(this.formatMinutes(minutes))}</span>
            </div>
        `;
    }

    renderRoutePart(part, routeIndex, partIndex) {
        const lineLabel = this.getDisplayLineLabel(part);
        const isWalk = this.isWalkingPart(part);
        const isSev = this.isSevPart(part);
        const infos = this.getInfoItems(part, routeIndex, partIndex);
        const intermediateStops = part.intermediateStops || [];
        const intermediateStopKey = `${routeIndex}-${partIndex}`;
        const intermediateStopsExpanded = this._expandedStops.has(intermediateStopKey);
        const platform = part.platform ? `${this.localize("frontend.column_track", "Track")} ${part.platform}` : "";
        const walkDistance = isWalk ? this.formatMeters(part.interchangePathDistance ?? part.distance) : "";
        const walkDuration = isWalk ? this.getPartDuration(part) : null;
        const walkDetails = isWalk
            ? [
                walkDuration !== null ? `${walkDuration} min` : "",
                walkDistance,
            ].filter(Boolean)
            : [];
        const partTimeHtml = isWalk
            ? (partIndex === 0
                ? this.getDisplayTime(part.plannedDepartureTime || part.departureTime, part.realtimeDepartureTime, part.departureDelayInMinutes)
                : "")
            : `
                ${this.getDisplayTime(part.plannedDepartureTime || part.departureTime, part.realtimeDepartureTime, part.departureDelayInMinutes)}
                ${this.getDisplayTime(part.plannedArrivalTime || part.arrivalTime, part.realtimeArrivalTime, part.arrivalDelayInMinutes)}
            `;

        return `
            <div class="part ${isWalk ? "walk" : ""}">
                <div class="part-time">
                    ${partTimeHtml}
                </div>
                <div class="part-line">
                    <span class="line ${this.escapeHtml(part.transportType)} ${this.escapeHtml(this.getLineCssClass(part))}">${this.escapeHtml(lineLabel)}</span>
                    ${isSev ? `<span class="sev-badge">SEV</span>` : ""}
                </div>
                <div class="part-main">
                    <div><strong>${this.escapeHtml(part.fromName)}</strong> → <strong>${this.escapeHtml(part.toName)}</strong></div>
                    ${part.destination ? `<div class="muted">${this.localize("frontend.column_destination", "Destination")}: ${this.escapeHtml(part.destination)}</div>` : ""}
                    <div class="muted">
                        ${walkDetails.map(detail => `<span>${this.escapeHtml(detail)}</span>`).join("")}
                        ${platform ? `<span>${this.escapeHtml(platform)}</span>` : ""}
                        ${isSev ? `<span class="sev-text">${this.localize("frontend.route_replacement_service", "Replacement service")}</span>` : ""}
                        ${intermediateStops.length ? `
                            <button class="link-button intermediate-toggle" data-stops-key="${this.escapeHtml(intermediateStopKey)}">
                                ${intermediateStops.length} ${this.localize("frontend.route_intermediate_stops", "intermediate stops")}
                                <ha-icon icon="${intermediateStopsExpanded ? "mdi:chevron-up" : "mdi:chevron-down"}"></ha-icon>
                            </button>
                        ` : ""}
                    </div>
                    ${intermediateStopsExpanded ? this.renderIntermediateStops(intermediateStops) : ""}
                    ${infos.length ? `
                        <div class="infos">
                            ${infos.map(info => `
                                <button class="info-button" data-info-key="${this.escapeHtml(info.key)}">
                                    ${this.escapeHtml(info.title)}
                                </button>
                            `).join("")}
                        </div>
                    ` : ""}
                </div>
            </div>
        `;
    }

    renderFavoriteMenu() {
        if (!this._showFavorites) return "";

        const configuredStations = this.getConfiguredStationFavorites();
        const configuredRoutes = this.getConfiguredRouteFavorites();
        const localStations = this.getVisibleLocalStationFavorites();
        const localRoutes = this.getVisibleLocalRouteFavorites();
        const currentOrigin = this.getStationFavoriteFromStation(this._originStation);
        const currentDestination = this.getStationFavoriteFromStation(this._destinationStation);
        const currentRoute = this.getRouteFavoriteFromCurrent();
        const currentOriginCanCopy = Boolean(currentOrigin?.globalId);
        const currentDestinationCanCopy = Boolean(currentDestination?.globalId);
        const currentRouteCanCopy = Boolean(currentRoute?.originGlobalId && currentRoute?.destinationGlobalId);
        const hasFavorites = configuredStations.length || configuredRoutes.length || localStations.length || localRoutes.length;

        const renderStationFavorite = (favorite, source, index) => {
            const ref = `${source}:${index}`;
            const key = this.escapeHtml(this.getStationFavoriteKey(favorite));
            const deleteButton = source === "local"
                ? `<button class="favorite-delete" data-delete-station-favorite="${key}" title="${this.localize("frontend.favorite_delete", "Delete favorite")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button>`
                : "";

            return `
                <div class="favorite-row station-favorite ${source === "local" ? "local" : "config"}">
                    <button class="favorite-action" data-station-origin="${this.escapeHtml(ref)}" title="${this.localize("frontend.route_use_as_origin", "Use as origin")}"><ha-icon icon="mdi:map-marker-up"></ha-icon></button>
                    <button class="favorite-action" data-station-destination="${this.escapeHtml(ref)}" title="${this.localize("frontend.route_use_as_destination", "Use as destination")}"><ha-icon icon="mdi:map-marker-down"></ha-icon></button>
                    <button class="favorite-item" data-station-origin="${this.escapeHtml(ref)}">
                        <span class="favorite-title">${this.escapeHtml(favorite.name)}</span>
                        <span class="favorite-meta">${this.escapeHtml(this.getLocationMeta(favorite))}</span>
                    </button>
                    ${deleteButton}
                </div>
            `;
        };
        const renderRouteFavorite = (favorite, source, index) => {
            const ref = `${source}:${index}`;
            const key = this.escapeHtml(this.getRouteFavoriteKey(favorite));
            const deleteButton = source === "local"
                ? `<button class="favorite-delete" data-delete-route-favorite="${key}" title="${this.localize("frontend.favorite_delete", "Delete favorite")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button>`
                : "";

            return `
                <div class="favorite-row route-favorite ${source === "local" ? "local" : "config"}">
                    <button class="favorite-item" data-route-favorite="${this.escapeHtml(ref)}">
                        <span class="favorite-title">${this.escapeHtml(favorite.name)}</span>
                        <span class="favorite-meta">${this.escapeHtml(favorite.originName)} → ${this.escapeHtml(favorite.destinationName)}</span>
                    </button>
                    ${deleteButton}
                </div>
            `;
        };
        const renderDeletePopup = () => {
            if (!this._pendingDeleteFavorite) return "";

            const type = this._pendingDeleteFavorite.type;
            const key = this._pendingDeleteFavorite.key;
            const favorite = type === "route"
                ? this.getLocalFavorites().routes.find(item => this.getRouteFavoriteKey(item) === key)
                : this.getLocalFavorites().stations.find(item => this.getStationFavoriteKey(item) === key);
            if (!favorite) return "";

            const title = type === "route" ? favorite.name : favorite.name;
            const meta = type === "route"
                ? `${favorite.originName} → ${favorite.destinationName}`
                : this.getLocationMeta(favorite);

            return `
                <div class="favorite-delete-backdrop">
                    <div class="favorite-delete-dialog">
                        <div>
                            <span class="favorite-title">${this.escapeHtml(title)}</span>
                            <span class="favorite-meta">${this.escapeHtml(meta)}</span>
                        </div>
                        <div>${this.localize("frontend.favorite_delete_confirm", "Delete this local favorite?")}</div>
                        <div class="favorite-confirm-actions">
                            <button class="favorite-confirm-cancel" data-cancel-delete-favorite>${this.localize("frontend.favorite_cancel", "Cancel")}</button>
                            <button class="favorite-confirm-delete" data-confirm-delete-favorite="${this.escapeHtml(type)}:${this.escapeHtml(key)}">${this.localize("frontend.favorite_delete", "Delete favorite")}</button>
                        </div>
                    </div>
                </div>
            `;
        };

        return `
            <div class="favorites-menu">
                <div class="favorite-save-row">
                    <button class="favorite-save" data-save-route-favorite ${currentRoute ? "" : "disabled"}>
                        ${this.localize("frontend.route_save_route_favorite", "Save current route")}
                    </button>
                    <button class="favorite-copy-button" data-copy-route-favorite ${currentRouteCanCopy ? "" : "disabled"} title="${this.localize("frontend.route_copy_route_favorite", "Copy current route")}"><ha-icon icon="mdi:content-copy"></ha-icon></button>
                </div>
                <div class="favorite-save-row two">
                    <button class="favorite-save" data-save-origin-favorite ${currentOrigin ? "" : "disabled"}>
                        ${this.localize("frontend.route_save_origin_favorite", "Save origin")}
                    </button>
                    <button class="favorite-copy-button" data-copy-origin-favorite ${currentOriginCanCopy ? "" : "disabled"} title="${this.localize("frontend.route_copy_origin_favorite", "Copy origin")}"><ha-icon icon="mdi:content-copy"></ha-icon></button>
                    <button class="favorite-save" data-save-destination-favorite ${currentDestination ? "" : "disabled"}>
                        ${this.localize("frontend.route_save_destination_favorite", "Save destination")}
                    </button>
                    <button class="favorite-copy-button" data-copy-destination-favorite ${currentDestinationCanCopy ? "" : "disabled"} title="${this.localize("frontend.route_copy_destination_favorite", "Copy destination")}"><ha-icon icon="mdi:content-copy"></ha-icon></button>
                </div>
                ${this._favoriteMessage ? `<div class="favorite-message">${this.escapeHtml(this._favoriteMessage)}</div>` : ""}
                ${configuredRoutes.length ? `<div class="favorite-section">${this.localize("frontend.route_favorite_routes", "Predefined routes")}</div>${configuredRoutes.map((favorite, index) => renderRouteFavorite(favorite, "config", index)).join("")}` : ""}
                ${configuredStations.length ? `<div class="favorite-section">${this.localize("frontend.route_favorite_stations", "Predefined stations")}</div>${configuredStations.map((favorite, index) => renderStationFavorite(favorite, "config", index)).join("")}` : ""}
                ${localRoutes.length ? `
                    <div class="favorite-section-row">
                        <div class="favorite-section">${this.localize("frontend.route_local_routes", "Local routes")}</div>
                        <button class="favorite-copy-button" data-copy-local-route-favorites title="${this.localize("frontend.route_copy_local_routes", "Copy all local routes")}"><ha-icon icon="mdi:content-copy"></ha-icon></button>
                    </div>
                    ${localRoutes.map((favorite, index) => renderRouteFavorite(favorite, "local", index)).join("")}
                ` : ""}
                ${localStations.length ? `
                    <div class="favorite-section-row">
                        <div class="favorite-section">${this.localize("frontend.route_local_stations", "Local stations")}</div>
                        <button class="favorite-copy-button" data-copy-local-station-favorites title="${this.localize("frontend.route_copy_local_stations", "Copy all local stations")}"><ha-icon icon="mdi:content-copy"></ha-icon></button>
                    </div>
                    ${localStations.map((favorite, index) => renderStationFavorite(favorite, "local", index)).join("")}
                ` : ""}
                ${hasFavorites ? "" : `<div class="empty">${this.localize("frontend.favorite_empty", "No favorites saved")}</div>`}
                ${renderDeletePopup()}
            </div>
        `;
    }

    renderStartRouteFavorites() {
        if (this.config.showRouteFavoritesOnStart !== true || this._routes.length || this._loading) return "";
        const title = this.translateIfAvailable("frontend.route_start_favorites");
        if (!title) return "";

        const routeFavorites = this.getStartRouteFavorites();
        if (!routeFavorites.length) return "";

        return `
            <div class="start-route-favorites">
                <div class="start-route-title">${this.escapeHtml(title)}</div>
                <div class="start-route-list">
                    ${routeFavorites.map(({ favorite, ref }) => `
                        <button class="start-route-item" data-start-route-favorite="${this.escapeHtml(ref)}">
                            <span class="start-route-name">${this.escapeHtml(favorite.name)}</span>
                            <span class="start-route-meta">${this.escapeHtml(favorite.originName)} → ${this.escapeHtml(favorite.destinationName)}</span>
                        </button>
                    `).join("")}
                </div>
            </div>
        `;
    }

    renderFilterPanel() {
        if (!this._showFilters) return "";

        const filters = this.getRouteFilters();
        const selectedTransportTypes = new Set(this.normalizeTransportTypes(filters.transportTypes, []));
        const timeMode = filters.timeMode || "now";
        const routeType = this.normalizeRouteType(filters.routeType);
        const changeSpeed = this.normalizeChangeSpeed(filters.changeSpeed);
        const dateTimeValue = filters.dateTime || this.getCurrentLocalDateTimeValue();

        const renderTransportChip = (type) => `
            <button class="filter-chip ${selectedTransportTypes.has(type) ? "active" : ""}" data-filter-transport="${this.escapeHtml(type)}">
                ${this.escapeHtml(this.getTransportTypeLabel(type))}
            </button>
        `;
        const renderTimeChip = (mode, label) => `
            <button class="filter-chip ${timeMode === mode ? "active" : ""}" data-filter-time-mode="${this.escapeHtml(mode)}">
                ${this.escapeHtml(label)}
            </button>
        `;

        return `
            <div class="filter-panel">
                <div class="filter-header">
                    <strong>${this.localize("frontend.route_filters", "Filters")}</strong>
                    <button class="filter-reset" data-filter-reset>${this.localize("frontend.route_filters_reset", "Reset")}</button>
                </div>
                <div class="filter-section">
                    <span class="filter-label">${this.localize("frontend.route_filter_transport_types", "Transport types")}</span>
                    <div class="filter-chips">${routeTransportTypes.map(type => renderTransportChip(type)).join("")}</div>
                    <small>${this.localize("frontend.route_filter_empty_transport_hint", "If none are selected, all transport types are requested.")}</small>
                </div>
                <div class="filter-section">
                    <span class="filter-label">${this.localize("frontend.route_filter_time", "Time")}</span>
                    <div class="filter-chips">
                        ${renderTimeChip("now", this.localize("frontend.route_time_now", "Now"))}
                        ${renderTimeChip("departure", this.localize("frontend.route_time_departure_at", "Departure at"))}
                        ${renderTimeChip("arrival", this.localize("frontend.route_time_arrival_at", "Arrival at"))}
                    </div>
                    ${timeMode !== "now" ? `
                        <input class="filter-datetime" type="datetime-local" value="${this.escapeHtml(dateTimeValue)}" aria-label="${this.escapeHtml(this.localize("frontend.route_filter_datetime", "Date and time"))}">
                    ` : ""}
                </div>
                <div class="filter-section compact">
                    <label>
                        <span class="filter-label">${this.localize("frontend.route_filter_route_type", "Route type")}</span>
                        <select class="filter-select" data-filter-route-type>
                            <option value="LEAST_TIME" ${routeType === "LEAST_TIME" ? "selected" : ""}>${this.localize("frontend.route_type_least_time", "Fastest route")}</option>
                            <option value="LEAST_INTERCHANGES" ${routeType === "LEAST_INTERCHANGES" ? "selected" : ""}>${this.localize("frontend.route_type_least_interchanges", "Fewest transfers")}</option>
                            <option value="LEAST_WALKING" ${routeType === "LEAST_WALKING" ? "selected" : ""}>${this.localize("frontend.route_type_least_walking", "Least walking")}</option>
                        </select>
                    </label>
                    <label>
                        <span class="filter-label">${this.localize("frontend.route_filter_change_speed", "Walking speed")}</span>
                        <select class="filter-select" data-filter-change-speed>
                            <option value="SLOW" ${changeSpeed === "SLOW" ? "selected" : ""}>${this.localize("frontend.route_change_speed_slow", "Slow")}</option>
                            <option value="NORMAL" ${changeSpeed === "NORMAL" ? "selected" : ""}>${this.localize("frontend.route_change_speed_normal", "Normal")}</option>
                            <option value="FAST" ${changeSpeed === "FAST" ? "selected" : ""}>${this.localize("frontend.route_change_speed_fast", "Fast")}</option>
                        </select>
                    </label>
                </div>
            </div>
        `;
    }

    renderInfoPopup() {
        if (!this._infoPopup) return "";

        const details = [
            this._infoPopup.type,
            this._infoPopup.network,
        ].filter(Boolean).join(" · ");

        return `
            <div class="route-info-backdrop" data-close-info-popup>
                <div class="route-info-dialog" role="dialog" aria-modal="true" aria-label="${this.escapeHtml(this.localize("frontend.route_info_details", "Details"))}">
                    <div class="route-info-title">${this.escapeHtml(this._infoPopup.title)}</div>
                    ${details ? `<div class="route-info-meta">${this.escapeHtml(details)}</div>` : ""}
                    ${this._infoPopup.description ? `<div class="route-info-text">${this.escapeHtml(this._infoPopup.description)}</div>` : ""}
                    <button class="route-info-close" data-close-info-popup>${this.localize("frontend.route_info_close", "Close")}</button>
                </div>
            </div>
        `;
    }

    render() {
        if (!this.content) {
            const card = document.createElement("ha-card");
            this.content = document.createElement("div");
            const style = document.createElement("style");
            style.textContent = `
                .container { background: var(--amvg-card-bg-color, #000080); color: var(--amvg-text-color, #fff); border-radius: var(--ha-card-border-radius, 12px); overflow: hidden; position: relative; }
                .container.favorites-open { min-height: min(560px, 88vh); }
                .header { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 10px; font-weight: bold; }
                .route-scroll { overscroll-behavior: contain; }
                .route-scroll.dragging { cursor: grabbing; user-select: none; }
                .controls { display: grid; gap: 8px; padding: 8px; background: rgba(255,255,255,0.08); }
                .search-grid { display: grid; grid-template-columns: minmax(0, 1fr) 42px; gap: 6px; }
                .search-grid.location { grid-template-columns: 42px minmax(0, 1fr) 42px; }
                .search { width: 100%; min-width: 0; box-sizing: border-box; border: 1px solid var(--divider-color, rgba(255,255,255,0.35)); border-radius: 6px; padding: 8px 9px; color: var(--primary-text-color, #fff); background: var(--secondary-background-color, rgba(255,255,255,0.14)); font: inherit; }
                .search:focus { outline: none; border-color: var(--primary-color, #03a9f4); box-shadow: 0 0 0 1px var(--primary-color, #03a9f4); }
                button { font: inherit; }
                .icon-button, .route-button { border: 1px solid var(--divider-color, rgba(255,255,255,0.35)); border-radius: 6px; color: var(--primary-text-color, #fff); background: var(--secondary-background-color, rgba(255,255,255,0.14)); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0 10px; min-height: 38px; }
                .icon-button { width: 42px; min-width: 42px; padding: 0; }
                .icon-button:hover, .icon-button:focus, .route-button:hover, .route-button:focus, .station:hover, .station:focus { outline: none; background: rgba(255,255,255,0.22); border-color: var(--primary-color, #03a9f4); }
                .actions { display: grid; grid-template-columns: 42px minmax(0, 1fr) 42px 42px; gap: 6px; }
                .route-button.primary { color: var(--amvg-header-text-color, #000080); background: var(--amvg-header-bg-color, #FAE10C); font-weight: bold; }
                .route-button.primary:disabled { opacity: 0.55; cursor: default; }
                .favorites-button.active, .filter-button.active { color: var(--amvg-header-text-color, #000080); background: var(--amvg-header-bg-color, #FAE10C); }
                .filter-panel { display: grid; gap: 8px; border: 1px solid rgba(255,255,255,0.28); border-radius: 8px; padding: 8px; background: rgba(0,0,0,0.14); }
                .filter-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
                .filter-reset { border: 0; border-radius: 5px; color: inherit; background: rgba(255,255,255,0.12); cursor: pointer; padding: 4px 8px; font: inherit; font-size: 0.82em; }
                .filter-section { display: grid; gap: 5px; }
                .filter-section.compact { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 8px; }
                .filter-section.compact label { min-width: 0; display: grid; gap: 5px; }
                .filter-label { font-size: 0.84em; font-weight: 800; opacity: 0.9; }
                .filter-section small { opacity: 0.72; line-height: 1.25; }
                .filter-chips { display: flex; flex-wrap: wrap; gap: 5px; }
                .filter-chip { border: 1px solid rgba(255,255,255,0.35); border-radius: 999px; color: inherit; background: rgba(255,255,255,0.1); cursor: pointer; padding: 4px 8px; font: inherit; font-size: 0.82em; }
                .filter-chip.active { color: var(--amvg-header-text-color, #000080); background: var(--amvg-header-bg-color, #FAE10C); border-color: var(--amvg-header-bg-color, #FAE10C); font-weight: bold; }
                .filter-select, .filter-datetime { width: 100%; min-width: 0; box-sizing: border-box; border: 1px solid var(--divider-color, rgba(255,255,255,0.35)); border-radius: 6px; padding: 6px 7px; color: var(--primary-text-color, #fff); background: var(--secondary-background-color, rgba(255,255,255,0.14)); font: inherit; }
                .filter-reset:hover, .filter-reset:focus, .filter-chip:hover, .filter-chip:focus, .filter-select:focus, .filter-datetime:focus { outline: none; background: rgba(255,255,255,0.22); border-color: var(--primary-color, #03a9f4); }
                .favorites-menu { position: absolute; right: 8px; top: 184px; z-index: 12; width: min(430px, calc(100% - 16px)); max-height: 52vh; overflow: auto; padding: 6px; background: var(--amvg-card-bg-color, #000080); border: 1px solid rgba(255,255,255,0.35); border-radius: 8px; box-shadow: 0 10px 24px rgba(0,0,0,0.35); display: grid; gap: 4px; }
                .favorite-save-row { display: grid; grid-template-columns: minmax(0, 1fr) 34px; align-items: stretch; gap: 4px; }
                .favorite-save-row.two { grid-template-columns: minmax(0, 1fr) 34px minmax(0, 1fr) 34px; }
                .favorite-save { width: 100%; text-align: left; border: 0; border-radius: 5px; padding: 7px 8px; color: inherit; background: rgba(255,255,255,0.16); cursor: pointer; font: inherit; }
                .favorite-save:disabled, .favorite-copy-button:disabled { opacity: 0.55; cursor: default; }
                .favorite-section { padding: 8px 6px 4px; margin-top: 3px; border-top: 1px solid rgba(255,255,255,0.25); font-size: 0.95em; opacity: 1; font-weight: 800; }
                .favorite-section:first-child { margin-top: 0; border-top: 0; }
                .favorite-section-row { display: grid; grid-template-columns: minmax(0, 1fr) 34px; align-items: stretch; gap: 4px; }
                .favorite-row { display: grid; grid-template-columns: minmax(0, 1fr) 34px; align-items: stretch; gap: 4px; }
                .favorite-row.config { grid-template-columns: minmax(0, 1fr); }
                .favorite-row.station-favorite.local { grid-template-columns: 34px 34px minmax(0, 1fr) 34px; }
                .favorite-row.station-favorite.config { grid-template-columns: 34px 34px minmax(0, 1fr); }
                .favorite-item, .favorite-action, .favorite-delete, .favorite-copy-button { border: 0; border-radius: 5px; color: inherit; background: rgba(255,255,255,0.12); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0; font: inherit; }
                .favorite-item { min-width: 0; text-align: left; display: block; padding: 6px 8px; }
                .favorite-action, .favorite-delete, .favorite-copy-button { width: 34px; min-width: 34px; min-height: 34px; }
                .favorite-item:hover, .favorite-item:focus, .favorite-action:hover, .favorite-action:focus, .favorite-delete:hover, .favorite-delete:focus, .favorite-save:hover:not(:disabled), .favorite-save:focus:not(:disabled), .favorite-copy-button:hover:not(:disabled), .favorite-copy-button:focus:not(:disabled), .favorite-confirm-cancel:hover, .favorite-confirm-cancel:focus { background: rgba(255,255,255,0.22); outline: none; }
                .favorite-title { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                .favorite-meta { display: block; opacity: 0.75; font-size: 0.78em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                .favorite-message { padding: 7px 8px; border-radius: 5px; color: var(--amvg-header-text-color, #000080); background: var(--amvg-header-bg-color, #FAE10C); font-weight: bold; }
                .favorite-delete-backdrop { position: absolute; inset: 6px; z-index: 15; padding: 10px; border-radius: 8px; background: rgba(0,0,0,0.48); display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
                .favorite-delete-dialog { width: 100%; box-sizing: border-box; padding: 12px; border-radius: 8px; background: var(--amvg-card-bg-color, #000080); border: 1px solid rgba(255,255,255,0.35); display: grid; gap: 10px; }
                .favorite-confirm-actions { display: flex; justify-content: flex-end; gap: 6px; }
                .favorite-confirm-cancel, .favorite-confirm-delete { border: 0; border-radius: 5px; padding: 6px 10px; color: inherit; cursor: pointer; font: inherit; }
                .favorite-confirm-cancel { background: rgba(255,255,255,0.12); }
                .favorite-confirm-delete { background: var(--error-color, #db4437); color: #fff; }
                .favorite-confirm-delete:hover, .favorite-confirm-delete:focus { filter: brightness(1.1); outline: none; }
                .station-list { display: grid; gap: 3px; padding: 0 8px 8px; background: rgba(255,255,255,0.08); }
                .station { text-align: left; border: 0; border-radius: 5px; padding: 7px 8px; color: inherit; background: rgba(255,255,255,0.12); cursor: pointer; }
                .station span, .station small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                .station small { opacity: 0.75; }
                .empty { padding: 10px; }
                .start-route-favorites { display: grid; gap: 6px; padding: 8px; }
                .start-route-title { font-size: 0.95em; font-weight: 800; opacity: 0.9; }
                .start-route-list { display: grid; gap: 5px; }
                .start-route-item { min-width: 0; text-align: left; border: 0; border-radius: 6px; padding: 8px 10px; color: inherit; background: rgba(255,255,255,0.12); cursor: pointer; font: inherit; }
                .start-route-item:hover, .start-route-item:focus { outline: none; background: rgba(255,255,255,0.22); }
                .start-route-name { display: block; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                .start-route-meta { display: block; opacity: 0.74; font-size: 0.82em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                .route-paging { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 6px; padding: 8px 8px 0; }
                .route-paging.bottom { padding: 0 8px 8px; }
                .route-paging-button { border: 1px solid var(--divider-color, rgba(255,255,255,0.35)); border-radius: 6px; color: var(--primary-text-color, #fff); background: var(--secondary-background-color, rgba(255,255,255,0.14)); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 4px; min-height: 34px; padding: 0 8px; font-weight: bold; }
                .route-paging-button:hover:not(:disabled), .route-paging-button:focus:not(:disabled) { outline: none; background: rgba(255,255,255,0.22); border-color: var(--primary-color, #03a9f4); }
                .route-paging-button:disabled { opacity: 0.55; cursor: default; }
                .route-paging-button ha-icon { --mdc-icon-size: 18px; width: 18px; height: 18px; }
                .routes { display: grid; gap: 8px; padding: 8px; }
                .route { border-top: 1px solid rgba(255,255,255,0.25); padding-top: 8px; }
                .route:first-child { border-top: 0; padding-top: 0; }
                .route-summary { display: flex; align-items: start; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
                .route-summary.collapsible { cursor: pointer; border-radius: 5px; padding: 2px 3px; margin: -2px -3px 6px; }
                .route-summary.collapsible:hover, .route-summary.collapsible:focus { outline: none; background: rgba(255,255,255,0.08); }
                .route-summary-main { min-width: 0; }
                .route-summary-meta { display: block; opacity: 0.78; font-size: 0.86em; }
                .route-summary-time { font-size: 1.16em; line-height: 1.18; }
                .route-summary-time .summary-time { display: inline; opacity: 1; font-size: inherit; }
                .route-summary-side { display: grid; justify-items: end; gap: 4px; min-width: 0; max-width: 48%; }
                .route-number { opacity: 0.75; font-size: 0.86em; }
                .route-line-chain { display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: center; gap: 3px; min-width: 0; }
                .route-line-separator { opacity: 0.7; font-size: 0.78em; }
                .parts { display: grid; gap: 6px; }
                .parts.hidden { display: none; }
                .part { display: grid; grid-template-columns: 76px 48px minmax(0, 1fr); gap: 6px; align-items: start; }
                .part-time { display: grid; gap: 3px; white-space: nowrap; opacity: 0.9; }
                .time-delay { margin-left: 3px; }
                .transfer-time { display: grid; grid-template-columns: 76px 48px minmax(0, 1fr); gap: 6px; align-items: center; color: var(--secondary-text-color, rgba(255,255,255,0.74)); font-size: 0.84em; }
                .transfer-time span:last-child { border-left: 2px solid rgba(255,255,255,0.28); padding-left: 7px; }
                .part-line { display: grid; gap: 3px; justify-items: start; }
                .part-main { min-width: 0; }
                .part-main strong { font-weight: bold; }
                .muted { opacity: 0.78; font-size: 0.86em; display: flex; gap: 8px; flex-wrap: wrap; }
                .link-button { border: 0; color: inherit; background: transparent; padding: 0; cursor: pointer; display: inline-flex; align-items: center; gap: 2px; opacity: 1; }
                .link-button:hover, .link-button:focus { outline: none; text-decoration: underline; }
                .link-button ha-icon { --mdc-icon-size: 14px; width: 14px; height: 14px; }
                .intermediate-list { display: grid; gap: 3px; margin: 4px 0 3px; padding: 5px 6px; border-left: 2px solid rgba(255,255,255,0.35); background: rgba(255,255,255,0.07); font-size: 0.86em; }
                .intermediate-stop { display: grid; grid-template-columns: 82px minmax(0, 1fr) auto; gap: 6px; align-items: center; }
                .intermediate-time { opacity: 0.82; white-space: nowrap; text-align: left; justify-self: start; }
                .intermediate-time .delay { margin-left: 3px; }
                .intermediate-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                .intermediate-platform { opacity: 0.78; white-space: nowrap; }
                .infos { margin-top: 3px; display: flex; gap: 4px; flex-wrap: wrap; }
                .info-button { border: 1px solid rgba(255,255,255,0.35); border-radius: 5px; color: var(--warning-color, #ff9800); background: rgba(255,255,255,0.08); cursor: pointer; padding: 2px 6px; font-size: 0.84em; text-align: left; }
                .info-button:hover, .info-button:focus { outline: none; border-color: var(--warning-color, #ff9800); background: rgba(255,255,255,0.16); }
                .route-info-backdrop { position: fixed; inset: 0; z-index: 999; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; }
                .route-info-dialog { max-width: 520px; width: min(520px, 100%); border-radius: 12px; border: 1px solid var(--divider-color, rgba(255,255,255,0.3)); background: var(--card-background-color, #1c1c1c); color: var(--primary-text-color, #fff); padding: 18px; box-sizing: border-box; box-shadow: var(--ha-card-box-shadow, 0 6px 18px rgba(0,0,0,0.35)); }
                .route-info-title { font-size: 1.05em; font-weight: bold; margin-bottom: 8px; }
                .route-info-meta { opacity: 0.72; font-size: 0.9em; margin-bottom: 8px; }
                .route-info-text { white-space: pre-wrap; line-height: 1.35; }
                .route-info-close { margin-top: 14px; border: 0; border-radius: 999px; color: var(--text-primary-color, #fff); background: var(--primary-color, #03a9f4); padding: 8px 16px; cursor: pointer; float: right; }
                .delay { color: red; font-weight: bold; }
                .sev-text { color: red; font-weight: bold; }
                .line { font-weight: bold; color: #fff; background: #000; border: 1px solid #fff; display: inline-block; min-width: 35px; text-align: center; padding: 0 3px; }
                .line.mini { min-width: 0; font-size: 0.72em; line-height: 1.35; padding: 0 5px; }
                .sev-badge { font-weight: bold; color: #E30613; background: #fff; border: 1px solid #E30613; display: inline-block; min-width: 35px; text-align: center; padding: 0 3px; font-size: 0.72em; line-height: 1.35; }
                .sev-badge.mini { min-width: 0; padding: 0 4px; }
                .PEDESTRIAN, .WALK { background: transparent; color: inherit; border-color: rgba(255,255,255,0.5); }
                .BUS, .REGIONAL_BUS { background-color: #00586A; }
                .BAHN { background-color: #fff; color: #E30613; border-color: #E30613; }
                .SBAHN { border-radius: 999px; }
                .S1 { background-color: #16BAE7; } .S2 { background-color: #76B82A; } .S3 { background-color: #951B81; } .S4 { background-color: #E30613; }
                .S5 { background-color: #005E82; } .S6 { background-color: #00975F; } .S7 { background-color: #943126; } .S8 { background-color: #000; }
                .S20 { background-color: #ED6B83; } .TRAM { background-color: #D82020; }
                .U1 { background-color: #438136; } .U2 { background-color: #C40C37; } .U3 { background-color: #F36E31; } .U4 { background-color: #0AB38D; }
                .U5 { background-color: #B8740E; } .U6 { background-color: #006CB3; } .U7 { background: linear-gradient(322deg, #C40C37 50%, #438136 50%); }
                .U8 { background: linear-gradient(322deg, #F36E31 50%, #C40C37 50%); }
                @media (max-width: 520px) {
                    .filter-section.compact { grid-template-columns: minmax(0, 1fr); }
                    .route-summary { display: grid; grid-template-columns: minmax(0, 1fr) auto; }
                    .route-summary-side { max-width: 100%; }
                    .route-line-chain { grid-column: 1 / -1; justify-content: flex-start; }
                }
            `;
            card.appendChild(style);
            card.appendChild(this.content);
            this.appendChild(card);
        }

        const title = this.config.name || "Another MVG Route";
        const canSearchRoutes = this._originStation && this._destinationStation && !this._loading;
        const canLoadMoreRoutes = this._routes.length && !this._loading && !this._loadingEarlier && !this._loadingLater;
        const showLocationSearch = this.config.showLocationSearch === true;
        const routeCardHeight = Number(this.config.routeMaxHeight || 0);
        const routeScrollStyle = routeCardHeight > 0 ? ` style="height:${Math.round(routeCardHeight)}px; overflow:auto;"` : "";
        const pagingPosition = this.config.routePagingPosition || "bottom";
        const shouldShowRoutePaging = (position) => (
            pagingPosition === position || pagingPosition === "both"
        );
        const routePaging = (position) => this._routes.length && shouldShowRoutePaging(position) ? `
            <div class="route-paging ${position}">
                <button class="route-paging-button load-earlier-routes" ${canLoadMoreRoutes ? "" : "disabled"}>
                    <ha-icon icon="mdi:chevron-up"></ha-icon>
                    ${this._loadingEarlier ? this.localize("frontend.loading", "Loading...") : this.localize("frontend.route_earlier", "Earlier")}
                </button>
                <button class="route-paging-button load-later-routes" ${canLoadMoreRoutes ? "" : "disabled"}>
                    ${this._loadingLater ? this.localize("frontend.loading", "Loading...") : this.localize("frontend.route_later", "Later")}
                    <ha-icon icon="mdi:chevron-down"></ha-icon>
                </button>
            </div>
        ` : "";

        this.content.innerHTML = `
            <div class="container ${this._showFavorites ? "favorites-open" : ""}">
                <div class="header">
                    <span>${this.escapeHtml(title)}</span>
                </div>
                <div class="route-scroll"${routeScrollStyle}>
                    <div class="controls">
                        <div class="search-grid ${showLocationSearch ? "location" : ""}">
                            ${showLocationSearch ? `<button class="icon-button origin-location-button" title="${this.localize("frontend.location_search_button", "Use current location")}">${this._locatingOrigin ? "..." : `<ha-icon icon="mdi:crosshairs-gps"></ha-icon>`}</button>` : ""}
                            <input class="search origin-search" type="search" placeholder="${this.localize("frontend.route_origin", "From")}" value="${this.escapeHtml(this._originQuery)}">
                            <button class="icon-button origin-button" title="${this.localize("frontend.search_button", "Search")}">${this._searchingOrigin ? "..." : `<ha-icon icon="mdi:magnify"></ha-icon>`}</button>
                        </div>
                        <div class="search-grid ${showLocationSearch ? "location" : ""}">
                            ${showLocationSearch ? `<button class="icon-button destination-location-button" title="${this.localize("frontend.location_search_button", "Use current location")}">${this._locatingDestination ? "..." : `<ha-icon icon="mdi:crosshairs-gps"></ha-icon>`}</button>` : ""}
                            <input class="search destination-search" type="search" placeholder="${this.localize("frontend.route_destination", "To")}" value="${this.escapeHtml(this._destinationQuery)}">
                            <button class="icon-button destination-button" title="${this.localize("frontend.search_button", "Search")}">${this._searchingDestination ? "..." : `<ha-icon icon="mdi:magnify"></ha-icon>`}</button>
                        </div>
                        <div class="actions">
                            <button class="icon-button swap-button" title="${this.localize("frontend.route_swap", "Swap")}"><ha-icon icon="mdi:swap-vertical"></ha-icon></button>
                            <button class="route-button primary fetch-routes" ${canSearchRoutes ? "" : "disabled"}>${this._loading ? this.localize("frontend.loading", "Loading...") : this.localize("frontend.route_search", "Find route")}</button>
                            <button class="icon-button filter-button ${this._showFilters ? "active" : ""}" title="${this.escapeHtml(this.localize("frontend.route_filters", "Filters"))}" aria-label="${this.escapeHtml(this.getRouteFilterSummary())}"><ha-icon icon="mdi:tune"></ha-icon></button>
                            <button class="icon-button favorites-button ${this._showFavorites ? "active" : ""}" title="${this.localize("frontend.favorites", "Favorites")}"><ha-icon icon="mdi:star-outline"></ha-icon></button>
                        </div>
                        ${this.renderFilterPanel()}
                    </div>
                    ${this.renderStationResults("origin", this._originResults)}
                    ${this.renderStationResults("destination", this._destinationResults)}
                    ${this._error ? `<div class="empty">${this.escapeHtml(this._error)}</div>` : ""}
                    ${!this._originResults.length && !this._destinationResults.length && !this._error ? this.renderStartRouteFavorites() : ""}
                    ${routePaging("top")}
                    ${this._routes.length ? `<div class="routes">${this._routes.map((route, index) => this.renderRoute(route, index)).join("")}</div>` : ""}
                    ${routePaging("bottom")}
                </div>
                ${this.renderFavoriteMenu()}
                ${this.renderInfoPopup()}
            </div>
        `;

        this.enableDragScroll(this.content.querySelector(".route-scroll"));

        const originInput = this.content.querySelector(".origin-search");
        const destinationInput = this.content.querySelector(".destination-search");
        this.content.querySelector(".origin-button")?.addEventListener("click", () => this.searchStations("origin"));
        this.content.querySelector(".destination-button")?.addEventListener("click", () => this.searchStations("destination"));
        this.content.querySelector(".origin-location-button")?.addEventListener("click", () => this.searchNearbyStations("origin"));
        this.content.querySelector(".destination-location-button")?.addEventListener("click", () => this.searchNearbyStations("destination"));
        this.content.querySelector(".swap-button")?.addEventListener("click", () => this.swapStations());
        this.content.querySelector(".fetch-routes")?.addEventListener("click", () => this.fetchRoutes());
        this.content.querySelectorAll(".load-earlier-routes").forEach(button => {
            button.addEventListener("click", () => this.fetchRoutes("earlier"));
        });
        this.content.querySelectorAll(".load-later-routes").forEach(button => {
            button.addEventListener("click", () => this.fetchRoutes("later"));
        });
        this.content.querySelector(".favorites-button")?.addEventListener("click", () => {
            this._showFavorites = !this._showFavorites;
            if (this._showFavorites) this._showFilters = false;
            this._favoriteMessage = "";
            this._pendingDeleteFavorite = null;
            this.render();
        });
        this.content.querySelector(".filter-button")?.addEventListener("click", () => {
            this._showFilters = !this._showFilters;
            if (this._showFilters) {
                this._showFavorites = false;
                this._favoriteMessage = "";
                this._pendingDeleteFavorite = null;
            }
            this.render();
        });
        this.content.querySelectorAll("[data-filter-transport]").forEach(button => {
            button.addEventListener("click", () => {
                const filters = this.getRouteFilters();
                const type = String(button.dataset.filterTransport || "").toUpperCase();
                const selected = new Set(this.normalizeTransportTypes(filters.transportTypes, []));
                if (selected.has(type)) selected.delete(type);
                else if (routeTransportTypes.includes(type)) selected.add(type);
                filters.transportTypes = [...selected];
                this.render();
            });
        });
        this.content.querySelectorAll("[data-filter-time-mode]").forEach(button => {
            button.addEventListener("click", () => {
                const filters = this.getRouteFilters();
                const mode = button.dataset.filterTimeMode;
                filters.timeMode = ["now", "departure", "arrival"].includes(mode) ? mode : "now";
                if (filters.timeMode !== "now" && !filters.dateTime) {
                    filters.dateTime = this.getCurrentLocalDateTimeValue();
                }
                this.render();
            });
        });
        this.content.querySelector(".filter-datetime")?.addEventListener("change", (event) => {
            this.getRouteFilters().dateTime = event.currentTarget.value || "";
            this.render();
        });
        this.content.querySelector("[data-filter-route-type]")?.addEventListener("change", (event) => {
            this.getRouteFilters().routeType = this.normalizeRouteType(event.currentTarget.value);
            this.render();
        });
        this.content.querySelector("[data-filter-change-speed]")?.addEventListener("change", (event) => {
            this.getRouteFilters().changeSpeed = this.normalizeChangeSpeed(event.currentTarget.value);
            this.render();
        });
        this.content.querySelector("[data-filter-reset]")?.addEventListener("click", () => {
            this._routeFilters = this.getDefaultRouteFilters();
            this.render();
        });
        this.content.querySelector("[data-save-origin-favorite]")?.addEventListener("click", () => this.saveStationFavorite(this._originStation));
        this.content.querySelector("[data-save-destination-favorite]")?.addEventListener("click", () => this.saveStationFavorite(this._destinationStation));
        this.content.querySelector("[data-save-route-favorite]")?.addEventListener("click", () => this.saveCurrentRouteFavorite());
        this.content.querySelector("[data-copy-origin-favorite]")?.addEventListener("click", () => {
            const favorite = this.getStationFavoriteFromStation(this._originStation);
            if (favorite) this.copyFavoriteText(this.formatStationFavoriteForConfig(favorite));
        });
        this.content.querySelector("[data-copy-destination-favorite]")?.addEventListener("click", () => {
            const favorite = this.getStationFavoriteFromStation(this._destinationStation);
            if (favorite) this.copyFavoriteText(this.formatStationFavoriteForConfig(favorite));
        });
        this.content.querySelector("[data-copy-route-favorite]")?.addEventListener("click", () => {
            const favorite = this.getRouteFavoriteFromCurrent();
            if (favorite) this.copyFavoriteText(this.formatRouteFavoriteForConfig(favorite));
        });
        this.content.querySelector("[data-copy-local-station-favorites]")?.addEventListener("click", () => {
            this.copyFavoriteText(this.getVisibleLocalStationFavorites().map(favorite => this.formatStationFavoriteForConfig(favorite)).filter(Boolean).join("\n"));
        });
        this.content.querySelector("[data-copy-local-route-favorites]")?.addEventListener("click", () => {
            this.copyFavoriteText(this.getVisibleLocalRouteFavorites().map(favorite => this.formatRouteFavoriteForConfig(favorite)).filter(Boolean).join("\n"));
        });
        this.content.querySelectorAll("[data-station-origin]").forEach(button => {
            button.addEventListener("click", () => this.setStationFavorite("origin", this.getStationFavoriteByRef(button.dataset.stationOrigin)));
        });
        this.content.querySelectorAll("[data-station-destination]").forEach(button => {
            button.addEventListener("click", () => this.setStationFavorite("destination", this.getStationFavoriteByRef(button.dataset.stationDestination)));
        });
        this.content.querySelectorAll("[data-route-favorite]").forEach(button => {
            button.addEventListener("click", () => this.loadRouteFavorite(this.getRouteFavoriteByRef(button.dataset.routeFavorite)));
        });
        this.content.querySelectorAll("[data-start-route-favorite]").forEach(button => {
            button.addEventListener("click", () => this.loadRouteFavorite(this.getRouteFavoriteByRef(button.dataset.startRouteFavorite)));
        });
        this.content.querySelectorAll("[data-delete-station-favorite]").forEach(button => {
            button.addEventListener("click", () => this.requestDeleteLocalFavorite("station", button.dataset.deleteStationFavorite));
        });
        this.content.querySelectorAll("[data-delete-route-favorite]").forEach(button => {
            button.addEventListener("click", () => this.requestDeleteLocalFavorite("route", button.dataset.deleteRouteFavorite));
        });
        this.content.querySelector("[data-cancel-delete-favorite]")?.addEventListener("click", () => {
            this._pendingDeleteFavorite = null;
            this.render();
        });
        this.content.querySelector("[data-confirm-delete-favorite]")?.addEventListener("click", (event) => {
            const [type, ...keyParts] = String(event.currentTarget.dataset.confirmDeleteFavorite || "").split(":");
            this.deleteLocalFavorite(type, keyParts.join(":"));
        });
        this.content.querySelectorAll("[data-info-key]").forEach(button => {
            button.addEventListener("click", () => {
                this._infoPopup = this.findInfoItem(button.dataset.infoKey);
                this.render();
            });
        });
        this.content.querySelectorAll("[data-close-info-popup]").forEach(element => {
            element.addEventListener("click", (event) => {
                if (event.target === element || element.classList.contains("route-info-close")) {
                    this._infoPopup = null;
                    this.render();
                }
            });
        });
        this.content.querySelectorAll("[data-stops-key]").forEach(button => {
            button.addEventListener("click", () => this.toggleIntermediateStops(button.dataset.stopsKey, button));
        });
        this.content.querySelectorAll("[data-route-toggle]").forEach(element => {
            const toggle = () => {
                const index = this._routes.findIndex((route, routeIndex) => this.getRouteKey(route, routeIndex) === element.dataset.routeToggle);
                if (index >= 0) this.toggleRouteCollapsed(this._routes[index], index, element);
            };
            element.addEventListener("click", toggle);
            element.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    toggle();
                }
            });
        });

        originInput?.addEventListener("input", () => {
            this._originQuery = originInput.value;
            this._originStation = null;
            this._originResults = [];
            this._routes = [];
        });
        destinationInput?.addEventListener("input", () => {
            this._destinationQuery = destinationInput.value;
            this._destinationStation = null;
            this._destinationResults = [];
            this._routes = [];
        });
        originInput?.addEventListener("keydown", (event) => {
            if (event.key === "Enter") this.searchStations("origin");
        });
        destinationInput?.addEventListener("keydown", (event) => {
            if (event.key === "Enter") this.searchStations("destination");
        });

        this.content.querySelectorAll("[data-select-origin]").forEach(button => {
            button.addEventListener("click", () => this.selectStation("origin", button.dataset.selectOrigin));
        });
        this.content.querySelectorAll("[data-select-destination]").forEach(button => {
            button.addEventListener("click", () => this.selectStation("destination", button.dataset.selectDestination));
        });
    }

    setConfig(config) {
        const previousDefaults = JSON.stringify({
            transportType: this.config?.transportType || this.config?.transportTypes || null,
            routeType: this.config?.routeType || null,
            changeSpeed: this.config?.changeSpeed || null,
        });
        this.config = config || {};
        const nextDefaults = JSON.stringify({
            transportType: this.config?.transportType || this.config?.transportTypes || null,
            routeType: this.config?.routeType || null,
            changeSpeed: this.config?.changeSpeed || null,
        });
        if (previousDefaults !== nextDefaults) {
            this._routeFilters = null;
        }
    }

    getCardSize() {
        return 6;
    }

    static getConfigForm() {
        const localizeSelectOptions = (schema, localize) => {
            const optionLabelKeys = {
                timeDisplayMode: {
                    delay: "route_time_display_delay",
                    realtime: "route_time_display_realtime",
                    planned: "route_time_display_planned",
                },
                routePagingPosition: {
                    off: "route_paging_off",
                    top: "route_paging_top",
                    bottom: "route_paging_bottom",
                    both: "route_paging_both",
                },
                routeSortMode: {
                    api: "route_sort_api",
                    realtime_departure: "route_sort_realtime_departure",
                },
                routeType: {
                    LEAST_TIME: "route_type_least_time",
                    LEAST_INTERCHANGES: "route_type_least_interchanges",
                    LEAST_WALKING: "route_type_least_walking",
                },
                changeSpeed: {
                    SLOW: "route_change_speed_slow",
                    NORMAL: "route_change_speed_normal",
                    FAST: "route_change_speed_fast",
                },
            };
            const labelKeys = optionLabelKeys[schema.name];

            if (!labelKeys || !schema.selector?.select?.options) {
                return;
            }

            schema.selector.select.options = schema.selector.select.options.map((option) => {
                if (!option?.value || !labelKeys[option.value]) {
                    return option;
                }

                const key = `component.another_mvg.cardeditor.${labelKeys[option.value]}`;
                const translated = localize(key);

                return {
                    ...option,
                    label: translated && translated !== key ? translated : option.label,
                };
            });
        };

        return {
            schema: [
                {
                    type: "expandable",
                    label: "route_editor_general",
                    icon: "mdi:cog-outline",
                    schema: [
                        { name: "name", selector: { text: {} }, default: "Another MVG Route" },
                        { name: "showLocationSearch", selector: { boolean: {} }, default: false },
                        { name: "showRouteFavoritesOnStart", selector: { boolean: {} }, default: false },
                        { name: "routeMaxHeight", selector: { number: { min: 0, max: 2000, step: 10, mode: "box" } }, default: 0 },
                    ],
                },
                {
                    type: "expandable",
                    label: "route_editor_favorites",
                    icon: "mdi:star-outline",
                    schema: [
                        { name: "favoriteStations", selector: { text: { multiline: true } } },
                        { name: "favoriteRoutes", selector: { text: { multiline: true } } },
                    ],
                },
                {
                    type: "expandable",
                    label: "route_editor_search",
                    icon: "mdi:map-search-outline",
                    schema: [
                        {
                            name: "transportType",
                            selector: {
                                select: {
                                    multiple: true,
                                    sort: false,
                                    options: [
                                        { value: "SBAHN", label: "S-Bahn" },
                                        { value: "UBAHN", label: "U-Bahn" },
                                        { value: "BAHN", label: "Bahn" },
                                        { value: "TRAM", label: "Tram" },
                                        { value: "BUS", label: "Bus" },
                                        { value: "REGIONAL_BUS", label: "Regional-Bus" },
                                    ]
                                }
                            },
                            default: ["SBAHN", "UBAHN", "TRAM", "BUS", "REGIONAL_BUS"]
                        },
                        {
                            name: "routeType",
                            selector: {
                                select: {
                                    mode: "dropdown",
                                    options: [
                                        { value: "LEAST_TIME", label: "Fastest route" },
                                        { value: "LEAST_INTERCHANGES", label: "Fewest transfers" },
                                        { value: "LEAST_WALKING", label: "Least walking" },
                                    ]
                                }
                            },
                            default: "LEAST_TIME"
                        },
                        {
                            name: "changeSpeed",
                            selector: {
                                select: {
                                    mode: "dropdown",
                                    options: [
                                        { value: "SLOW", label: "Slow" },
                                        { value: "NORMAL", label: "Normal" },
                                        { value: "FAST", label: "Fast" },
                                    ]
                                }
                            },
                            default: "NORMAL"
                        },
                        {
                            name: "routeSortMode",
                            selector: {
                                select: {
                                    mode: "dropdown",
                                    options: [
                                        { value: "api", label: "API order" },
                                        { value: "realtime_departure", label: "Actual departure time" },
                                    ]
                                }
                            },
                            default: "api"
                        },
                        {
                            name: "routePagingPosition",
                            selector: {
                                select: {
                                    mode: "dropdown",
                                    options: [
                                        { value: "off", label: "Disabled" },
                                        { value: "top", label: "Top" },
                                        { value: "bottom", label: "Bottom" },
                                        { value: "both", label: "Top and bottom" },
                                    ]
                                }
                            },
                            default: "bottom"
                        },
                    ],
                },
                {
                    type: "expandable",
                    label: "route_editor_display",
                    icon: "mdi:monitor-dashboard",
                    schema: [
                        {
                            name: "timeDisplayMode",
                            selector: {
                                select: {
                                    mode: "dropdown",
                                    options: [
                                        { value: "delay", label: "12:34 +5" },
                                        { value: "realtime", label: "12:39" },
                                        { value: "planned", label: "12:34" },
                                    ]
                                }
                            },
                            default: "delay"
                        },
                        { name: "showTransferTime", selector: { boolean: {} }, default: false },
                        { name: "routesCollapsible", selector: { boolean: {} }, default: false },
                        { name: "routesDefaultCollapsed", selector: { boolean: {} }, default: false },
                    ],
                },
            ],
            computeLabel: (schema, localize) => {
                localizeSelectOptions(schema, localize);
                if (!schema.name) {
                    const key = `component.another_mvg.cardeditor.${schema.label}`;
                    const translated = localize(key);
                    return translated && translated !== key ? translated : schema.label;
                }

                const labels = {
                    name: "route_card_name",
                    showLocationSearch: "search_show_location_search",
                    showRouteFavoritesOnStart: "route_show_favorites_on_start",
                    favoriteStations: "route_favorite_stations_editor",
                    favoriteRoutes: "route_favorite_routes_editor",
                    routeMaxHeight: "route_max_height",
                    routesCollapsible: "route_collapsible",
                    routesDefaultCollapsed: "route_default_collapsed",
                    routePagingPosition: "route_paging_position",
                    showTransferTime: "route_show_transfer_time",
                    timeDisplayMode: "route_time_display_mode",
                    routeSortMode: "route_sort_mode",
                    routeType: "route_type",
                    changeSpeed: "route_change_speed",
                    transportType: "search_transport_type",
                };
                const label = labels[schema.name];
                return label ? localize(`component.another_mvg.cardeditor.${label}`) : schema.name;
            },
            computeHelper: (schema, localize) => {
                const labels = {
                    name: "route_card_name_desc",
                    showLocationSearch: "search_show_location_search_desc",
                    showRouteFavoritesOnStart: "route_show_favorites_on_start_desc",
                    favoriteStations: "route_favorite_stations_editor_desc",
                    favoriteRoutes: "route_favorite_routes_editor_desc",
                    routeMaxHeight: "route_max_height_desc",
                    routesCollapsible: "route_collapsible_desc",
                    routesDefaultCollapsed: "route_default_collapsed_desc",
                    routePagingPosition: "route_paging_position_desc",
                    showTransferTime: "route_show_transfer_time_desc",
                    timeDisplayMode: "route_time_display_mode_desc",
                    routeSortMode: "route_sort_mode_desc",
                    routeType: "route_type_desc",
                    changeSpeed: "route_change_speed_desc",
                    transportType: "route_transport_type_desc",
                };
                const label = labels[schema.name];
                return label ? localize(`component.another_mvg.cardeditor.${label}`) : "";
            },
        };
    }
}

customElements.define("content-card-another-mvg-route", ContentAnotherMVGRoute);

window.customCards = window.customCards || [];
window.customCards.push({
    type: "content-card-another-mvg-route",
    name: "AnotherMVG Route Card",
    preview: false,
    description: "DE: Einfache MVG/MVV Routenplanung mit Start- und Zielsuche. EN: Simple MVG/MVV route planning with origin and destination search.",
    documentationURL: "https://github.com/Nisbo/another_mvg",
});
