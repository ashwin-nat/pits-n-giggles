class F1LapSectorRecords {
  constructor(containerDiv) {
    this.container = containerDiv;
    this.data = null;
    this.init();
  }

  init() {
    this.container.className = 'f1-lapsec-records';
    this.showLoading();
  }

  showLoading() {
    this.container.innerHTML = '';
    const loadingDiv = this.createElement('div', 'f1-lapsec-records-loading');
    loadingDiv.textContent = 'Loading records...';
    this.container.appendChild(loadingDiv);
  }

  showError(message = 'Error loading records') {
    this.container.innerHTML = '';
    const errorDiv = this.createElement('div', 'f1-lapsec-records-error');
    errorDiv.textContent = message;
    this.container.appendChild(errorDiv);
  }

  createElement(tag, className = '', textContent = '') {
    const element = document.createElement(tag);
    if (className) {
      element.className = className;
    }
    if (textContent) {
      element.textContent = textContent;
    }
    return element;
  }

  formatTime(timeStr) {
    return timeStr || '--:--.---';
  }

  createHeader() {
    const header = this.createElement('div', 'f1-lapsec-records-header');

    const title = this.createElement('h1', 'f1-lapsec-records-title', 'Track Records');
    const subtitle = this.createElement('p', 'f1-lapsec-records-subtitle', 'Fastest Lap & Sector Times');

    header.appendChild(title);
    header.appendChild(subtitle);

    return header;
  }

  createFastestLapSection() {
    const section = this.createElement('div', 'f1-lapsec-records-fastest-lap');

    const sectionTitle = this.createElement('div', 'f1-lapsec-records-section-title');
    const icon = this.createElement('div', 'f1-lapsec-records-section-icon', '🏆');
    const titleText = this.createElement('span', '', 'Fastest Lap');
    sectionTitle.appendChild(icon);
    sectionTitle.appendChild(titleText);

    if (!this.data.lap) {
      const noData = this.createElement('div', 'f1-lapsec-records-no-data', 'No fastest lap data available');
      section.appendChild(sectionTitle);
      section.appendChild(noData);
      return section;
    }

    const driverInfo = this.createElement('div', 'f1-lapsec-records-driver-info');

    const teamNameStr = getTeamName(this.data.lap['team-id']);
    const driverDetails = this.createElement('div', 'f1-lapsec-records-driver-details');
    const driverName = this.createElement('h3', '', this.data.lap['driver-name'] || 'Unknown Driver');
    const teamName = this.createElement('p', '', teamNameStr);
    driverDetails.appendChild(driverName);
    driverDetails.appendChild(teamName);

    const lapInfo = this.createElement('div', 'f1-lapsec-records-lap-info');
    const time = this.createElement('p', 'f1-lapsec-records-time', this.formatTime(this.data.lap['time-str']));
    const lapNumber = this.createElement('p', 'f1-lapsec-records-lap-number',
      this.data.lap['lap-number'] ? `Lap ${this.data.lap['lap-number']}` : 'Lap --');
    lapInfo.appendChild(time);
    lapInfo.appendChild(lapNumber);

    driverInfo.appendChild(driverDetails);
    driverInfo.appendChild(lapInfo);

    const stats = this.createElement('div', 'f1-lapsec-records-stats');

    const teamStat = this.createElement('div', 'f1-lapsec-records-stat');
    const teamLabel = this.createElement('p', 'f1-lapsec-records-stat-label', 'Team');
    const teamValue = this.createElement('p', 'f1-lapsec-records-stat-value', teamNameStr || 'Unknown');
    teamStat.appendChild(teamLabel);
    teamStat.appendChild(teamValue);

    const lapStat = this.createElement('div', 'f1-lapsec-records-stat');
    const lapLabel = this.createElement('p', 'f1-lapsec-records-stat-label', 'Lap');
    const lapValue = this.createElement('p', 'f1-lapsec-records-stat-value',
      this.data.lap['lap-number'] ? this.data.lap['lap-number'].toString() : '--');
    lapStat.appendChild(lapLabel);
    lapStat.appendChild(lapValue);

    const timeStat = this.createElement('div', 'f1-lapsec-records-stat');
    const timeLabel = this.createElement('p', 'f1-lapsec-records-stat-label', 'Time');
    const timeValue = this.createElement('p', 'f1-lapsec-records-stat-value', this.formatTime(this.data.lap['time-str']));
    timeStat.appendChild(timeLabel);
    timeStat.appendChild(timeValue);

    stats.appendChild(teamStat);
    stats.appendChild(lapStat);
    stats.appendChild(timeStat);

    section.appendChild(sectionTitle);
    section.appendChild(driverInfo);
    section.appendChild(stats);

    return section;
  }

  createSectorRecord(sectorData, sectorName) {
    const sector = this.createElement('div', 'f1-lapsec-records-sector');

    const header = this.createElement('div', 'f1-lapsec-records-sector-header');
    const label = this.createElement('h4', 'f1-lapsec-records-sector-label', sectorName);

    if (!sectorData) {
      const time = this.createElement('p', 'f1-lapsec-records-sector-time', '--:--.---');
      header.appendChild(label);
      header.appendChild(time);

      const driver = this.createElement('p', 'f1-lapsec-records-sector-driver', 'No Data');
      const team = this.createElement('p', 'f1-lapsec-records-sector-team', '--');

      sector.appendChild(header);
      sector.appendChild(driver);
      sector.appendChild(team);

      return sector;
    }

    const time = this.createElement('p', 'f1-lapsec-records-sector-time', this.formatTime(sectorData['time-str']));
    header.appendChild(label);
    header.appendChild(time);

    const teamNameStr = getTeamName(sectorData['team-id']);
    const driver = this.createElement('p', 'f1-lapsec-records-sector-driver',
      sectorData['driver-name'] || 'Unknown Driver');
    const team = this.createElement('p', 'f1-lapsec-records-sector-team', teamNameStr);

    sector.appendChild(header);
    sector.appendChild(driver);
    sector.appendChild(team);

    return sector;
  }

  createSectorsSection() {
    const sectorsContainer = this.createElement('div', 'f1-lapsec-records-sectors');

    const s1 = this.createSectorRecord(this.data.s1, 'Sector 1');
    sectorsContainer.appendChild(s1);

    const s2 = this.createSectorRecord(this.data.s2, 'Sector 2');
    sectorsContainer.appendChild(s2);

    const s3 = this.createSectorRecord(this.data.s3, 'Sector 3');
    sectorsContainer.appendChild(s3);

    return sectorsContainer;
  }

  render() {
    this.container.innerHTML = '';

    const header = this.createHeader();
    this.container.appendChild(header);

    const grid = this.createElement('div', 'f1-lapsec-records-grid');

    const fastestLap = this.createFastestLapSection();
    grid.appendChild(fastestLap);

    const sectors = this.createSectorsSection();
    grid.appendChild(sectors);

    this.container.appendChild(grid);
  }

  updateData(newData) {
    try {
      if (!newData || typeof newData !== 'object') {
        throw new Error('Invalid data format');
      }

      // Ensure all required keys exist, even if null
      this.data = {
        lap: newData.lap || null,
        s1: newData.s1 || null,
        s2: newData.s2 || null,
        s3: newData.s3 || null
      };

      this.render();
    } catch (error) {
      console.error('Error updating F1 records:', error);
      this.showError('Error updating records');
    }
  }

  // Public method to update with new data
  update(data) {
    this.updateData(data);
  }

  // Method to get current data
  getData() {
    return this.data;
  }

  // Method to clear the display
  clear() {
    this.container.innerHTML = '';
    this.data = null;
  }

  // Static method to create instance
  static create(containerDiv) {
    return new F1LapSectorRecords(containerDiv);
  }
}
