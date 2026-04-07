class TelemetryRenderer {
  constructor(iconCache) {
    this.timeTrialDataPopulator = new TimeTrialDataPopulator();
    this.splashDiv = document.getElementById('splash-div');
    this.raceTableDiv = document.getElementById('race-table-div');
    this.timeTrialDiv = document.getElementById('time-trial-div');
    this.telemetryTable = document.getElementById('telemetry-data');
    this.weatherWidget = new WeatherWidget(document.getElementById('weather-predictions'));
    this.fastestLapTimeSpan = document.getElementById('fastestLapTimeSpan');
    this.fastestLapNameSpan = document.getElementById('fastestLapNameSpan');
    this.fastestLapTyreSpan = document.getElementById('fastestLapTyreSpan');
    this.trackName = document.getElementById('track-name');
    this.pitLaneSpeedLimit = document.getElementById('pit-speed-limit');
    this.trackTempSpan = document.getElementById('track-temp');
    this.airTempSpan = document.getElementById('air-temp');
    this.indexByPosition = null;
    this.iconCache = iconCache;
    this.uiMode = 'Splash';
    this.driverContextMap = new Map();
    this.sessionUID = null;

    this.connected = null;
    this.statusContainer   = document.getElementById('status-wrapper')
    this.blinkingDot       = document.createElement('span')
    this.statusText        = document.createElement('p')

    this.blinkingDot.classList.add('blinking-dot')
    this.statusContainer.append(this.blinkingDot, this.statusText)

    // Column config
    this.columnConfig = new ColumnConfig();
    this.allColumnsHiddenHint = document.getElementById('all-columns-hidden-hint');
    this.lastIncomingData = null;
    this.columnConfig.onChange(() => {
      this.applyHeaderVisibility();
      this.updateAllColumnsHiddenHint();
      if (this.lastIncomingData) {
        this.updateRaceTableData(this.lastIncomingData);
      }
    });
    this.initColumnConfigPanel();
    this.applyHeaderVisibility();
    this.updateAllColumnsHiddenHint();
    this._handleAutoPreset();
  }

  renderTelemetryRow(data, packetFormat, isLiveDataMode, raceEnded, spectatorIndex, sessionType, driverContext) {
    const { 'driver-info': driverInfo } = data;
    const row = document.createElement('tr');

    // Populate row with data
    new RaceTableRowPopulator(row, data, packetFormat, isLiveDataMode, this.iconCache, raceEnded, spectatorIndex,
                                     sessionType, driverContext, this.columnConfig).populate();

    // Apply CSS classes based on row state
    const cssClasses = this.determineRowClasses(driverInfo, isLiveDataMode, spectatorIndex);
    row.classList.add(...cssClasses);

    return row;
  }

  determineRowClasses(driverInfo, isLiveDataMode, spectatorIndex) {
    const classes = [];

    if ((spectatorIndex !== null && driverInfo['index'] === spectatorIndex) ||
        (spectatorIndex === null && driverInfo['is-player'])) {
      classes.push('player-row');
    }

    if (driverInfo['dnf-status'] === 'DNF') {
      classes.push('dnf-row');
    }

    else if (isLiveDataMode && driverInfo['drs']) {
      classes.push('drs-row');
    }

    return classes;
  }

  updateDashboard(incomingData) {

    const sessionType = incomingData["session-type"];
    switch (sessionType) {
      case "Time Trial":
        this.updateTimeTrialData(incomingData);
        break;
      case "Unknown":
      case "---":
        this.updateConnectedStatus(incomingData["wdt-status"]);
        this.setUIMode('Splash');
        break;
      default:
        this.updateRaceTableData(incomingData);
        break;
    }

    // update the header section regardless of mode
    this.updateHeader(incomingData);
  }

  updateTimeTrialData(incomingData) {

    // enable the time trial UI and set the data
    this.setUIMode('Time Trial');
    this.timeTrialDataPopulator.populate(incomingData["tt-data"], incomingData["packet-format"]);
  }

  // Extract existing driver rows and remove them from the DOM
  extractDriverRows() {
    const driverRowMap = new Map();
    Array.from(this.telemetryTable.querySelectorAll('tr[data-driver-index]')).forEach(row => {
      const driverIndex = row.getAttribute('data-driver-index');
      const existingContext = this.driverContextMap.get(driverIndex) || {};
      driverRowMap.set(driverIndex, { row: row, context: existingContext });
      row.parentNode.removeChild(row);
    });
    return driverRowMap;
  }

  // Ensure the header row is preserved
  preserveHeaderRow() {
    if (this.telemetryTable.children.length === 1) {
      const headerRow = this.telemetryTable.children[0];
      this.telemetryTable.textContent = '';
      this.telemetryTable.appendChild(headerRow);
    }
  }

  // Update or create row based on existing data
  updateOrCreateRow(driverRowObj, data, packetFormat, isLiveDataMode, driverIndex, raceEnded, spectatorIndex, sessionType) {
    const newRow = this.renderTelemetryRow(data, packetFormat, isLiveDataMode, raceEnded, spectatorIndex, sessionType,
                          driverRowObj.context);
    if (driverRowObj.row) {
      driverRowObj.row.replaceChildren(...Array.from(newRow.childNodes));
    } else {
      driverRowObj.row = newRow;
      driverRowObj.row.setAttribute('data-driver-index', driverIndex);
    }
    this.driverContextMap.set(driverIndex, driverRowObj.context);
    return driverRowObj;
  }

  updateRaceTableData(incomingData) {
    this.lastIncomingData = incomingData;
    this.setUIMode('Race');
    const isLiveDataMode = incomingData["live-data"];
    const raceEnded = incomingData["race-ended"];
    const spectatorMode = incomingData["is-spectating"];
    const spectatorCarIndex = incomingData["spectator-car-index"];
    const sessionType = incomingData["session-type"];

    if (this.sessionUID != incomingData["session-uid"]) {
      // reset map when session changes
      this.driverContextMap = new Map();
    }
    this.sessionUID = incomingData["session-uid"];

    this.setDeltaColumnState(isLiveDataMode);
    this.setFuelColumnState(isLiveDataMode, sessionType);
    this.setCurrLapColumnState(isLiveDataMode, sessionType);
    this.setWearPredictionColumnState(isLiveDataMode, sessionType);
    this.setWingDamageColumnState(sessionType);

    const shouldInsertRejoinPositions = true;
    const tableEntries = getRelevantRaceTableRows(incomingData, g_pref_numAdjacentCars, shouldInsertRejoinPositions);
    updateReferenceLapTimes(tableEntries,
      (spectatorMode) ?
      ((entry) => entry["driver-info"]?.["index"] == spectatorCarIndex) :
      ((entry) => entry["driver-info"]?.["is-player"])
    );
    const packetFormat = incomingData["packet-format"];
    this.indexByPosition = incomingData["table-entries"].map(entry => entry["driver-info"]["index"]);

    // Extract and remove existing driver rows
    const driverRowMap = this.extractDriverRows();
    // Preserve header row if needed
    this.preserveHeaderRow();

    tableEntries.forEach(data => {
      const driverIndex = data["driver-info"]["index"];
      let driverRowObj = driverRowMap.get(driverIndex);

      if (!driverRowObj) {
        const existingContext = this.driverContextMap.get(driverIndex) || {};
        driverRowObj = { row: null, context: existingContext };
      }

      driverRowObj = this.updateOrCreateRow(driverRowObj, data, packetFormat, isLiveDataMode, driverIndex, raceEnded, spectatorCarIndex,
                                    sessionType);
      this.telemetryTable.appendChild(driverRowObj.row);
    });
    // Rows not referenced in tableEntries will be left out
  }

  updateHeader(incomingData) {
    const weatherSamples = incomingData['weather-forecast-samples'].slice(0, g_pref_numWeatherPredictionSamples);
    this.weatherWidget.update(weatherSamples);

    this.fastestLapTimeSpan.textContent = formatLapTime(incomingData['fastest-lap-overall']);
    this.fastestLapNameSpan.textContent = (incomingData['event-type'] === 'Time Trial') ?
        ('') : (getTLA(incomingData['fastest-lap-overall-driver']));

    this.fastestLapTyreSpan.textContent = '';
    const fastestLapTyre = incomingData['fastest-lap-overall-tyre'];
    if (fastestLapTyre) {
      const icon = this.iconCache.getIcon(fastestLapTyre);
      if (icon) {
        this.fastestLapTyreSpan.appendChild(icon);
      }
    }

    this.populateCircuitSpan(incomingData);
    this.airTempSpan.textContent = formatTemperature(incomingData['air-temperature'], {
      isMetric: g_pref_tempUnitMetric,
      decimalPlaces: 0,
      addUnitSuffix: true
    });
    this.trackTempSpan.textContent = formatTemperature(incomingData['track-temperature'], {
      isMetric: g_pref_tempUnitMetric,
      decimalPlaces: 0,
      addUnitSuffix: true
    });
  }


  // Utility methods:
  populateCircuitSpan(incomingData) {
    this.populateTrackName(incomingData);
    const pitLaneSpeedLimit = incomingData['pit-speed-limit'];
    if (pitLaneSpeedLimit) {
      this.pitLaneSpeedLimit.textContent = formatSpeed(pitLaneSpeedLimit, {
        isMetric: g_pref_speedUnitMetric,
        decimalPlaces: 0,
        addUnitSuffix: false
      });
      this.pitLaneSpeedLimit.style.display = "inline-flex"; // Ensure it's visible if there's a value
    } else {
      this.pitLaneSpeedLimit.style.display = "none"; // Hide if the value is 0;
    }
  }

  populateTrackName(incomingData) {
    const trackName = incomingData['circuit'];
    const trackNameContainer = this.trackName;

    // Clear any existing content in the span
    trackNameContainer.textContent = "";
    if ("---" === trackName) {
      this.trackName.textContent = "PITS N' GIGGLES";
    } else {
      // Create the first div for the track name
      const trackNameDiv = document.createElement("div");
      trackNameDiv.textContent = replaceRevSuffix(trackName).toUpperCase();
      trackNameDiv.style.textAlign = "center";
      trackNameDiv.style.margin = "0 auto";
      trackNameContainer.appendChild(trackNameDiv);

      // Create the second div for session info
      const sessionInfoDiv = document.createElement("div");
      sessionInfoDiv.style.textAlign = "center";
      sessionInfoDiv.style.margin = "0 auto";

      let sessionInfoText = "";
      if (this.shouldShowLapNumber(incomingData['event-type'])) {
        if (incomingData['current-lap']) {
          sessionInfoText += "L" + incomingData['current-lap'].toString();
        }
        if (incomingData['event-type'] != "Time Trial" && ((incomingData['total-laps'] ?? 0) > 1)) {
          sessionInfoText += "/" + incomingData['total-laps'].toString();
        }
      } else {
        const sessionTime = incomingData['session-time-left'];
        sessionInfoText += formatSecondsToMMSS(sessionTime);
      }

      sessionInfoDiv.textContent = sessionInfoText;
      trackNameContainer.appendChild(sessionInfoDiv);
    }
  }

  shouldShowLapNumber(sessionType) {
    const unsupportedSessionTypes = ['Qualifying', 'Practice', 'Sprint Shootout'];
    return !unsupportedSessionTypes.some(type => sessionType.includes(type));
  }

  setDeltaColumnState(isLiveDataMode) {
    this.columnConfig.setSessionOverride('delta', !isLiveDataMode);
    this.applyHeaderVisibility();
  }

  setFuelColumnState(isLiveDataMode, sessionType) {
    const allowed = isLiveDataMode && isRaceSession(sessionType);
    this.columnConfig.setSessionOverride('fuel', allowed);
    this.applyHeaderVisibility();
  }

  setCurrLapColumnState(isLiveDataMode, sessionType) {
    const allowed = isLiveDataMode && !isRaceSession(sessionType);
    this.columnConfig.setSessionOverride('current-lap', allowed);
    this.applyHeaderVisibility();
  }

  setWearPredictionColumnState(isLiveDataMode, sessionType) {
    const allowed = isLiveDataMode && isRaceSession(sessionType);
    this.columnConfig.setSessionOverride('wear-prediction', allowed);
    this.applyHeaderVisibility();
  }

  setWingDamageColumnState(sessionType) {
    const allowed = isRaceSession(sessionType);
    this.columnConfig.setSessionOverride('damage', allowed);
    this.applyHeaderVisibility();
  }

  applyHeaderVisibility() {
    const table = document.getElementById('race-table');
    const headers = table.querySelectorAll('th[data-column-group]');
    headers.forEach(th => {
      const group = th.getAttribute('data-column-group');
      th.style.display = this.columnConfig.isVisible(group) ? '' : 'none';
    });
  }

  updateAllColumnsHiddenHint() {
    if (!this.allColumnsHiddenHint) return;
    this.allColumnsHiddenHint.style.display =
      this.columnConfig.areAllUserColumnsHidden() ? '' : 'none';
  }

  initColumnConfigPanel() {
    const panel = document.getElementById('settings-panel');
    const columnBtn = document.getElementById('column-config-btn');
    const settingsBtn = document.getElementById('settings-btn');
    const closeBtn = document.getElementById('settings-panel-close-btn');
    const resetBtn = document.getElementById('reset-columns-btn');
    const saveSettingsBtn = document.getElementById('saveSettings');
    const togglesContainer = document.getElementById('column-toggles-container');
    const presetsContainer = document.getElementById('preset-buttons-container');
    const tabButtons = panel.querySelectorAll('.panel-tab');
    const tabColumns = document.getElementById('tab-columns');
    const tabDisplay = document.getElementById('tab-display');

    if (!panel) return;

    this._activeSettingsTab = 'columns';

    const refreshPanel = () => {
      this.populatePresetButtons(presetsContainer);
      this.populateColumnToggles(togglesContainer);
      this.populateCustomPresetButton();
    };

    const switchTab = (tabName) => {
      this._activeSettingsTab = tabName;
      tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
      });
      tabColumns.style.display = tabName === 'columns' ? '' : 'none';
      tabDisplay.style.display = tabName === 'display' ? '' : 'none';
      // Toggle footer buttons
      resetBtn.style.display = tabName === 'columns' ? '' : 'none';
      saveSettingsBtn.style.display = tabName === 'display' ? '' : 'none';
    };

    const openPanel = (tabName) => {
      if (!panel.classList.contains('open')) {
        panel.classList.add('open');
        refreshPanel();
      }
      switchTab(tabName || this._activeSettingsTab);
      // If opening display tab, populate settings fields
      if ((tabName || this._activeSettingsTab) === 'display' && window.modalManager) {
        window.modalManager.populateSettingsFields();
      }
    };

    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        switchTab(btn.dataset.tab);
        if (btn.dataset.tab === 'display' && window.modalManager) {
          window.modalManager.populateSettingsFields();
        }
      });
    });

    if (columnBtn) {
      columnBtn.addEventListener('click', () => {
        if (panel.classList.contains('open') && this._activeSettingsTab === 'columns') {
          panel.classList.remove('open');
        } else {
          openPanel('columns');
        }
      });
    }

    // settings-btn click is handled by ModalManager — we set up a fallback here
    // that gets overridden by ModalManager.setupEventListeners if settingsModal is true
    this._openSettingsPanel = openPanel;

    closeBtn.addEventListener('click', () => panel.classList.remove('open'));

    resetBtn.addEventListener('click', () => {
      this.columnConfig.resetToDefault();
      refreshPanel();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && panel.classList.contains('open')) {
        panel.classList.remove('open');
      }
    });

    // Listen for config changes to refresh preset highlighting
    this.columnConfig.onChange(() => {
      if (panel.classList.contains('open')) {
        this.populatePresetButtons(presetsContainer);
        this.populateCustomPresetButton();
      }
    });
  }

  populatePresetButtons(container) {
    container.textContent = '';
    ColumnConfig.PRESETS.forEach(preset => {
      const btn = document.createElement('button');
      btn.classList.add('preset-btn');
      if (this.columnConfig.activePreset === preset.id) {
        btn.classList.add('active');
      }
      btn.innerHTML = `<span class="preset-emoji">${preset.emoji}</span>${preset.label}`;
      btn.addEventListener('click', () => {
        this.columnConfig.applyPreset(preset.id);
        const togglesContainer = document.getElementById('column-toggles-container');
        this.populateColumnToggles(togglesContainer);
      });
      container.appendChild(btn);
    });

    // Custom preset button (if saved)
    if (this.columnConfig.hasCustomPreset()) {
      const customBtn = document.createElement('button');
      customBtn.classList.add('preset-btn');
      if (this.columnConfig.activePreset === 'custom') {
        customBtn.classList.add('active');
      }
      customBtn.innerHTML = `<span class="preset-emoji">🎯</span>My Layout`;
      customBtn.addEventListener('click', () => {
        this.columnConfig.applyPreset('custom');
        const togglesContainer = document.getElementById('column-toggles-container');
        this.populateColumnToggles(togglesContainer);
      });

      // Delete button
      const deleteBtn = document.createElement('button');
      deleteBtn.classList.add('preset-delete');
      deleteBtn.innerHTML = '✕';
      deleteBtn.title = 'Delete custom layout';
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.columnConfig.deleteCustomPreset();
        this.populatePresetButtons(container);
        this.populateCustomPresetButton();
      });
      customBtn.appendChild(deleteBtn);
      container.appendChild(customBtn);
    }
  }

  populateCustomPresetButton() {
    const container = document.getElementById('save-custom-preset-container');
    if (!container) return;
    container.textContent = '';

    const btn = document.createElement('button');
    btn.classList.add('save-custom-preset-btn');
    btn.textContent = '💾 Save as My Layout';
    btn.addEventListener('click', () => {
      this.columnConfig.saveCustomPreset();
      const presetsContainer = document.getElementById('preset-buttons-container');
      this.populatePresetButtons(presetsContainer);
      this.populateCustomPresetButton();
    });
    container.appendChild(btn);
  }

  populateColumnToggles(container) {
    container.textContent = '';
    ColumnConfig.COLUMN_GROUPS.forEach(group => {
      // Parent toggle
      const div = document.createElement('div');
      div.classList.add('form-check', 'form-switch', 'column-toggle-item');

      const input = document.createElement('input');
      input.classList.add('form-check-input');
      input.type = 'checkbox';
      input.role = 'switch';
      input.id = `col-toggle-${group.id}`;
      input.setAttribute('aria-label', `Toggle ${group.label} column visibility`);

      if (group.children) {
        const state = this.columnConfig.getParentCheckState(group.id);
        input.checked = state !== 'none';
        input.indeterminate = state === 'indeterminate';
      } else {
        input.checked = this.columnConfig.isUserEnabled(group.id);
      }

      input.addEventListener('change', () => {
        this.columnConfig.setUserVisible(group.id, input.checked);
        // Re-render to update indeterminate states
        this.populateColumnToggles(container);
        // Update preset highlighting
        const presetsContainer = document.getElementById('preset-buttons-container');
        this.populatePresetButtons(presetsContainer);
      });

      const label = document.createElement('label');
      label.classList.add('form-check-label');
      label.htmlFor = `col-toggle-${group.id}`;
      label.textContent = group.label;

      div.appendChild(input);
      div.appendChild(label);
      container.appendChild(div);

      // Child toggles (sub-toggles)
      if (group.children) {
        group.children.forEach(child => {
          const childDiv = document.createElement('div');
          childDiv.classList.add('form-check', 'form-switch', 'column-toggle-sub-item');

          const childInput = document.createElement('input');
          childInput.classList.add('form-check-input');
          childInput.type = 'checkbox';
          childInput.role = 'switch';
          childInput.id = `col-toggle-${child.id}`;
          childInput.checked = this.columnConfig.isUserEnabled(child.id);
          childInput.setAttribute('aria-label', `Toggle ${child.label} visibility`);

          childInput.addEventListener('change', () => {
            this.columnConfig.setUserVisible(child.id, childInput.checked);
            this.populateColumnToggles(container);
            const presetsContainer = document.getElementById('preset-buttons-container');
            this.populatePresetButtons(presetsContainer);
          });

          const childLabel = document.createElement('label');
          childLabel.classList.add('form-check-label');
          childLabel.htmlFor = `col-toggle-${child.id}`;
          childLabel.textContent = child.label;

          childDiv.appendChild(childInput);
          childDiv.appendChild(childLabel);
          container.appendChild(childDiv);
        });
      }
    });
  }

  _handleAutoPreset() {
    const applied = this.columnConfig.checkAutoPreset();
    if (!applied) return;

    const toast = document.getElementById('auto-preset-toast');
    if (!toast) return;

    toast.style.display = 'flex';

    const dismiss = () => { toast.style.display = 'none'; };
    const dismissBtn = document.getElementById('auto-preset-toast-dismiss');
    if (dismissBtn) dismissBtn.addEventListener('click', dismiss);
    setTimeout(dismiss, 5000);
  }

  setUIMode(uiMode) {

    // only process on change
    if (this.uiMode === uiMode) {
      return;
    }

    console.log(`changing UI mode from ${this.uiMode} to ${uiMode}`);
    this.uiMode = uiMode;
    switch(uiMode) {
      case 'Splash':
        this.splashDiv.style.display = '';
        this.raceTableDiv.style.display = 'none';
        this.timeTrialDiv.style.display = 'none';
        break;
      case 'Time Trial':
        this.splashDiv.style.display = 'none';
        this.raceTableDiv.style.display = 'none';
        this.timeTrialDiv.style.display = '';
        break;
      case 'Race':
        this.splashDiv.style.display = 'none';
        this.raceTableDiv.style.display = '';
        this.timeTrialDiv.style.display = 'none';
        break;
      default:
        console.error('Unknown UI mode:', uiMode);
        break;
    }
  }

  updateConnectedStatus(connected) {
    if (this.uiMode !== 'Splash' || this.connected === connected) {
      return
    }
    this.connected = connected

    // toggle color class
    this.blinkingDot.classList.toggle('green', connected)
    this.blinkingDot.classList.toggle('red', !connected)

    // update text
    this.statusText.textContent = connected
      ? 'Connected to F1 game. Waiting for session start ...'
      : 'Waiting for F1 game UDP telemetry data ...'
  }

}