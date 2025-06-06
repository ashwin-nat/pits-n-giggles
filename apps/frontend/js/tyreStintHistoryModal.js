// F1 Tyre Stint Chart Class
class TyreStintChart {
  constructor(container, options = {}, iconCache) {
    if (typeof container === 'string') {
      this.container = document.getElementById(container);
    } else if (container instanceof HTMLElement) {
      this.container = container;
    } else {
      throw new Error('Container must be a valid HTML element or element ID');
    }

    if (!this.container) {
      throw new Error('Container element not found');
    }

    // Validate required totalLaps parameter
    if (!options.totalLaps || typeof options.totalLaps !== 'number' || options.totalLaps <= 0) {
      throw new Error('totalLaps is required and must be a positive number');
    }

    this.options = {
      height: options.height || 30,
      gap: options.gap || 2,
      padding: options.padding || 15,
      totalLaps: options.totalLaps,
      trackName: options.trackName || '',
      airTemp: options.airTemp || '',
      trackTemp: options.trackTemp || '',
      isNewStyle: options.isNewStyle || false
    };

    this.iconCache = iconCache;
    this.tooltip = this.createTooltip();
    this.initializeChart();
  }

  // Static utility methods
  static processStintData(data) {
    if (!data || !Array.isArray(data)) {
      console.error('Invalid data format: data must be an array');
      return [];
    }

    const processedData = [];

    for (let i = 0; i < data.length; i++) {
      const driver = data[i];

      if (!driver || typeof driver !== 'object') {
        console.error('Invalid driver data format');
        continue;
      }

      if (!driver['tyre-stint-history'] || !Array.isArray(driver['tyre-stint-history'])) {
        console.error('Invalid tyre stint history for driver ' + (driver.name || 'unknown'));
        continue;
      }

      const processedStints = [];
      const stints = driver['tyre-stint-history'];

      for (let j = 0; j < stints.length; j++) {
        const stint = stints[j];

        if (!stint || typeof stint !== 'object') {
          console.error('Invalid stint data format');
          continue;
        }

        if (!stint['tyre-set-data'] || typeof stint['tyre-set-data'] !== 'object') {
          console.error('Invalid tyre set data format');
          continue;
        }

        processedStints.push(stint);
      }

      if (processedStints.length > 0) {
        const processedDriver = {};
        for (const key in driver) {
          if (driver.hasOwnProperty(key)) {
            processedDriver[key] = driver[key];
          }
        }
        processedDriver['tyre-stint-history'] = processedStints;
        processedData.push(processedDriver);
      }
    }

    return processedData;
  }

  static getTotalLaps(data) {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return 0;
    }

    let maxLap = 0;

    for (let i = 0; i < data.length; i++) {
      const driver = data[i];
      const stints = driver['tyre-stint-history'];

      if (stints && stints.length > 0) {
        const lastStint = stints[stints.length - 1];
        if (lastStint && typeof lastStint['end-lap'] === 'number') {
          maxLap = Math.max(maxLap, lastStint['end-lap']);
        }
      }
    }

