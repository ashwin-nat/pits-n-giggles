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

  openDriverModal(driver) {
    const modalTitle = document.querySelector('#driverModal .modal-title');
    const modalBody = document.querySelector('#driverModal .modal-body');
    
    modalTitle.textContent = `${driver.driver} - Position ${driver.position}`;
    modalBody.innerHTML = `
      <div class="driver-stats">
        <h6>Lap Times</h6>
        <p>Last Lap: ${driver.lastLap}</p>
        <p>Best Lap: ${driver.bestLap}</p>
        <p>Delta: ${driver.delta}</p>
        
        <h6 class="mt-4">Tyre Information</h6>
        <p>Compound: <span class="tyre-compound tyre-${driver.tyreInfo.compound}">${driver.tyreInfo.compound.toUpperCase()}</span></p>
        <p>Age: ${driver.tyreInfo.age} laps</p>
        <p>Wear: ${driver.tyreInfo.wear}%</p>
        <p>Prediction: ${driver.tyreInfo.prediction}</p>
        
        <h6 class="mt-4">Power Unit</h6>
        <p>ERS: ${driver.ers}%</p>
        <p>Fuel: ${driver.fuel}%</p>
      </div>
    `;
    
    this.driverModal.show();
  }

  openSettingsModal() {
    this.settingsModal.show();
  }

  saveSettings() {
    const carsToShow = document.getElementById('carsToShow').value;
    const updateInterval = document.getElementById('updateInterval').value;
    
    // Save settings to localStorage
    localStorage.setItem('dashboardSettings', JSON.stringify({
      carsToShow: parseInt(carsToShow),
      updateInterval: parseInt(updateInterval)
    }));
    
    this.settingsModal.hide();
    
    // Dispatch event for other components to react to settings changes
    window.dispatchEvent(new CustomEvent('settingsChanged'));
  }
}

// Export for use in other modules
window.modalManager = new ModalManager();