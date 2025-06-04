// F1 Tyre Stint Chart Class
class TyreStintChart {
  constructor(container, options = {}, iconCache) {
    if (!(container instanceof HTMLElement)) {
      console.error('Container must be a valid HTML element');
      return;
    }

    this.container = container;
    this.options = {
      height: options.height || 30,
      gap: options.gap || 2,
      padding: options.padding || 15,
      maxLaps: options.totalLaps || 0,
      trackName: options.trackName || '',
      airTemp: options.airTemp || '',
      trackTemp: options.trackTemp || ''
    };

    this.iconCache = iconCache;
    this.initializeChart();
  }

  initializeChart() {
    this.container.innerHTML = '';
    this.container.classList.add('f1-tsc-container');

    // Add track info header
    const header = document.createElement('div');
    header.classList.add('f1-tsc-header');
    header.innerHTML = `
      <div class="f1-tsc-track-name">${this.options.trackName.toUpperCase()}</div>
      <div class="f1-tsc-info">
        <div class="f1-tsc-temp">
          <span class="f1-tsc-temp-label">TRACK</span>
          <span class="f1-tsc-temp-value">${this.options.trackTemp}°C</span>
        </div>
        <div class="f1-tsc-temp">
          <span class="f1-tsc-temp-label">AIR</span>
          <span class="f1-tsc-temp-value">${this.options.airTemp}°C</span>
        </div>
        <div class="f1-tsc-laps">
          <span class="f1-tsc-temp-value">${this.options.maxLaps}</span>
          <span class="f1-tsc-temp-label">LAPS</span>
        </div>
      </div>
    `;
    this.container.appendChild(header);

    // Add lap markers
    const lapMarkers = document.createElement('div');
    lapMarkers.classList.add('f1-tsc-lap-markers');
    const intervals = [1, 5, 10, 15, 20, 25];
    intervals.forEach(lap => {
      const marker = document.createElement('div');
      marker.classList.add('f1-tsc-lap-marker');
      marker.style.left = `${(lap / this.options.maxLaps) * 100}%`;
      marker.textContent = lap;
      lapMarkers.appendChild(marker);
    });
    this.container.appendChild(lapMarkers);

    // Container for driver rows
    this.chartContent = document.createElement('div');
    this.chartContent.classList.add('f1-tsc-content');
    this.container.appendChild(this.chartContent);
  }

  updateChart(data) {
    if (!data || !Array.isArray(data)) {
      console.error('Invalid data provided');
      return;
    }

    this.chartContent.innerHTML = '';
    data.forEach((driver, index) => {
      const row = this.createDriverRow(driver, index + 1);
      this.chartContent.appendChild(row);
    });
  }

  createDriverRow(driver, position) {
    const row = document.createElement('div');
    row.classList.add('f1-tsc-row');

    // Driver info
    const info = document.createElement('div');
    info.classList.add('f1-tsc-driver-info');

    const positionEl = document.createElement('div');
    positionEl.classList.add('f1-tsc-position');
    positionEl.textContent = position;

    const driverEl = document.createElement('div');
    driverEl.classList.add('f1-tsc-driver');

    const nameEl = document.createElement('div');
    nameEl.classList.add('f1-tsc-name');
    nameEl.textContent = driver.name;

    const deltaEl = document.createElement('div');
    deltaEl.classList.add('f1-tsc-delta');
    const deltaTime = (driver['delta-to-leader'] / 1000).toFixed(3);
    deltaEl.textContent = position === 1 ? 'LEADER' : `+${deltaTime}`;

    driverEl.appendChild(nameEl);
    driverEl.appendChild(deltaEl);
    info.appendChild(positionEl);
    info.appendChild(driverEl);

    // Stint visualization
    const stints = document.createElement('div');
    stints.classList.add('f1-tsc-stints');

    driver['tyre-stint-history'].forEach(stint => {
      const stintEl = this.createStintElement(stint);
      stints.appendChild(stintEl);
    });

    // Check for DNF
    const lastStint = driver['tyre-stint-history'][driver['tyre-stint-history'].length - 1];
    if (lastStint && lastStint['end-lap'] < this.options.maxLaps) {
      const dnfMarker = document.createElement('div');
      dnfMarker.classList.add('f1-tsc-dnf');
      dnfMarker.style.left = `${(lastStint['end-lap'] / this.options.maxLaps) * 100}%`;
      stints.appendChild(dnfMarker);
    }

    row.appendChild(info);
    row.appendChild(stints);
    return row;
  }

  createStintElement(stint) {
    const tyreSet = stint['tyre-set-data'];
    const compound = tyreSet['visual-tyre-compound'];
    const startLap = stint['start-lap'];
    const endLap = stint['end-lap'];

    const stintEl = document.createElement('div');
    stintEl.classList.add('f1-tsc-stint');
    stintEl.classList.add(`f1-tsc-${compound.toLowerCase().replace(/\s+/g, '-')}`);
    stintEl.style.left = `${(startLap / this.options.maxLaps) * 100}%`;
    stintEl.style.width = `${((endLap - startLap) / this.options.maxLaps) * 100}%`;

    // Add tyre icon using the iconCache class
    if (this.iconCache) {
      const svgElement = this.iconCache.getIcon(compound);
      if (svgElement) {
        const iconWrapper = document.createElement('div');
        iconWrapper.classList.add('f1-tsc-tyre-icon');
        iconWrapper.appendChild(svgElement.cloneNode(true));
        stintEl.appendChild(iconWrapper);
      }
    }

    return stintEl;
  }
}
