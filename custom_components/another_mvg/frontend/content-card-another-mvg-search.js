/* AnotherMVG Search */
const version = "3.0.0-BETA-11.0";
const favoritesStorageKey = "another_mvg_search_favorites_v1";
const lastSearchStoragePrefix = "another_mvg_search_last_v1";

class ContentAnotherMVGSearch extends HTMLElement {
    constructor() {
        super();

        console.log(
            "%cAnotherMVG-Search %cv" + version,
            "color:#fff;background:#2196f3;padding:2px 6px;border-radius:3px;",
            "color:#fff;background:#4caf50;padding:2px 6px;border-radius:3px;"
        );

        this._stations = [];
        this._selectedStation = null;
        this._departures = [];
        this._loading = false;
        this._searching = false;
        this._locating = false;
        this._error = "";
        this._selectedLine = "";
        this._monitorType = "departure";
        this._searchQuery = "";
        this._showResults = false;
        this._showFavorites = false;
        this._favoriteMessage = "";
        this._pendingDeleteFavoriteKey = "";
        this._rememberedSearchLoadedForKey = "";
        this._pendingRememberedFetch = false;
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

        if (this._pendingRememberedFetch && this._selectedStation) {
            this._pendingRememberedFetch = false;
            this.fetchMonitor();
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
        } catch (e) {
            console.warn("AnotherMVG-Search - translation load failed", e);
        }
    }

    hasTranslation(key) {
        const fullKey = `component.another_mvg.${key}`;
        const translated = this._hass?.localize(fullKey);
        return Boolean(translated && translated !== fullKey);
    }

    localize(key, fallback) {
        const translated = this._hass?.localize(`component.another_mvg.${key}`);
        return translated && translated !== `component.another_mvg.${key}` ? translated : fallback;
    }

    getDisplayLineLabel(departure) {
        const rawLabel = String(departure.label || "");
        const label = rawLabel.toUpperCase() === "LUFTHANSA EXPRESS BUS" ? "LEB" : rawLabel;
        return `${departure.trainType || ""}${label || ""}`.trim();
    }

