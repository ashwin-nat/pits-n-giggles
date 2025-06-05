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
      trackTemp: options.trackTemp || '',
      isNewStyle: options.isNewStyle || false
    };

    this.iconCache = iconCache;
    console.log('Creating tooltip...');
    this.tooltip = this.createTooltip();
    this.initializeChart();
  }

  createTooltip() {
    const tooltip = document.createElement('div');
    tooltip.classList.add('f1-tsc-tooltip');
    tooltip.style.display = 'none';
    document.body.appendChild(tooltip);
    console.log('Tooltip created and added to body');
    return tooltip;
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
          <span class="f1-tsc-temp-label">LAPS</span>
          <span class="f1-tsc-temp-value">${this.options.maxLaps}</span>
        </div>
      </div>
    `;
    this.container.appendChild(header);

    // Add lap markers with axis label
    const lapMarkersContainer = document.createElement('div');
    lapMarkersContainer.classList.add('f1-tsc-lap-markers-container');

    const axisLabel = document.createElement('div');
    axisLabel.classList.add('f1-tsc-axis-label');
    axisLabel.textContent = 'LAP NUMBER';
    lapMarkersContainer.appendChild(axisLabel);

    const lapMarkers = document.createElement('div');
    lapMarkers.classList.add('f1-tsc-lap-markers');

    // Calculate lap intervals based on total laps
    const intervals = this.calculateLapIntervals(this.options.maxLaps);
    intervals.forEach(lap => {
      const marker = document.createElement('div');
      marker.classList.add('f1-tsc-lap-marker');
      marker.style.left = `${((lap - 1) / (this.options.maxLaps)) * 100}%`;
      marker.textContent = lap;
      lapMarkers.appendChild(marker);
    });

    lapMarkersContainer.appendChild(lapMarkers);
    this.container.appendChild(lapMarkersContainer);

    // Container for driver rows
    this.chartContent = document.createElement('div');
    this.chartContent.classList.add('f1-tsc-content');
    this.container.appendChild(this.chartContent);
  }

  calculateLapIntervals(totalLaps) {
    if (totalLaps <= 5) {
      return Array.from({length: totalLaps}, (_, i) => i + 1);
    } else if (totalLaps < 40) {
      const step = Math.ceil(totalLaps / 4);
      const intervals = [];
      for (let lap = 1; lap <= totalLaps; lap += step) {
        intervals.push(lap);
      }
      if (!intervals.includes(totalLaps)) {
        intervals.push(totalLaps);
      }
      return intervals;
    } else {
      const intervals = [];
      for (let lap = 10; lap <= totalLaps; lap += 10) {
        intervals.push(lap);
      }
      return intervals;
    }
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

    const teamEl = document.createElement('div');
    teamEl.classList.add('f1-tsc-team');
    teamEl.textContent = driver.team;

    driverEl.appendChild(nameEl);
    driverEl.appendChild(teamEl);

    const rightInfo = document.createElement('div');
    rightInfo.classList.add('f1-tsc-right-info');

    // Position change with chevron
    if (driver.position && driver['grid-position']) {
      const posChange = driver['grid-position'] - driver.position;
      const changeEl = document.createElement('div');
      changeEl.classList.add('f1-tsc-position-text');

      if (posChange > 0) {
        changeEl.classList.add('gained');
        changeEl.innerHTML = `▲ ${posChange}`;
      } else if (posChange < 0) {
        changeEl.classList.add('lost');
        changeEl.innerHTML = `▼ ${Math.abs(posChange)}`;
      } else {
        changeEl.classList.add('neutral');
        changeEl.innerHTML = `― 0`;
      }

      rightInfo.appendChild(changeEl);
    }

    if (this.options.isNewStyle) {
      const deltaEl = document.createElement('div');
      deltaEl.classList.add('f1-tsc-delta');
      const deltaTime = (driver['delta-to-leader'] / 1000).toFixed(3);
      deltaEl.textContent = position === 1 ? 'LEADER' : `+${deltaTime}`;
      rightInfo.appendChild(deltaEl);
    }

    info.appendChild(positionEl);
    info.appendChild(driverEl);
    info.appendChild(rightInfo);

    // Stint visualization
    const stints = document.createElement('div');
    stints.classList.add('f1-tsc-stints');

    let dnfMarkerLeftPosition = 0.0;
    driver['tyre-stint-history'].forEach(stint => {
      const stintEl = this.createStintElement(stint);
      dnfMarkerLeftPosition += stintEl.style.width;
      stints.appendChild(stintEl);
    });

    // Check for DNF
    const lastStint = driver['tyre-stint-history'][driver['tyre-stint-history'].length - 1];
    if (lastStint && lastStint['end-lap'] < this.options.maxLaps) {
      const dnfMarker = document.createElement('div');
      dnfMarker.classList.add('f1-tsc-dnf');
      dnfMarker.style.left = dnfMarkerLeftPosition;
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
    stintEl.style.left = `${((startLap - 1) / (this.options.maxLaps)) * 100}%`;
    stintEl.style.width = `${((endLap - startLap) / (this.options.maxLaps)) * 100}%`;

    // Add tyre icon and tooltip
    if (this.iconCache) {
      const svgElement = this.iconCache.getIcon(compound);
      if (svgElement) {
        const iconWrapper = document.createElement('div');
        iconWrapper.classList.add('f1-tsc-tyre-icon');
        iconWrapper.appendChild(svgElement.cloneNode(true));

        // Add tooltip events
        iconWrapper.addEventListener('mouseover', (e) => {
          const tooltipContent = `
            ${compound} Tyre<br>
            Laps: ${startLap} - ${endLap}<br>
            Duration: ${endLap - startLap + 1} laps
          `;
          this.tooltip.innerHTML = tooltipContent;
          this.tooltip.style.display = 'block';
          this.updateTooltipPosition(e);
        });

        iconWrapper.addEventListener('mousemove', (e) => {
          this.updateTooltipPosition(e);
        });

        iconWrapper.addEventListener('mouseout', () => {
          this.tooltip.style.display = 'none';
        });

        stintEl.appendChild(iconWrapper);
      }
    }

    return stintEl;
  }

  updateTooltipPosition(e) {
    const offset = 10;
    this.tooltip.style.left = `${e.pageX + offset}px`;
    this.tooltip.style.top = `${e.pageY + offset}px`;
  }
}
