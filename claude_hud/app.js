// DOM elements
const speedEl = document.getElementById('speed');
const rpmEl = document.getElementById('rpm');
const gearEl = document.getElementById('gear');
const lapTimeEl = document.getElementById('lapTime');

// Update telemetry data
function updateTelemetry(data) {
    console.log("got data:", data);

    speedEl.textContent = data.speed;
    rpmEl.textContent = data.rpm;
    gearEl.textContent = data.gear;
    lapTimeEl.textContent = data.lap_time;
}

// Listen for updates from Python
window.addEventListener('telemetry-update', (event) => {
    updateTelemetry(event.detail);
});

// Initial update when ready
window.addEventListener('pywebviewready', async () => {
    try {
        const data = await pywebview.api.get_data();
        updateTelemetry(data);
    } catch (error) {
        console.error('Error getting initial telemetry:', error);
    }
});
