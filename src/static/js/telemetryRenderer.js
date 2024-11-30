class TelemetryRenderer {
  constructor() {
    this.telemetryTable = document.getElementById('telemetry-data');
    this.weatherContainer = document.getElementById('weather-predictions');
  }

  renderTelemetryRow(data) {
    const row = document.createElement('tr');
    new RaceTableRowPopulator(row, data, this.gameYear).populate();
    if (data['driver-info']['is-player']) row.classList.add('player-row');

    // Helper to create a cell with optional content and class
    // const createCell = (content, className = '') => {
    //     const cell = document.createElement('td');
    //     if (className) {
    //       cell.className = className;
    //     }
    //     if (content instanceof HTMLElement) {
    //         cell.appendChild(content);
    //     } else {
    //         cell.textContent = content;
    //     }
    //     return cell;
    // };

    // Position cell
    // row.appendChild(createCell(data['driver-info']['position']));

    // // Driver name cell with link
    // const driverLink = document.createElement('a');
    // driverLink.href = '#';
    // driverLink.className = 'driver-name';
    // driverLink.textContent = data['driver-info']['name'];
    // driverLink.dataset.driver = JSON.stringify(data);
    // driverLink.addEventListener('click', (e) => {
    //     e.preventDefault();
    //     const driverData = JSON.parse(e.target.dataset.driver);
    //     window.modalManager.openDriverModal(driverData);
    // });
    // row.appendChild(createCell(driverLink));

    // // Delta cell
    // const deltaClass = data['delta-info']['delta'].startsWith('-') ? 'delta-negative' : 'delta-positive';
    // row.appendChild(createCell(data['delta-info']['delta'], deltaClass));

    // // Last lap time cell
    // row.appendChild(createCell(data['lap-info']['last-lap-ms']));

    // // Best lap time cell
    // row.appendChild(createCell(data['lap-info']['best-lap-ms']));

    // // Tyre compound cell
    // const tyreCompound = document.createElement('span');
    // tyreCompound.className = `tyre-compound tyre-${data['tyre-info']['visual-tyre-compound']}`;
    // tyreCompound.textContent = data['tyre-info']['visual-tyre-compound'].toUpperCase();
    // row.appendChild(createCell(tyreCompound));

    // // Tyre age cell
    // row.appendChild(createCell(`${data['tyre-info']['tyre-age']} laps`));

    // // Tyre wear cell
    // row.appendChild(createCell(`${data['tyre-info']['current-wear']['average']}%`));

    // // Static value cell
    // row.appendChild(createCell('0'));

    // // ERS percentage cell
    // const ersValue = document.createElement('span');
    // ersValue.className = 'stat-value';
    // ersValue.textContent = data['ers-info']['ers-percent'];
    // row.appendChild(createCell(ersValue));

    // // Fuel rate cell
    // const fuelCell = document.createElement('span');
    // fuelCell.className = 'stat-value';
    // fuelCell.textContent = data['fuel-info']['curr-fuel-rate'];
    // const fuelUnit = document.createElement('span');
    // fuelUnit.className = 'stat-unit';
    // fuelUnit.textContent = '%';
    // const fuelContainer = document.createElement('div');
    // fuelContainer.appendChild(fuelCell);
    // fuelContainer.appendChild(fuelUnit);
    // row.appendChild(createCell(fuelContainer));

    return row;
  }


  renderWeatherPrediction(prediction) {
    const predictionElement = document.createElement('div');
    predictionElement.classList.add('weather-prediction');

    const weatherIcon = WEATHER_ICONS[prediction['weather']];
    predictionElement.innerHTML = `
      <i class="bi ${weatherIcon.icon} weather-icon ${weatherIcon.class}"></i>
      <div class="weather-info">
        <span class="weather-time">+${prediction['time-offset']}min</span>
        <span class="weather-probability">${prediction['rain-probability']}%</span>
      </div>
    `;

    return predictionElement;
  }

  updateDashboard(incomingData) {
    this.telemetryTable.innerHTML = '';
    const tableEntries = this.getRelevantRaceTableRows(incomingData);
    const gameYear = incomingData["f1-game-year"];
    tableEntries.forEach(data => {
      this.telemetryTable.appendChild(this.renderTelemetryRow(data, gameYear));
    });

    this.weatherContainer.innerHTML = '';
    const weatherPredictions = incomingData['weather-forecast-samples'].slice(0, g_pref_numWeatherPredictionSamples+1);
    weatherPredictions.forEach(prediction => {
      this.weatherContainer.appendChild(this.renderWeatherPrediction(prediction));
    });
  }


  // Utility methods:
  truncateName(name) {
    const maxLength = 25;
    if (name.length > maxLength) {
      return name.substring(0, maxLength - 3) + '...';
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
    // if (!(1 <= position && position <= total_cars)) {
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
}