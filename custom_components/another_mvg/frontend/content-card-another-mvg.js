class ContentAnotherMVG extends HTMLElement {
  // Whenever the state changes, a new `hass` object is set. Use this to
  // update your content.
  set hass(hass) {
    // Initialize the content if it's not there yet.
    if (!this.content) {
      const card    = document.createElement('ha-card');
      this.content  = document.createElement('div');
      const style   = document.createElement('style');

      style.textContent = `

        /* Card background */
        .amvg-container {
          background-color: #000080;
          border-radius: var(--ha-card-border-radius,12px);
          padding-bottom: 5px;
        }
        /* Name of the card - from name parameter */
        .amvg-cardname {
          font-weight: bold;
          font-size:1.0em;
          padding: 2px 0 2px 8px;
          color: #FFFFFF;
        }
        /* Table */
        .amvg-table {
          width: 100%;
          border-collapse:collapse;
        }

        /* Table Header - Linie, Ziel, Gleis, Abfahrt */
        .amvg-headline {
          font-weight: bold;
          background-color: #FAE10C;
          color: #000080;
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
          color: #FFFFFF;
        }
        .track {
          padding: 0 5px;
          width: fit-content;
          color: #FFFFFF;
        }
        .time {
          padding-right: 5px;
          width: fit-content;
          white-space: nowrap;
          color: #FFFFFF;
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

		let html = `
		<div class="amvg-container">
		  ${!state.attributes.config.hide_name ? `<div class="amvg-cardname">${state.attributes.config.name}${state.attributes.dataOutdated !== undefined ? ` ${state.attributes.dataOutdated}` : " (loading)"}<span class="currentTime" style="float: right; margin-right: 5px;">${state.attributes.config.show_clock ? ` ${getCurrentTime()} ` : ""}</span></div>` : ""}
		  <table class="amvg-table">
			<tr class="amvg-headline">
			  <th class="labelHL">Linie</th>
			  <th class="destinationHL">Ziel</th>
			  <th class="trackHL">Gleis</th>
			  <th class="timeHL">Abfahrt</th>
			</tr>
		  `;

		this.data = state.attributes.departures;
		if (!this.data || this.data === "undefined") {
			  html += `<tr class="item">`;
			  html += `<td class="label">XX</td>`;
			  html += `<td class="destination">Addon is loading.</td>`;
			  html += `<td class="track">-</td>`;
			  html += `<td class="time">-</td>`;
			  html += `</tr>`;
		} else {
			this.data.forEach((departure) => {
			  html += `<tr class="item">`;
			  html += `<td class="label"><span class="line ${departure.transport_type} ${departure.label}">${departure.trainType}${departure.label}</span></td>`;
			  html += `<td class="destination">${departure.destination}</td>`;
			  html += `<td class="track">${departure.track}</td>`;
			  
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

			  html += `<td class="time">${timeDisplay}</td>`;
			  html += `</tr>`;
			});
		}

		html += `</table></div>`; 
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
}

customElements.define("content-card-another-mvg", ContentAnotherMVG);
