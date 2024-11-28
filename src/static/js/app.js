loadPreferences();
// Initialize renderer
const telemetryRenderer = new TelemetryRenderer();

// Initial render
// telemetryRenderer.updateDashboard(mockTelemetryData, mockWeatherPredictions);

// Update interval for periodic updates
let updateInterval;

let awaitingResponse = false;
let timeoutIntervalId;
let timeoutIntervalMs = 3000;
let socketio;

// socket = io.connect('http://' + document.domain + ':' + location.port, {
socketio = io.connect('http://' + location.hostname + ':' + location.port, {
    reconnection: true,           // Enables reconnection
    reconnectionAttempts: Infinity, // Number of attempts before giving up (Infinity means never stop trying)
    reconnectionDelay: 1000,      // Initial delay before reconnection (in ms)
    reconnectionDelayMax: 5000,   // Maximum delay between reconnections (in ms)
    randomizationFactor: 0.5,     // Randomization factor to prevent reconnection storms
    timeout: 20000                // Connection timeout before giving up (in ms)
});
console.log("SocketIO initialized");

function clearSocketIoRequestTimeout() {
    awaitingResponse = false;
    clearInterval(timeoutIntervalId);
}

socketio.on('connect', function () {
    socketio.emit('register-client', { type: 'race-table' });
});

// Receive details from server
socketio.on('race-table-update', function (data) {
    telemetryRenderer.updateDashboard(data);
});

socketio.on('race-info-response', function (data) {
    clearSocketIoRequestTimeout();
    if (!('error' in data)) {
        // openRaceInfoModal(data);
        console.log("race-info-response", data);
    } else {
        console.error("Received error for race-info request", data);
    }
});

socketio.on('driver-info-response', function (data) {
    clearSocketIoRequestTimeout();
    if (!('error' in data)) {
        // openDriverInfoModal(data);
        window.modalManager.openDriverModal(data);
        console.log("driver-info-response", data);
    } else {
        console.error("Received error for driver-info request", data);
        // showToast("Received error for driver info request");
    }
});

// function startUpdates() {
//   if (updateInterval) {
//     clearInterval(updateInterval);
//   }

//   updateInterval = setInterval(() => {
//     telemetryRenderer.updateDashboard(mockTelemetryData, mockWeatherPredictions);
//   }, settings.updateInterval);
// }

// // Start updates with initial settings
// startUpdates();

// // Listen for settings changes
// window.addEventListener('settingsChanged', () => {
//   settings = LoadPreferences();
//   // startUpdates();
// });