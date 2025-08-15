class WeatherOverlay {
    constructor(element) {
        this.container = element;
        this.lastProcessedData = null;
        this.weatherIcons = {
            "Clear": "☀️",
            "Light Cloud": "☁️",
            "Overcast": "☁️",
            "Light Rain": "🌦️",
            "Heavy Rain": "🌧️",
            "Storm": "⛈️",
            "Thunderstorm": "⛈️"
        };
    }

    update(weatherData) {
        this.container.innerHTML = ''; // Clear previous content
        if (_.isEqual(data, this.lastData)) {
            return;
        }

        this.lastProcessedData = weatherData;

        weatherData.forEach(sample => {
            const card = document.createElement('div');
            card.classList.add('weather-overlay-card');

            const time = document.createElement('div');
            time.classList.add('weather-overlay-time');
            time.textContent = `+${sample['time-offset']}m`;
            card.appendChild(time);

            const icon = document.createElement('div');
            icon.classList.add('weather-overlay-icon');
            icon.textContent = this.weatherIcons[sample.weather] || "❓";
            card.appendChild(icon);

            const rainProbability = document.createElement('div');
            rainProbability.classList.add('weather-overlay-rain-probability');
            rainProbability.textContent = `${sample['rain-probability']}%`;
            card.appendChild(rainProbability);

            const progressContainer = document.createElement('div');
            progressContainer.classList.add('progress');
            progressContainer.style.height = '5px';

            const progressBar = document.createElement('div');
            progressBar.classList.add('progress-bar');
            progressBar.style.width = `${sample['rain-probability']}%`;
            progressBar.setAttribute('role', 'progressbar');
            progressBar.setAttribute('aria-valuenow', sample['rain-probability']);
            progressBar.setAttribute('aria-valuemin', '0');
            progressBar.setAttribute('aria-valuemax', '100');
            progressContainer.appendChild(progressBar);

            card.appendChild(progressContainer);

            this.container.appendChild(card);
        });
    }
}