    getLineCssClass(departure) {
        return this.getDisplayLineLabel(departure).replace(/[^a-zA-Z0-9_-]/g, "");
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

    escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    getEffectiveTransportType(departure) {
        const type = String(departure.transport_type || "").toUpperCase();
        const lineLabel = this.getDisplayLineLabel(departure).toUpperCase();

        if (
            (!type || type === "UNKNOWN") &&
            /^(RE|RB|BRB|ALX|EC|EN|IC|ICE|IRE|MEX|NJ|RJ|SWE)\s*\d*/.test(lineLabel)
        ) {
            return "BAHN";
        }

        return type;
    }

    parseCardFilterValues(value) {
        if (!value) return [];
        if (Array.isArray(value)) {
            return value.map(item => String(item).trim().toUpperCase()).filter(Boolean);
        }

        return String(value)
            .split(/[;,]/)
            .map(item => item.trim().toUpperCase())
            .filter(Boolean);
    }

    normalizeMonitorType(value) {
        return value === "arrival" ? "arrival" : "departure";
    }

    getFavoriteKey(favorite) {
        return `${favorite.globalId || ""}|${this.normalizeMonitorType(favorite.monitorType)}`;
    }

    formatFavoriteForConfig(favorite) {
        return `${favorite.name || favorite.stationName}|${favorite.globalId}|${this.normalizeMonitorType(favorite.monitorType)}`;
    }

    getLocalFavorites() {
        try {
            const favorites = JSON.parse(localStorage.getItem(favoritesStorageKey) || "[]");
            if (!Array.isArray(favorites)) return [];

            return favorites
                .map((favorite) => ({
                    source: "local",
                    name: String(favorite.name || favorite.stationName || "").trim(),
                    stationName: String(favorite.stationName || favorite.name || "").trim(),
                    globalId: String(favorite.globalId || favorite.globalid || "").trim(),
                    monitorType: this.normalizeMonitorType(favorite.monitorType || favorite.monitor_type),
                    createdAt: favorite.createdAt || "",
                }))
                .filter((favorite) => favorite.name && favorite.globalId);
        } catch (err) {
            console.warn("AnotherMVG-Search - failed to read favorites", err);
            return [];
        }
    }

    saveLocalFavorites(favorites) {
        try {
            localStorage.setItem(favoritesStorageKey, JSON.stringify(favorites));
        } catch (err) {
            console.warn("AnotherMVG-Search - failed to save favorites", err);
        }
    }

    getLastSearchStorageKey() {
        const name = String(this.config?.name || "default").trim() || "default";
        return `${lastSearchStoragePrefix}:${name}`;
    }

    loadRememberedSearch() {
        if (!(this.config?.rememberLastSearch ?? false)) return;

        const key = this.getLastSearchStorageKey();
        if (this._rememberedSearchLoadedForKey === key) return;
        this._rememberedSearchLoadedForKey = key;

        try {
            const remembered = JSON.parse(localStorage.getItem(key) || "{}");
            if (!remembered?.globalId || !remembered?.name) return;

            this._selectedStation = {
                name: String(remembered.name),
                globalId: String(remembered.globalId),
                transportTypes: Array.isArray(remembered.transportTypes) ? remembered.transportTypes : [],
            };
            this._searchQuery = this._selectedStation.name;
            this._monitorType = this.normalizeMonitorType(remembered.monitorType || this._monitorType);
            this._selectedLine = "";
            this._pendingRememberedFetch = true;
        } catch (err) {
            console.warn("AnotherMVG-Search - failed to load remembered search", err);
        }
    }

    saveRememberedSearch() {
        if (!(this.config?.rememberLastSearch ?? false) || !this._selectedStation?.globalId) return;

        try {
            localStorage.setItem(this.getLastSearchStorageKey(), JSON.stringify({
                name: this._selectedStation.name,
                globalId: this._selectedStation.globalId,
                monitorType: this.normalizeMonitorType(this._monitorType),
                transportTypes: this._selectedStation.transportTypes || [],
            }));
        } catch (err) {
            console.warn("AnotherMVG-Search - failed to save remembered search", err);
        }
    }

    getConfiguredFavorites() {
        const rawFavorites = this.config.favoriteStops || this.config.favorites || "";
        return String(rawFavorites)
            .split(/\r?\n/)
            .map(line => line.trim())
            .filter(Boolean)
            .map((line) => {
                const [name, globalId, monitorType = this.config.monitorType || "departure"] = line.split("|").map(part => part.trim());
                if (!name || !globalId) return null;
                return {
                    source: "config",
                    name,
                    stationName: name,
                    globalId,
                    monitorType: this.normalizeMonitorType(monitorType),
                };
            })
            .filter(Boolean);
    }

    getAllFavorites() {
        const configuredFavorites = this.getConfiguredFavorites();
        const configuredKeys = new Set(configuredFavorites.map(favorite => this.getFavoriteKey(favorite)));
        const localFavorites = this.getLocalFavorites().filter(favorite => !configuredKeys.has(this.getFavoriteKey(favorite)));
        return [...configuredFavorites, ...localFavorites];
    }

    getVisibleLocalFavorites() {
        const configuredKeys = new Set(this.getConfiguredFavorites().map(favorite => this.getFavoriteKey(favorite)));
        return this.getLocalFavorites().filter(favorite => !configuredKeys.has(this.getFavoriteKey(favorite)));
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

    saveCurrentFavorite() {
        if (!this._selectedStation?.globalId) return;

        const newFavorite = {
            name: this._selectedStation.name,
            stationName: this._selectedStation.name,
            globalId: this._selectedStation.globalId,
            monitorType: this.normalizeMonitorType(this._monitorType),
            createdAt: new Date().toISOString(),
        };
        const localFavorites = this.getLocalFavorites();
        const newKey = this.getFavoriteKey(newFavorite);
        const filteredFavorites = localFavorites.filter(favorite => this.getFavoriteKey(favorite) !== newKey);

        this.saveLocalFavorites([newFavorite, ...filteredFavorites]);
        this._showFavorites = true;
        this._pendingDeleteFavoriteKey = "";
        this.render();
    }

    deleteLocalFavorite(key) {
        const localFavorites = this.getLocalFavorites().filter(favorite => this.getFavoriteKey(favorite) !== key);
        this.saveLocalFavorites(localFavorites);
        this._showFavorites = true;
        this._pendingDeleteFavoriteKey = "";
        this.showFavoriteMessage("frontend.favorite_deleted", "Favorite deleted");
    }

    requestDeleteLocalFavorite(key) {
        this._pendingDeleteFavoriteKey = key;
        this._favoriteMessage = "";
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
            console.warn("AnotherMVG-Search - clipboard API failed, using fallback", err);
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

    async copyCurrentFavorite() {
        if (!this._selectedStation?.globalId) return;

        const copied = await this.copyText(this.formatFavoriteForConfig({
            name: this._selectedStation.name,
            globalId: this._selectedStation.globalId,
            monitorType: this._monitorType,
        }));
        if (copied) {
            this.showFavoriteMessage("frontend.favorite_copied", "Copied to clipboard");
        }
    }

    async copyLocalFavorites() {
        const text = this.getVisibleLocalFavorites()
            .map(favorite => this.formatFavoriteForConfig(favorite))
            .join("\n");
        const copied = await this.copyText(text);
        if (copied) {
            this.showFavoriteMessage("frontend.favorite_copied", "Copied to clipboard");
        }
    }

    selectFavorite(favorite) {
        this._selectedStation = {
            name: favorite.stationName || favorite.name,
            globalId: favorite.globalId,
            transportTypes: [],
        };
        this._searchQuery = this._selectedStation.name;
        this._monitorType = this.normalizeMonitorType(favorite.monitorType);
        this._selectedLine = "";
        this._showResults = false;
        this._showFavorites = false;
        this.saveRememberedSearch();
        this.fetchMonitor();
    }

    getTransportGroup(departure) {
        const type = this.getEffectiveTransportType(departure);
        const groups = {
            SBAHN: { key: "SBAHN", label: "S-Bahn", order: 10 },
            UBAHN: { key: "UBAHN", label: "U-Bahn", order: 20 },
            TRAM: { key: "TRAM", label: "Tram", order: 30 },
            BUS: { key: "BUS", label: "Bus", order: 40 },
            REGIONAL_BUS: { key: "BUS", label: "Bus", order: 40 },
            BAHN: { key: "BAHN", label: "Bahn", order: 50 },
        };

        return groups[type] || { key: type || "OTHER", label: type || "Other", order: 99 };
    }

    groupDepartures(departures) {
        const groupingMode = this.config.groupingMode || "none";
        const groupingSort = this.config.groupingSort || "alphabetical";

        if (groupingMode === "none") {
            return [{ label: "", departures }];
        }

        const groups = new Map();
        departures.forEach((departure) => {
            const group = groupingMode === "transport_type"
                ? this.getTransportGroup(departure)
                : { key: this.getDisplayLineLabel(departure), label: this.getDisplayLineLabel(departure), order: 0 };

            if (!groups.has(group.key)) {
                groups.set(group.key, { ...group, departures: [] });
            }
            groups.get(group.key).departures.push(departure);
        });

        return [...groups.values()].sort((a, b) => {
            if (groupingSort === "next_departure") {
                const aNext = Math.min(...a.departures.map(dep => dep.time_diff ?? Number.MAX_SAFE_INTEGER));
                const bNext = Math.min(...b.departures.map(dep => dep.time_diff ?? Number.MAX_SAFE_INTEGER));
                return aNext - bNext;
            }

            if (groupingMode === "transport_type" && a.order !== b.order) {
                return a.order - b.order;
            }

            return a.label.localeCompare(b.label, undefined, { numeric: true, sensitivity: "base" });
        });
    }

    async searchStations(query) {
        if (!query || query.trim().length < 2) {
            this._stations = [];
            this._showResults = false;
            this.render();
            return;
        }

        this._searching = true;
        this._error = "";
        this._showResults = false;
        this.render();

        try {
            const result = await this._hass.callApi(
                "GET",
                `another_mvg/search_stations?query=${encodeURIComponent(query.trim())}`
            );
            this._stations = result.stations || [];
            this._showResults = this._stations.length > 0;
        } catch (err) {
            this._stations = [];
            this._showResults = false;
            this._error = "station_search_failed";
            console.warn("AnotherMVG-Search - station search failed", err);
        } finally {
            this._searching = false;
            this.render();
        }
    }

    async searchNearbyStations() {
        if (!navigator.geolocation) {
            this._error = this.localize("frontend.location_not_supported", "Location is not supported by this browser");
            this.render();
            return;
        }

        this._locating = true;
        this._error = "";
        this._showResults = false;
        this._showFavorites = false;
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
            this._stations = result.stations || [];
            this._showResults = this._stations.length > 0;
            this._searchQuery = this.localize("frontend.nearby_stations", "Nearby stations");
            if (!this._stations.length) {
                this._error = this.localize("frontend.location_no_stations", "No nearby stations found");
            }
        } catch (err) {
            this._stations = [];
            this._showResults = false;
            this._error = this.getLocationErrorMessage(err);
            console.warn("AnotherMVG-Search - nearby station search failed", err);
        } finally {
            this._locating = false;
            this.render();
        }
    }

    async fetchMonitor() {
        if (!this._selectedStation) return;

        this._loading = true;
        this._error = "";
        this.render();

        try {
            const result = await this._hass.callApi("POST", "another_mvg/search_monitor", {
                globalid: this._selectedStation.globalId,
                globalId: this._selectedStation.globalId,
                name: this._selectedStation.name,
                monitor_type: this._monitorType,
                transporttypes: this.config.transportType || this.config.transportTypes || ["SBAHN", "UBAHN", "TRAM", "BUS", "REGIONAL_BUS"],
                limit: this.config.limit || 40,
                offset_in_minutes: this.config.offsetInMinutes || 0,
            });
            this._departures = result.departures || [];
        } catch (err) {
            this._departures = [];
            this._error = "monitor_request_failed";
            console.warn("AnotherMVG-Search - monitor request failed", err);
        } finally {
            this._loading = false;
            this.render();
        }
    }

    renderTime(departure) {
        const format = this.config.displayOptions || "1";
        const cancelled = this.localize("frontend.cancelled", "Cancelled");

        if (format === "2") {
            return `${departure.planned_departure}${departure.cancelled ? ` <span class="cancelled">${cancelled}</span>` : departure.delay > 0 ? ` <span class="delay">+${departure.delay}</span>` : ""}`;
        }
        if (format === "3") {
            return departure.cancelled
                ? `${departure.expected_departure} <span class="cancelled">${cancelled}</span>`
                : departure.delay > 0 ? `<span class="delay">${departure.expected_departure}</span>` : departure.expected_departure;
        }
        if (format === "4") {
            return `${Math.floor(departure.time_diff / 60)}${departure.cancelled ? ` <span class="cancelled">${cancelled}</span>` : ""}`;
        }
        if (format === "5") {
            return `${Math.floor(departure.time_diff / 60)}${departure.delay > 0 ? ` <span class="delay">(+${departure.delay})</span>` : ""}${departure.cancelled ? ` <span class="cancelled">${cancelled}</span>` : ""}`;
        }

        return `${departure.planned_departure}${departure.cancelled ? ` <span class="cancelled">${cancelled}</span>` : departure.delay > 0 ? ` <span class="delay">+${departure.delay}</span> (${departure.expected_departure})` : ""}`;
    }

    getFilteredDepartures() {
        const transportTypes = this.parseCardFilterValues(this.config.transportType || this.config.transportTypes);
        let departures = this._departures || [];

        if (transportTypes.length > 0) {
            departures = departures.filter(dep => transportTypes.includes(this.getEffectiveTransportType(dep)));
        }

        if (this._selectedLine) {
            departures = departures.filter(dep => this.getDisplayLineLabel(dep) === this._selectedLine);
        }

        return departures;
    }

    renderRows() {
        const showType = this.config.showType ?? false;
        const hideTrack = this.config.hideTrack ?? false;
        const visibleRows = this.config.maxDepartures ? Math.max(1, Number(this.config.maxDepartures) || 1) : null;
        const fillRows = this.config.maxDeparturesFixed ?? false;
        const monitorType = this._monitorType || "departure";
        const destinationLabel = monitorType === "arrival"
            ? this.localize("frontend.column_origin", "From")
            : this.localize("frontend.column_destination", "Destination");
        const timeLabel = monitorType === "arrival"
            ? this.localize("frontend.column_arrival", "Arrival")
            : this.localize("frontend.column_departure", "Departure");
        const colSpan = 3 + (showType ? 1 : 0) + (!hideTrack ? 1 : 0);
        const transportTypeMap = {
            REGIONAL_BUS: "R-Bus",
            BUS: "Bus",
            SBAHN: "S-Bahn",
            UBAHN: "U-Bahn",
            TRAM: "Tram",
            BAHN: "Bahn",
        };
        let html = `
            <tr class="amvg-headline">
                ${showType ? `<th>${this.localize("frontend.column_type", "Type")}</th>` : ""}
                <th>${this.localize("frontend.column_line", "Line")}</th>
                <th>${destinationLabel}</th>
                ${!hideTrack ? `<th>${this.localize("frontend.column_track", "Track")}</th>` : ""}
                <th>${timeLabel}</th>
            </tr>
        `;

        const departures = this.getFilteredDepartures();
        if (!departures.length) {
            html += `<tr><td colspan="${colSpan}" class="empty">${this._loading ? this.localize("frontend.loading", "Loading...") : this.localize("frontend.no_data", "No data")}</td></tr>`;
            if (fillRows && visibleRows) {
                for (let i = 1; i < visibleRows; i++) {
                    html += this.renderPlaceholderRow(showType, hideTrack);
                }
            }
            return html;
        }

        let visibleTableRows = 0;
        this.groupDepartures(departures).forEach((group) => {
            if (group.label) {
                html += `<tr><td colspan="${colSpan}" class="group">${this.escapeHtml(group.label)}</td></tr>`;
                visibleTableRows += 1;
            }

            group.departures.forEach((departure) => {
                visibleTableRows += 1;
                const effectiveType = this.getEffectiveTransportType(departure);
                const lineLabel = this.getDisplayLineLabel(departure);
                const lineCssClass = this.getLineCssClass(departure);
                const canFilterLine = (this.config.labelClickAction || "off") === "filter_line";
                const selected = this._selectedLine === lineLabel;

                html += `
                    <tr>
                        ${showType ? `<td><nobr>${transportTypeMap[effectiveType] || effectiveType}</nobr></td>` : ""}
                        <td>
                            <span class="line ${effectiveType} ${lineCssClass} ${canFilterLine ? "clickable" : ""} ${selected ? "selected" : ""}" data-line="${this.escapeHtml(lineLabel)}">
                                ${this.escapeHtml(lineLabel)}
                            </span>
                        </td>
                        <td class="destination"><span class="destination-text">${this.escapeHtml(departure.destination)}</span></td>
                        ${!hideTrack ? `<td>${this.escapeHtml(departure.track)}</td>` : ""}
                        <td class="time">${this.renderTime(departure)}</td>
                    </tr>
                `;
            });
        });

        if (fillRows && visibleRows && visibleTableRows < visibleRows) {
            for (let i = visibleTableRows; i < visibleRows; i++) {
                html += this.renderPlaceholderRow(showType, hideTrack);
            }
        }

        return html;
    }

    renderPlaceholderRow(showType, hideTrack) {
        return `
            <tr class="placeholder-row">
                ${showType ? `<td>&nbsp;</td>` : ""}
                <td><span class="line placeholder-line">&nbsp;</span></td>
                <td class="destination">&nbsp;</td>
                ${!hideTrack ? `<td>&nbsp;</td>` : ""}
                <td class="time">&nbsp;</td>
            </tr>
        `;
    }

    renderPlaceholderRows() {
        const showType = this.config.showType ?? false;
        const hideTrack = this.config.hideTrack ?? false;
        const visibleRows = this.config.maxDepartures ? Math.max(1, Number(this.config.maxDepartures) || 1) : 1;
        const monitorType = this._monitorType || "departure";
        const destinationLabel = monitorType === "arrival"
            ? this.localize("frontend.column_origin", "From")
            : this.localize("frontend.column_destination", "Destination");
        const timeLabel = monitorType === "arrival"
            ? this.localize("frontend.column_arrival", "Arrival")
            : this.localize("frontend.column_departure", "Departure");
        let html = `
            <tr class="amvg-headline placeholder-header">
                ${showType ? `<th>${this.localize("frontend.column_type", "Type")}</th>` : ""}
                <th>${this.localize("frontend.column_line", "Line")}</th>
                <th>${destinationLabel}</th>
                ${!hideTrack ? `<th>${this.localize("frontend.column_track", "Track")}</th>` : ""}
                <th>${timeLabel}</th>
            </tr>
        `;

        for (let i = 0; i < visibleRows; i++) {
            html += this.renderPlaceholderRow(showType, hideTrack);
        }

        return html;
    }

    applyTableLimit() {
        const wrap = this.content?.querySelector(".table-wrap.limited");
        if (!wrap) return;

        const visibleRows = Math.max(1, Number(wrap.dataset.visibleRows) || 1);
        const rows = [...wrap.querySelectorAll("tr")];
        let tableRows = 0;
        let height = 0;

        for (const row of rows) {
            const isHeader = row.classList.contains("amvg-headline");
            height += row.getBoundingClientRect().height;

            if (!isHeader) {
                tableRows += 1;
            }

            if (tableRows >= visibleRows) {
                break;
            }
        }

        if (height > 0) {
            wrap.style.maxHeight = `${Math.ceil(height)}px`;
        }
    }

    applyDestinationTextMode() {
        const mode = ["wrap", "clip", "marquee", "manual"].includes(this.config.destinationTextMode)
            ? this.config.destinationTextMode
            : "wrap";

        this.content?.querySelectorAll(".destination").forEach((cell) => {
            const text = cell.querySelector(".destination-text");
            if (!text) return;

            cell.classList.remove("is-overflowing");
            text.style.removeProperty("--amvg-marquee-distance");

            if (!["marquee", "manual"].includes(mode)) return;

            const overflow = text.scrollWidth > cell.clientWidth + 1;
            if (!overflow) return;

            cell.classList.add("is-overflowing");
            if (mode === "marquee") {
                text.style.setProperty("--amvg-marquee-distance", `${text.scrollWidth - cell.clientWidth}px`);
            }
        });

        if (mode === "manual") {
            this.enableManualDestinationScroll();
        }
    }

    enableManualDestinationScroll() {
        this.content?.querySelectorAll(".destination.is-overflowing .destination-text").forEach((text) => {
            let isDragging = false;
            let startX = 0;
            let startScrollLeft = 0;

            text.addEventListener("pointerdown", (event) => {
                isDragging = true;
                startX = event.clientX;
                startScrollLeft = text.scrollLeft;
                text.classList.add("dragging");
                text.setPointerCapture?.(event.pointerId);
                event.preventDefault();
            });

            text.addEventListener("pointermove", (event) => {
                if (!isDragging) return;
                text.scrollLeft = startScrollLeft - (event.clientX - startX);
                event.preventDefault();
            });

            const stopDragging = (event) => {
                if (!isDragging) return;
                isDragging = false;
                text.classList.remove("dragging");
                text.releasePointerCapture?.(event.pointerId);
            };

            text.addEventListener("pointerup", stopDragging);
            text.addEventListener("pointercancel", stopDragging);
            text.addEventListener("lostpointercapture", () => {
                isDragging = false;
                text.classList.remove("dragging");
            });
        });
    }

    renderFavoriteMenu(favorites) {
        const configuredFavorites = favorites.filter(favorite => favorite.source === "config");
        const localFavorites = favorites.filter(favorite => favorite.source === "local");
        const monitorLabel = (monitorType) => this.normalizeMonitorType(monitorType) === "arrival"
            ? this.localize("frontend.column_arrival", "Arrival")
            : this.localize("frontend.column_departure", "Departure");
        const renderFavorite = (favorite) => {
            const key = this.escapeHtml(this.getFavoriteKey(favorite));
            const sourceClass = favorite.source === "config" ? "config" : "local";
            const deleteButton = favorite.source === "local"
                ? `<button class="favorite-delete" data-delete-favorite="${key}" title="${this.localize("frontend.favorite_delete", "Delete favorite")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button>`
                : "";

            return `
                <div class="favorite-block ${sourceClass}" data-favorite-block="${key}">
                    <div class="favorite-row ${sourceClass}">
                        <button class="favorite-item" data-favorite="${key}">
                            <span class="favorite-title">${this.escapeHtml(favorite.name)}</span>
                            <span class="favorite-meta">${this.escapeHtml(monitorLabel(favorite.monitorType))} · ${this.escapeHtml(favorite.globalId)}</span>
                        </button>
                        ${deleteButton}
                    </div>
                </div>
            `;
        };
        const configuredHtml = configuredFavorites.length
            ? `<div class="favorite-section">${this.localize("frontend.favorite_configured", "Configured favorites")}</div>${configuredFavorites.map(renderFavorite).join("")}`
            : "";
        const localHtml = localFavorites.length
            ? `
                <div class="favorite-section-row">
                    <div class="favorite-section">${this.localize("frontend.favorite_local", "Local favorites")}</div>
                    <button class="favorite-copy-button" data-copy-local-favorites title="${this.localize("frontend.favorite_copy_all", "Copy all local favorites")}"><ha-icon icon="mdi:content-copy"></ha-icon></button>
                </div>
                ${localFavorites.map(renderFavorite).join("")}
            `
            : "";

        return `
            <div class="favorites-menu">
                <div class="favorite-save-row">
                    <button class="favorite-save" ${this._selectedStation ? "" : "disabled"}>
                        ${this.localize("frontend.favorite_save_current", "Save current search")}
                    </button>
                    <button class="favorite-copy-button" data-copy-current-favorite ${this._selectedStation ? "" : "disabled"} title="${this.localize("frontend.favorite_copy_current", "Copy current search")}"><ha-icon icon="mdi:content-copy"></ha-icon></button>
                </div>
                ${this._favoriteMessage ? `<div class="favorite-message">${this.escapeHtml(this._favoriteMessage)}</div>` : ""}
                ${configuredHtml}
                ${localHtml}
                ${favorites.length ? "" : `<div class="empty">${this.localize("frontend.favorite_empty", "No favorites saved")}</div>`}
            </div>
        `;
    }

    renderFavoriteDeletePopup() {
        if (!this._pendingDeleteFavoriteKey) return "";

        const favorite = this.getLocalFavorites().find(item => this.getFavoriteKey(item) === this._pendingDeleteFavoriteKey);
        if (!favorite) return "";

        const monitorLabel = this.normalizeMonitorType(favorite.monitorType) === "arrival"
            ? this.localize("frontend.column_arrival", "Arrival")
            : this.localize("frontend.column_departure", "Departure");
        const key = this.escapeHtml(this.getFavoriteKey(favorite));

        return `
            <div class="favorite-delete-backdrop">
                <div class="favorite-delete-dialog">
                    <div>
                        <span class="favorite-title">${this.escapeHtml(favorite.name)}</span>
                        <span class="favorite-meta">${this.escapeHtml(monitorLabel)} · ${this.escapeHtml(favorite.globalId)}</span>
                    </div>
                    <div>${this.localize("frontend.favorite_delete_confirm", "Delete this local favorite?")}</div>
                    <div class="favorite-confirm-actions">
                        <button class="favorite-confirm-cancel" data-cancel-delete-favorite>${this.localize("frontend.favorite_cancel", "Cancel")}</button>
                        <button class="favorite-confirm-delete" data-confirm-delete-favorite="${key}">${this.localize("frontend.favorite_delete", "Delete favorite")}</button>
                    </div>
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
                .container.search-open { overflow: visible; }
                .header { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 6px 10px; font-weight: bold; }
                .controls-wrap { position: relative; z-index: 2; }
                .controls { display: grid; gap: 8px; padding: 8px; background: rgba(255,255,255,0.08); }
                .search-row { display: grid; grid-template-columns: minmax(0, 1fr) 42px; gap: 6px; }
                .search-row.location { grid-template-columns: 42px minmax(0, 1fr) 42px; }
                .action-row { display: grid; grid-template-columns: minmax(0, 1fr) 42px; justify-content: stretch; align-items: center; gap: 8px; }
                .action-row .monitor-switch { justify-self: start; }
                .search { width: 100%; min-width: 0; box-sizing: border-box; border: 1px solid var(--divider-color, rgba(255,255,255,0.35)); border-radius: 6px; padding: 8px 9px; color: var(--primary-text-color, #fff); background: var(--secondary-background-color, rgba(255,255,255,0.14)); font: inherit; }
                .search:focus { outline: none; border-color: var(--primary-color, #03a9f4); box-shadow: 0 0 0 1px var(--primary-color, #03a9f4); }
                .search-button { width: 42px; min-width: 42px; min-height: 38px; border: 1px solid var(--divider-color, rgba(255,255,255,0.35)); border-radius: 6px; color: var(--primary-text-color, #fff); background: var(--secondary-background-color, rgba(255,255,255,0.14)); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0; }
                .search-button:hover, .search-button:focus { outline: none; background: rgba(255,255,255,0.22); border-color: var(--primary-color, #03a9f4); }
                .refresh { width: 22px; min-width: 22px; height: 22px; min-height: 22px; border: 1px solid var(--divider-color, rgba(255,255,255,0.35)); border-radius: 5px; color: var(--primary-text-color, #fff); background: var(--secondary-background-color, rgba(255,255,255,0.14)); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0; font: inherit; line-height: 1; }
                .refresh ha-icon { --mdc-icon-size: 16px; width: 16px; height: 16px; }
                .refresh:hover, .refresh:focus { outline: none; background: rgba(255,255,255,0.22); border-color: var(--primary-color, #03a9f4); }
                .favorites-button.active { color: var(--amvg-header-text-color, #000080); background: var(--amvg-header-bg-color, #FAE10C); }
                .favorites-menu { position: absolute; right: 8px; top: calc(100% - 4px); z-index: 12; width: min(360px, calc(100% - 16px)); max-height: 45vh; overflow: auto; padding: 6px; background: var(--amvg-card-bg-color, #000080); border: 1px solid rgba(255,255,255,0.35); border-radius: 8px; box-shadow: 0 10px 24px rgba(0,0,0,0.35); display: grid; gap: 4px; }
                .favorite-save-row { display: grid; grid-template-columns: minmax(0, 1fr) 34px; align-items: stretch; gap: 4px; }
                .favorite-save { width: 100%; text-align: left; border: 0; border-radius: 5px; padding: 7px 8px; color: inherit; background: rgba(255,255,255,0.16); cursor: pointer; font: inherit; }
                .favorite-save:disabled, .favorite-copy-button:disabled { opacity: 0.55; cursor: default; }
                .favorite-section { padding: 8px 6px 4px; margin-top: 3px; border-top: 1px solid rgba(255,255,255,0.25); font-size: 0.95em; opacity: 1; font-weight: 800; }
                .favorite-section:first-child { margin-top: 0; border-top: 0; }
                .favorite-section-row { display: grid; grid-template-columns: minmax(0, 1fr) 34px; align-items: stretch; gap: 4px; }
                .favorite-block { display: grid; gap: 4px; }
                .favorite-row { display: grid; grid-template-columns: minmax(0, 1fr) 34px; align-items: stretch; gap: 4px; }
                .favorite-row.config { grid-template-columns: minmax(0, 1fr); }
                .favorite-item { min-width: 0; text-align: left; border: 0; border-radius: 5px; padding: 6px 8px; color: inherit; background: rgba(255,255,255,0.12); cursor: pointer; font: inherit; }
                .favorite-item:hover, .favorite-item:focus, .favorite-save:hover:not(:disabled), .favorite-save:focus:not(:disabled), .favorite-copy-button:hover:not(:disabled), .favorite-copy-button:focus:not(:disabled), .favorite-confirm-cancel:hover, .favorite-confirm-cancel:focus { background: rgba(255,255,255,0.22); outline: none; }
                .favorite-title { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                .favorite-meta { display: block; opacity: 0.75; font-size: 0.78em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                .favorite-copy-button { width: 34px; min-width: 34px; min-height: 34px; border: 0; border-radius: 5px; color: inherit; background: rgba(255,255,255,0.12); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0; }
                .favorite-delete { border: 0; border-radius: 5px; color: inherit; background: rgba(255,255,255,0.12); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0; }
                .favorite-delete:hover, .favorite-delete:focus { background: rgba(255,255,255,0.22); outline: none; }
                .favorite-delete-backdrop { position: absolute; left: 8px; right: 8px; top: calc(100% - 4px); z-index: 14; min-height: 190px; max-height: 45vh; padding: 10px; border: 1px solid rgba(255,255,255,0.35); border-radius: 8px; background: rgba(0,0,0,0.48); box-shadow: 0 10px 24px rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
                .favorite-delete-dialog { width: 100%; box-sizing: border-box; padding: 12px; border-radius: 8px; background: var(--amvg-card-bg-color, #000080); border: 1px solid rgba(255,255,255,0.35); display: grid; gap: 10px; }
                .favorite-confirm { padding: 8px; border-radius: 5px; background: rgba(0,0,0,0.26); border: 1px solid rgba(255,255,255,0.22); display: grid; gap: 8px; }
                .favorite-confirm-actions { display: flex; justify-content: flex-end; gap: 6px; }
                .favorite-confirm-cancel, .favorite-confirm-delete { border: 0; border-radius: 5px; padding: 6px 10px; color: inherit; cursor: pointer; font: inherit; }
                .favorite-confirm-cancel { background: rgba(255,255,255,0.12); }
                .favorite-confirm-delete { background: var(--error-color, #db4437); color: #fff; }
                .favorite-confirm-delete:hover, .favorite-confirm-delete:focus { filter: brightness(1.1); outline: none; }
                .favorite-message { padding: 7px 8px; border-radius: 5px; color: var(--amvg-header-text-color, #000080); background: var(--amvg-header-bg-color, #FAE10C); font-weight: bold; }
                .monitor-switch { display: inline-grid; grid-template-columns: 1fr 1fr; border: 1px solid var(--divider-color, rgba(255,255,255,0.35)); border-radius: 6px; overflow: hidden; background: rgba(0,0,0,0.18); }
                .monitor-option { min-height: 34px; border: 0; border-right: 1px solid var(--divider-color, rgba(255,255,255,0.35)); padding: 0 12px; color: inherit; background: transparent; font: inherit; cursor: pointer; }
                .monitor-option:last-child { border-right: 0; }
                .monitor-option.active { color: var(--amvg-header-text-color, #000080); background: var(--amvg-header-bg-color, #FAE10C); font-weight: bold; }
                .station-list { display: grid; gap: 2px; }
                .station-list.inline { padding: 0 8px 8px; }
                .station-list.dropdown { position: absolute; left: 8px; right: 8px; top: calc(100% - 4px); z-index: 10; max-height: 45vh; overflow: auto; padding: 4px; background: var(--amvg-card-bg-color, #000080); border: 1px solid rgba(255,255,255,0.35); border-top: 0; border-radius: 0 0 8px 8px; box-shadow: 0 10px 24px rgba(0,0,0,0.35); }
                .station { text-align: left; border: 0; padding: 6px 8px; color: inherit; background: rgba(255,255,255,0.12); cursor: pointer; }
                .station:hover, .station:focus { background: rgba(255,255,255,0.2); outline: none; }
                .station.selected { outline: 2px solid var(--amvg-header-bg-color, #FAE10C); }
                table { width: 100%; border-collapse: collapse; }
                .table-wrap.limited { overflow-y: auto; }
                .table-wrap.limited .amvg-headline th { position: sticky; top: 0; z-index: 1; }
                th { background: var(--amvg-header-bg-color, #FAE10C); color: var(--amvg-header-text-color, #000080); text-align: left; }
                td, th { padding: 2px 6px; vertical-align: top; }
                .group { font-weight: bold; border-top: 1px solid rgba(255,255,255,0.25); padding-top: 5px; }
                .empty { padding: 10px; }
                .placeholder-header { visibility: hidden; }
                .placeholder-row { visibility: hidden; }
                .time { white-space: nowrap; }
                .destination-mode-wrap .destination .destination-text { white-space: normal; overflow-wrap: anywhere; }
                .destination-mode-clip .destination, .destination-mode-manual .destination, .destination-mode-marquee .destination { max-width: 0; overflow: hidden; }
                .destination-mode-clip .destination .destination-text { display: block; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: clip; }
                .destination-mode-manual .destination .destination-text { display: block; max-width: 100%; white-space: nowrap; overflow: hidden; }
                .destination-mode-manual .destination.is-overflowing .destination-text { overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; scrollbar-width: thin; touch-action: none; cursor: grab; user-select: none; }
                .destination-mode-manual .destination.is-overflowing .destination-text.dragging { cursor: grabbing; }
                .destination-mode-marquee .destination { overflow: hidden; white-space: nowrap; }
                .destination-mode-marquee .destination .destination-text { display: block; max-width: 100%; white-space: nowrap; overflow: hidden; }
                .destination-mode-marquee .destination.is-overflowing .destination-text { display: inline-block; max-width: none; min-width: max-content; animation: amvg-marquee 10s ease-in-out infinite alternate; }
                .destination-mode-marquee .destination.is-overflowing:hover .destination-text { animation-play-state: paused; }
                @keyframes amvg-marquee { from { transform: translateX(0); } to { transform: translateX(calc(-1 * var(--amvg-marquee-distance, 0px))); } }
                .cancelled, .delay { color: red; }
                .line { font-weight: bold; color: #fff; background: #000; border: 1px solid #fff; display: inline-block; min-width: 35px; text-align: center; padding: 0 3px; }
                .line.clickable { cursor: pointer; box-shadow: 0 0 0 2px rgba(255,255,255,0.25); }
                .line.selected { box-shadow: 0 0 0 2px #FAE10C; }
                .BUS, .REGIONAL_BUS { background-color: #00586A; }
                .BAHN { background-color: #fff; color: #E30613; border-color: #E30613; }
                .SBAHN { border-radius: 999px; }
                .S1 { background-color: #16BAE7; } .S2 { background-color: #76B82A; } .S3 { background-color: #951B81; } .S4 { background-color: #E30613; }
                .S5 { background-color: #005E82; } .S6 { background-color: #00975F; } .S7 { background-color: #943126; } .S8 { background-color: #000; }
                .S20 { background-color: #ED6B83; } .TRAM { background-color: #D82020; }
                .U1 { background-color: #438136; } .U2 { background-color: #C40C37; } .U3 { background-color: #F36E31; } .U4 { background-color: #0AB38D; }
                .U5 { background-color: #B8740E; } .U6 { background-color: #006CB3; } .U7 { background: linear-gradient(322deg, #C40C37 50%, #438136 50%); }
                .U8 { background: linear-gradient(322deg, #F36E31 50%, #C40C37 50%); }
            `;
            card.appendChild(style);
            card.appendChild(this.content);
            this.appendChild(card);
        }

        const title = this.config.name || "Another MVG Search";
        const resultsMode = this.config.searchResultsMode || "dropdown";
        const showMonitorSwitch = this.config.showMonitorSwitch ?? true;
        const showLocationSearch = this.config.showLocationSearch ?? false;
        const showResults = this._showResults && this._stations.length > 0;
        const allFavorites = this.getAllFavorites();
        const favoriteMenuHtml = this.renderFavoriteMenu(allFavorites);
        const visibleRows = this.config.maxDepartures ? Math.max(1, Number(this.config.maxDepartures) || 1) : null;
        const tableLimitAttributes = visibleRows ? ` data-visible-rows="${visibleRows}"` : "";
        const showPreSearchPlaceholders = !this._selectedStation && visibleRows && (this.config.maxDeparturesFixed ?? false);
        const destinationTextMode = ["wrap", "clip", "marquee", "manual"].includes(this.config.destinationTextMode)
            ? this.config.destinationTextMode
            : "wrap";
        const departureLabel = this.localize("frontend.column_departure", "Departure");
        const arrivalLabel = this.localize("frontend.column_arrival", "Arrival");
        const stationResultsHtml = this._stations.map(station => `
            <button class="station ${this._selectedStation?.globalId === station.globalId ? "selected" : ""}" data-global-id="${this.escapeHtml(station.globalId)}">
                ${this.escapeHtml(station.name)} · ${this.escapeHtml((station.transportTypes || []).join(", "))}<br>
                <small>${this.escapeHtml(station.globalId)}${station.distanceInMeters !== undefined && station.distanceInMeters !== null ? ` · ${Math.round(Number(station.distanceInMeters))} m` : ""}</small>
            </button>
        `).join("");

        this.content.innerHTML = `
            <div class="container ${(showResults && resultsMode === "dropdown") || this._showFavorites ? "search-open" : ""}">
                <div class="header">
                    <span>${this.escapeHtml(title)}</span>
                    ${this._selectedStation ? `<button class="refresh">${this._loading ? "..." : `<ha-icon icon="mdi:refresh"></ha-icon>`}</button>` : ""}
                </div>
                <div class="controls-wrap">
                    <div class="controls">
                        <div class="search-row ${showLocationSearch ? "location" : ""}">
                            ${showLocationSearch ? `
                                <button class="search-button location-search-button" title="${this.localize("frontend.location_search_button", "Use current location")}">${this._locating ? "..." : `<ha-icon icon="mdi:crosshairs-gps"></ha-icon>`}</button>
                            ` : ""}
                            <input class="search" type="search" placeholder="${this.localize("frontend.search_placeholder", "Search station")}" value="${this.escapeHtml(this._searchQuery)}">
                            <button class="search-button monitor-search-button" title="${this.localize("frontend.search_button", "Search")}">${this._searching ? "..." : `<ha-icon icon="mdi:magnify"></ha-icon>`}</button>
                        </div>
                        ${showMonitorSwitch ? `
                            <div class="action-row">
                                <div class="monitor-switch" role="group" aria-label="${this.localize("cardeditor.search_monitor_type", "Monitor type")}">
                                    <button class="monitor-option ${this._monitorType === "departure" ? "active" : ""}" data-monitor-type="departure">${departureLabel}</button>
                                    <button class="monitor-option ${this._monitorType === "arrival" ? "active" : ""}" data-monitor-type="arrival">${arrivalLabel}</button>
                                </div>
                                <button class="search-button favorites-button ${this._showFavorites ? "active" : ""}" title="${this.localize("frontend.favorites", "Favorites")}"><ha-icon icon="mdi:star-outline"></ha-icon></button>
                            </div>
                        ` : `
                            <div class="action-row">
                                <span></span>
                                <button class="search-button favorites-button ${this._showFavorites ? "active" : ""}" title="${this.localize("frontend.favorites", "Favorites")}"><ha-icon icon="mdi:star-outline"></ha-icon></button>
                            </div>
                        `}
                    </div>
                    ${showResults && resultsMode === "dropdown" ? `<div class="station-list dropdown">${stationResultsHtml}</div>` : ""}
                    ${this._showFavorites ? favoriteMenuHtml : ""}
                    ${this._showFavorites ? this.renderFavoriteDeletePopup() : ""}
                </div>
                ${this._error ? `<div class="empty">${this.escapeHtml(this._error)}</div>` : ""}
                ${showResults && resultsMode === "inline" ? `<div class="station-list inline">${stationResultsHtml}</div>` : ""}
                ${this._selectedStation ? `<div class="table-wrap ${visibleRows ? "limited" : ""}"${tableLimitAttributes}><table class="destination-mode-${destinationTextMode}">${this.renderRows()}</table></div>` : ""}
                ${showPreSearchPlaceholders ? `<div class="table-wrap limited placeholder-table"${tableLimitAttributes}><table class="destination-mode-${destinationTextMode}">${this.renderPlaceholderRows()}</table></div>` : ""}
            </div>
        `;

        requestAnimationFrame(() => {
            this.applyTableLimit();
            this.applyDestinationTextMode();
        });

        const input = this.content.querySelector(".search");
        const searchButton = this.content.querySelector(".monitor-search-button");
        const locationSearchButton = this.content.querySelector(".location-search-button");
        const refreshButton = this.content.querySelector(".refresh");
        const favoritesButton = this.content.querySelector(".favorites-button");
        const favoriteSaveButton = this.content.querySelector(".favorite-save");
        const copyCurrentFavoriteButton = this.content.querySelector("[data-copy-current-favorite]");
        const copyLocalFavoritesButton = this.content.querySelector("[data-copy-local-favorites]");

        input?.addEventListener("input", () => {
            this._searchQuery = input.value;
            this._showResults = false;
            this._showFavorites = false;
            this.content.querySelectorAll(".station-list").forEach(list => {
                list.hidden = true;
            });
        });
        searchButton?.addEventListener("click", () => {
            this._showFavorites = false;
            this.searchStations(input.value);
        });
        locationSearchButton?.addEventListener("click", () => {
            this.searchNearbyStations();
        });
        input?.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                this._searchQuery = input.value;
                this._showFavorites = false;
                this.searchStations(input.value);
            }
        });
        favoritesButton?.addEventListener("click", () => {
            this._showResults = false;
            this._showFavorites = !this._showFavorites;
            this.render();
        });
        favoriteSaveButton?.addEventListener("click", () => this.saveCurrentFavorite());
        copyCurrentFavoriteButton?.addEventListener("click", (event) => {
            event.stopPropagation();
            this.copyCurrentFavorite();
        });
        copyLocalFavoritesButton?.addEventListener("click", (event) => {
            event.stopPropagation();
            this.copyLocalFavorites();
        });
        this.content.querySelectorAll("[data-favorite]").forEach((button) => {
            button.addEventListener("click", () => {
                const favorite = this.getAllFavorites().find(item => this.getFavoriteKey(item) === button.dataset.favorite);
                if (favorite) {
                    this.selectFavorite(favorite);
                }
            });
        });
        this.content.querySelectorAll("[data-delete-favorite]").forEach((button) => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                this.requestDeleteLocalFavorite(button.dataset.deleteFavorite);
            });
        });
        this.content.querySelectorAll("[data-cancel-delete-favorite]").forEach((button) => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                this._pendingDeleteFavoriteKey = "";
                this.render();
            });
        });
        this.content.querySelectorAll("[data-confirm-delete-favorite]").forEach((button) => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                this.deleteLocalFavorite(button.dataset.confirmDeleteFavorite);
            });
        });
        this.content.querySelectorAll("[data-monitor-type]").forEach((button) => {
            button.addEventListener("click", () => {
                this._monitorType = button.dataset.monitorType;
                this._showFavorites = false;
                this.saveRememberedSearch();
                if (this._selectedStation) {
                    this.fetchMonitor();
                } else {
                    this.render();
                }
            });
        });

        if (!showMonitorSwitch) {
            this._monitorType = this.config.monitorType || this._monitorType || "departure";
        }

        refreshButton?.addEventListener("click", () => this.fetchMonitor());

        this.content.querySelectorAll(".station").forEach((button) => {
            button.addEventListener("click", () => {
                this._selectedStation = this._stations.find(station => station.globalId === button.dataset.globalId);
                this._selectedLine = "";
                this._showResults = false;
                this._showFavorites = false;
                if (this._selectedStation) {
                    this._searchQuery = this._selectedStation.name;
                }
                this.saveRememberedSearch();
                this.fetchMonitor();
            });
        });

        this.content.querySelectorAll("[data-line]").forEach((label) => {
            label.addEventListener("click", () => {
                if ((this.config.labelClickAction || "off") !== "filter_line") return;
                const line = label.dataset.line;
                this._selectedLine = this._selectedLine === line ? "" : line;
                this.render();
            });
        });
    }

    setConfig(config) {
        this.config = config || {};
        this._monitorType = this.config.monitorType || "departure";
        this.loadRememberedSearch();
        if (this._hass && this._pendingRememberedFetch && this._selectedStation) {
            this._pendingRememberedFetch = false;
            this.fetchMonitor();
        }
    }

    getCardSize() {
        return 6;
    }

    static getConfigForm() {
        const localizeSelectOptions = (schema, localize) => {
            const optionLabelKeys = {
                monitorType: {
                    departure: "departure_monitor",
                    arrival: "arrival_monitor",
                },
                groupingMode: {
                    none: "grouping_none",
                    transport_type: "grouping_transport_type",
                    line: "grouping_line",
                },
                groupingSort: {
                    alphabetical: "grouping_sort_alphabetical",
                    next_departure: "grouping_sort_next_departure",
                },
                labelClickAction: {
                    off: "label_click_off",
                    filter_line: "label_click_filter_line",
                },
                searchResultsMode: {
                    dropdown: "search_results_dropdown",
                    inline: "search_results_inline",
                },
                destinationTextMode: {
                    wrap: "destination_text_wrap",
                    clip: "destination_text_clip",
                    marquee: "destination_text_marquee",
                    manual: "destination_text_manual",
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
                { name: "name", selector: { text: {} }, default: "Another MVG Search" },
                {
                    name: "monitorType",
                    selector: {
                        select: {
                            mode: "dropdown",
                            options: [
                                { value: "departure", label: "Departure" },
                                { value: "arrival", label: "Arrival" },
                            ]
                        }
                    },
                    default: "departure"
                },
                { name: "showMonitorSwitch", selector: { boolean: {} }, default: true },
                { name: "showLocationSearch", selector: { boolean: {} }, default: false },
                { name: "rememberLastSearch", selector: { boolean: {} }, default: false },
                { name: "favoriteStops", selector: { text: { multiline: true } } },
                {
                    name: "searchResultsMode",
                    selector: {
                        select: {
                            mode: "dropdown",
                            options: [
                                { value: "dropdown", label: "Dropdown" },
                                { value: "inline", label: "Inline" },
                            ]
                        }
                    },
                    default: "dropdown"
                },
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
                { name: "limit", selector: { number: { min: 1, max: 80, step: 1, mode: "box" } }, default: 40 },
                {
                    name: "displayOptions",
                    selector: {
                        select: {
                            mode: "dropdown",
                            options: [
                                { value: "1", label: "16:27 +2 (16:29)" },
                                { value: "2", label: "16:27 +2" },
                                { value: "3", label: "16:29" },
                                { value: "4", label: "7" },
                                { value: "5", label: "7 (+2)" },
                            ]
                        }
                    },
                    default: "1"
                },
                { name: "showType", selector: { boolean: {} }, default: false },
                { name: "hideTrack", selector: { boolean: {} }, default: false },
                {
                    name: "destinationTextMode",
                    selector: {
                        select: {
                            mode: "dropdown",
                            options: [
                                { value: "wrap", label: "Wrap" },
                                { value: "clip", label: "Clip" },
                                { value: "marquee", label: "Auto scroll" },
                                { value: "manual", label: "Manual scroll" },
                            ]
                        }
                    },
                    default: "wrap"
                },
                { name: "maxDepartures", selector: { number: { min: 1, max: 100, step: 1 } } },
                { name: "maxDeparturesFixed", selector: { boolean: {} }, default: false },
                {
                    name: "groupingMode",
                    selector: {
                        select: {
                            mode: "dropdown",
                            options: [
                                { value: "none", label: "None" },
                                { value: "transport_type", label: "Transport type" },
                                { value: "line", label: "Line" },
                            ]
                        }
                    },
                    default: "none"
                },
                {
                    name: "groupingSort",
                    selector: {
                        select: {
                            mode: "dropdown",
                            options: [
                                { value: "alphabetical", label: "Alphabetical" },
                                { value: "next_departure", label: "Next departure" },
                            ]
                        }
                    },
                    default: "alphabetical"
                },
                {
                    name: "labelClickAction",
                    selector: {
                        select: {
                            mode: "dropdown",
                            options: [
                                { value: "off", label: "Off" },
                                { value: "filter_line", label: "Filter line" },
                            ]
                        }
                    },
                    default: "off"
                },
            ],
            computeLabel: (schema, localize) => {
                localizeSelectOptions(schema, localize);
                const labels = {
                    name: "search_card_name",
                    monitorType: "search_monitor_type",
                    favoriteStops: "search_favorite_stops",
                    searchResultsMode: "search_results_mode",
                    showMonitorSwitch: "search_show_monitor_switch",
                    showLocationSearch: "search_show_location_search",
                    rememberLastSearch: "search_remember_last_search",
                    transportType: "search_transport_type",
                    limit: "request_limit",
                    displayOptions: "departure_options",
                    showType: "show_type",
                    hideTrack: "hide_track",
                    destinationTextMode: "destination_text_mode",
                    maxDepartures: "max_departures",
                    maxDeparturesFixed: "max_departures_fixed",
                    groupingMode: "grouping_mode",
                    groupingSort: "grouping_sort",
                    labelClickAction: "label_click_action",
                };
                const label = labels[schema.name];
                return label ? localize(`component.another_mvg.cardeditor.${label}`) : schema.name;
            },
            computeHelper: (schema, localize) => {
                const labels = {
                    name: "search_card_name_desc",
                    monitorType: "search_monitor_type_desc",
                    favoriteStops: "search_favorite_stops_desc",
                    searchResultsMode: "search_results_mode_desc",
                    showMonitorSwitch: "search_show_monitor_switch_desc",
                    showLocationSearch: "search_show_location_search_desc",
                    rememberLastSearch: "search_remember_last_search_desc",
                    transportType: "search_transport_type_desc",
                    limit: "request_limit_desc",
                    displayOptions: "departure_options_desc",
                    showType: "show_type_desc",
                    hideTrack: "hide_track_desc",
                    destinationTextMode: "destination_text_mode_desc",
                    maxDepartures: "search_max_departures_desc",
                    maxDeparturesFixed: "search_max_departures_fixed_desc",
                    groupingMode: "grouping_mode_desc",
                    groupingSort: "grouping_sort_desc",
                    labelClickAction: "label_click_action_desc",
                };
                const label = labels[schema.name];
                return label ? localize(`component.another_mvg.cardeditor.${label}`) : "";
            },
        };
    }
}

customElements.define("content-card-another-mvg-search", ContentAnotherMVGSearch);

window.customCards = window.customCards || [];
window.customCards.push({
    type: "content-card-another-mvg-search",
    name: "AnotherMVG Search Card",
    preview: false,
    description: "DE: Dynamische Suche nach MVG/MVV Haltestellen mit Abfahrts- oder Ankunftsanzeige. EN: Dynamic MVG/MVV station search with departure or arrival display.",
    documentationURL: "https://github.com/Nisbo/another_mvg",
});
