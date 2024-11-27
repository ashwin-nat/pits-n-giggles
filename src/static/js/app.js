// Initialize renderer
const telemetryRenderer = new TelemetryRenderer();

// Load settings from localStorage or use defaults
function getSettings() {
  const defaultSettings = {
    carsToShow: 2,
    updateInterval: 1000
  };
  
  const savedSettings = localStorage.getItem('dashboardSettings');
  return savedSettings ? JSON.parse(savedSettings) : defaultSettings;
}

let settings = getSettings();

// Initial render
telemetryRenderer.updateDashboard(mockTelemetryData, mockWeatherPredictions);

// Update interval for periodic updates
let updateInterval;

function startUpdates() {
  if (updateInterval) {
    clearInterval(updateInterval);
  }
  
  updateInterval = setInterval(() => {
    telemetryRenderer.updateDashboard(mockTelemetryData, mockWeatherPredictions);
  }, settings.updateInterval);
}

// Start updates with initial settings
startUpdates();

// Listen for settings changes
window.addEventListener('settingsChanged', () => {
  settings = getSettings();
  startUpdates();
});