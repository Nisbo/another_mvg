/* AnotherMVG */
const version = "3.0.0-BETA-1";
let debug = false;

class ContentAnotherMVG extends HTMLElement {
    constructor(){
        super();

        console.log(
            "%cAnotherMVG %cv" + version,
            "color:#fff;background:#2196f3;padding:2px 6px;border-radius:3px;",
            "color:#fff;background:#4caf50;padding:2px 6px;border-radius:3px;"
        );
    }

    set hass(hass) {
        // only update if there is a change in the data of the monitored entities and if translations are loaded
        const entities = Object.keys(this.config)
            .filter((key) => key === "entity" || key.startsWith("entity"))
            .sort((a, b) => {
                if (a === "entity") return -1;
                if (b === "entity") return 1;

                return parseInt(a.replace("entity", "")) - parseInt(b.replace("entity", ""));
            })
            .map((key) => this.config[key])
            .filter(Boolean);

        if (!this._lastEntityData) {
            this._lastEntityData = {};
        }

        let changedEntities = [];

        entities.forEach((entityId) => {
            const newData = hass.states[entityId]?.attributes?.departures;
            const newString = JSON.stringify(newData);

            if (this._lastEntityData[entityId] !== newString) {
                changedEntities.push(entityId);
                this._lastEntityData[entityId] = newString;
            }
        });

        if (changedEntities.length === 0 && this._translationsLoaded) {
            console.log("AnotherMVG - Data Update (without changes) received for card with main entity: ", this.config.entity);
            return;
        }

        // load translations only once
        if (!this._translationsRequested) {
            this._translationsRequested = true;
            this.loadTranslations(hass);
        }

        // check if translations are loaded
        if (!this._translationsLoaded) {
            const test = hass.localize("component.another_mvg.frontend.column_type");
            if (test) {
                this._translationsLoaded = true;
                if (debug) {
                    console.log("AnotherMVG - translations ready.");
                }
            }
        }

        if (debug && changedEntities.length > 0) {
            console.log("AnotherMVG - Data Update received for: ", changedEntities);
        }

        this.render(hass);
    }

    async loadTranslations(hass) {
        try {
            //await hass.loadBackendTranslation("frontend", "another_mvg");
            //await hass.loadBackendTranslation("cardeditor", "another_mvg");
            await Promise.all([
                hass.loadBackendTranslation("frontend", "another_mvg"),
                hass.loadBackendTranslation("cardeditor", "another_mvg")
            ]);
            if (debug) {
                console.log("AnotherMVG - translations requested");
            }
        } catch (e) {
            console.warn("AnotherMVG - translation load failed", e);
        }
    }

    getConfiguredCss(state) {
        const cardCss = this.config?.customCss;
        if (typeof cardCss === "string" && cardCss.trim()) {
            return cardCss;
        }

        return state?.attributes?.config?.css_code || "";
    }

    applyCustomCss(state) {
        const cssCode = this.getConfiguredCss(state);
        const nextStyleContent = this.baseStyleElementText + (cssCode?.trim() ? `\n${cssCode}` : "");

        if (this.styleElement.textContent !== nextStyleContent) {
            this.styleElement.textContent = nextStyleContent;
        }
    }

