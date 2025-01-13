class TelemetryRenderer {
  constructor() {
    this.telemetryTable = document.getElementById('telemetry-data');
    this.weatherWidget = new WeatherWidget(document.getElementById('weather-predictions'));
    this.fastestLapTimeSpan = document.getElementById('fastestLapTimeSpan');
    this.fastestLapNameSpan = document.getElementById('fastestLapNameSpan');
    this.trackName = document.getElementById('track-name');
    this.pitLaneSpeedLimit = document.getElementById('pit-speed-limit');
    this.trackTempSpan = document.getElementById('track-temp');
    this.airTempSpan = document.getElementById('air-temp');
    this.indexByPosition = null;
  }

  renderTelemetryRow(data, gameYear, isLiveDataMode) {
    const row = document.createElement('tr');
    new RaceTableRowPopulator(row, data, gameYear, isLiveDataMode).populate();
    if (data['driver-info']['is-player']) {
      row.classList.add('player-row');
    }
    if (data['driver-info']['drs']) {
      row.classList.add('drs-row');
    }
    return row;
  }

  updateDashboard(incomingData) {

    // hide/unhide the delta column
    const isLiveDataMode = incomingData["live-data"];
    this.setDeltaColumnState(isLiveDataMode);
    this.setFuelColumnState(isLiveDataMode);

    // update array of indices by position-1
    const tableEntries = this.getRelevantRaceTableRows(incomingData);
    const gameYear = incomingData["f1-game-year"];
    this.indexByPosition = incomingData["table-entries"].map(entry => entry["driver-info"]["index"]);

    // clear the table and populate with data
    this.telemetryTable.innerHTML = '';
    tableEntries.forEach(data => {
      this.telemetryTable.appendChild(this.renderTelemetryRow(data, gameYear, isLiveDataMode));
    });

    const weatherSamples = incomingData['weather-forecast-samples'].slice(0, g_pref_numWeatherPredictionSamples + 1);
    this.weatherWidget.update(weatherSamples);

    this.fastestLapTimeSpan.textContent = formatLapTime(incomingData['fastest-lap-overall']);
    this.fastestLapNameSpan.textContent = this.truncateName(incomingData['fastest-lap-overall-driver']).toUpperCase();
    this.populateCircuitSpan(incomingData);
    this.airTempSpan.textContent = incomingData['air-temperature'] + ' °C';
    this.trackTempSpan.textContent = incomingData['track-temperature'] + ' °C';
  }


  // Utility methods:
  populateCircuitSpan(incomingData) {
    const trackName = incomingData['circuit'];
    const trackNameContainer = this.trackName;
    // Clear any existing content in the span
    trackNameContainer.innerHTML = "";
    if ("---" === trackName) {
      this.trackName.textContent = "PITS N' GIGGLES";
    } else {
      // Create the first div for the track name
      const trackNameDiv = document.createElement("div");
      trackNameDiv.textContent = trackName.toUpperCase();
      trackNameDiv.style.textAlign = "center"; // Center the text
      trackNameDiv.style.margin = "0 auto";   // Ensure centering in flex/inline-flex containers
      trackNameContainer.appendChild(trackNameDiv);

      // Create the second div for dummy text
      const lapCountDiv = document.createElement("div");
      lapCountDiv.style.textAlign = "center"; // Center the text
      lapCountDiv.style.margin = "0 auto";   // Ensure centering in flex/inline-flex containers
      let lapCountText = "";
      lapCountText += "L" + incomingData['current-lap'].toString();
      if (incomingData['total-laps'] > 1) {
        lapCountText += "/" + incomingData['total-laps'].toString();
      }
      lapCountDiv.textContent = lapCountText;
      trackNameContainer.appendChild(lapCountDiv);
    }
    const pitLaneSpeedLimit = incomingData['pit-speed-limit'];
    if (pitLaneSpeedLimit) {
      this.pitLaneSpeedLimit.textContent = pitLaneSpeedLimit;
      this.pitLaneSpeedLimit.style.display = "inline-flex"; // Ensure it's visible if there's a value
    } else {
      this.pitLaneSpeedLimit.style.display = "none"; // Hide if the value is 0;
    }
  }

  truncateName(name) {
    const maxLength = 3;
    if (name.length > maxLength) {
      return name.substring(0, maxLength);
    } else {
      return name;
    }
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
    if (data["table-entries"].length == 0) {
      return [];
    }
    if (data["is-spectating"] || data["race-ended"]) {
      return data["table-entries"];
    }
    const totalCars = data["table-entries"].length;
    const playerPosition = this.getPlayerPosition(data);
    const relevantPositions = this.getAdjacentPositions(playerPosition, totalCars, g_pref_numAdjacentCars);

    const lowerIndex = relevantPositions[0] - 1;
    const upperIndex = relevantPositions[relevantPositions.length - 1];
    return data["table-entries"].slice(lowerIndex, upperIndex);
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
    const shouldHide = isLiveDataMode;
    this.hideColumn('DELTA', isLiveDataMode);
  }

  setFuelColumnState(isLiveDataMode) {
    // show the column in live mode
    const shouldHide = !isLiveDataMode;
    this.hideColumn('FUEL', shouldHide);
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
}