loadPreferences();
// Initialize renderer
const iconCache = new IconCache();
const telemetryRenderer = new TelemetryRenderer(iconCache);
telemetryRenderer.updateConnectedStatus(false);
window.modalManager = new ModalManager();

let awaitingResponse = false;
let timeoutIntervalId;
let timeoutIntervalMs = 3000;
let socketio;

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

socketio = initializeSocketIO('race-table', 'driver-view');

// Receive details from server
socketio.on('race-table-update', function (binaryData) {
    try {
        const data = window.msgpack.decode(new Uint8Array(binaryData));
        telemetryRenderer.updateDashboard(data);
    } catch (err) {
        console.error('Failed to decode race-table-update:', err);
    }
});

socketio.on('frontend-update', function (binaryData) {
    const data = window.msgpack.decode(new Uint8Array(binaryData));
    console.log("frontend-update", data);
    switch (data['message-type']) {
        case 'custom-marker':
            processCustomMarkerMessage(data['message']);
            break;
        case 'tyre-delta':
            processTyreDeltaMessage(data['message']);
            break;
        case 'tyre-delta-v2':
            processTyreDeltaMessageV2(data['message'], iconCache);
            break;
        case 'final-classification-notification':
            processFinalClassificationNotification(data['message']);
            break;
        default:
            console.error("received unsupported message type in frontend-update");
    }
});

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

document.getElementById('tt-vmax-th').addEventListener('click', function (e) {
    g_pref_speedUnitMetric = !g_pref_speedUnitMetric;
    showToast("Speed Format Changed to " + (g_pref_speedUnitMetric ? ("km/h") : ("mph")));
    savePreferences();
});