    // Function, to show the current time
    getCurrentTime(clockWithSeconds = false) {
        const now = new Date();
        if (clockWithSeconds) {
            return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } else {
            return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }

    updateClock(clockWithSeconds) {
        if (!this.content) return;

        const el = this.content.querySelector(".currentTime");
        if (!el) return;

        el.textContent = this.getCurrentTime(clockWithSeconds);
    }

    startClockTimer(clockWithSeconds) {
        if (this._clockTimer) return;

        const now = new Date();

        if (clockWithSeconds) {
            const msUntilNextSecond = (1000 - now.getMilliseconds());

            this._clockTimeout = setTimeout(() => {
                this.updateClock(clockWithSeconds);

                this._clockTimer = setInterval(() => {
                    this.updateClock(clockWithSeconds);
                }, 1000);

            }, msUntilNextSecond);

        } else {
            const msUntilNextMinute = (60 - now.getSeconds()) * 1000;

            this._clockTimeout = setTimeout(() => {
                this.updateClock(clockWithSeconds);

                this._clockTimer = setInterval(() => {
                    this.updateClock(clockWithSeconds);
                }, 60000);

            }, msUntilNextMinute);
        }
    }

    stopClockTimer() {
        if (this._clockTimeout) {
            clearTimeout(this._clockTimeout);
            this._clockTimeout = null;
        }
        if (this._clockTimer) {
            clearInterval(this._clockTimer);
            this._clockTimer = null;
        }
    }

    connectedCallback() {
        if (this.config?.showClock) {
            const clockWithSeconds = this.config.clockWithSeconds ?? false;

            this.stopClockTimer();
            this.startClockTimer(clockWithSeconds);

            // sofort aktualisieren (wichtig!)
            this.updateClock(clockWithSeconds);
        }
    }

    disconnectedCallback() {
        this.stopClockTimer();
    }

    render(hass) {
        if (!this.content) {
            const card        = document.createElement('ha-card');
            this.content      = document.createElement('div');
            this.styleElement = document.createElement('style');

            this.styleElement.textContent = `
              /* Card background */
              .amvg-container {
                background-color: var(--amvg-card-bg-color, #000080);
                border-radius: var(--ha-card-border-radius,12px);
                padding-bottom: 5px;
              }
              
              /* Name of the card - from name parameter */
              .amvg-cardname {
                font-weight: bold;
                font-size:1.0em;
                padding: 2px 0 2px 8px;
                color: var(--amvg-text-color, #FFFFFF);
              }
              
              /* Table */
              .amvg-table {
                width: 100%;
                border-collapse:collapse;
              }
              
              /* Table Header - Linie, Ziel, Gleis, Abfahrt */
              .amvg-headline {
                font-weight: bold;
                background-color: var(--amvg-header-bg-color, #FAE10C);
                color: var(--amvg-header-text-color, #000080);
                border-width: 0;
                text-align: left;
              }
              
              /* Column widths and spacing */
              .label {
                width: 10%;
                padding: 0 6px;
              }
              .destination {
                width: 60%;
                text-wrap: wrap;
                color: var(--amvg-text-color, #FFFFFF);

              }
              .track {
                padding: 0 5px;
                width: fit-content;
                color: var(--amvg-text-color, #FFFFFF);
              }
              .time {
                padding-right: 5px;
                width: fit-content;
                white-space: nowrap;
                color: var(--amvg-text-color, #FFFFFF);
              }
              .labelHL {
                width: 10%;
                padding: 0 6px;
              }
              .destinationHL {
                width: 60%;
                text-wrap: wrap;
              }
              .trackHL {
                padding: 0 5px;
                width: fit-content;
              }
              .timeHL {
                padding-right: 5px;
                width: fit-content;
                white-space: nowrap;
              }
              .cancelled {
                color: red;
              }
              .delay {
                color: red;
              }
              
              /* General formatting for the labels */
              span.line {
                font-weight: bold;
                color: #FFFFFF;
                background-color: #000000;
                border: 1px solid #FFFFFF;
                font-size:0.9em;
                margin-right:0.5em;
                margin-left:0.1em;
                display: block;
                text-align: center;
                width: 35px;
                margin: 2px 0;
              }
              
              /* BUS */
              span.BUS {
                background-color: #00586A;
              }
              
              /* REGIONAL_BUS */
              span.REGIONAL_BUS {
                background-color: #4682B4;
              }
              
              /* BAHN */
              span.BAHN {
                background-color: #FFFFFF;
                color: #E30613;
                border: 1px solid #E30613;
              }
              
              /* SBAHN */
              span.SBAHN {
                border-radius:1000px;
                border: 1px solid #FFFFFF;
              }
              span.S1  {background-color: #16BAE7;}
              span.S2  {background-color: #76B82A;}
              span.S3  {background-color: #951B81;}
              span.S4  {background-color: #E30613;}
              span.S5  {background-color: #005E82;}
              span.S6  {background-color: #00975F;}
              span.S7  {background-color: #943126;}
              span.S8  {background-color: #000000; color: #FFFFFF;}
              span.S20 {background-color: #ED6B83;}
              
              /* TRAM */
              span.TRAM {background-color: #D82020;}
              
              /* UBAHN */
              span.UBAHN {/* special formating for general UBAHN - place holder */}
              span.U1 {background-color: #438136;}
              span.U2 {background-color: #C40C37;}
              span.U3 {background-color: #F36E31;}
              span.U4 {background-color: #0AB38D;}
              span.U5 {background-color: #B8740E;}
              span.U6 {background-color: #006CB3;}
              span.U7 {background: linear-gradient(322deg, #C40C37 50%, #438136 50%);}
              span.U8 {background: linear-gradient(322deg, #F36E31 50%, #C40C37 50%);}
              `
            card.appendChild(this.styleElement);
            card.appendChild(this.content);
            this.appendChild(card);
        }

        // put all the configured entities in an array, sorted by entity, entity2, entity3, etc. with entity as the first one
        const entityKeys = Object.keys(this.config)
            .filter((key) => key === "entity" || /^entity\d+$/.test(key))
            .sort((a, b) => {
                if (a === "entity") return -1;
                if (b === "entity") return 1;
                return Number(a.slice(6)) - Number(b.slice(6));
            });

        // for each entity, get the corresponding maxDepartures and displayOptions, if available
        const fields = ["maxDepartures", "displayOptions", "transportType", "name", "maxDeparturesFixed"];
        const entityConfigs = entityKeys.map((key) => {
            const index = key === "entity" ? "" : key.slice(6);

            const getKey = (base) =>
                index === "" ? base : `${base}${index}`;

            const obj = {
                entity: this.config[key]
            };

            fields.forEach((field) => {
                obj[field] = this.config[getKey(field)];
            });

            return obj;
        });

        debug                       = this.config.debug ?? false;
        const entityId              = this.config.entity; // main entity
        const state                 = hass.states[entityId]; // state for main entity
        const globalDepartureFormat = this.config.displayOptions && ["1", "2", "3", "4", "5"].includes(this.config.displayOptions) ? this.config.displayOptions : "1"; // 1 as default
        const hideTrack             = this.config.hideTrack ?? false; // false as default
        const showType              = this.config.showType  ?? false; // false as default
        const showClock             = this.config.showClock ?? false; // false as default
        const clockWithSeconds      = this.config.clockWithSeconds ?? false; // false as default
        const hideName              = this.config.hideName  ?? false; // false as default
        const stopName              = this.config.name ?? state?.attributes?.config?.name ?? entityId; // name from config or from entity or entityId as default
        const globalMax             = this.config.maxDepartures ? parseInt(this.config.maxDepartures) : null; // no default, show all departures
        const globalMaxDepFixed     = this.config.maxDeparturesFixed ?? false; // false as default, if true, the card will always show the number of departures defined in maxDepartures, if there are less departures available, empty rows will be shown
        const cardBackgroundColor   = this.config.cardBackgroundColor   || "#000080";
        const textColor             = this.config.textColor             || "#FFFFFF";
        const headerBackgroundColor = this.config.headerBackgroundColor || "#FAE10C";
        const headerTextColor       = this.config.headerTextColor       || "#000080";
        const transportTypeMap      = {
                                        "REGIONAL_BUS" : "R-Bus",
                                        "BUS"          : "Bus",
                                        "SBAHN"        : "S-Bahn",
                                        "UBAHN"        : "U-Bahn",
                                        "TRAM"         : "Tram",
                                        "BAHN"         : "Bahn"
                                      };

        if (showClock && !hideName) {
            this.startClockTimer(clockWithSeconds);
        } else {
            this.stopClockTimer();
        }

        if (state?.attributes?.config?.css_code?.trim() && !this.cssCodeApplied) {
            const onlyDarkMode = state.attributes.config.css_code_darkmode_only;
            const isDarkMode   = hass.themes.darkMode;
          
            if ((onlyDarkMode && isDarkMode) || !onlyDarkMode) {
                this.styleElement.textContent += state.attributes.config.css_code;
                this.cssCodeApplied = true; // Apply only ones
                //console.log("AnotherMVG - own CSS Code added:", state.attributes.config.css_code);
                //console.log(`AnotherMVG - own CSS Code added (DarkModeOnly: ${onlyDarkMode}, DarkMode: ${isDarkMode})`);
            } else {
                //console.log(`AnotherMVG - Skipping CSS Code (DarkModeOnly: ${onlyDarkMode}, DarkMode: ${isDarkMode})`);
            }
        }
        //else if (!state?.attributes?.config?.css_code?.trim() && !this.cssCodeApplied) {
        //    console.log("AnotherMVG - no CSS Code available or empty.");
        //}

        this.baseStyleElementText = this.styleElement.textContent;
        this.style.setProperty("--amvg-card-bg-color",     cardBackgroundColor);
        this.style.setProperty("--amvg-text-color",        textColor);
        this.style.setProperty("--amvg-header-bg-color",   headerBackgroundColor);
        this.style.setProperty("--amvg-header-text-color", headerTextColor);
        this.applyCustomCss(state);
        
        /* state for main entity undefined */
        if (!state || !state.attributes || !state.attributes.config) {
            let html = "<b><u>Another MVG:</u></b><br>The main entity <b>" + entityId + "</b> is undefined!<br>Maybe only a typo or disabled ?<br>Or did you delete the stop ?";
            this.content.innerHTML = html;
        } else {
            let html = ``;
            let ccc = 0;
            let colspawn = 4;

            if (hideTrack) colspawn -= 1;
            if (showType)  colspawn += 1;

            // show all stations in the same card, if there are more than one station configured
            entityConfigs.forEach(({ entity, maxDepartures, displayOptions, transportType, name, maxDeparturesFixed }) => {
                ccc++;

                const departureFormat = displayOptions && ["1", "2", "3", "4", "5"].includes(displayOptions) ? displayOptions : globalDepartureFormat;

                const state2 = hass.states[entity];
                if (!state2?.attributes?.config) {
                    html += `
                        <tr>
                            <td colspan="${colspawn}" class="amvg-cardname"><br />
                                <b><u>Another MVG:</u></b><br />
                                The additional entity <b>"${entity}"</b> is undefined!<br>
                                Maybe only a typo or disabled ?<br />
                                Or did you delete the stop ?
                            </td>
                        </tr>
                    `;
                } else{
                    // only show as separator for the additionally stations
                    if (ccc > 1) {
                        html += `
                            ${!hideName ? `
                                <tr>
                                    <td colspan="${colspawn}" class="amvg-cardname"><br />
                                        ${name || state2?.attributes?.config?.name || stopName}
                                        ${state2.attributes.dataOutdated !== undefined
                                            ? ` ${state2.attributes.dataOutdated}`
                                            : " (loading)"}
                                    </td>
                                </tr>` : ""}
                        `;
                    }

                    html += `
                        <tr class="amvg-headline">
                            ${showType ? `<th class="labelHL">${hass.localize("component.another_mvg.frontend.column_type")}</th>` : ""}
                            <th class="labelHL">${hass.localize("component.another_mvg.frontend.column_line")}</th>
                            <th class="destinationHL">${hass.localize("component.another_mvg.frontend.column_destination")}</th>
                            ${!hideTrack ? `<th class="trackHL">${hass.localize("component.another_mvg.frontend.column_track")}</th>` : ""}
                            <th class="timeHL">${hass.localize("component.another_mvg.frontend.column_departure")}</th>
                        </tr>
                        `;

                    const data2 = state2.attributes.departures || [];

                    // if there are no departures, show a loading message
                    if (!data2 || data2 === "undefined" || (Array.isArray(data2) && data2.length === 0)) {
                        html += `
                            <tr>
                                <td colspan="${colspawn}" class="amvg-cardname">
                                    Addon is loading or no departures available.
                                </td>
                            </tr>
                            `;
                    } else {
                        let transportTypes = null;

                        if (transportType) {
                            if (Array.isArray(transportType)) {
                                transportTypes = transportType.map(t => t.trim().toUpperCase());
                            } else if (typeof transportType === "string") {
                                transportTypes = transportType.split(",").map(t => t.trim().toUpperCase());
                            }
                        }

                        let filtered = data2;

                        if (transportTypes && transportTypes.length > 0) {
                            filtered = data2.filter(dep => {
                                const type = dep.transport_type?.toUpperCase();
                                return type && transportTypes.includes(type);
                            });
                        }

                        const list2 = (maxDepartures ?? globalMax)
                            ? filtered.slice(0, maxDepartures ?? globalMax)
                            : filtered;

                        let rowCount = 0;
                        list2.forEach((departure) => {
                            rowCount++;
                            let transportType = transportTypeMap[departure.transport_type] || departure.transport_type;

                            if (departure.label === "LUFTHANSA EXPRESS BUS") {
                                departure.label = "LEB";
                            }

                            html += `<tr class="item">`;

                            if (showType) {
                                html += `<td class="label"><nobr>${transportType}</nobr></td>`;
                            }

                            html += `<td class="label">
                                        <span class="line ${departure.transport_type} ${departure.label}">
                                            ${departure.trainType}${departure.label}
                                        </span>
                                    </td>`;

                            html += `<td class="destination">${departure.destination}</td>`;

                            if (!hideTrack) {
                                html += `<td class="track">${departure.track}</td>`;
                            }

                            let timeDisplay = "";

                            if (departureFormat === "1") {
                                timeDisplay = departure.planned_departure;

                                if (departure.cancelled) {
                                    timeDisplay += ` <span class="cancelled">${hass.localize("component.another_mvg.frontend.cancelled")}</span>`;
                                } else if (departure.delay > 0) {
                                    timeDisplay += ` <span class="delay">+${departure.delay}</span> (${departure.expected_departure})`;
                                }

                            } else if (departureFormat === "2") {
                                timeDisplay = departure.planned_departure;

                                if (departure.cancelled) {
                                    timeDisplay += ` <span class="cancelled">${hass.localize("component.another_mvg.frontend.cancelled")}</span>`;
                                } else if (departure.delay > 0) {
                                    timeDisplay += ` <span class="delay">+${departure.delay}</span>`;
                                }

                            } else if (departureFormat === "3") {
                                timeDisplay = departure.delay > 0
                                    ? `<span class="delay">${departure.expected_departure}</span>`
                                    : departure.expected_departure;

                                if (departure.cancelled) {
                                    timeDisplay += ` <span class="cancelled">${hass.localize("component.another_mvg.frontend.cancelled")}</span>`;
                                }

                            } else if (departureFormat === "4") {
                                timeDisplay = Math.floor(departure.time_diff / 60);

                                if (departure.cancelled) {
                                    timeDisplay += ` <span class="cancelled">${hass.localize("component.another_mvg.frontend.cancelled")}</span>`;
                                }

                            } else if (departureFormat === "5") {
                                timeDisplay = Math.floor(departure.time_diff / 60);

                                if (departure.delay > 0) {
                                    timeDisplay += ` <span class="delay">(+${departure.delay})</span>`;
                                }

                                if (departure.cancelled) {
                                    timeDisplay += ` <span class="cancelled">${hass.localize("component.another_mvg.frontend.cancelled")}</span>`;
                                }
                            }

                            html += `<td class="time">${timeDisplay}</td>`;
                            html += `</tr>`;
                        });

                        if ((maxDeparturesFixed ?? globalMaxDepFixed) && rowCount < (maxDepartures ?? globalMax)) {
                            for (let i = rowCount; i < (maxDepartures ?? globalMax); i++) {
                                html += `                            
                                <tr>
                                    <td colspan="${colspawn}" class="amvg-cardname">
                                        &#160;
                                    </td>
                                </tr>`;
                            }
                        }
                    }
                }
            });
            
            this.content.innerHTML = `
                <div class="amvg-container">
                    ${!hideName ? `<div class="amvg-cardname">${stopName}${state.attributes.dataOutdated !== undefined ? ` ${state.attributes.dataOutdated}` : " (loading)"}<span class="currentTime" style="float: right; margin-right: 5px;">${showClock ? this.getCurrentTime(clockWithSeconds) : ""}</span></div>` : ""}
                    <table class="amvg-table"> 
                        ` + html + `
                    </table>
                </div>
                `;
        }
    }
    
    // The user supplied configuration. Throw an exception and Home Assistant
    // will render an error card.
    setConfig(config) {
        if (!config.entity) {
            throw new Error("You need to define an entity");
        }
        this.config = config;
    }
    
    // The height of your card. Home Assistant uses this to automatically
    // distribute all cards over the available columns.
    getCardSize() {
        return 6;
    }
    
    // Editor Configuration
    static getConfigForm() {
    return {
        schema: [
            // Entity Selection
            {
                name: "entity",
                required: true,
                selector: {
                    entity: {
                        filter: [
                            {
                                integration: "another_mvg"
                            }
                        ]
                    }
                },
            },
            {
                name: "name",
                selector: { text: {} },
                default: ""
            },
            {
                name: "transportType",
                selector: {
                    select: {
                        multiple : true,
                        sort: false,
                        options: [
                            { value: "SBAHN",        label: "S-Bahn" },
                            { value: "UBAHN",        label: "U-Bahn" },
                            { value: "BAHN",         label: "Bahn" },
                            { value: "TRAM",         label: "Tram" },
                            { value: "BUS",          label: "Bus" },
                            { value: "REGIONAL_BUS", label: "Regional-Bus" }
                        ]
                    }
                }
            },

            // Options
            {
                type: 'expandable',
                label: 'options',
                icon: 'mdi:cog-outline',
                schema: [
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
                                    { value: "5", label: "7 (+2)" }
                                ]
                            }
                        },
                        default: "1"
                    },
                    { name: "showClock",        selector: { boolean: {} }, default: false },
                    { name: "clockWithSeconds", selector: { boolean: {} }, default: false },
                    { name: "hideName",         selector: { boolean: {} }, default: false },
                    { name: "hideTrack",        selector: { boolean: {} }, default: false },
                    { name: "showType",         selector: { boolean: {} }, default: false },
                    {
                        name: "maxDepartures",
                        selector: { number: { min: 1, max: 100, step: 1 } }
                    },
                    { name: "maxDeparturesFixed", selector: { boolean: {} }, default: false }
                ]
            },

