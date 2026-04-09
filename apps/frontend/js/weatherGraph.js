// Weather forecast graph using Chart.js — mirrors the MFD weather graph.
// Shows rain probability, track temperature, and air temperature over time.

class WeatherGraph {
    constructor(container) {
        if (!container || !(container instanceof HTMLElement)) {
            throw new Error('WeatherGraph requires a valid container element');
        }
        this.container = container;
        this.chart = null;
        this.lastData = null;
        this.lastSessionKey = null;
    }

    update(weatherData, sessionKey) {
        if (!weatherData || weatherData.length === 0) {
            this._destroy();
            return;
        }

        // Skip re-render if data and session haven't changed
        if (sessionKey === this.lastSessionKey && weatherData === this.lastData) {
            return;
        }
        const labels = weatherData.map(s => `+${s['time-offset']}m`);
        const rainData = weatherData.map(s => parseInt(s['rain-probability'], 10) || 0);
        const trackTempData = weatherData.map(s => parseInt(s['track-temperature'], 10) || 0);
        const airTempData = weatherData.map(s => parseInt(s['air-temperature'], 10) || 0);

        // Always destroy and recreate the chart when data changes,
        // matching the WeatherOverlay pattern of full rebuild.
        this._destroy();
        this._createChart(labels, rainData, trackTempData, airTempData);

        // Store AFTER destroy/create so the dedup check works on next call
        this.lastData = weatherData;
        this.lastSessionKey = sessionKey;
    }

    _createChart(labels, rainData, trackTempData, airTempData) {
        this.container.textContent = '';
        const canvas = document.createElement('canvas');
        this.container.appendChild(canvas);

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Rain %',
                        data: rainData,
                        borderColor: '#7dafff',
                        backgroundColor: 'rgba(125, 175, 255, 0.15)',
                        fill: true,
                        yAxisID: 'yRain',
                        tension: 0.3,
                        pointRadius: 2,
                        pointBackgroundColor: '#7dafff',
                    },
                    {
                        label: 'Track Temp (°C)',
                        data: trackTempData,
                        borderColor: '#ff6666',
                        backgroundColor: 'transparent',
                        yAxisID: 'yTemp',
                        tension: 0.3,
                        pointRadius: 2,
                        pointBackgroundColor: '#ff6666',
                    },
                    {
                        label: 'Air Temp (°C)',
                        data: airTempData,
                        borderColor: '#66ff66',
                        backgroundColor: 'transparent',
                        yAxisID: 'yTemp',
                        tension: 0.3,
                        pointRadius: 2,
                        pointBackgroundColor: '#66ff66',
                    }
                ]
            },
            options: this._chartOptions()
        });
    }

    _chartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        font: { size: 10 }
                    }
                },
                yRain: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: '#7dafff',
                        font: { size: 10 },
                        callback: function (value) { return value + '%'; },
                    },
                    title: {
                        display: false,
                    }
                },
                yTemp: {
                    type: 'linear',
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    },
                    ticks: {
                        color: '#ff6666',
                        font: { size: 10 },
                        callback: function (value) { return value + '°C'; },
                    },
                    title: {
                        display: false,
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        boxWidth: 14,
                        padding: 6,
                        font: { size: 10 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    animation: { duration: 0 },
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.dataset.yAxisID === 'yRain') {
                                label += context.parsed.y + '%';
                            } else {
                                label += context.parsed.y + '°C';
                            }
                            return label;
                        }
                    }
                }
            }
        };
    }

    _destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        this.lastData = null;
        this.lastSessionKey = null;
        this.container.textContent = '';
    }
}
