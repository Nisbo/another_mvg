class ContentAnotherMVGbig extends HTMLElement {
  // Whenever the state changes, a new `hass` object is set. Use this to
  // update your content.
  set hass(hass) {
    // Initialize the content if it's not there yet.
    if (!this.content) {
      const card    = document.createElement('ha-card');
      this.content  = document.createElement('div');
      const style   = document.createElement('style');

      style.textContent = `
         table {
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
      card.appendChild(style);
      card.appendChild(this.content);
      this.appendChild(card);
    }

    const entityId = this.config.entity;
    const state    = hass.states[entityId];
    const stateStr = state ? state.state : "unavailable";
	const departureFormat = state && state.attributes && state.attributes.config && 
    ["1", "2", "3"].includes(state.attributes.config.departure_format ?? "") 
    ? state.attributes.config.departure_format 
    : "1";

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

		let html = `<table><tr><td colspan="4" class="amvg-cardname">${state.attributes.config.name}${state.attributes.dataOutdated !== undefined ? ` ${state.attributes.dataOutdated}` : " (loading)"}<span class="currentTime" style="float: right; margin-right: 5px;">${state.attributes.config.show_clock ? ` ${getCurrentTime()} ` : ""}</span></td></tr>
							  <tr>
								<td class="amvg-headline">Linie</td>
								<td class="amvg-headline">Ziel</td>
								<td class="amvg-headline">Gleis</td>
								<td class="amvg-headline">Abfahrt</td>
							  </tr>
		  `;

		this.data = state.attributes.departures;
		if (!this.data || this.data === "undefined") {
			  html += `<tr>`;
			  html += `<td class="departureline">XX</td>`;
			  html += `<td class="departureline">Addon is loading.</td>`;
			  html += `<td class="departureline">-</td>`;
			  html += `<td class="departureline">-</td>`;
			  html += `</tr>`;
		} else {
			this.data.forEach((departure) => {
			  html += `<tr>`;
			  html += `<td class="departureline"><span class="line ${departure.transport_type} ${departure.label}">${departure.trainType}${departure.label}</span></td>`;
			  html += `<td class="departureline">${departure.destination}</td>`;
			  html += `<td class="departureline">${departure.track}</td>`;
			  
			  let timeDisplay = "";
			  
			  if (departureFormat === "1") {
				timeDisplay = departure.planned_departure;

				if (departure.cancelled) {
				  timeDisplay += ` <span class="cancelled">Entfällt</span>`;
				} else if (departure.delay > 0) {
				  timeDisplay += ` <span class="delay">+${departure.delay}</span> (${departure.expected_departure})`;
				}
				
			  } else if (departureFormat === "2") {
				timeDisplay = departure.planned_departure;

				if (departure.cancelled) {
				  timeDisplay += ` <span class="cancelled">Entfällt</span>`;
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
				  timeDisplay += ` <span class="cancelled">Entfällt</span>`;
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

  setConfig(config) {
    this.config = { ...config };
    this.render();
  }

  render() {
    this.innerHTML = ''; // Reset inner HTML

    const container = document.createElement('div');
    container.style.display = "flex";
    container.style.flexDirection = "column";

    // Beschreibung hinzufügen
    const description = document.createElement('p');
    description.innerHTML = `Bitte wählen Sie eine Haltestelle aus der Liste aus.<br /><br />Es werden nur Haltestellen angezeigt, die Sie erstellt haben. Wenn hier keine Einträge angezeigt werden, haben Sie noch keine Haltestelle erstellt oder alle Haltestellen wurden gelöscht.<br /><br />Um eine Haltestelle zu erstellen, gehen Sie zu<br /><b>"Einstellungen"</b> &rarr; <b>"Geräte & Dienste"</b>, klicken Sie auf <b>"INTEGRATION HINZUFÜGEN"</b>, suchen Sie nach <b>"Another MVG"</b> und folgen Sie den Anweisungen.`;
    description.style.fontSize = "14px";
    description.style.marginBottom = "15px";
    container.appendChild(description);

    // Dropdown for entities
    const entitySelect = document.createElement('ha-select');
    entitySelect.label = "Wählen Sie eine Haltestelle";
    entitySelect.value = this.config.entity || "";
    entitySelect.addEventListener('change', (event) => {
      const selectedEntity = event.target.value;
      this.config = {
        ...this.config,
        entity: selectedEntity
      };
      this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
    });

    // get entities from hass
    const entities = Object.values(this.hass.states)
      .filter(entity => entity.entity_id && this.isAnotherMvgEntity(entity))  // only entities for 'another_mvg'

    // sort by friendly_name
    entities.sort((a, b) => {
      const nameA = a.attributes.friendly_name || a.entity_id;
      const nameB = b.attributes.friendly_name || b.entity_id;
      return nameA.localeCompare(nameB);
    });

    // add entities to dropdown
    entities.forEach(entity => {
      const option = document.createElement('mwc-list-item');
      option.value = entity.entity_id;
      option.innerText = entity.attributes.friendly_name || entity.entity_id;
      entitySelect.appendChild(option);
    });

    // if no entity is set (adding a card) select the 1st entity
    if (!this.config.entity && entities.length > 0) {
      this.config.entity = entities[0].entity_id;
      entitySelect.value = this.config.entity; // Select Dropdown
      this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
    }

    // add dropdown to container
    container.appendChild(entitySelect);

    this.appendChild(container);
  }

  // Try to find only entities for 'another_mvg' assuming departures is only defined for 'another_mvg'
  isAnotherMvgEntity(entity) {
    return entity.attributes && entity.attributes.departures !== undefined;
  }
}

customElements.define("content-card-another-mvg-big", ContentAnotherMVGbig);
customElements.define("content-card-another-mvg-editor-big", ContentAnotherMVGEditorBig);

// add the card to the list of custom cards for the card picker
window.customCards = window.customCards || []; // Create the list if it doesn't exist.
window.customCards.push({
    type: "content-card-another-mvg-big",
    name: "AnotherMVG Departure Card (Big)",
    preview: false, // Optional - defaults to false
    description: "Mit dieser Karte kann man sich die Abfahrtzeiten einer Station als einzelne Karte auf einer Seite anzeigen lassen.",
    documentationURL: "https://github.com/Nisbo/another_mvg",
});
