class TelemetryRenderer {
  constructor() {
    this.telemetryTable = document.getElementById('telemetry-data');
    this.weatherContainer = document.getElementById('weather-predictions');
  }

  renderTelemetryRow(data) {
    const row = document.createElement('tr');
    if (data.isPlayer) row.classList.add('player-row');

    row.innerHTML = `
      <td>${data.position}</td>
      <td><a href="#" class="driver-name" data-driver='${JSON.stringify(data)}'>${data.driver}</a></td>
      <td class="${data.delta.startsWith('+') ? 'delta-positive' : 'delta-negative'}">${data.delta}</td>
      <td>${data.lastLap}</td>
      <td>${data.bestLap}</td>
      <td><span class="tyre-compound tyre-${data.tyreInfo.compound}">${data.tyreInfo.compound.toUpperCase()}</span></td>
      <td>${data.tyreInfo.age} laps</td>
      <td>${data.tyreInfo.wear}%</td>
      <td>${data.tyreInfo.prediction}</td>
      <td><span class="stat-value">${data.ers}</span><span class="stat-unit">%</span></td>
      <td><span class="stat-value">${data.fuel}</span><span class="stat-unit">%</span></td>
    `;

    // Add click event for driver name
    const driverLink = row.querySelector('.driver-name');
    driverLink.addEventListener('click', (e) => {
      e.preventDefault();
      const driverData = JSON.parse(e.target.dataset.driver);
      window.modalManager.openDriverModal(driverData);
    });

    return row;
  }

  renderWeatherPrediction(prediction) {
    const predictionElement = document.createElement('div');
    predictionElement.classList.add('weather-prediction');
    
    const weatherIcon = WEATHER_ICONS[prediction.weatherType];
    predictionElement.innerHTML = `
      <i class="bi ${weatherIcon.icon} weather-icon ${weatherIcon.class}"></i>
      <div class="weather-info">
        <span class="weather-time">+${prediction.timeOffset}min</span>
        <span class="weather-probability">${prediction.rainProbability}%</span>
      </div>
    `;

    return predictionElement;
  }

  updateDashboard(telemetryData, weatherPredictions) {
    this.telemetryTable.innerHTML = '';
    telemetryData.forEach(data => {
      this.telemetryTable.appendChild(this.renderTelemetryRow(data));
    });

    this.weatherContainer.innerHTML = '';
    weatherPredictions.forEach(prediction => {
      this.weatherContainer.appendChild(this.renderWeatherPrediction(prediction));
    });
  }
}