            // Color Options
            {
                type: 'expandable',
                label: 'colors',
                //name: 'colors', --> no name set to avoid grouping (indent)
                icon: 'mdi:format-color-fill',
                schema: [
                    {
                        name: "cardBackgroundColor",
                        selector: { text: {} },
                        default: "#000080"
                    },
                    {
                        name: "textColor",
                        selector: { text: {} },
                        default: "#FFFFFF"
                    },
                    {
                        name: "headerBackgroundColor",
                        selector: { text: {} },
                        default: "#FAE10C"
                    },                    
                    {
                        name: "headerTextColor",
                        selector: { text: {} },
                        default: "#000080"
                    },
                    {
                        name: "customCss",
                        required: false,
                        selector: {
                            object: {
                                properties: {
                                    "category2": { type: "string", name: "Only a placeholder" },
                                    "items2": { type: "text", name: "to let HA fall back to yaml mode" }
                                }
                            }
                        }
                    }
                ]
            },

            // Other Stations
            {
                type: 'expandable',
                label: 'otherstations',
                icon: 'mdi:shape-outline',
                schema: [
                    {
                        type: 'expandable',
                        label: 'entity2',
                        icon: 'mdi:shape-outline',
                        schema: [
                            {
                                name: "entity2",
                                required: false,
                                selector: {
                                    entity: {
                                        filter: [
                                            {
                                                integration: "another_mvg"
                                            }
                                        ]
                                    }
                                },
                            },

                            {
                                name: "name2",
                                selector: { text: {} },
                                default: ""
                            },
                            {
                                name: "transportType2",
                                selector: {
                                    select: {
                                        multiple : true,
                                        sort: false,
                                        options: [
                                            { value: "SBAHN",        label: "S-Bahn" },
                                            { value: "UBAHN",        label: "U-Bahn" },
                                            { value: "BAHN",         label: "Bahn" },
                                            { value: "TRAM",         label: "Tram" },
                                            { value: "BUS",          label: "Bus" },
                                            { value: "REGIONAL_BUS", label: "Regional-Bus" }
                                        ]
                                    }
                                }
                            },
                            {
                                name: "displayOptions2",
                                selector: {
                                    select: {
                                        mode: "dropdown",
                                        options: [
                                            { value: "1", label: "16:27 +2 (16:29)" },
                                            { value: "2", label: "16:27 +2" },
                                            { value: "3", label: "16:29" },
                                            { value: "4", label: "7" },
                                            { value: "5", label: "7 (+2)" }
                                        ]
                                    }
                                },
                                default: "1"
                            },
                            {
                                name: "maxDepartures2",
                                selector: { number: { min: 1, max: 100, step: 1 } }
                            },
                            { name: "maxDeparturesFixed2", selector: { boolean: {} }, default: false }
                        ]
                    },

                    {
                        type: 'expandable',
                        label: 'entity3',
                        icon: 'mdi:shape-outline',
                        schema: [
                            {
                                name: "entity3",
                                required: false,
                                selector: {
                                    entity: {
                                        filter: [
                                            {
                                                integration: "another_mvg"
                                            }
                                        ]
                                    }
                                },
                            },
                            {
                                name: "name3",
                                selector: { text: {} },
                                default: ""
                            },
                            {
                                name: "transportType3",
                                selector: {
                                    select: {
                                        multiple : true,
                                        sort: false,
                                        options: [
                                            { value: "SBAHN",        label: "S-Bahn" },
                                            { value: "UBAHN",        label: "U-Bahn" },
                                            { value: "BAHN",         label: "Bahn" },
                                            { value: "TRAM",         label: "Tram" },
                                            { value: "BUS",          label: "Bus" },
                                            { value: "REGIONAL_BUS", label: "Regional-Bus" }
                                        ]
                                    }
                                }
                            },
                            {
                                name: "displayOptions3",
                                selector: {
                                    select: {
                                        mode: "dropdown",
                                        options: [
                                            { value: "1", label: "16:27 +2 (16:29)" },
                                            { value: "2", label: "16:27 +2" },
                                            { value: "3", label: "16:29" },
                                            { value: "4", label: "7" },
                                            { value: "5", label: "7 (+2)" }
                                        ]
                                    }
                                },
                                default: "1"
                            },
                            {
                                name: "maxDepartures3",
                                selector: { number: { min: 1, max: 100, step: 1 } }
                            },
                            { name: "maxDeparturesFixed3", selector: { boolean: {} }, default: false }
                        ]
                    },
                    {
                        type: 'expandable',
                        label: 'entity4',
                        icon: 'mdi:shape-outline',
                        schema: [
                            {
                                name: "entity4",
                                required: false,
                                selector: {
                                    entity: {
                                        filter: [
                                            {
                                                integration: "another_mvg"
                                            }
                                        ]
                                    }
                                },
                            },

                            {
                                name: "name4",
                                selector: { text: {} },
                                default: ""
                            },
                            {
                                name: "transportType4",
                                selector: {
                                    select: {
                                        multiple : true,
                                        sort: false,
                                        options: [
                                            { value: "SBAHN",        label: "S-Bahn" },
                                            { value: "UBAHN",        label: "U-Bahn" },
                                            { value: "BAHN",         label: "Bahn" },
                                            { value: "TRAM",         label: "Tram" },
                                            { value: "BUS",          label: "Bus" },
                                            { value: "REGIONAL_BUS", label: "Regional-Bus" }
                                        ]
                                    }
                                }
                            },
                            {
                                name: "displayOptions4",
                                selector: {
                                    select: {
                                        mode: "dropdown",
                                        options: [
                                            { value: "1", label: "16:27 +2 (16:29)" },
                                            { value: "2", label: "16:27 +2" },
                                            { value: "3", label: "16:29" },
                                            { value: "4", label: "7" },
                                            { value: "5", label: "7 (+2)" }
                                        ]
                                    }
                                },
                                default: "1"
                            },
                            {
                                name: "maxDepartures4",
                                selector: { number: { min: 1, max: 100, step: 1 } }
                            },
                            { name: "maxDeparturesFixed4", selector: { boolean: {} }, default: false }
                        ]
                    },
                    {
                        type: 'expandable',
                        label: 'entity5',
                        icon: 'mdi:shape-outline',
                        schema: [
                            {
                                name: "entity5",
                                required: false,
                                selector: {
                                    entity: {
                                        filter: [
                                            {
                                                integration: "another_mvg"
                                            }
                                        ]
                                    }
                                },
                            },

                            {
                                name: "name5",
                                selector: { text: {} },
                                default: ""
                            },
                            {
                                name: "transportType5",
                                selector: {
                                    select: {
                                        multiple : true,
                                        sort: false,
                                        options: [
                                            { value: "SBAHN",        label: "S-Bahn" },
                                            { value: "UBAHN",        label: "U-Bahn" },
                                            { value: "BAHN",         label: "Bahn" },
                                            { value: "TRAM",         label: "Tram" },
                                            { value: "BUS",          label: "Bus" },
                                            { value: "REGIONAL_BUS", label: "Regional-Bus" }
                                        ]
                                    }
                                }
                            },
                            {
                                name: "displayOptions5",
                                selector: {
                                    select: {
                                        mode: "dropdown",
                                        options: [
                                            { value: "1", label: "16:27 +2 (16:29)" },
                                            { value: "2", label: "16:27 +2" },
                                            { value: "3", label: "16:29" },
                                            { value: "4", label: "7" },
                                            { value: "5", label: "7 (+2)" }
                                        ]
                                    }
                                },
                                default: "1"
                            },
                            {
                                name: "maxDepartures5",
                                selector: { number: { min: 1, max: 100, step: 1 } }
                            },
                            { name: "maxDeparturesFixed5", selector: { boolean: {} }, default: false }
                        ]
                    },
                ]
            }
            ],

            computeLabel: (schema, localize) => {
                let label = "";

                // this is only for the expandable options, because they don't have a name property, but we want to translate them as well
                if (!schema.name) {
                    const key = `component.another_mvg.cardeditor.${schema.label}`;
                    const translated = localize(key);

                    if (translated && translated !== key) {
                        return translated;
                    }

                    // fallback
                    return schema.name || schema.label;
                }

                if (schema.name == "displayOptions")        label = "departure_options";
                if (schema.name == "displayOptions2")       label = "departure_options";
                if (schema.name == "displayOptions3")       label = "departure_options";
                if (schema.name == "displayOptions4")       label = "departure_options";
                if (schema.name == "displayOptions5")       label = "departure_options";

                if (schema.name == "transportType")         label = "transport_type";
                if (schema.name == "transportType2")        label = "transport_type";
                if (schema.name == "transportType3")        label = "transport_type";
                if (schema.name == "transportType4")        label = "transport_type";
                if (schema.name == "transportType5")        label = "transport_type";

                if (schema.name == "entity")                label = "entity";
                if (schema.name == "entity2")               label = "entity2";
                if (schema.name == "entity3")               label = "entity3";
                if (schema.name == "entity4")               label = "entity4";
                if (schema.name == "entity5")               label = "entity5";

                if (schema.name == "name")                  label = "name";
                if (schema.name == "name2")                 label = "name";
                if (schema.name == "name3")                 label = "name";
                if (schema.name == "name4")                 label = "name";
                if (schema.name == "name5")                 label = "name";

                if (schema.name == "showClock")             label = "show_clock";
                if (schema.name == "clockWithSeconds")      label = "clock_with_seconds";
                if (schema.name == "hideName")              label = "hidename";
                if (schema.name == "hideTrack")             label = "hide_track";
                if (schema.name == "showType")              label = "show_type";
                if (schema.name == "maxDepartures")         label = "max_departures";
                if (schema.name == "maxDepartures2")        label = "max_departures";
                if (schema.name == "maxDepartures3")        label = "max_departures";
                if (schema.name == "maxDepartures4")        label = "max_departures";
                if (schema.name == "maxDepartures5")        label = "max_departures";
                if (schema.name == "maxDeparturesFixed")    label = "max_departures_fixed";
                if (schema.name == "maxDeparturesFixed2")   label = "max_departures_fixed";
                if (schema.name == "maxDeparturesFixed3")   label = "max_departures_fixed";
                if (schema.name == "maxDeparturesFixed4")   label = "max_departures_fixed";
                if (schema.name == "maxDeparturesFixed5")   label = "max_departures_fixed";

                if (schema.name == "cardBackgroundColor")   label = "card_bg_color";
                if (schema.name == "textColor")             label = "text_color";
                if (schema.name == "headerBackgroundColor") label = "header_bg_color";
                if (schema.name == "headerTextColor")       label = "header_text_color";
                if (schema.name == "customCss")             label = "custom_css";

                return localize(`component.another_mvg.cardeditor.${label}`);
            },

            computeHelper: (schema, localize) => {
                let label = "";

                // this is only for the expandable options, because they don't have a name property, but we want to translate them as well
                if (!schema.name) {
                    const key = `component.another_mvg.cardeditor.${schema.label}_desc`;
                    const translated = localize(key);

                    if (translated && translated !== key) {
                        return translated;
                    }

                    // fallback
                    //return `component.another_mvg.cardeditor.${schema.label}_desc`;
                    return "";
                }

                if (schema.name == "displayOptions")        label = "departure_options_desc";
                if (schema.name == "displayOptions2")       label = "departure_options_desc";
                if (schema.name == "displayOptions3")       label = "departure_options_desc";
                if (schema.name == "displayOptions4")       label = "departure_options_desc";
                if (schema.name == "displayOptions5")       label = "departure_options_desc";

                if (schema.name == "transportType")         label = "transport_type_desc";
                if (schema.name == "transportType2")        label = "transport_type_desc";
                if (schema.name == "transportType3")        label = "transport_type_desc";
                if (schema.name == "transportType4")        label = "transport_type_desc";
                if (schema.name == "transportType5")        label = "transport_type_desc";

                if (schema.name == "entity")                label = "station_desc";

                if (schema.name == "name")                  label = "name_desc";
                if (schema.name == "name2")                 label = "name_desc";
                if (schema.name == "name3")                 label = "name_desc";
                if (schema.name == "name4")                 label = "name_desc";
                if (schema.name == "name5")                 label = "name_desc";

                if (schema.name == "showClock")             label = "show_clock_desc";
                if (schema.name == "clockWithSeconds")      label = "clock_with_seconds_desc";
                if (schema.name == "hideName")              label = "hidename_desc";
                if (schema.name == "hideTrack")             label = "hide_track_desc";
                if (schema.name == "showType")              label = "show_type_desc";
                if (schema.name == "maxDepartures")         label = "max_departures_desc";
                if (schema.name == "maxDepartures2")        label = "max_departures_desc";
                if (schema.name == "maxDepartures3")        label = "max_departures_desc";
                if (schema.name == "maxDepartures4")        label = "max_departures_desc";
                if (schema.name == "maxDepartures5")        label = "max_departures_desc";
                if (schema.name == "maxDeparturesFixed")    label = "max_departures_fixed_desc";
                if (schema.name == "maxDeparturesFixed2")   label = "max_departures_fixed_desc";
                if (schema.name == "maxDeparturesFixed3")   label = "max_departures_fixed_desc";
                if (schema.name == "maxDeparturesFixed4")   label = "max_departures_fixed_desc";
                if (schema.name == "maxDeparturesFixed5")   label = "max_departures_fixed_desc";

                if (schema.name == "cardBackgroundColor")   label = "card_bg_color_desc";
                if (schema.name == "textColor")             label = "text_color_desc";
                if (schema.name == "headerBackgroundColor") label = "header_bg_color_desc";
                if (schema.name == "headerTextColor")       label = "header_text_color_desc";
                if (schema.name == "customCss")             label = "custom_css_desc";

                return localize(`component.another_mvg.cardeditor.${label}`);
            },

            assertConfig: (config) => {
                if (config.notify_on_change_time !== undefined && isNaN(Number(config.notify_on_change_time))) {
                    throw new Error('Configuration error: "notify_on_change_time" must be a valid number between 0 and 300.');
                }
            }
        };
    }
}

customElements.define("content-card-another-mvg", ContentAnotherMVG);

// add the card to the list of custom cards for the card picker
window.customCards = window.customCards || []; // Create the list if it doesn't exist.
window.customCards.push({
    type: "content-card-another-mvg",
    name: "AnotherMVG Departure Card",
    preview: false, // Optional - defaults to false
    description: "DE: Mit dieser Karte kann man sich die Abfahrtzeiten einer Station anzeigen lassen. EN: This card allows you to view the departure times of a station.",
    documentationURL: "https://github.com/Nisbo/another_mvg",
});
