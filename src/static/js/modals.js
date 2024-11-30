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

    console.log("openDriverModal", data);

    // Update modal title
    modalTitle.textContent = `${data["driver-name"]} - ${data["index"]}`;

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

    // Show the modal
    this.driverModal.show();
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

class DriverModalDataPopulator {
  constructor(data) {
    this.data = data;
  }

  // Method to populate the Overview tab
  populateOverviewTab(tabPane) {
    tabPane.innerHTML = `
      <h5>Driver Overview</h5>
      <p>Name: ${this.data["driver-name"]}</p>
      <p>Index: ${this.data["index"]}</p>
      <p>Team: ${this.data["team"]}</p>
    `;
  }

  // Method to populate the Performance tab
  populatePerformanceTab(tabPane) {
    tabPane.innerHTML = `
      <h5>Performance Details</h5>
      <p>Fastest Lap: ${this.data["fastest-lap"] || "N/A"}</p>
      <p>Last Lap Time: ${this.data["last-lap-time"] || "N/A"}</p>
      <p>Position: ${this.data["position"] || "N/A"}</p>
    `;
  }

  // Method to populate the Strategy tab
  populateStrategyTab(tabPane) {
    tabPane.innerHTML = `
      <h5>Strategy Insights</h5>
      <p>Tyre Strategy: ${this.data["tyre-strategy"] || "N/A"}</p>
      <p>Fuel Remaining: ${this.data["fuel"] || "N/A"}</p>
      <p>Next Pit Stop: ${this.data["next-pit"] || "N/A"}</p>
    `;
  }