    return maxLap;
  }

  static sortDriversByPosition(data) {
    if (!data || !Array.isArray(data)) {
      return [];
    }

    const sortedData = data.slice();

    return sortedData.sort(function(a, b) {
      if ('delta-to-leader' in a && 'delta-to-leader' in b) {
        return a['delta-to-leader'] - b['delta-to-leader'];
      }

      if ('driver-number' in a && 'driver-number' in b) {
        return a['driver-number'] - b['driver-number'];
      }

      const nameA = a.name || '';
      const nameB = b.name || '';
      return nameA.localeCompare(nameB);
    });
  }

  createTooltip() {
    const tooltip = document.createElement('div');
    tooltip.classList.add('f1-tsc-tooltip');
    tooltip.style.display = 'none';
    document.body.appendChild(tooltip);
    return tooltip;
  }

  initializeChart() {
    // Clear container
    while (this.container.firstChild) {
      this.container.removeChild(this.container.firstChild);
    }

    this.container.classList.add('f1-tsc-container');

    // Add track info header
    const header = document.createElement('div');
    header.classList.add('f1-tsc-header');

    const trackName = document.createElement('div');
    trackName.classList.add('f1-tsc-track-name');
    trackName.textContent = this.options.trackName.toUpperCase();
    header.appendChild(trackName);

    const info = document.createElement('div');
    info.classList.add('f1-tsc-info');

    // Track temperature
    const trackTemp = document.createElement('div');
    trackTemp.classList.add('f1-tsc-temp');
    const trackTempLabel = document.createElement('span');
    trackTempLabel.classList.add('f1-tsc-temp-label');
    trackTempLabel.textContent = 'TRACK';
    const trackTempValue = document.createElement('span');
    trackTempValue.classList.add('f1-tsc-temp-value');
    trackTempValue.textContent = this.options.trackTemp + '°C';
    trackTemp.appendChild(trackTempLabel);
    trackTemp.appendChild(trackTempValue);
    info.appendChild(trackTemp);

    // Air temperature
    const airTemp = document.createElement('div');
    airTemp.classList.add('f1-tsc-temp');
    const airTempLabel = document.createElement('span');
    airTempLabel.classList.add('f1-tsc-temp-label');
    airTempLabel.textContent = 'AIR';
    const airTempValue = document.createElement('span');
    airTempValue.classList.add('f1-tsc-temp-value');
    airTempValue.textContent = this.options.airTemp + '°C';
    airTemp.appendChild(airTempLabel);
    airTemp.appendChild(airTempValue);
    info.appendChild(airTemp);

    // Laps
    const laps = document.createElement('div');
    laps.classList.add('f1-tsc-laps');
    const lapsLabel = document.createElement('span');
    lapsLabel.classList.add('f1-tsc-temp-label');
    lapsLabel.textContent = 'LAPS';
    const lapsValue = document.createElement('span');
    lapsValue.classList.add('f1-tsc-temp-value');
    lapsValue.textContent = this.options.totalLaps.toString();
    laps.appendChild(lapsLabel);
    laps.appendChild(lapsValue);
    info.appendChild(laps);

    header.appendChild(info);
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
    const intervals = this.calculateLapIntervals(this.options.totalLaps);
    for (let i = 0; i < intervals.length; i++) {
      const lap = intervals[i];
      const marker = document.createElement('div');
      marker.classList.add('f1-tsc-lap-marker');
      // Use consistent calculation: (lap - 1) / totalLaps for both markers and stints
      marker.style.left = ((lap - 1) / this.options.totalLaps) * 100 + '%';
      marker.textContent = lap.toString();
      lapMarkers.appendChild(marker);
    }

    lapMarkersContainer.appendChild(lapMarkers);
    this.container.appendChild(lapMarkersContainer);

    // Container for driver rows
    this.chartContent = document.createElement('div');
    this.chartContent.classList.add('f1-tsc-content');
    this.container.appendChild(this.chartContent);
  }

  calculateLapIntervals(totalLaps) {
    const intervals = [];

    if (totalLaps <= 5) {
      // Interval of 1: show every lap
      for (let i = 1; i <= totalLaps; i++) {
        intervals.push(i);
      }
    } else if (totalLaps <= 25) {
      // Interval of 5: show 1, 5, 10, 15, 20, 25
      for (let lap = 1; lap <= totalLaps; lap += 5) {
        intervals.push(lap);
      }
      // Always include the last lap if it's not already included
      if (intervals[intervals.length - 1] !== totalLaps) {
        intervals.push(totalLaps);
      }
    } else {
      // Interval of 10: show 1, 10, 20, 30, etc.
      intervals.push(1); // Always start with lap 1
      for (let lap = 10; lap <= totalLaps; lap += 10) {
        intervals.push(lap);
      }
      // Always include the last lap if it's not already included
      if (intervals[intervals.length - 1] !== totalLaps) {
        intervals.push(totalLaps);
      }
    }

    return intervals;
  }

  updateChart(data) {
    if (!data || !Array.isArray(data)) {
      console.error('Invalid data provided');
      return;
    }

    // Clear existing content
    while (this.chartContent.firstChild) {
      this.chartContent.removeChild(this.chartContent.firstChild);
    }

    for (let i = 0; i < data.length; i++) {
      const driver = data[i];
      const row = this.createDriverRow(driver, i + 1);
      this.chartContent.appendChild(row);
    }
  }

  createDriverRow(driver, position) {
    const row = document.createElement('div');
    row.classList.add('f1-tsc-row');

    // Driver info
    const info = document.createElement('div');
    info.classList.add('f1-tsc-driver-info');

    const positionEl = document.createElement('div');
    positionEl.classList.add('f1-tsc-position');
    positionEl.textContent = position.toString();

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

      const changeText = document.createElement('span');
      if (posChange > 0) {
        changeEl.classList.add('gained');
        changeText.textContent = '▲ ' + posChange;
      } else if (posChange < 0) {
        changeEl.classList.add('lost');
        changeText.textContent = '▼ ' + Math.abs(posChange);
      } else {
        changeEl.classList.add('neutral');
        changeText.textContent = '― 0';
      }
      changeEl.appendChild(changeText);

      rightInfo.appendChild(changeEl);
    }

    if (this.options.isNewStyle) {
      const deltaEl = document.createElement('div');
      deltaEl.classList.add('f1-tsc-delta');
      const deltaTime = (driver['delta-to-leader'] / 1000).toFixed(3);
      deltaEl.textContent = position === 1 ? 'LEADER' : '+' + deltaTime;
      rightInfo.appendChild(deltaEl);
    }

    info.appendChild(positionEl);
    info.appendChild(driverEl);
    info.appendChild(rightInfo);

    // Stint visualization
    const stints = document.createElement('div');
    stints.classList.add('f1-tsc-stints');

    const stintHistory = driver['tyre-stint-history'];
    for (let i = 0; i < stintHistory.length; i++) {
      const stint = stintHistory[i];
      const stintEl = this.createStintElement(stint);
      stints.appendChild(stintEl);
    }

    // Check for DNF - calculate position based on last stint's end lap
    const lastStint = stintHistory[stintHistory.length - 1];
    if (lastStint && lastStint['end-lap'] < this.options.totalLaps) {
      const dnfMarker = document.createElement('div');
      dnfMarker.classList.add('f1-tsc-dnf');
      dnfMarker.style.left = ((lastStint['end-lap'] - 1) / this.options.totalLaps) * 100 + '%';
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
    stintEl.classList.add('f1-tsc-' + compound.toLowerCase().replace(/\s+/g, '-'));

    // FIXED: Use consistent calculation for both position and width
    // Position: where the stint starts (lap 1 = 0%, lap 2 = 1/totalLaps%, etc.)
    stintEl.style.left = ((startLap - 1) / this.options.totalLaps) * 100 + '%';

    // Width: how many laps the stint covers (FIXED: endLap - startLap, not +1)
    const stintLength = endLap - startLap;
    stintEl.style.width = (stintLength / this.options.totalLaps) * 100 + '%';

    // Add tyre icon and tooltip
    if (this.iconCache) {
      const svgElement = this.iconCache.getIcon(compound);
      if (svgElement) {
        const iconWrapper = document.createElement('div');
        iconWrapper.classList.add('f1-tsc-tyre-icon');
        iconWrapper.appendChild(svgElement.cloneNode(true));

        // Add tooltip events
        const self = this;
        iconWrapper.addEventListener('mouseover', function(e) {
          const tooltipContent = document.createElement('div');

          const compoundText = document.createElement('span');
          compoundText.textContent = compound + ' Tyre';
          tooltipContent.appendChild(compoundText);

          tooltipContent.appendChild(document.createElement('br'));

          const lapsText = document.createElement('span');
          lapsText.textContent = 'Laps: ' + startLap + ' - ' + endLap;
          tooltipContent.appendChild(lapsText);

          tooltipContent.appendChild(document.createElement('br'));

          const durationText = document.createElement('span');
          durationText.textContent = 'Duration: ' + (endLap - startLap + 1) + ' laps';
          tooltipContent.appendChild(durationText);

          while (self.tooltip.firstChild) {
            self.tooltip.removeChild(self.tooltip.firstChild);
          }
          self.tooltip.appendChild(tooltipContent);
          self.tooltip.style.display = 'block';
          self.updateTooltipPosition(e);
        });

        iconWrapper.addEventListener('mousemove', function(e) {
          self.updateTooltipPosition(e);
        });

        iconWrapper.addEventListener('mouseout', function() {
          self.tooltip.style.display = 'none';
        });

        stintEl.appendChild(iconWrapper);
      }
    } else {
      // Add hover tooltip even without icons
      const self = this;
      stintEl.addEventListener('mouseover', function(e) {
        const tooltipContent = document.createElement('div');

        const compoundText = document.createElement('span');
        compoundText.textContent = compound + ' Tyre';
        tooltipContent.appendChild(compoundText);

        tooltipContent.appendChild(document.createElement('br'));

        const lapsText = document.createElement('span');
        lapsText.textContent = 'Laps: ' + startLap + ' - ' + endLap;
        tooltipContent.appendChild(lapsText);

        tooltipContent.appendChild(document.createElement('br'));

        const durationText = document.createElement('span');
        durationText.textContent = 'Duration: ' + (endLap - startLap + 1) + ' laps';
        tooltipContent.appendChild(durationText);

        while (self.tooltip.firstChild) {
          self.tooltip.removeChild(self.tooltip.firstChild);
        }
        self.tooltip.appendChild(tooltipContent);
        self.tooltip.style.display = 'block';
        self.updateTooltipPosition(e);
      });

      stintEl.addEventListener('mousemove', function(e) {
        self.updateTooltipPosition(e);
      });

      stintEl.addEventListener('mouseout', function() {
        self.tooltip.style.display = 'none';
      });
    }

    return stintEl;
  }

  updateTooltipPosition(e) {
    const offset = 10;
    this.tooltip.style.left = (e.pageX + offset) + 'px';
    this.tooltip.style.top = (e.pageY + offset) + 'px';
  }

  // Keep the old method name for backward compatibility
  initTooltips() {
    // This method is no longer needed - tooltips are handled automatically
  }

  destroy() {
    if (this.tooltip && this.tooltip.parentNode) {
      this.tooltip.parentNode.removeChild(this.tooltip);
    }
  }
}
