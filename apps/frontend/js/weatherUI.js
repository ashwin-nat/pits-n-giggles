const WEATHER_ICONS = {
  'Clear': { icon: 'bi-sun-fill', class: 'weather-clear' },
  'Light Cloud': { icon: 'bi-cloud-sun-fill', class: 'weather-cloud' },
  'Overcast': { icon: 'bi-clouds-fill', class: 'weather-cloud' },
  'Light Rain': { icon: 'bi-cloud-drizzle-fill', class: 'weather-rain' },
  'Heavy Rain': { icon: 'bi-cloud-rain-heavy-fill', class: 'weather-rain' },
  'Storm': { icon: 'bi-cloud-lightning-rain-fill', class: 'weather-storm' },
  'Thunderstorm': { icon: 'bi-cloud-lightning-fill', class: 'weather-thunder' }
};

function transformForecast(data) {
  const sessions = [];
  let currentSession = [];

  for (const sample of data) {
    // When time-offset is 0 and we already have data, start a new session
    if (sample["time-offset"] === "0" && currentSession.length > 0) {
      sessions.push([...currentSession]);
      currentSession = [];
    }

    // Add the current sample to the current session
    currentSession.push(sample);
  }

  // Don't forget to add the last session
  if (currentSession.length > 0) {
    sessions.push(currentSession);
  }

  return sessions;
}

function renderWeatherPrediction(prediction) {
  const predictionElement = document.createElement('div');
  predictionElement.classList.add('weather-prediction');

  const weatherIcon = WEATHER_ICONS[prediction['weather']];

  const icon = document.createElement('i');
  icon.classList.add('bi', weatherIcon.icon, 'weather-icon', weatherIcon.class);

  const weatherInfo = document.createElement('div');
  weatherInfo.classList.add('weather-info');

  const timeSpan = document.createElement('span');
  timeSpan.classList.add('weather-time');
  timeSpan.textContent = `+${prediction['time-offset']}min`;

  const probabilitySpan = document.createElement('span');
  probabilitySpan.classList.add('weather-probability');
  probabilitySpan.textContent = `${prediction['rain-probability']}%`;

  weatherInfo.appendChild(timeSpan);
  weatherInfo.appendChild(probabilitySpan);

  predictionElement.appendChild(icon);
  predictionElement.appendChild(weatherInfo);

  return predictionElement;
}

function updateWeatherUI(weatherContainer, weatherData) {

  weatherContainer.textContent = '';
  if (weatherData.length === 0) {
    return;
  }
  const sessionWeather = transformForecast(weatherData)[0];
  sessionWeather.forEach(prediction => {
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

    const icon = document.createElement('i');
    icon.classList.add('bi', weatherIcon.icon, 'weather-icon', weatherIcon.class);

    const weatherInfo = document.createElement('div');
    weatherInfo.classList.add('weather-info');

    const timeSpan = document.createElement('span');
    timeSpan.classList.add('weather-time');
    timeSpan.textContent = `+${prediction['time-offset']}min`;

    const probabilitySpan = document.createElement('span');
    probabilitySpan.classList.add('weather-probability');
    probabilitySpan.textContent = `${prediction['rain-probability']}%`;

    weatherInfo.appendChild(timeSpan);
    weatherInfo.appendChild(probabilitySpan);

    predictionElement.appendChild(icon);
    predictionElement.appendChild(weatherInfo);

    return predictionElement;
  }

  // Method to update the weather UI with an array of weather predictions
  update(weatherData) {
    this.weatherContainer.textContent = ''; // Clear previous content
    if (weatherData.length === 0) {
      return;
    }
    const sessionWeather = transformForecast(weatherData)[0];
    sessionWeather.forEach(prediction => {
      this.weatherContainer.appendChild(this.renderWeatherPrediction(prediction));
    });
  }
}
