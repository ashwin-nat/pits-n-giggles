// DOM elements
const speedEl = document.getElementById('speed');
const rpmEl = document.getElementById('rpm');
const gearEl = document.getElementById('gear');
const lapTimeEl = document.getElementById('lapTime');

// Update telemetry data
async function updateTelemetry() {
    try {
        const data = await pywebview.api.get_data();
        console.log("got data:", data);

        speedEl.textContent = data.speed;
        rpmEl.textContent = data.rpm;
        gearEl.textContent = data.gear;
        lapTimeEl.textContent = data.lap_time;
    } catch (error) {
        console.error('Error updating telemetry:', error);
    }
}

// Update every 100ms
setInterval(updateTelemetry, 100);

// Initial update
window.addEventListener('pywebviewready', () => {
    updateTelemetry();
});