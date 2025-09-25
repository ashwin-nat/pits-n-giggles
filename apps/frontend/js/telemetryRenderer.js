class TelemetryRenderer {
  constructor(iconCache) {
    this.timeTrialDataPopulator = new TimeTrialDataPopulator();
    this.splashDiv = document.getElementById('splash-div');
    this.raceTableDiv = document.getElementById('race-table-div');
    this.timeTrialDiv = document.getElementById('time-trial-div');
    this.telemetryTable = document.getElementById('telemetry-data');
    this.weatherWidget = new WeatherWidget(document.getElementById('weather-predictions'));
    this.fastestLapTimeSpan = document.getElementById('fastestLapTimeSpan');
    this.fastestLapNameSpan = document.getElementById('fastestLapNameSpan');
    this.fastestLapTyreSpan = document.getElementById('fastestLapTyreSpan');
    this.trackName = document.getElementById('track-name');
    this.pitLaneSpeedLimit = document.getElementById('pit-speed-limit');
    this.trackTempSpan = document.getElementById('track-temp');
    this.airTempSpan = document.getElementById('air-temp');
    this.indexByPosition = null;
    this.iconCache = iconCache;
    this.uiMode = 'Splash';

    this.connected = null;
    this.statusContainer   = document.getElementById('status-wrapper')
    this.blinkingDot       = document.createElement('span')
    this.statusText        = document.createElement('p')

    this.blinkingDot.classList.add('blinking-dot')
    this.statusContainer.append(this.blinkingDot, this.statusText)
  }

  renderTelemetryRow(data, packetFormat, isLiveDataMode, raceEnded, spectatorIndex, sessionType) {
    const { 'driver-info': driverInfo } = data;
    const row = document.createElement('tr');

    // Populate row with data
    new RaceTableRowPopulator(row, data, packetFormat, isLiveDataMode, this.iconCache, raceEnded, spectatorIndex,
                                    sessionType).populate();

    // Apply CSS classes based on row state
    const cssClasses = this.determineRowClasses(driverInfo, isLiveDataMode, spectatorIndex);
    row.classList.add(...cssClasses);

    return row;
  }

  determineRowClasses(driverInfo, isLiveDataMode, spectatorIndex) {
    const classes = [];

    if ((spectatorIndex !== null && driverInfo['index'] === spectatorIndex) ||
        (spectatorIndex === null && driverInfo['is-player'])) {
      classes.push('player-row');
    }

    if (driverInfo['dnf-status'] === 'DNF') {
      classes.push('dnf-row');
    }

    else if (isLiveDataMode && driverInfo['drs']) {
      classes.push('drs-row');
    }

    return classes;
  }

  updateDashboard(incomingData) {

    const sessionType = incomingData["session-type"];
    switch (sessionType) {
      case "Time Trial":
        this.updateTimeTrialData(incomingData);
        break;
      case "Unknown":
      case "---":
        this.updateConnectedStatus(incomingData["wdt-status"]);
        this.setUIMode('Splash');
        break;
      default:
        this.updateRaceTableData(incomingData);
        break;
    }

    // update the header section regardless of mode
    this.updateHeader(incomingData);
  }

  updateTimeTrialData(incomingData) {

    // enable the time trial UI and set the data
    this.setUIMode('Time Trial');
    this.timeTrialDataPopulator.populate(incomingData["tt-data"], incomingData["packet-format"]);
  }

  // Extract existing driver rows and remove them from the DOM
  extractDriverRows() {
    const driverRowMap = new Map();
    Array.from(this.telemetryTable.querySelectorAll('tr[data-driver-index]')).forEach(row => {
      const driverIndex = row.getAttribute('data-driver-index');
      driverRowMap.set(driverIndex, row);
      row.parentNode.removeChild(row);
    });
    return driverRowMap;
  }

  // Ensure the header row is preserved
  preserveHeaderRow() {
    if (this.telemetryTable.children.length === 1) {
      const headerRow = this.telemetryTable.children[0];
      this.telemetryTable.innerHTML = '';
      this.telemetryTable.appendChild(headerRow);
    }
  }

  // Update or create row based on existing data
  updateOrCreateRow(row, data, packetFormat, isLiveDataMode, driverIndex, raceEnded, spectatorIndex, sessionType) {
    const newRow = this.renderTelemetryRow(data, packetFormat, isLiveDataMode, raceEnded, spectatorIndex, sessionType);
    if (row) {
      row.innerHTML = newRow.innerHTML;
    } else {
      row = newRow;
      row.setAttribute('data-driver-index', driverIndex);
    }
    return row;
  }

  updateRaceTableData(incomingData) {
    this.setUIMode('Race');
    const isLiveDataMode = incomingData["live-data"];
    const raceEnded = incomingData["race-ended"];
    const spectatorMode = incomingData["is-spectating"];
    const spectatorCarIndex = incomingData["spectator-car-index"];
    const sessionType = incomingData["session-type"];
    this.setDeltaColumnState(isLiveDataMode);
    this.setFuelColumnState(isLiveDataMode, sessionType);
    this.setCurrLapColumnState(isLiveDataMode, sessionType);
    this.setWearPredictionColumnState(isLiveDataMode, sessionType);
    this.setWingDamageColumnState(sessionType);

    const tableEntries = this.getRelevantRaceTableRows(incomingData);
    updateReferenceLapTimes(tableEntries,
      (spectatorMode) ?
      ((entry) => entry["driver-info"]?.["index"] == spectatorCarIndex) :
      ((entry) => entry["driver-info"]?.["is-player"])
    );
    const packetFormat = incomingData["packet-format"];
    this.indexByPosition = incomingData["table-entries"].map(entry => entry["driver-info"]["index"]);

    // Extract and remove existing driver rows
    const driverRowMap = this.extractDriverRows();
    // Preserve header row if needed
    this.preserveHeaderRow();

    tableEntries.forEach(data => {
      const driverIndex = data["driver-info"]["index"];
      let row = driverRowMap.get(driverIndex);
      row = this.updateOrCreateRow(row, data, packetFormat, isLiveDataMode, driverIndex, raceEnded, spectatorCarIndex,
                                    sessionType);
      this.telemetryTable.appendChild(row);
    });
    // Rows not referenced in tableEntries will be left out
  }

  updateHeader(incomingData) {
    const weatherSamples = incomingData['weather-forecast-samples'].slice(0, g_pref_numWeatherPredictionSamples);
    this.weatherWidget.update(weatherSamples);

    this.fastestLapTimeSpan.textContent = formatLapTime(incomingData['fastest-lap-overall']);
    this.fastestLapNameSpan.textContent = (incomingData['event-type'] === 'Time Trial') ?
        ('') : (truncateName(incomingData['fastest-lap-overall-driver']).toUpperCase());

    this.fastestLapTyreSpan.innerHTML = '';
    const fastestLapTyre = incomingData['fastest-lap-overall-tyre'];
    if (fastestLapTyre) {
      const icon = this.iconCache.getIcon(fastestLapTyre);
      if (icon) {
        this.fastestLapTyreSpan.appendChild(icon);
      }
    }

    this.populateCircuitSpan(incomingData);
    this.airTempSpan.textContent = formatTemperature(incomingData['air-temperature'], {
      isMetric: g_pref_tempUnitMetric,
      decimalPlaces: 0,
      addUnitSuffix: true
    });
    this.trackTempSpan.textContent = formatTemperature(incomingData['track-temperature'], {
      isMetric: g_pref_tempUnitMetric,
      decimalPlaces: 0,
      addUnitSuffix: true
    });
  }


  // Utility methods:
  populateCircuitSpan(incomingData) {
    this.populateTrackName(incomingData);
    const pitLaneSpeedLimit = incomingData['pit-speed-limit'];
    if (pitLaneSpeedLimit) {
      this.pitLaneSpeedLimit.textContent = formatSpeed(pitLaneSpeedLimit, {
        isMetric: g_pref_speedUnitMetric,
        decimalPlaces: 0,
        addUnitSuffix: false
      });
      this.pitLaneSpeedLimit.style.display = "inline-flex"; // Ensure it's visible if there's a value
    } else {
      this.pitLaneSpeedLimit.style.display = "none"; // Hide if the value is 0;
    }
  }

  populateTrackName(incomingData) {
    const trackName = incomingData['circuit'];
    const trackNameContainer = this.trackName;

    // Clear any existing content in the span
    trackNameContainer.innerHTML = "";
    if ("---" === trackName) {
      this.trackName.textContent = "PITS N' GIGGLES";
    } else {
      // Create the first div for the track name
      const trackNameDiv = document.createElement("div");
      trackNameDiv.textContent = replaceRevSuffix(trackName).toUpperCase();
      trackNameDiv.style.textAlign = "center";
      trackNameDiv.style.margin = "0 auto";
      trackNameContainer.appendChild(trackNameDiv);

      // Create the second div for session info
      const sessionInfoDiv = document.createElement("div");
      sessionInfoDiv.style.textAlign = "center";
      sessionInfoDiv.style.margin = "0 auto";

      let sessionInfoText = "";
      if (this.shouldShowLapNumber(incomingData['event-type'])) {
        if (incomingData['current-lap']) {
          sessionInfoText += "L" + incomingData['current-lap'].toString();
        }
        if (incomingData['event-type'] != "Time Trial" && ((incomingData['total-laps'] ?? 0) > 1)) {
          sessionInfoText += "/" + incomingData['total-laps'].toString();
        }
      } else {
        const sessionTime = incomingData['session-time-left'];
        sessionInfoText += formatSecondsToMMSS(sessionTime);
      }

      sessionInfoDiv.innerHTML = sessionInfoText;
      trackNameContainer.appendChild(sessionInfoDiv);
    }
  }

  shouldShowLapNumber(sessionType) {
    const unsupportedSessionTypes = ['Qualifying', 'Practice', 'Sprint Shootout'];
    return !unsupportedSessionTypes.some(type => sessionType.includes(type));
  }

  getPlayerPosition(data) {
    let tableEntries = data["table-entries"];
    let playerPosition = null;

    for (let i = 0; i < tableEntries.length; i++) {
      let entry = tableEntries[i];
      const driverInfo = entry["driver-info"];
      if (driverInfo["is-player"]) {
        playerPosition = driverInfo["position"];
        break; // Breaks out of the loop once player position is found
      }
    }

    return playerPosition;
  }

  getRelevantRaceTableRows(data) {
    const tableEntries = data["table-entries"];
    if (tableEntries.length == 0) {
      return [];
    }
    // Sort the list by position before computing relevant positions and update rejoin positions
    const sortedTableEntries = tableEntries.sort((a, b) => a["driver-info"]["position"] - b["driver-info"]["position"]);
    insertRejoinPositions(sortedTableEntries, data["pit-time-loss"] ?? null);

    if (data["is-spectating"] || data["race-ended"]) {
      return sortedTableEntries;
    }

    const totalCars = sortedTableEntries.length;
    const playerPosition = this.getPlayerPosition(data);
    const relevantPositions = this.getAdjacentPositions(playerPosition, totalCars, g_pref_numAdjacentCars);

    const lowerIndex = relevantPositions[0] - 1;
    const upperIndex = relevantPositions[relevantPositions.length - 1];
    return sortedTableEntries.slice(lowerIndex, upperIndex);
  }

  getAdjacentPositions(position, total_cars, num_adjacent_cars) {
      if (!(position >= 1 && position <= total_cars)) {
      return [];
    }

    let min_valid_lower_bound = 1;
    let max_valid_upper_bound = total_cars;
    let lower_bound;
    let upper_bound;

    // In time trial, total_cars will be lower than num_adjacent_cars
    if (num_adjacent_cars >= total_cars) {
      num_adjacent_cars = total_cars;
      lower_bound = min_valid_lower_bound;
      upper_bound = max_valid_upper_bound;
    }
    // GP scenario, lower bound and upper bound are off input position by num_adjacent_cars
    else {
      lower_bound = position - num_adjacent_cars;
      upper_bound = position + num_adjacent_cars;
    }

    // now correct if lower and upper bounds have become invalid
    if (lower_bound < min_valid_lower_bound) {
      // lower bound is negative, need to shift the entire window right
      upper_bound += min_valid_lower_bound - lower_bound;
      lower_bound = min_valid_lower_bound;
    }
    if (upper_bound > total_cars) {
      // upper bound is greater than limit, need to shift the entire window left
      lower_bound -= upper_bound - total_cars;
      upper_bound = max_valid_upper_bound;
    }

    return Array.from({ length: upper_bound - lower_bound + 1 }, (_, i) => lower_bound + i);
  }

  setDeltaColumnState(isLiveDataMode) {
    // hide the column in live mode
    this.hideColumn('DELTA 🛈', isLiveDataMode);
  }

  setFuelColumnState(isLiveDataMode, sessionType) {
    // show the column in live mode, but only for race sessions
    let shouldHide;
    if (!isLiveDataMode) {
      shouldHide = true;
    } else {
      shouldHide = !isRaceSession(sessionType);
    }
    this.hideColumn('FUEL 🛈', shouldHide);
  }

  setCurrLapColumnState(isLiveDataMode, sessionType) {
    // show the column in live mode, but only in FP and quali sessions
    let shouldHide = false;
    if (!isLiveDataMode) {
      shouldHide = true;
    }
    else {
      shouldHide = isRaceSession(sessionType);
    }

    this.hideColumn('CURRENT LAP', shouldHide);
  }

  setWearPredictionColumnState(isLiveDataMode, sessionType) {
      const shouldHide = !isLiveDataMode || !isRaceSession(sessionType);
      this.hideColumn('WEAR PREDICTION', shouldHide);
  }

  setWingDamageColumnState(sessionType) {
    // hide the column in FP/Quali modes
    const shouldHide = !isRaceSession(sessionType);
    this.hideColumn('WING DAMAGE', shouldHide);
  }

  hideColumn(columnName, shouldHide) {
    const table = document.getElementById("race-table");
    const headers = table.getElementsByTagName("th");
    let columnIndex = -1;

    // Find the column index
    for (let i = 0; i < headers.length; i++) {
        if (headers[i].textContent === columnName) {
            columnIndex = i;
            headers[i].style.display = shouldHide ? "none" : "";
            break;
        }
    }

    // If column was found, hide/show all cells in that column
    if (columnIndex > -1) {
        const rows = table.getElementsByTagName("tr");

        // Start from 1 to skip header row if it's already handled above
        for (let i = 1; i < rows.length; i++) {
            const cells = rows[i].getElementsByTagName("td");
            if (cells.length > columnIndex) {
                cells[columnIndex].style.display = shouldHide ? "none" : "";
            }
        }
    }
  }

  setUIMode(uiMode) {

    // only process on change
    if (this.uiMode === uiMode) {
      return;
    }

    console.log(`changing UI mode from ${this.uiMode} to ${uiMode}`);
    this.uiMode = uiMode;
    switch(uiMode) {
      case 'Splash':
        this.splashDiv.style.display = '';
        this.raceTableDiv.style.display = 'none';
        this.timeTrialDiv.style.display = 'none';
        break;
      case 'Time Trial':
        this.splashDiv.style.display = 'none';
        this.raceTableDiv.style.display = 'none';
        this.timeTrialDiv.style.display = '';
        break;
      case 'Race':
        this.splashDiv.style.display = 'none';
        this.raceTableDiv.style.display = '';
        this.timeTrialDiv.style.display = 'none';
        break;
      default:
        console.error('Unknown UI mode:', uiMode);
        break;
    }
  }

  updateConnectedStatus(connected) {
    if (this.uiMode !== 'Splash' || this.connected === connected) {
      return
    }
    this.connected = connected

    // toggle color class
    this.blinkingDot.classList.toggle('green', connected)
    this.blinkingDot.classList.toggle('red', !connected)

    // update text
    this.statusText.textContent = connected
      ? 'Connected to F1 game. Waiting for session start ...'
      : 'Waiting for F1 game UDP telemetry data ...'
  }

}