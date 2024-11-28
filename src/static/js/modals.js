class ModalManager {
  constructor() {
    this.driverModal = new bootstrap.Modal(document.getElementById('driverModal'));
    this.settingsModal = new bootstrap.Modal(document.getElementById('settingsModal'));
    this.setupEventListeners();
  }

  setupEventListeners() {
    document.getElementById('settings-btn').addEventListener('click', () => this.openSettingsModal());
    document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());
  }

  openDriverModal(data) {
    const modalTitle = document.querySelector('#driverModal .modal-title');
    const modalBody = document.querySelector('#driverModal .modal-body');
    console.log("openDriverModal", data);

    modalTitle.textContent = `${data["driver-name"]} - ${data["index"]}`;
    modalBody.textContent = `Index: ${data["index"]}`

    this.driverModal.show();
  }

  openSettingsModal() {

    // Populate the fields with the default values
    document.getElementById("carsToShow").value = g_pref_numAdjacentCars;
    document.getElementById("teamName").value = g_pref_myTeamName;

    // Set the radio buttons for time format
    document.getElementById("timeFormat12").checked = !g_pref_is24HourFormat;
    document.getElementById("timeFormat24").checked = g_pref_is24HourFormat;

    // Set the radio buttons for last lap time format
    document.getElementById("lastLapAbsolute").checked = g_pref_lastLapAbsoluteFormat;
    document.getElementById("lastLapRelative").checked = !g_pref_lastLapAbsoluteFormat;

    // Set the radio buttons for best lap time format
    document.getElementById("bestLapAbsolute").checked = g_pref_bestLapAbsoluteFormat;
    document.getElementById("bestLapRelative").checked = !g_pref_bestLapAbsoluteFormat;

    // Set the radio buttons for tyre wear format
    document.getElementById("tyreWearAbsolute").checked = !g_pref_tyreWearAverageFormat;
    document.getElementById("tyreWearRelative").checked = g_pref_tyreWearAverageFormat;

    this.settingsModal.show();
  }
  saveSettings() {

    // Validate numAdjacentCars input
    const numInput = document.getElementById('carsToShow');
    const min = parseInt(numInput.min, 10);
    const max = parseInt(numInput.max, 10);
    const numAdjacentCars_temp = parseInt(numInput.value, 10);

    if (isNaN(g_pref_numAdjacentCars) || g_pref_numAdjacentCars < min || g_pref_numAdjacentCars > max) {
        showToast(`Please enter a valid number between ${min} and ${max}.`);
        return; // Exit without saving anything
    }

    // Collect and log the selected settings
    g_pref_myTeamName = document.getElementById('teamNameInput').value;
    g_pref_is24HourFormat = (document.querySelector('input[name="timeFormat"]:checked').value === "24") ? (true) : (false);
    g_pref_lastLapAbsoluteFormat = (document.querySelector('input[name="lastLapTimeFormat"]:checked').value === "absolute") ? (true) : (false);
    g_pref_bestLapAbsoluteFormat = (document.querySelector('input[name="bestLapTimeFormat"]:checked').value === "absolute") ? (true) : (false);
    g_pref_tyreWearAverageFormat = (document.querySelector('input[name="tyreWearFormat"]:checked').value === "average") ? (true) : (false);
    g_pref_numAdjacentCars = numAdjacentCars_temp;
    savePreferences();

    this.settingsModal.hide();

    // Dispatch event for other components to react to settings changes
    window.dispatchEvent(new CustomEvent('settingsChanged'));
  }
}

// Export for use in other modules
window.modalManager = new ModalManager();