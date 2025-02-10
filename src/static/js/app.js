loadPreferences();
// Initialize renderer
const iconCache = new IconCache();
const telemetryRenderer = new TelemetryRenderer(iconCache);

// Update interval for periodic updates
let updateInterval;

let awaitingResponse = false;
let timeoutIntervalId;
let timeoutIntervalMs = 3000;
let socketio;

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

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
        if ('__dummy' in data) {
            // this request is meant for a synchronous listener, ignore
            console.debug("Ignoring race-info-response in main listener");
        } else {
            window.modalManager.openRaceStatsModal(data);
        }
    } else {
        console.error("Received error for race-info request", data);
    }
});

socketio.on('driver-info-response', function (data) {
    clearSocketIoRequestTimeout();
    if (!('error' in data)) {
        if ('__dummy' in data) {
            // this request is meant for a synchronous listener, ignore
            console.debug("Ignoring driver-info-response in main listener");
        } else {
            window.modalManager.openDriverModal(data, iconCache);
        }
    } else {
        console.error("Received error for driver-info request", data);
        // showToast("Received error for driver info request");
    }
});

socketio.on('frontend-update', function (data) {
    console.log("frontend-update", data);
    switch (data['message-type']) {
        case 'custom-marker':
            processCustomMarkerMessage(data['message']);
            break;
        case 'tyre-delta':
            processTyreDeltaMessage(data['message']);
            break;
        default:
            console.error("received unsupported message type in frontend-update");
    }
});

// Generic function to handle any request-response via socket events
async function sendSynchronousRequest(requestEvent, requestData, responseEvent) {
    return new Promise((resolve, reject) => {
        // Send the request event with data
        socketio.emit(requestEvent, requestData);

        // Listen for the response event
        socketio.once(responseEvent, (response) => {
            resolve(response);  // Resolve the promise with the response
        });

        // Optional: Timeout after 5 seconds (adjust as needed)
        setTimeout(() => {
            reject(new Error(`Timeout waiting for response event: ${responseEvent}`));
        }, 5000);  // 5 seconds timeout
    });
}

document.getElementById("best-lap-th").addEventListener("click", function () {
    g_pref_bestLapAbsoluteFormat = !g_pref_bestLapAbsoluteFormat;
    showToast("Best Lap Format Changed to " + (g_pref_bestLapAbsoluteFormat ? "Absolute" : "Relative"));
    savePreferences();
});

document.getElementById("last-lap-th").addEventListener("click", function () {
    g_pref_lastLapAbsoluteFormat = !g_pref_lastLapAbsoluteFormat;
    showToast("Last Lap Format Changed to " + (g_pref_lastLapAbsoluteFormat ? "Absolute" : "Relative"));
    savePreferences();
});

document.getElementById("wear-prediction-th").addEventListener("click", function () {
    g_pref_tyreWearAverageFormat = !g_pref_tyreWearAverageFormat;
    showToast("Tyre Wear Format Changed to " + (g_pref_tyreWearAverageFormat ? "Average" : "Max"));
    savePreferences();
});


document.getElementById("tyre-info-th").addEventListener("click", function () {
    g_pref_tyreWearAverageFormat = !g_pref_tyreWearAverageFormat;
    showToast("Tyre Wear Format Changed to " + (g_pref_tyreWearAverageFormat ? "Average" : "Max"));
    savePreferences();
});

document.getElementById("fuel-info-th").addEventListener("click", function () {
    g_pref_fuelTargetAverageFormat = !g_pref_fuelTargetAverageFormat;
    showToast("Target fuel usage Format Changed to " + (g_pref_fuelTargetAverageFormat ?
        ("Average target fuel rate") : ("Fuel usage target for next lap")));
    savePreferences();
});

document.getElementById('volumeRange').addEventListener('input', function (e) {
    document.getElementById('volumeLabel').textContent = e.target.value;
});

