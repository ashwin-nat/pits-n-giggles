class ModalManager {
  constructor(driverModal=true, settingsModal=true, raceStatsModal=true) {
    const modalElement = document.getElementById('driverModal');
    console.log("modalElement", modalElement);
    this.driverModal = (driverModal) ? (new bootstrap.Modal(modalElement)) : (null);
    this.settingsModal = (settingsModal) ? (new bootstrap.Modal(document.getElementById('settingsModal'))) : (null);
    this.raceStatsModal = (raceStatsModal) ? (new bootstrap.Modal(document.getElementById('raceStatsModal'))) : (null);
    this.iconCache = new IconCache();
    this.setupEventListeners();
    console.log("Modal manager initialized with driverModal:", driverModal,
      "settingsModal:", settingsModal, "raceStatsModal:", raceStatsModal);
    this.toggleFuelTargetShowSetting(g_pref_showFuelTarget);
  }

  setupEventListeners() {
    if (this.settingsModal) {
      document.getElementById('settings-btn').addEventListener('click', () => this.openSettingsModal());
      document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());
      document.getElementById('fuelTargetEnabled').addEventListener('change', (event) => {
        this.toggleFuelTargetShowSetting(event.target.checked);
      });
    }
    if (this.raceStatsModal) {
      document.getElementById('race-stats-btn').addEventListener('click', () => {
        socketio.emit('race-info', { 'message': 'dummy' });
      });
    }
  }

  toggleFuelTargetShowSetting(enabled) {
    const isDisabled = !enabled; // Disable when checkbox is unchecked
    document.getElementById('fuelTargetAverage').disabled = isDisabled;
    document.getElementById('fuelTargetNextLap').disabled = isDisabled;
    console.log("Changed fuel target state to ", !isDisabled);
  }

  openDriverModal(data) {
    if (!this.driverModal) {
      console.error("Driver modal not initialized");
      return;
    }
    const modalTitle = document.querySelector('#driverModal .driver-modal-header .modal-title');
    const modalBody = document.querySelector('#driverModal .modal-body');
    const refreshButton = document.getElementById('refreshButtonDriver');

    // Update modal title
    modalTitle.textContent = `${data["driver-name"]} - ${getTeamName(data["team"])}`;

    // Clear existing content
    modalBody.innerHTML = '';

    // Create the modal content using the DriverModalPopulator class
    const modalDataPopulator = new DriverModalPopulator(data, this.iconCache);

    // Create and append navigation tabs
    const navTabs = modalDataPopulator.createNavTabs();
    modalBody.appendChild(navTabs);

    // Create and append tab content
    const tabContent = modalDataPopulator.createTabContent();
    modalBody.appendChild(tabContent);

    // Event Listeners for Buttons
    refreshButton.onclick = () => this.refreshDriverData(data);

    // Show the modal
    this.driverModal.show();
  }

  refreshDriverData(data) {
    console.log("Refresh clicked", data);
    const requestPayload = {
      "index" : data["index"],
      "__dummy" : {
        "refresh" : true
      }
    };
    sendSynchronousRequest('driver-info', requestPayload, 'driver-info-response')
      .then(driverInfo => {
        console.log('Driver info sync response received:', driverInfo);
        this.openDriverModal(driverInfo, this.iconCache); // Reload the modal with the current data
      })
      .catch(error => {
        console.error('Error fetching driver info:', error);
      });
  }

  openSettingsModal() {

    if (!this.settingsModal) {
      console.error("Settings modal not initialized");
      return;
    }

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

    // Set the radio buttons for tyre wear format
    document.getElementById("deltaLeader").checked = !g_pref_relativeDelta;
    document.getElementById("deltaRelative").checked = g_pref_relativeDelta;

    // Set the switch for fuel target show
    document.getElementById("fuelTargetEnabled").checked = g_pref_showFuelTarget;

    // Set the radio buttons for fuel
    document.getElementById("fuelTargetAverage").checked = g_pref_fuelTargetAverageFormat;
    document.getElementById("fuelTargetNextLap").checked = !g_pref_fuelTargetAverageFormat;

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
    g_pref_relativeDelta = (document.querySelector('input[name="deltaFormat"]:checked').value === "relative") ? (true) : (false);
    g_pref_showFuelTarget = (document.getElementById('fuelTargetEnabled').checked) ? (true) : (false);
    g_pref_fuelTargetAverageFormat = (document.querySelector('input[name="fuelFormat"]:checked').value === "average") ? (true) : (false);
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

  openRaceStatsModal(data) {

    if (!this.raceStatsModal) {
      this.console.error("Race stats modal not initialized");
      return;
    }

    const modalTitle = document.querySelector('#raceStatsModal .race-stats-modal-header .modal-title');
    const modalBody = document.querySelector('#raceStatsModal .modal-body');
    const refreshButton = document.getElementById('refreshButtonRace');

    // Update modal title
    modalTitle.textContent = `RACE STATS`;

    // Clear existing content
    modalBody.innerHTML = '';

    // Create the modal content using the RaceStatsModalPopulator class
    const modalDataPopulator = new RaceStatsModalPopulator(data);

    // Create and append navigation tabs
    const navTabs = modalDataPopulator.createNavTabs();
    modalBody.appendChild(navTabs);

    // Create and append tab content
    const tabContent = modalDataPopulator.createTabContent();
    modalBody.appendChild(tabContent);

    // Event Listeners for Buttons
    refreshButton.onclick = () => this.refreshRaceStatsData(data);

    // Show the modal
    this.raceStatsModal.show();
  }

  refreshRaceStatsData(data) {
    console.log("Refresh race stats clicked", data);
    const requestPayload = {
      "__dummy" : {
        "refresh" : true
      }
    };
    sendSynchronousRequest('race-info', requestPayload, 'race-info-response')
      .then(raceInfo => {
        console.log('Race info sync response received:', raceInfo);
        this.openRaceStatsModal(data); // Reload the modal with the current data
      })
      .catch(error => {
        console.error('Error fetching race info:', error);
      });
  }
}
