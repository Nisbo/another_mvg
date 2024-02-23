class ContentAnotherMVG extends HTMLElement {
  // Whenever the state changes, a new `hass` object is set. Use this to
  // update your content.
  set hass(hass) {
    // Initialize the content if it's not there yet.
    if (!this.content) {
      const card    = document.createElement('ha-card');
      //card.header = "Another MVG Card";
      this.content  = document.createElement('div');
      const style   = document.createElement('style');

      style.textContent = `

        /* Card background */
        .mvg-card {
          background-color: #000080;
          border-radius: var(--ha-card-border-radius,12px);
        }

        /* Table Header - Linie, Ziel, Gleis, Abfahrt */
        .headline {
          display: flex;
          font-weight: bold;
          background-color: #FAE10C;
          color: #000080;
        }

        .content {
          padding: 5px 3px;
        }

        /* Column widths */
        .label {
          width: 15%;
          padding-left: 5px;
        }
        .destination {
          width: 45%;
        }
        .track {
          width: 15%;
        }
        .time {
          width: 25%;
        }

        /* Record row */
        .item {
          display: flex;
          padding-left: 4px;
        }

        /* Name of the card - from name parameter */
        .cardname {
          font-weight: bold;
          font-size:1.0em;
          padding: 2px 0 2px 8px;
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

        /* SBAHN */
        span.SBAHN {
          border-radius:1000px;
          border: 1px solid #FFFFFF;
        }
        span.S1  {background-color: #16BAE7;}
        span.S2  {background-color: #76B82A;}
        span.S3  {background-color: #951B81;}
        span.S4  {background-color: #E30613;}
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

    let html = `
      <div class="mvg-card">
        ${!state.attributes.config.hide_name ? `<div class="cardname">${state.attributes.config.name}</div>` : ""}
        <div class="headline">
          <div class="label">Linie</div>
          <div class="destination">Ziel</div>
          <div class="track">Gleis</div>
          <div class="time">Abfahrt</div>
        </div>
        <div class="content">
      `;
    this.data = state.attributes.departures;
    this.data.forEach((departure) => {
      html += `<div class="item">`;
      html += `<div class="label"><span class="line ${departure.transport_type} ${departure.label}" > ${departure.label}</span></div>`;
      html += `<div class="destination">${departure.destination}</div>`;
      html += `<div class="track">${departure.track}</div>`;
      let delay = ``;
      if (departure.cancelled) {
        delay = `<span class="cancelled">Entfällt</span>`;
      } else if(departure.delay > 0) {
        delay = `<span class="delay"> +${departure.delay}</span> <span class="expected">(${departure.expected_departure})</span>`;
      }
      html += `<div class="time">${departure.planned_departure} ${delay ? delay: ""}</div>`;
      html += `</div>`;
    });
    html += `</div></div>`;

    this.content.innerHTML = html;

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


