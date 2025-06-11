class ContentAnotherMVGbig extends HTMLElement {
    set hass(hass) {
        if (!this.content) this.loadTranslations(hass);
        this.render(hass);
    }

    async loadTranslations(hass) {
        await hass.loadBackendTranslation("frontend", "another_mvg");
        console.log("AnotherMVG - custom translations should be loaded");
    }

    render(hass) {
        // Initialize the content if it's not there yet.
        if (!this.content) {
            const card        = document.createElement('ha-card');
            this.content      = document.createElement('div');
            this.styleElement = document.createElement('style');

            this.styleElement.textContent = `
              .amvg-table-big {
                background-color: #000080;
                color: #FFFFFF;
                width: 100%;
                border-spacing: 0px;
                border-collapse: separate;
                border-radius: 10px;
              }

              table tr {
                border-radius: 10px;
              }

              table td {
                padding: 2px;
                vertical-align: top; /* or middle */
                word-wrap: break-word;
                line-height: normal;
              }

              table tr:first-child td:first-child {
                border-radius: 9px 0 0 0;
              }

              table tr:first-child td:last-child {
                border-radius: 0 9px 0 0;
              }

              table tr:last-child td:first-child {
                border-radius: 0 0 0 10px;
              }

              table tr:last-child td:last-child {
                border-radius: 0 0 10px 0;
              }

              table tr td:last-child {
                white-space: nowrap;
              }

              table tr td:first-child {
                vertical-align: top;  /* or middle */
              }

              table tr:last-child td {
                padding-bottom: 10px;
              }

              /* General formatting for the labels */
              span.line {
                font-weight: bold;
                color: #FFFFFF;
                background-color: #000000;
                border: 1px solid #FFFFFF;
                font-size:0.9em;
                padding:2px 8px 2px 8px;
                margin-right:0.5em;
                margin-left:0.1em;
              }

              /* Table Header - Linie, Ziel, Gleis, Abfahrt */
              .amvg-headline {
                font-weight: bold;
                background-color: #FAE10C;
                font-size:3.9em;
                color: #000080;
                vertical-align: middle;
                height:50px;
              }

              /* Table Content - Departure Lines */
              .departureline {
                height: auto;
                font-size: 3.9em;
                vertical-align: top;
                color: #FFFFFF;
                word-wrap: break-word;
                white-space: normal;
              }

              /* Name of the card - from name parameter */
              .amvg-cardname {
                font-weight: bold;
                font-size:1.0em;
                color: #FFFFFF;
              }

              .cancelled {
                color: red;
              }

              .delay {
                color: red;
              }

              /* BUS */
              span.BUS {
                background-color: #00586A;
                padding:2px 4px 2px 4px;
              }

              /* REGIONAL_BUS */
              span.REGIONAL_BUS {
                background-color: #4682B4;
                padding:2px 4px 2px 4px;
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

        const entityId         = this.config.entity;
        const state            = hass.states[entityId];
        const stateStr         = state ? state.state : "unavailable";
        const departureFormat  = this.config.displayOptions && ["1", "2", "3", "4", "5"].includes(this.config.displayOptions) ? this.config.displayOptions : "1"; // 1 as default
        const hideTrack        = this.config.hideTrack ?? false; // false as default
        const showType         = this.config.showType  ?? false; // false as default
        const showClock        = this.config.showClock ?? false; // false as default
        const hideName         = this.config.hideName  ?? false; // false as default
        const transportTypeMap = {
            "REGIONAL_BUS" : "R-Bus",
            "BUS"          : "Bus",
            "SBAHN"        : "S-Bahn",
            "UBAHN"        : "U-Bahn",
            "TRAM"         : "Tram",
            "BAHN"         : "Bahn"
        };

        let colspawn = 4;
        if (hideTrack) colspawn -= 1;
        if (showType)  colspawn += 1;

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

        /* state undefined */
        if (!state || state === "undefined") {
            var html = "<b><u>Another MVG:</u></b><br>The entity <b>" + entityId + "</b> is undefined!<br>Maybe only a typo ?<br>Or did you delete the stop ?";
            this.content.innerHTML = html;
        } else {
            // Function, to show the current time
            function getCurrentTime() {
                const now = new Date();
                return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                //return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }); // only for testing, there is no update every second
            }

        let html = `
        <table class="amvg-table-big">
            ${!hideName ? `
            <tr>
                <td colspan="${colspawn}" class="amvg-cardname">${state.attributes.config.name}${state.attributes.dataOutdated !== undefined ? ` ${state.attributes.dataOutdated}` : " (loading)"}<span class="currentTime" style="float: right; margin-right: 5px;">${showClock ? ` ${getCurrentTime()} ` : ""}</span></td>
            </tr>` : ""}
            <tr>
                ${showType ? `<td class="amvg-headline">${hass.localize("component.another_mvg.frontend.column_type")}</td>` : ""}
                <td class="amvg-headline">${hass.localize("component.another_mvg.frontend.column_line")}</td>
                <td class="amvg-headline">${hass.localize("component.another_mvg.frontend.column_destination")}</td>
                ${!hideTrack ? `<td class="amvg-headline">${hass.localize("component.another_mvg.frontend.column_track")}</td>` : ""}
                <td class="amvg-headline">${hass.localize("component.another_mvg.frontend.column_departure")}</td>
            </tr>
            `;

            this.data = state.attributes.departures;
            if (!this.data || this.data === "undefined") {
                html += `<tr>`;
                if (showType) {
                    html += `<td class="departureline">XX</td>`;
                }
                html += `<td class="departureline">XX</td>`;
                html += `<td class="departureline">Addon is loading.</td>`;
                if (!hideTrack) {
                    html += `<td class="departureline">-</td>`;
                }
                html += `<td class="departureline">-</td>`;
                html += `</tr>`;
            } else {
                this.data.forEach((departure) => {
                let transportType = transportTypeMap[departure.transport_type] || departure.transport_type;
                //if(departure.label == "LUFTHANSA EXPRESS BUS") departure.label = "LEB";
                html += `<tr>`;
                if (showType) {
                    html += `<td class="departureline"><nobr>${transportType}</nobr></td>`;
                }
                html += `<td class="departureline"><span class="line ${departure.transport_type} ${departure.label}">${departure.trainType}${departure.label}</span></td>`;
                html += `<td class="departureline">${departure.destination}</td>`;
                if (!hideTrack) {
                    html += `<td class="departureline">${departure.track}</td>`;
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
                    if (departure.delay > 0) {
                        timeDisplay = `<span class="delay">${departure.expected_departure}</span>`;
                    } else {
                        timeDisplay = departure.expected_departure;
                    }
                    if (departure.cancelled) {
                        timeDisplay += ` <span class="cancelled">${hass.localize("component.another_mvg.frontend.cancelled")}</span>`;
                    }
                } else if (departureFormat === "4") {
                    timeDisplay = Math.floor(departure.time_diff / 60);

                    if (departure.cancelled) {
                        timeDisplay += ` <span class="cancelled">${hass.localize("component.another_mvg.frontend.cancelled")}</span>`;
                    }
                } else if (departureFormat === "5") {
                    timeDisplay = Math.floor(departure.time_diff / 60);;
                    if (departure.delay > 0) {
                        timeDisplay += ` <span class="delay">(+${departure.delay})</span>`;
                    }
                    
                    if (departure.cancelled) {
                        timeDisplay += ` <span class="cancelled">${hass.localize("component.another_mvg.frontend.cancelled")}</span>`;
                    }
                }
                
                html += `<td class="departureline">${timeDisplay}</td>`;
                html += `</tr>`;
                });
            }
            
            html += `</table>`;
            this.content.innerHTML = html;
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
    
    static getConfigElement() {
        return document.createElement('content-card-another-mvg-editor-big');
    }
}


class ContentAnotherMVGEditorBig extends HTMLElement {
    constructor() {
        super();
        this.config = {};
    }

    async connectedCallback() {
        //await Promise.resolve({});
        await this.loadTranslations();
        this.render();
    }

    async loadTranslations() {
        console.log("AnotherMVG - load custom translation - cardeditor");
        await this.hass.loadBackendTranslation("cardeditor", "another_mvg");
    }

    setConfig(config) {
        this.config = { ...config };
        this.render();
    }

    render() {
        this.innerHTML = ''; // Reset inner HTML
        
        /* Create the Container */
        const container = document.createElement('div');
        container.style.display = "flex";
        container.style.flexDirection = "column";
        
        /* Description for Station select */
        const description = document.createElement('p');
        description.innerHTML = this.hass.localize("component.another_mvg.cardeditor.station_desc");
        description.style.fontSize = "14px";
        description.style.marginBottom = "15px";
        container.appendChild(description);
      
        /* Get AnotherMVG entities from Home Assistant and sort by friendly_name */
        const entities = Object.values(this.hass.states).filter(entity => entity.entity_id && this.isAnotherMvgEntity(entity));
        entities.sort((a, b) => {
            const nameA = a.attributes.friendly_name || a.entity_id;
            const nameB = b.attributes.friendly_name || b.entity_id;
            return nameA.localeCompare(nameB);
        });
      
        /* 
          Station select
          Here we have to use an own class, because the 'ha-select' is closing the editor
          if we select the same menu item again, dont know why.
        */
        const entitySelect = document.createElement('another-mvg-custom-select-big');
        entitySelect.value = this.config.entity || "";
        entitySelect.addEventListener('change', (event) => {
            const selectedEntity = event.detail.value;
            
            // only fire the event if the value was changed
            if (this.config.entity !== selectedEntity) {
                //console.log("AnotherMVG - this.config.entity !== selectedEntity:");
                this.config = {
                    ...this.config,
                    entity: selectedEntity
                };
                this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
            } else {
                //console.log("AnotherMVG - Value did not change, not dispatching event.");
            }
        });
      
        // Add the entities to the dropdown
        entitySelect.options = entities.map(entity => ({
            value: entity.entity_id,
            text: entity.attributes.friendly_name || entity.entity_id
        }));
      
        // Set the initial value (current entity or select the 1st entity in the dropdown)
        if (this.config.entity) {
            entitySelect.value = this.config.entity;
        } else if (entities.length > 0) {
            this.config.entity = entities[0].entity_id;
            entitySelect.value = this.config.entity;
            this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
        }
      
        container.appendChild(entitySelect);
      
        /* Display options for departure column - label */
        const displayOptionsSelectLabel = document.createElement('label');
        displayOptionsSelectLabel.innerText = this.hass.localize("component.another_mvg.cardeditor.departure_options");
        displayOptionsSelectLabel.style.marginTop = "10px";
        container.appendChild(displayOptionsSelectLabel);
      
        /* Display options for departure column */
        const displayOptionsSelect = document.createElement('another-mvg-custom-select');
        displayOptionsSelect.value = this.config.displayOptions || "1";
        displayOptionsSelect.addEventListener('change', (event) => {
            const selectedOption = event.detail.value;
            if (this.config.displayOptions !== selectedOption) {
                this.config = {
                    ...this.config,
                    displayOptions: selectedOption
                };
                this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
            }
        });
      
        // Options for departure column
        displayOptionsSelect.options = [
            { text: "16:27 +2 (16:29)", value: "1" },
            { text: "16:27 +2",         value: "2" },
            { text: "16:29",            value: "3" },
            { text: "7",                value: "4" },
            { text: "7 (+2)",           value: "5" }
        ];
      
        // Set the initial value (current displayOptions or select the 1st displayOptions in the dropdown)
        if (this.config.displayOptions) {
            displayOptionsSelect.value = this.config.displayOptions;
        } else {
            this.config.displayOptions = "1";
            displayOptionsSelect.value = 1;
            this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
        }
        
        container.appendChild(displayOptionsSelect);
      
        /* Display options for departure column - description for options */
        const displayOptionsSelectLabel2 = document.createElement('label');
        displayOptionsSelectLabel2.innerText = this.hass.localize("component.another_mvg.cardeditor.departure_options_desc");
        displayOptionsSelectLabel2.style.marginTop = "10px";
        container.appendChild(displayOptionsSelectLabel2);
        
        /* Checkbox for showClock */
        const showClockCheckbox = document.createElement('ha-switch');
        showClockCheckbox.checked = this.config.showClock || false;
        showClockCheckbox.addEventListener('change', (event) => {
            this.config = { ...this.config, showClock: event.target.checked };
            this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
        });
      
        const showClockLabel = document.createElement('label');
        showClockLabel.innerText = this.hass.localize("component.another_mvg.cardeditor.show_clock");
        showClockLabel.style.marginTop = "10px";
        
        container.appendChild(showClockLabel);
        container.appendChild(showClockCheckbox);
      
        /* Checkbox for hideName */
        const hideNameCheckbox = document.createElement('ha-switch');
        hideNameCheckbox.checked = this.config.hideName || false;
        hideNameCheckbox.addEventListener('change', (event) => {
            this.config = { ...this.config, hideName: event.target.checked };
            this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
        });
        
        const hideNameLabel = document.createElement('label');
        hideNameLabel.innerText = this.hass.localize("component.another_mvg.cardeditor.hidename");
        hideNameLabel.style.marginTop = "10px";
        
        container.appendChild(hideNameLabel);
        container.appendChild(hideNameCheckbox);
      
        /* Checkbox for hideTrack */
        const hideTrackCheckbox = document.createElement('ha-switch');
        hideTrackCheckbox.checked = this.config.hideTrack || false;
        hideTrackCheckbox.addEventListener('change', (event) => {
            this.config = { ...this.config, hideTrack: event.target.checked };
            this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
        });
        
        const hideTrackLabel = document.createElement('label');
        hideTrackLabel.innerText = this.hass.localize("component.another_mvg.cardeditor.hide_track");
        hideTrackLabel.style.marginTop = "10px";
        
        container.appendChild(hideTrackLabel);
        container.appendChild(hideTrackCheckbox);
      
        /* Checkbox for showType */
        const showTypeCheckbox = document.createElement('ha-switch');
        showTypeCheckbox.checked = this.config.showType || false;
        showTypeCheckbox.addEventListener('change', (event) => {
            this.config = { ...this.config, showType: event.target.checked };
            this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
        });
        
        const showTypeLabel = document.createElement('label');
        showTypeLabel.innerText = this.hass.localize("component.another_mvg.cardeditor.show_type");
        showTypeLabel.style.marginTop = "10px";
        
        container.appendChild(showTypeLabel);
        container.appendChild(showTypeCheckbox);
        
        this.appendChild(container);
    }

    // check if 'another_mvg' entity
    isAnotherMvgEntity(entity) {
        return entity.attributes && entity.attributes.departures !== undefined;
    }
}


class AnotherMVGCustomSelectBig extends HTMLElement {
  constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      
      this.select = document.createElement('select');
      this.select.style.width = '100%';
      this.select.style.padding = '8px';
      this.select.style.border = '1px solid #ccc';
      this.select.style.borderRadius = '4px';
      this.select.style.boxSizing = 'border-box';
      this.shadowRoot.appendChild(this.select);
      this.select.addEventListener('change', (event) => {
          const selectedValue = event.target.value;
          if (this.lastSelectedValue !== selectedValue) {
              this.lastSelectedValue = selectedValue;
              this.dispatchEvent(new CustomEvent('change', { detail: { value: selectedValue } }));
          }
      });
  }

  set options(options) {
      this.select.innerHTML = '';
      options.forEach(option => {
          const opt = document.createElement('option');
          opt.value = option.value;
          opt.text = option.text;
          this.select.appendChild(opt);
      });
  }
  
  set value(value) {
      this.select.value = value;
      this.lastSelectedValue = value;
  }
  
  get value() {
      return this.select.value;
  }
}

customElements.define('another-mvg-custom-select-big', AnotherMVGCustomSelectBig);
customElements.define("content-card-another-mvg-big", ContentAnotherMVGbig);
customElements.define("content-card-another-mvg-editor-big", ContentAnotherMVGEditorBig);


for (var state of Object.values(document.querySelector("home-assistant").hass.states)) {
  //if (state.attributes["run_state"] !== undefined) {
    //return { entity: state.entity_id };
//console.log("AnotherMVG - test: ", state.entity_id);
  //}
}

async function loadTranslations() {
    var hass = document.querySelector("home-assistant")?.hass;
    
    if (!hass) {
        console.error("Home Assistant not found!");
        return;
    }

    await hass.loadBackendTranslation("frontend", "another_mvg");
    await Promise.resolve({});
    console.log("Loaded Resources:", hass.resources);

    // Wait if it last longer (max. 5 seconds)
    const startTime = Date.now();
    while (Date.now() - startTime < 5000) {
        const columnTypeLabel = hass.localize("component.another_mvg.frontend.column_type");
        if (columnTypeLabel && columnTypeLabel !== "") {
            console.log("Translation for column_type:", columnTypeLabel);
            return;
        }
        await new Promise(resolve => setTimeout(resolve, 200)); // Warte 200ms und prüfe erneut
        console.log("2nd Test for Translation for column_type:", columnTypeLabel);

    }

    console.warn("Translation not found after waiting.");
}

loadTranslations();


// add the card to the list of custom cards for the card picker
window.customCards = window.customCards || []; // Create the list if it doesn't exist.
window.customCards.push({
    type: "content-card-another-mvg-big",
    name: "AnotherMVG Departure Card (Big)",
    preview: false, // Optional - defaults to false
    description: "DE: Mit dieser Karte kann man sich die Abfahrtzeiten einer Station als einzelne Karte auf einer Seite anzeigen lassen. EN: This card allows you to display the departure times of a station as a standalone card on a page.",
    documentationURL: "https://github.com/Nisbo/another_mvg",
});
