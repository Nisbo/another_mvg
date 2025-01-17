class ContentAnotherMVGlivemap extends HTMLElement {
  set hass(hass) {
    if (!this.content) {
      const card = document.createElement('ha-card');
      card.style.display = "flex";
      card.style.flexDirection = "column";
      card.style.height = "100%";
      card.style.overflow = "hidden";

      this.content = document.createElement('div');
      this.content.style.flex = "1";
      this.content.style.display = "flex";
      this.content.style.alignItems = "stretch";

      card.appendChild(this.content);
      this.appendChild(card);

      this.updateIframe();
    }
  }

  setConfig(config) {
    this.config = {
      x: config.x || 2750799,
      y: config.y || 1560004,
      zoom: config.zoom || 4.8,
      mode: config.mode || "schematic",
      ...config,
    };
    this.updateIframe();
  }

  updateIframe() {
    if (!this.content) return;

    const { x, y, zoom, mode } = this.config;
    const url = `https://s-bahn-muenchen-live.de/?mode=${mode}&showDepartures=true&x=${x}&y=${y}&z=${zoom}`;

    this.content.innerHTML = `
      <iframe 
        style="flex: 1; width: 100%; height: 100%; border: none;"
        src="${url}" 
        title="LiveMap">
      </iframe>
    `;
  }

  getCardSize() {
    return 26;
  }

  static getConfigElement() {
    return document.createElement('content-another-mvg-livemap-editor');
  }
}

class ContentAnotherMVGlivemapEditor extends HTMLElement {
  constructor() {
    super();
    this.config = {};
  }

  setConfig(config) {
    this.config = config;
    this.render();
  }

  render() {
    this.innerHTML = ''; // Reset inner HTML

    const container = document.createElement('div');
    container.style.display = "flex";
    container.style.flexDirection = "column";

    // Add a description at the top of the editor
    const description = document.createElement('p');
    description.innerHTML = `Alle 4 Werte hängen voneinander ab. Am besten öffnet man die <a href="https://s-bahn-muenchen-live.de/?mode=schematic&showDepartures=true&x=2657030&y=1727560&z=5.02" target="_blank" style="color: #1a73e8; text-decoration: none;">LiveMap (klick)</a> im Browser (PC) und übernimmt die Werte aus der Adresszeile, sobald der gewünschte Zoom eingestellt ist.`;
    description.style.fontSize = "14px";
    description.style.marginBottom = "15px";
    container.appendChild(description);

    // Define input fields with descriptions
    const fields = [
      { name: 'x',    label: 'X - Koordinate',    type: 'number', defaultValue: 2750799, description: 'Je kleiner die Zahl, desto weiter wandert der Mittelpunkt der Ansicht nach links.' },
      { name: 'y',    label: 'Y - Koordinate',    type: 'number', defaultValue: 1560004, description: 'Je kleiner die Zahl, desto weiter wandert der Mittelpunkt der Ansicht nach unten.' },
      { name: 'zoom', label: 'Zoom',              type: 'number', defaultValue: 4.8, step: 0.01, description: 'Größerer Wert bedeutet weiter rangezoomt.' },
      { name: 'mode', label: 'Kartenhintergrund', type: 'dropdown', options: ['schematic', 'topographic'], defaultValue: 'schematic', description: 'Der Hintgergrund der LiveMap: schematic (MVG-Plan) oder topographic (Karte).' },
    ];

    fields.forEach(field => {
      // Create the input element
      let inputElement;
      if (field.type === 'dropdown') {
        inputElement = document.createElement('ha-select');
        field.options.forEach(option => {
          const optionElement = document.createElement('mwc-list-item');
          optionElement.value = option;
          optionElement.innerText = option;
          inputElement.appendChild(optionElement);
        });
        inputElement.value = this.config.mode || field.defaultValue;
      } else {
        inputElement = document.createElement('ha-textfield');
        inputElement.type = field.type;
        inputElement.step = field.step || "1";
        inputElement.value = this.config[field.name] || field.defaultValue;
      }

      inputElement.label = field.label;
      inputElement.configValue = field.name;

      // Event listener to update config on change
      inputElement.addEventListener('change', (event) => {
        const target = event.target;
        this.config = {
          ...this.config,
          [target.configValue]: target.value
        };
        this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: this.config } }));
      });

      // Create description element
      const description = document.createElement('span');
      description.innerText = field.description;
      description.style.fontSize = "12px";
      description.style.color = "#888";
      description.style.marginBottom = "6px";

      // Append elements
      container.appendChild(inputElement);
      container.appendChild(description); // Add description below input
    });

    this.appendChild(container);
  }
}

customElements.define("content-card-another-mvg-livemap", ContentAnotherMVGlivemap);
customElements.define("content-another-mvg-livemap-editor", ContentAnotherMVGlivemapEditor);

// add the card to the list of custom cards for the card picker
window.customCards = window.customCards || []; // Create the list if it doesn't exist.
window.customCards.push({
	type: "content-card-another-mvg-livemap",
	name: "AnotherMVG LiveMap",
	preview: false, // Optional - defaults to false
	description: "Mit dieser Karte kann die MVG Live Map eingebunden werden. Sie ist für die Anzeige einer Karte pro Seite gedacht, funktioniert jedoch auch in Kombination mit anderen Karten. In diesem Fall ist die Anzeige jedoch eingeschränkt, besonders wenn Meldungen vorliegen.",
});
