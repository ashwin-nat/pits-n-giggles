import io from 'https://cdn.jsdelivr.net/npm/socket.io-client@4.4.1/dist/socket.io.esm.min.js';
import { CarTelemetryWidget } from './carTelemetryOverlay.js';
import { GForceDisplay } from './gforceOverlay.js';
import { WeatherWidget } from './weatherUI.js';
import { PenaltiesStatsWidget } from './penaltiesStatsOverlay.js';
import { LapTimeTableWidget } from './lapTimeHistoryOverlay.js';

const socket = io();
const carTelemetryWidget = new CarTelemetryWidget('CarTelemetryWidget');
const gForceDisplayWidget = new GForceDisplay('gforce-display');
const weatherWidget = new WeatherWidget(document.getElementById('weatherDiv'));
const pensStatsWidget = new PenaltiesStatsWidget();
const lapTimesWidget = new LapTimeTableWidget();
const maxWeatherSamples = 5;

// Emit a custom event to register client type upon connection
socket.on('connect', function () {
    socket.emit('register-client', { type: 'player-stream-overlay' });
});

socket.on('player-overlay-update', function (data) {
    carTelemetryWidget.update(data["car-telemetry"]);
    pensStatsWidget.update(data["penalties-and-stats"], data["f1-game-year"]);
    lapTimesWidget.update(data["lap-time-history"]);
    weatherWidget.update(data["weather-forecast-samples"].slice(0, maxWeatherSamples+1));
    gForceDisplayWidget.update(data["g-force"]);
});