  populateLapTimesTab(tabPane) {
    const lapTimeHistory = this.data["lap-time-history"];
    const lapHistoryData = lapTimeHistory["lap-history-data"];

    // Split the tab content into two vertical halves
    const containerDiv = document.createElement('div');
    containerDiv.className = 'd-flex';

    // Left half: Create the lap time table
    const leftDiv = document.createElement('div');
    leftDiv.className = 'w-50';

    const table = document.createElement('table');
    table.className = 'table table-bordered table-striped';

    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const headers = ['Lap', 'S1', 'S2', 'S3', 'Time', 'Tyre', 'Wear'];

    headers.forEach(headerText => {
      const th = document.createElement('th');
      th.textContent = headerText;
      headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');

    lapHistoryData.forEach((lap, index) => {
      const row = document.createElement('tr');

      const lapCell = document.createElement('td');
      lapCell.textContent = index + 1; // Lap number
      row.appendChild(lapCell);

      const sector1Cell = document.createElement('td');
      sector1Cell.textContent = lap["sector-1-time-str"];
      row.appendChild(sector1Cell);

      const sector2Cell = document.createElement('td');
      sector2Cell.textContent = lap["sector-2-time-str"];
      row.appendChild(sector2Cell);

      const sector3Cell = document.createElement('td');
      sector3Cell.textContent = lap["sector-3-time-str"];
      row.appendChild(sector3Cell);

      const lapTimeCell = document.createElement('td');
      lapTimeCell.textContent = lap["lap-time-str"];
      row.appendChild(lapTimeCell);

      const tyreCell = document.createElement('td');
      tyreCell.textContent = lap["tyre-set-info"]["tyre-set"]["visual-tyre-compound"];
      row.appendChild(tyreCell);

      const wearCell = document.createElement('td');
      wearCell.textContent = lap["tyre-set-info"]["tyre-wear"]["average"].toFixed(2) + '%';
      row.appendChild(wearCell);

      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    leftDiv.appendChild(table);

    // Right half: Create the graph for lap times
    const rightDiv = document.createElement('div');
    rightDiv.className = 'w-50 ms-3';

    // Prepare data for the graph
    const sector1Data = lapHistoryData.map((lap, index) => ({
      x: index + 1, // Lap number (index + 1)
      y: lap["sector-1-time-in-ms"] // Time in milliseconds
    }));
    const sector2Data = lapHistoryData.map((lap, index) => ({
      x: index + 1, // Lap number (index + 1)
      y: lap["sector-2-time-in-ms"] // Time in milliseconds
    }));
    const sector3Data = lapHistoryData.map((lap, index) => ({
      x: index + 1, // Lap number (index + 1)
      y: lap["sector-3-time-in-ms"] // Time in milliseconds
    }));
    const totalTimeData = lapHistoryData.map((lap, index) => ({
      x: index + 1, // Lap number (index + 1)
      y: lap["lap-time-in-ms"] // Total lap time in milliseconds
    }));
    console.log("totalTimeData", totalTimeData);

    const datasets = [
      {
        label: "S1",
        data: sector1Data,
        borderColor: 'red',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: false
      },
      {
        label: "S2",
        data: sector2Data,
        borderColor: 'blue',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        fill: false
      },
      {
        label: "S3",
        data: sector3Data,
        borderColor: 'cyan',
        backgroundColor: 'rgba(153, 102, 255, 0.2)',
        fill: false
      },
      {
        label: "Lap",
        data: totalTimeData,
        borderColor: 'purple',
        backgroundColor: 'rgba(153, 102, 255, 0.2)',
        fill: false
      }
    ];

    // Pass the graph data to plotGraph function
    const canvas = document.createElement('canvas');
    rightDiv.appendChild(canvas);
    plotGraph(canvas, datasets, 'Lap', 'Lap Time (ms)', true);

    containerDiv.appendChild(leftDiv);
    containerDiv.appendChild(rightDiv);

    tabPane.appendChild(containerDiv);
  }

  populateFuelUsageTab(tabPane) {
    const fuelUsageData = this.data["per-lap-info"];

    // Split the tab content into two vertical halves
    const containerDiv = document.createElement('div');
    containerDiv.className = 'd-flex';

    // Left half: Create the fuel usage table
    const leftDiv = document.createElement('div');
    leftDiv.className = 'w-50'; // Half width

    const table = document.createElement('table');
    table.className = 'table table-bordered table-striped';

    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const headers = ['Lap', 'Fuel Load (kg)', 'Usage Per Lap (kg)', 'Excess Laps', 'Excess Laps Delta'];

    headers.forEach(headerText => {
      const th = document.createElement('th');
      th.textContent = headerText;
      headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');

    let previousFuelLoad = null;
    let previousExcessLaps = null;

    const fuelUsagePerLap = [];
    fuelUsageData.forEach((lapData, index) => {
      const row = document.createElement('tr');

      const lapCell = document.createElement('td');
      lapCell.textContent = lapData["lap-number"]; // Lap number
      row.appendChild(lapCell);

      const fuelLoadCell = document.createElement('td');
      fuelLoadCell.textContent = lapData["car-status-data"]["fuel-in-tank"].toFixed(2); // Fuel load (kg)
      row.appendChild(fuelLoadCell);

      const usagePerLapCell = document.createElement('td');
      if (previousFuelLoad !== null) {
        const usagePerLap = previousFuelLoad - lapData["car-status-data"]["fuel-in-tank"];
        usagePerLapCell.textContent = usagePerLap.toFixed(2); // Usage per lap (kg)
        fuelUsagePerLap.push({
          x: lapData["lap-number"],
          y: usagePerLap
        });
      } else {
        usagePerLapCell.textContent = '-'; // First lap, no previous value to calculate
      }
      row.appendChild(usagePerLapCell);

      const excessLapsCell = document.createElement('td');
      const excessLaps = lapData["car-status-data"]["fuel-remaining-laps"];
      excessLapsCell.textContent = excessLaps.toFixed(2); // Excess laps
      row.appendChild(excessLapsCell);

      const excessLapsDeltaCell = document.createElement('td');
      if (previousExcessLaps !== null) {
        const excessLapsDelta = excessLaps - previousExcessLaps;
        excessLapsDeltaCell.textContent = excessLapsDelta.toFixed(2); // Excess laps delta
      } else {
        excessLapsDeltaCell.textContent = '-'; // First lap, no previous value to calculate
      }
      row.appendChild(excessLapsDeltaCell);

      tbody.appendChild(row);

      // Update previous values for next iteration
      previousFuelLoad = lapData["car-status-data"]["fuel-in-tank"];
      previousExcessLaps = excessLaps;
    });

    table.appendChild(tbody);
    leftDiv.appendChild(table);

    // Right half: Empty for now
    const rightDiv = document.createElement('div');
    rightDiv.className = 'w-50'; // Half width, empty for now
    rightDiv.style.backgroundColor = '#333'; // Optional: dark background for clarity
    const datasets = [
      {
        label: "Fuel Usage",
        data: fuelUsagePerLap,
        borderColor: 'red',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: false
      }
    ];

    // Pass the graph data to plotGraph function
    const canvas = document.createElement('canvas');
    rightDiv.appendChild(canvas);
    plotGraph(canvas, datasets, 'Lap', 'Fuel used (kg)');

    containerDiv.appendChild(leftDiv);
    containerDiv.appendChild(rightDiv);

    tabPane.appendChild(containerDiv);
  }



  // Method to create the navigation tabs
  createNavTabs() {
    const navTabs = document.createElement('ul');
    navTabs.className = 'nav nav-tabs driver-modal-nav';
    navTabs.setAttribute('role', 'tablist');

    // Array of tabs with ID and label
    const tabs = [
      { id: 'lap-times', label: 'Lap Times' },  // New Lap Times tab
      { id: 'fuel-usage', label: 'Fuel Usage History' },  // New Lap Times tab
    ];

    // Sort tabs alphabetically based on the label
    tabs.sort((a, b) => a.label.localeCompare(b.label));

    tabs.forEach((tab, index) => {
      const navItem = document.createElement('li');
      navItem.className = 'nav-item';
      navItem.setAttribute('role', 'presentation');

      const navLink = document.createElement('button');
      navLink.className = `nav-link driver-modal-nav-link ${index === 0 ? 'active' : ''}`;
      navLink.id = `${tab.id}-tab`;
      navLink.setAttribute('data-bs-toggle', 'tab');
      navLink.setAttribute('data-bs-target', `#${tab.id}`);
      navLink.setAttribute('type', 'button');
      navLink.setAttribute('role', 'tab');
      navLink.setAttribute('aria-controls', tab.id);
      navLink.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
      navLink.textContent = tab.label;

      navItem.appendChild(navLink);
      navTabs.appendChild(navItem);
    });

    return navTabs;
  }

  // Method to create the tab content container
  createTabContent() {
    const tabContent = document.createElement('div');
    tabContent.className = 'tab-content driver-modal-tab-content';

    // Array of tabs with ID and method to populate content
    const tabs = [
      { id: 'lap-times', method: this.populateLapTimesTab },  // Lap Times tab
      { id: 'fuel-usage', method: this.populateFuelUsageTab },  // Lap Times tab
    ];

    // Sort tabs alphabetically based on the label
    tabs.sort((a, b) => a.id.localeCompare(b.id));

    tabs.forEach((tab, index) => {
      const tabPane = document.createElement('div');
      tabPane.className = `tab-pane fade driver-modal-tab-pane ${index === 0 ? 'show active' : ''}`;
      tabPane.id = tab.id;
      tabPane.setAttribute('role', 'tabpanel');
      tabPane.setAttribute('aria-labelledby', `${tab.id}-tab`);

      // Populate the tab content using the respective method
      tab.method.call(this, tabPane);

      tabContent.appendChild(tabPane);
    });

    return tabContent;
  }
}



// Export for use in other modules
window.modalManager = new ModalManager();