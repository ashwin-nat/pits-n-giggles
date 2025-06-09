class F1TyreRecords {
  constructor(container, iconCache) {
    this.container = container;
    this.iconCache = iconCache;
    this.data = null;
    this.init();
  }

  init() {
    // Clear the container completely
    this.container.innerHTML = '';

    // Create main wrapper
    this.wrapper = document.createElement('div');
    this.wrapper.className = 'f1-tyre-records-wrapper';
    this.container.appendChild(this.wrapper);

    // Create content container (no header)
    this.contentContainer = document.createElement('div');
    this.contentContainer.className = 'f1-tyre-records-content';
    this.wrapper.appendChild(this.contentContainer);
  }

  update(data) {
    console.log('F1TyreRecords.update called with data:', data);
    this.data = data;
    this.render();
  }

  render() {
    console.log('F1TyreRecords.render called, data:', this.data);

    // Clear content
    this.contentContainer.innerHTML = '';

    if (!this.data || Object.keys(this.data).length === 0) {
      console.log('No data available, showing empty state');
      this.showEmptyState();
      return;
    }

    // Create grid container
    const grid = document.createElement('div');
    grid.className = 'f1-tyre-records-grid';
    this.contentContainer.appendChild(grid);

    // Sort tyre compounds by actual compound (C1, C2, C3, etc.)
    const sortedEntries = Object.entries(this.data).sort(([a], [b]) => {
      const aCompound = a.split(' - ')[0];
      const bCompound = b.split(' - ')[0];
      return aCompound.localeCompare(bCompound);
    });

    // Process each tyre compound in sorted order
    sortedEntries.forEach(([tyreType, records]) => {
      console.log('Processing tyre type:', tyreType, 'with records:', records);
      const card = this.createTyreCard(tyreType, records);
      grid.appendChild(card);
    });
  }

  createTyreCard(tyreType, records) {
    const [actualCompound, visualCompound] = tyreType.split(' - ');
    console.log('Creating card for:', { actualCompound, visualCompound, records });

    const card = document.createElement('div');
    card.className = 'f1-tyre-records-card';

    // Card header with tyre info
    const cardHeader = document.createElement('div');
    cardHeader.className = 'f1-tyre-records-card-header';

    const tyreInfo = document.createElement('div');
    tyreInfo.className = 'f1-tyre-records-tyre-info';

    // Try to get icon from cache
    let iconElement = null;
    if (this.iconCache && typeof this.iconCache.getIcon === 'function') {
      try {
        const icon = this.iconCache.getIcon(visualCompound);
        if (icon) {
          iconElement = document.createElement('div');
          iconElement.className = 'f1-tyre-records-tyre-icon';
          iconElement.appendChild(icon);
        }
      } catch (e) {
        console.log('Icon not found for', visualCompound, 'using fallback');
      }
    }

    // Fallback if no icon
    if (!iconElement) {
      iconElement = document.createElement('div');
      iconElement.className = 'f1-tyre-records-tyre-icon';
      iconElement.innerHTML = `<span class="f1-tyre-records-tyre-icon-fallback">${visualCompound.charAt(0)}</span>`;
    }

    const tyreText = document.createElement('div');
    tyreText.className = 'f1-tyre-records-tyre-text';

    const compoundName = document.createElement('h3');
    compoundName.className = 'f1-tyre-records-compound-name';
    compoundName.textContent = visualCompound.toUpperCase(); // Make uppercase

    const compoundCode = document.createElement('span');
    compoundCode.className = 'f1-tyre-records-compound-code';
    compoundCode.textContent = actualCompound;

    tyreText.appendChild(compoundName);
    tyreText.appendChild(compoundCode);

    tyreInfo.appendChild(iconElement);
    tyreInfo.appendChild(tyreText);
    cardHeader.appendChild(tyreInfo);
    card.appendChild(cardHeader);

    // Card body with records
    const cardBody = document.createElement('div');
    cardBody.className = 'f1-tyre-records-card-body';

    // Process each record type with Bootstrap icons
    const recordTypes = [
      { key: 'highest-tyre-wear', label: 'Highest Wear', unit: '%', icon: 'bi-arrow-up-circle' },
      { key: 'longest-tyre-stint', label: 'Longest Stint', unit: ' laps', icon: 'bi-stopwatch' },
      { key: 'lowest-tyre-wear-per-lap', label: 'Lowest Wear/Lap', unit: '%', icon: 'bi-arrow-down-circle' }
    ];

    recordTypes.forEach(recordType => {
      if (records[recordType.key]) {
        const recordItem = this.createRecordItem(recordType, records[recordType.key]);
        cardBody.appendChild(recordItem);
      }
    });

    card.appendChild(cardBody);
    return card;
  }

  createRecordItem(recordType, recordData) {
    const item = document.createElement('div');
    item.className = 'f1-tyre-records-record-item';

    const iconContainer = document.createElement('div');
    iconContainer.className = 'f1-tyre-records-record-icon';

    // Use Bootstrap icon
    const icon = document.createElement('i');
    icon.className = recordType.icon;
    iconContainer.appendChild(icon);

    const content = document.createElement('div');
    content.className = 'f1-tyre-records-record-content';

    const label = document.createElement('div');
    label.className = 'f1-tyre-records-record-label';
    label.textContent = recordType.label;

    const driver = document.createElement('div');
    driver.className = 'f1-tyre-records-record-driver';
    driver.textContent = recordData['driver-name'];

    const value = document.createElement('div');
    value.className = 'f1-tyre-records-record-value';

    // Format value based on type - integers for stint length, decimals for others
    let formattedValue;
    if (recordType.key === 'longest-tyre-stint') {
      formattedValue = Math.round(recordData.value);
    } else {
      formattedValue = typeof recordData.value === 'number'
        ? recordData.value.toFixed(2)
        : recordData.value;
    }
    value.textContent = formattedValue + recordType.unit;

    content.appendChild(label);
    content.appendChild(driver);

    item.appendChild(iconContainer);
    item.appendChild(content);
    item.appendChild(value);

    return item;
  }

  showEmptyState() {
    const emptyState = document.createElement('div');
    emptyState.className = 'f1-tyre-records-empty-state';

    const emptyIcon = document.createElement('div');
    emptyIcon.className = 'f1-tyre-records-empty-icon';
    emptyIcon.textContent = '🏎️';

    const emptyText = document.createElement('p');
    emptyText.className = 'f1-tyre-records-empty-text';
    emptyText.textContent = 'No tyre records available';

    emptyState.appendChild(emptyIcon);
    emptyState.appendChild(emptyText);
    this.contentContainer.appendChild(emptyState);
  }
}
