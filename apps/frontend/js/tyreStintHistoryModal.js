class TyreStintHistoryChart {
    constructor(container, tyreStintHistoryData, trackName, trackTemp, airTemp, numLaps) {
      this.container = container;
      this.tyreStintHistoryData = tyreStintHistoryData;
      this.trackName = trackName;
      this.trackTemp = trackTemp;
      this.airTemp = airTemp;
      this.numLaps = numLaps;
    }

    draw() {
      const container = this.createContainer();
      container.appendChild(this.createHeader());
      container.appendChild(this.createLapIndicators());
      container.appendChild(this.createStandingsList());
      this.container.appendChild(container);
    }

    createContainer() {
      const container = document.createElement('div');
      container.className = 'f1-standings-container';
      container.style.height = '100%';
      container.style.overflow = 'hidden';
      return container;
    }

    createHeader() {
      const header = document.createElement('div');
      header.className = 'f1-header';

      const trackName = document.createElement('h1');
      trackName.className = 'f1-track-name';
      trackName.textContent = this.trackName;

      const raceInfo = document.createElement('div');
      raceInfo.className = 'f1-race-info';
      raceInfo.appendChild(this.createInfoBox(`${this.trackTemp}°C`, 'TRACK'));
      raceInfo.appendChild(this.createInfoBox(`${this.airTemp}°C`, 'AIR'));
      raceInfo.appendChild(this.createInfoBox(this.numLaps.toString(), 'LAPS'));

      header.appendChild(trackName);
      header.appendChild(raceInfo);
      return header;
    }

    createInfoBox(value, label) {
      const infoBox = document.createElement('div');
      infoBox.className = 'f1-info-box';

      const valueSpan = document.createElement('span');
      valueSpan.className = label === 'LAPS' ? 'f1-laps' : 'f1-temp';
      valueSpan.textContent = value;

      const labelSpan = document.createElement('span');
      labelSpan.className = 'f1-label';
      labelSpan.textContent = label;

      infoBox.appendChild(valueSpan);
      infoBox.appendChild(labelSpan);
      return infoBox;
    }

    createLapIndicators() {
      const container = document.createElement('div');
      container.className = 'f1-lap-indicators';

      // Create dynamic lap markers based on total laps
      const numMarkers = 6;
      const interval = Math.ceil(this.numLaps / (numMarkers - 1));
      const laps = Array.from({ length: numMarkers }, (_, i) =>
        i === numMarkers - 1 ? this.numLaps : 1 + i * interval
      );

      laps.forEach(lap => {
        const lapNumber = document.createElement('span');
        lapNumber.className = 'f1-lap-number';
        lapNumber.textContent = lap;
        container.appendChild(lapNumber);
      });

      return container;
    }

    createStandingsList() {
      const container = document.createElement('div');
      container.className = 'f1-standings-list';

      this.tyreStintHistoryData.forEach((driver, index) => {
        container.appendChild(this.createDriverRow(driver, index));
      });

      return container;
    }

    createDriverRow(driver, index) {
      const row = document.createElement('div');
      row.className = 'f1-driver-row';

      const driverInfo = this.createDriverInfo(driver, index);
      const stintTimeline = this.createStintTimeline(driver);

      row.appendChild(driverInfo);
      row.appendChild(stintTimeline);
      return row;
    }

    createDriverInfo(driver, index) {
      const container = document.createElement('div');
      container.className = 'f1-driver-info';

      const position = document.createElement('span');
      position.className = 'f1-position';
      position.textContent = index + 1;

      const number = document.createElement('span');
      number.className = 'f1-driver-number';
      number.textContent = driver['driver-number'];

      const name = document.createElement('span');
      name.className = 'f1-driver-name';
      name.textContent = driver.name;

      const team = document.createElement('span');
      team.className = 'f1-team';
      team.textContent = driver.team;

      const delta = document.createElement('span');
      delta.className = `f1-delta ${driver['delta-to-leader'] >= 0 ? 'positive' : 'negative'}`;
      const positionChange = driver['delta-to-leader'] !== 0
        ? (driver['delta-to-leader'] >= 0 ? '↑' : '↓')
        : '';
      delta.textContent = `${positionChange} ${Math.abs(driver['delta-to-leader'])}`;

      [position, number, name, team, delta].forEach(el => container.appendChild(el));
      return container;
    }

    createStintTimeline(tyreStintHistory) {
      const timeline = document.createElement('div');
      timeline.className = 'f1-stint-timeline';

      tyreStintHistory["tyre-stint-history"].forEach(stint => {
        const stintElement = this.createStintElement(stint);
        timeline.appendChild(stintElement);
      });

      return timeline;
    }

    createStintElement(stint) {
      const stintElement = document.createElement('div');
      stintElement.className = `f1-tyre-stint ${this.getTyreClass(stint['tyre-set-data']['visual-tyre-compound'])}`;

      const width = ((stint['end-lap'] - stint['start-lap'] + 1) / this.numLaps) * 100;
      const left = ((stint['start-lap'] - 1) / this.numLaps) * 100;

      stintElement.style.width = `${width}%`;
      stintElement.style.left = `${left}%`;

      const tyreIcon = document.createElement('img');
      tyreIcon.className = 'f1-tyre-icon';
      tyreIcon.src = this.getTyreIcon(stint['tyre-set-data']['visual-tyre-compound']);
      tyreIcon.alt = stint['tyre-set-data']['visual-tyre-compound'];

      stintElement.appendChild(tyreIcon);
      return stintElement;
    }

    getTyreClass(compound) {
      const tyreClasses = {
        'Soft': 'tyre-soft',
        'Medium': 'tyre-medium',
        'Hard': 'tyre-hard',
        'Intermediate': 'tyre-intermediate',
        'Wet': 'tyre-wet'
      };
      return tyreClasses[compound] || '';
    }

    getTyreIcon(compound) {
      const tyreIcons = {
        'Soft': '/tyre-icons/soft.svg',
        'Medium': '/tyre-icons/medium.svg',
        'Hard': '/tyre-icons/hard.svg',
        'Intermediate': '/tyre-icons/intermediate.svg',
        'Wet': '/tyre-icons/wet.svg'
      };
      return tyreIcons[compound] || '';
    }
  }