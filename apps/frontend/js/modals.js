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
    if(settingsModal) {
      this.toggleFuelTargetShowSetting(g_pref_showFuelTarget);
    }
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
    this._showModal(this.driverModal, 'driverModal', () => {
      const modalElement = document.getElementById('driverModal');
      const modalTitle = modalElement.querySelector('.driver-modal-header .modal-title');
      const modalBody = modalElement.querySelector('.modal-body');
      const refreshButton = document.getElementById('refreshButtonDriver');

      modalTitle.textContent = `${data["driver-name"]} - ${getTeamName(data["team"])}`;

      const modalDataPopulator = new DriverModalPopulator(data, this.iconCache);
      modalBody.appendChild(modalDataPopulator.createNavTabs());
      modalBody.appendChild(modalDataPopulator.createTabContent());

      refreshButton.onclick = () => this.refreshDriverData(data);
    });
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
    this._showModal(this.settingsModal, 'settingsModal', () => {
      // Setup radio buttons
      document.getElementById("carsToShow").value = g_pref_numAdjacentCars;
      document.getElementById("teamNameInput").value = g_pref_myTeamName;

      document.getElementById("timeFormat12").checked = !g_pref_is24HourFormat;
      document.getElementById("timeFormat24").checked = g_pref_is24HourFormat;

      document.getElementById("lastLapAbsolute").checked = g_pref_lastLapAbsoluteFormat;
      document.getElementById("lastLapRelative").checked = !g_pref_lastLapAbsoluteFormat;

      document.getElementById("bestLapAbsolute").checked = g_pref_bestLapAbsoluteFormat;
      document.getElementById("bestLapRelative").checked = !g_pref_bestLapAbsoluteFormat;

      document.getElementById("tyreWearAbsolute").checked = !g_pref_tyreWearAverageFormat;
      document.getElementById("tyreWearRelative").checked = g_pref_tyreWearAverageFormat;

      document.getElementById("deltaLeader").checked = !g_pref_relativeDelta;
      document.getElementById("deltaRelative").checked = g_pref_relativeDelta;

      document.getElementById("fuelSurplusLapsGame").checked = !g_pref_fuelSurplusLapsPng;
      document.getElementById("fuelSurplusLapsPng").checked = g_pref_fuelSurplusLapsPng;

      document.getElementById("fuelTargetEnabled").checked = g_pref_showFuelTarget;
      document.getElementById("fuelTargetAverage").checked = g_pref_fuelTargetAverageFormat;
      document.getElementById("fuelTargetNextLap").checked = !g_pref_fuelTargetAverageFormat;

      // Set initial value for volume slider
      const volumeSlider = document.getElementById('volumeRange');
      const volumeLabel = document.getElementById('volumeLabel');
      volumeSlider.value = g_pref_ttsVolume;
      volumeLabel.textContent = g_pref_ttsVolume;

      // Populate the "Text to Speech Voice" dropdown
      const voiceSelect = document.getElementById("voiceSelect");
      voiceSelect.innerHTML = "";
      const voices = window.speechSynthesis.getVoices();
      const defaultVoice = voices[0]?.name || "";
      const selectedVoice = g_pref_ttsVoice || defaultVoice;

      voices.forEach((voice) => {
        const option = document.createElement("option");
        option.value = voice.name;
        option.textContent = `${voice.name} (${voice.lang})`;
        option.selected = (voice.name === selectedVoice);
        voiceSelect.appendChild(option);
      });

      // event listener to "Play Sample" button
      document.getElementById("playSampleButton").onclick = () => {
        const volume = parseInt(document.getElementById('volumeRange').value, 10);
        const lines = [
          "Copy that, we are checking",
          "And box box. Stay Out! Stay Out! Stay Out!",
          "Must be the water",
          "OK Kimi, we have now 5 second time penalty",
        ];
        const randomLine = lines[Math.floor(Math.random() * lines.length)];
        textToSpeech(randomLine, volume);
      };
    });
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
    g_pref_fuelSurplusLapsPng = (document.querySelector('input[name="fuelSurplusLapsSrc"]:checked').value === "png") ? (true) : (false);
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
    this._showModal(this.raceStatsModal, 'raceStatsModal', () => {
      const modalElement = document.getElementById('raceStatsModal');
      const modalTitle = modalElement.querySelector('.race-stats-modal-header .modal-title');
      const modalBody = modalElement.querySelector('.modal-body');
      const refreshButton = document.getElementById('refreshButtonRace');

      modalTitle.textContent = `RACE STATS`;

      const modalDataPopulator = new RaceStatsModalPopulator(data, this.iconCache);
      modalBody.appendChild(modalDataPopulator.createNavTabs());
      modalBody.appendChild(modalDataPopulator.createTabContent());

      // Event Listeners for Buttons
      refreshButton.onclick = () => this.refreshRaceStatsData(data);
    });
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

  _showModal(modalRef, modalId, onShown) {
    const modalElement = document.getElementById(modalId);
    if (!modalRef || !modalElement) {
      console.error(`Modal ${modalId} not initialized`);
      return;
    }

    // Pre-clear stale content
    const modalTitle = modalElement.querySelector('.modal-title');
    const modalBody = modalElement.querySelector('.modal-body');
    if (modalTitle) modalTitle.textContent = '';
    if (modalBody) modalBody.innerHTML = '';

    const isVisible = modalElement.classList.contains('show');

    const wrappedOnShown = () => {
      onShown();

      // 🛠 Ensure first tab and its content are visible (prevents empty panels)
      const firstTab = modalElement.querySelector('.nav-link[data-bs-toggle="tab"]');
      if (firstTab) {
        const tab = new bootstrap.Tab(firstTab);
        tab.show();
      }
    };

    if (isVisible) {
      wrappedOnShown();
    } else {
      modalElement.addEventListener('shown.bs.modal', wrappedOnShown, { once: true });
      modalRef.show();
    }
  }
}
