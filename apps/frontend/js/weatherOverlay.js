function updateWeatherTable(weatherForecastSamples) {
    const maxWeatherSamples = 5;
    const weatherSamples = weatherForecastSamples.slice(0, maxWeatherSamples + 1);
    const weatherContainer = document.getElementById('weatherDiv');
    updateWeatherUI(weatherContainer, weatherSamples);
}
