const WEATHER_ICONS = {
  'Clear': { icon: 'bi-sun-fill', class: 'weather-clear' },
  'Light Cloud': { icon: 'bi-cloud-sun-fill', class: 'weather-cloud' },
  'Overcast': { icon: 'bi-clouds-fill', class: 'weather-cloud' },
  'Light Rain': { icon: 'bi-cloud-drizzle-fill', class: 'weather-rain' },
  'Heavy Rain': { icon: 'bi-cloud-rain-heavy-fill', class: 'weather-rain' },
  'Storm': { icon: 'bi-cloud-lightning-rain-fill', class: 'weather-storm' },
  'Thunderstorm': { icon: 'bi-cloud-lightning-fill', class: 'weather-thunder' }
};

function renderWeatherPrediction(prediction) {
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

function updateWeatherUI(weatherContainer, weatherData) {

  weatherContainer.innerHTML = '';
  weatherData.forEach(prediction => {
    weatherContainer.appendChild(renderWeatherPrediction(prediction));
  });
}

class WeatherWidget {
  constructor(container) {
    if (!container) {
      throw new Error("WeatherWidget requires a valid container element.");
    }
    this.weatherContainer = container;
  }

  // Method to render a single weather prediction
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

  // Method to update the weather UI with an array of weather predictions
  update(weatherData) {
    this.weatherContainer.innerHTML = ''; // Clear previous content

    weatherData.forEach(prediction => {
      this.weatherContainer.appendChild(this.renderWeatherPrediction(prediction));
    });
  }
}
