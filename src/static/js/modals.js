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
    const modalTitle = document.querySelector('#driverModal .driver-modal-header .modal-title');
    const modalBody = document.querySelector('#driverModal .modal-body');
    const prevButton = document.querySelector('#prevButton');
    const nextButton = document.querySelector('#nextButton');
    const refreshButton = document.querySelector('#refreshButton');

    // Update modal title
    modalTitle.textContent = `${data["driver-name"]} - ${getTeamName(data["team"])}`;

    // Clear existing content
    modalBody.innerHTML = '';

    // Create the modal content using the DriverModalDataPopulator class
    const modalDataPopulator = new DriverModalDataPopulator(data);

    // Create and append navigation tabs
    const navTabs = modalDataPopulator.createNavTabs();
    modalBody.appendChild(navTabs);

    // Create and append tab content
    const tabContent = modalDataPopulator.createTabContent();
    modalBody.appendChild(tabContent);

    // Event Listeners for Buttons
    prevButton.onclick = () => this.loadPreviousDriver();
    nextButton.onclick = () => this.loadNextDriver();
    refreshButton.onclick = () => this.refreshDriverData(data);

    // Show the modal
    this.driverModal.show();
  }

  // Example Functions for Button Actions
  loadPreviousDriver() {
    console.log("Previous driver clicked");
    // Implement logic to load previous driver data
  }

  loadNextDriver() {
    console.log("Next driver clicked");
    // Implement logic to load next driver data
  }

  refreshDriverData(data) {
    console.log("Refresh clicked", data);
    this.openDriverModal(data); // Reload the modal with the current data
  }


  openSettingsModal() {

    // Populate the fields with the default values
    document.getElementById("carsToShow").value = g_pref_numAdjacentCars;
    document.getElementById("teamNameInput").value = g_pref_myTeamName;

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

    // Set initial value for volume slider
    const volumeSlider = document.getElementById('volumeRange');
    const volumeLabel = document.getElementById('volumeLabel');
    volumeSlider.value = g_pref_ttsVolume;
    volumeLabel.textContent = g_pref_ttsVolume;

    // Populate the "Text to Speech Voice" dropdown
    const voiceSelect = document.getElementById("voiceSelect");
    voiceSelect.innerHTML = ""; // Clear existing options
    const voices = window.speechSynthesis.getVoices(); // Get available voices
    console.log("voices", voices);

    const defaultVoice = voices[0]?.name || ""; // Use the first voice as default if available
    const selectedVoice = g_pref_ttsVoice || defaultVoice; // Use g_pref_ttsVoice if not null/empty, otherwise default voice

    voices.forEach((voice) => {
      const option = document.createElement("option");
      option.value = voice.name; // Use the voice name as the value
      option.textContent = `${voice.name} (${voice.lang})`; // Display voice name and language
      if (voice.name === selectedVoice) {
        option.selected = true; // Select the appropriate voice
      }
      voiceSelect.appendChild(option);
    });

    // Add event listener to "Play Sample" button
    const playSampleButton = document.getElementById("playSampleButton");
    playSampleButton.onclick = () => {
      const selectedVoiceName = voiceSelect.value;
      const selectedVoice = voices.find((voice) => voice.name === selectedVoiceName);

      if (selectedVoice) {
        const utterance = new SpeechSynthesisUtterance("Copy that, we are checking");
        utterance.voice = selectedVoice;
        utterance.volume = parseInt(document.getElementById('volumeRange').value, 10);
        window.speechSynthesis.speak(utterance);
      } else {
        alert("Please select a voice to play the sample.");
      }
    };

    this.settingsModal.show();
  }
  saveSettings() {

    // Validate numAdjacentCars input
    const numAdjacentCars_temp = this.validateIntField('carsToShow', "Number of adjacent cars");
    const numWeatherForecastSamples_temp = this.validateIntField('weatherSamplesToShow', 'Number of weather forecast samples');
    if ((null === numAdjacentCars_temp) || (null === numWeatherForecastSamples_temp)) {
      return;
    }

    // Collect and log the selected settings
    g_pref_myTeamName = document.getElementById('teamNameInput').value;
    g_pref_is24HourFormat = (document.querySelector('input[name="timeFormat"]:checked').value === "24") ? (true) : (false);
    g_pref_lastLapAbsoluteFormat = (document.querySelector('input[name="lastLapTimeFormat"]:checked').value === "absolute") ? (true) : (false);
    g_pref_bestLapAbsoluteFormat = (document.querySelector('input[name="bestLapTimeFormat"]:checked').value === "absolute") ? (true) : (false);
    g_pref_tyreWearAverageFormat = (document.querySelector('input[name="tyreWearFormat"]:checked').value === "average") ? (true) : (false);
    g_pref_numAdjacentCars = numAdjacentCars_temp;
    g_pref_numWeatherPredictionSamples = numWeatherForecastSamples_temp;
    g_pref_ttsVoice = document.getElementById('voiceSelect').value;
    g_pref_ttsVolume = parseInt(document.getElementById('volumeRange').value, 10);
    savePreferences();

    this.settingsModal.hide();

    // Dispatch event for other components to react to settings changes
    window.dispatchEvent(new CustomEvent('settingsChanged'));
  }

  validateIntField(elementId, fieldName) {
    const numInput = document.getElementById(elementId);
    const min = parseInt(numInput.min, 10);
    const max = parseInt(numInput.max, 10);
    const tempVal = parseInt(numInput.value, 10);

    if (isNaN(tempVal) || tempVal < min || tempVal > max) {
      showToast(`Please enter a valid number between ${min} and ${max} for ${fieldName}.`);
      return null;
    }
    return tempVal;
  }
}

// Export for use in other modules
window.modalManager = new ModalManager();
