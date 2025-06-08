// F1 Tyre Selection Interface JavaScript

class F1TyreManager {
  constructor(containerElement, iconCache) {
    // Validate required parameters
    if (!containerElement) {
      throw new Error('F1TyreManager: containerElement is required and cannot be null');
    }
    if (!iconCache) {
      throw new Error('F1TyreManager: iconCache is required and cannot be null');
    }

    this.container = containerElement;
    this.iconCache = iconCache;
    this.tyreData = null;
  }

  updateData(newData) {
    if (!newData) {
      throw new Error('F1TyreManager: data cannot be null or undefined');
    }
    this.tyreData = newData;
    this.render();
  }

  getTyreIcon(compound) {
    if (this.iconCache && this.iconCache.getIcon) {
      return this.iconCache.getIcon(compound);
    }
    return null; // Return null if no icon cache available
  }

  getCompoundClass(compound) {
    const compoundMap = {
      'Soft': 'soft',
      'Medium': 'medium',
      'Hard': 'hard',
      'Inters': 'inters',
      'Wet': 'wet'
    };
    return compoundMap[compound] || 'hard';
  }

  getCompoundSortOrder(compound) {
    // Define the order for sorting compounds
    const compoundOrder = {
      'Soft': 1,
      'Medium': 2,
      'Hard': 3,
      'Inters': 4,
      'Wet': 5
    };
    return compoundOrder[compound] || 999;
  }

  // Check if a tyre is used based on wear or life span
  isTyreUsed(tyre) {
    return tyre.wear > 0 || tyre['usable-life'] < tyre['life-span'];
  }

  groupTyres(tyreSets) {
    const groups = new Map();

    tyreSets.forEach((tyre, originalIndex) => {
      const tyreWithIndex = { ...tyre, originalIndex };
      const compound = tyre['visual-tyre-compound'];
      const isNew = tyre.wear === 0 && tyre['usable-life'] === tyre['life-span'];
      const isAvailable = tyre.available;
      const isFitted = tyre.fitted;

      // Create a grouping key based on compound and condition
      let groupKey;

      if (isNew && !isFitted) {
        // Group new, unfitted tyres by compound and availability status
        groupKey = `new-${compound}-${isAvailable ? 'available' : 'unavailable'}`;
      } else {
        // Individual cards for used, fitted tyres
        groupKey = `individual-${originalIndex}`;
      }

      if (!groups.has(groupKey)) {
        groups.set(groupKey, {
          ...tyreWithIndex,
          count: 1,
          isGroup: groupKey.startsWith('new-'),
          groupedTyres: [tyreWithIndex],
          groupKey: groupKey
        });
      } else {
        const group = groups.get(groupKey);
        group.count++;
        group.groupedTyres.push(tyreWithIndex);
      }
    });

    return Array.from(groups.values());
  }

  sortTyres(tyreSets) {
    const grouped = this.groupTyres(tyreSets);

    return grouped.sort((a, b) => {
      // First sort by availability (available first)
      if (a.available !== b.available) {
        return b.available - a.available; // true (1) comes before false (0)
      }

      // Then sort by fitted status (fitted first among available)
      if (a.available && b.available && a.fitted !== b.fitted) {
        return b.fitted - a.fitted; // fitted (true) comes before unfitted (false)
      }

      // Then sort by compound type
      const compoundOrderA = this.getCompoundSortOrder(a['visual-tyre-compound']);
      const compoundOrderB = this.getCompoundSortOrder(b['visual-tyre-compound']);
      if (compoundOrderA !== compoundOrderB) {
        return compoundOrderA - compoundOrderB;
      }

      // Then sort by wear (lower wear first)
      if (a.wear !== b.wear) {
        return a.wear - b.wear;
      }

      // If all else is equal, maintain original order
      return a.originalIndex - b.originalIndex;
    });
  }

  formatDeltaTime(deltaTime) {
    if (deltaTime === 0) return 'Baseline';
    const seconds = (deltaTime / 1000).toFixed(3);
    return deltaTime > 0 ? `+${seconds}s` : `${seconds}s`;
  }

  getAvailabilityStats() {
    if (!this.tyreData || !this.tyreData['tyre-set-data']) {
      return { total: 0, available: 0, fitted: 0, compounds: {} };
    }

    const tyreSets = this.tyreData['tyre-set-data'];
    const stats = {
      total: tyreSets.length,
      available: tyreSets.filter(t => t.available).length,
      fitted: tyreSets.filter(t => t.fitted).length,
      compounds: {}
    };

    tyreSets.forEach(tyre => {
      const compound = tyre['visual-tyre-compound'];
      if (!stats.compounds[compound]) {
        stats.compounds[compound] = { total: 0, available: 0 };
      }
      stats.compounds[compound].total++;
      if (tyre.available) {
        stats.compounds[compound].available++;
      }
    });

    // Sort compounds for consistent display
    const sortedCompounds = {};
    Object.keys(stats.compounds)
      .sort((a, b) => this.getCompoundSortOrder(a) - this.getCompoundSortOrder(b))
      .forEach(compound => {
        sortedCompounds[compound] = stats.compounds[compound];
      });
    stats.compounds = sortedCompounds;

    return stats;
  }

  createElement(tag, className = '', textContent = '') {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (textContent) element.textContent = textContent;
    return element;
  }

  createTyreIcon(compound) {
    const iconSpan = this.createElement('span', 'f1-ts-tyre-icon');
    const iconElement = this.getTyreIcon(compound);
    if (iconElement) {
      iconSpan.appendChild(iconElement);
    }
    return iconSpan;
  }

  createTyreCard(tyreGroup) {
    const tyre = tyreGroup;
    const compound = tyre['visual-tyre-compound'];
    const compoundClass = this.getCompoundClass(compound);
    const isAvailable = tyre.available;
    const isFitted = tyre.fitted;
    const isUsed = this.isTyreUsed(tyre);
    const isGroup = tyreGroup.isGroup && tyreGroup.count > 1;

    // Main card container - add fitted class if tyre is fitted
    let cardClasses = `f1-ts-tyre-card f1-ts-compound-${compoundClass}`;
    if (!isAvailable) {
      cardClasses += ' f1-ts-not-available';
    }
    if (isFitted) {
      cardClasses += ' f1-ts-fitted-card';
    }

    const card = this.createElement('div', cardClasses);

    // Add count badge for grouped tyres
    if (isGroup) {
      const countBadge = this.createElement('div', 'f1-ts-count-badge', `x${tyreGroup.count}`);
      card.appendChild(countBadge);
    }

    // Header section
    const header = this.createElement('div', 'f1-ts-tyre-header');

    const compoundName = this.createElement('div', 'f1-ts-compound-name');
    const tyreIcon = this.createTyreIcon(compound);
    if (tyreIcon.children.length > 0) {
      compoundName.appendChild(tyreIcon);
    }
    compoundName.appendChild(document.createTextNode(tyre['actual-tyre-compound']));

    const compoundBadge = this.createElement('div', `f1-ts-compound-badge f1-ts-badge-${compoundClass}`, compound);

    header.appendChild(compoundName);
    header.appendChild(compoundBadge);

    // Status row
    const statusRow = this.createElement('div', 'f1-ts-status-row');

    // Determine status text based on availability and usage - fitted takes precedence
    let statusText, statusClass;
    if (!isAvailable) {
      statusText = '✗ Unavailable';
      statusClass = 'f1-ts-unavailable';
    } else if (isFitted) {
      // Fitted takes precedence - don't show used status for fitted tyres
      statusText = '✓ Available';
      statusClass = 'f1-ts-available';
    } else if (isUsed) {
      statusText = '⚠ Used';
      statusClass = 'f1-ts-unavailable';
    } else {
      statusText = '✓ Available';
      statusClass = 'f1-ts-available';
    }

    const availabilityBadge = this.createElement('span', `f1-ts-status-badge ${statusClass}`, statusText);
    statusRow.appendChild(availabilityBadge);

    if (isFitted) {
      const fittedBadge = this.createElement('span', 'f1-ts-status-badge f1-ts-fitted', '🔧 Fitted');
      statusRow.appendChild(fittedBadge);
    }

    // Info grid
    const infoGrid = this.createElement('div', 'f1-ts-info-grid');

    // Life info - flipped numerator and denominator, renamed to "Life (laps)"
    const lifeSpanItem = this.createElement('div', 'f1-ts-info-item');
    lifeSpanItem.appendChild(this.createElement('div', 'f1-ts-info-label', 'Life (laps)'));
    lifeSpanItem.appendChild(this.createElement('div', 'f1-ts-info-value', `${tyre['life-span']}/${tyre['usable-life']}`));

    // Wear info - for new tyre groups, always show 0%
    const wearItem = this.createElement('div', 'f1-ts-info-item');
    wearItem.appendChild(this.createElement('div', 'f1-ts-info-label', 'Wear'));
    wearItem.appendChild(this.createElement('div', 'f1-ts-info-value', `${tyre.wear}%`));

    // Delta time info
    const deltaItem = this.createElement('div', 'f1-ts-info-item');
    deltaItem.appendChild(this.createElement('div', 'f1-ts-info-label', 'Delta Time'));
    const deltaValue = this.createElement('div', 'f1-ts-info-value f1-ts-delta-time', this.formatDeltaTime(tyre['lap-delta-time']));
    deltaItem.appendChild(deltaValue);

    // Set number info (show range for groups, single number for individuals) - start from 0
    const setItem = this.createElement('div', 'f1-ts-info-item');
    setItem.appendChild(this.createElement('div', 'f1-ts-info-label', isGroup ? 'Sets' : 'Set #'));
    if (isGroup) {
      const setNumbers = tyreGroup.groupedTyres.map(t => t.originalIndex).sort((a, b) => a - b);
      const setRange = setNumbers.length > 2 ?
        `${setNumbers[0]}-${setNumbers[setNumbers.length - 1]}` :
        setNumbers.join(', ');
      setItem.appendChild(this.createElement('div', 'f1-ts-info-value', setRange));
    } else {
      setItem.appendChild(this.createElement('div', 'f1-ts-info-value', `${tyre.originalIndex}`));
    }

    infoGrid.appendChild(lifeSpanItem);
    infoGrid.appendChild(wearItem);
    infoGrid.appendChild(deltaItem);
    infoGrid.appendChild(setItem);

    // Assemble card
    card.appendChild(header);
    card.appendChild(statusRow);
    card.appendChild(infoGrid);

    return card;
  }

  createSummarySection(stats) {
    const summary = this.createElement('div', 'f1-ts-summary');

    const title = this.createElement('div', 'f1-ts-summary-title', '📊 Summary');
    summary.appendChild(title);

    const statsGrid = this.createElement('div', 'f1-ts-summary-stats');

    // Total sets
    const totalItem = this.createElement('div', 'f1-ts-summary-item');
    totalItem.appendChild(this.createElement('div', 'f1-ts-info-label', 'Total Sets'));
    totalItem.appendChild(this.createElement('div', 'f1-ts-info-value', stats.total.toString()));
    statsGrid.appendChild(totalItem);

    // Available
    const availableItem = this.createElement('div', 'f1-ts-summary-item');
    availableItem.appendChild(this.createElement('div', 'f1-ts-info-label', 'Available'));
    availableItem.appendChild(this.createElement('div', 'f1-ts-info-value', stats.available.toString()));
    statsGrid.appendChild(availableItem);

    // Currently fitted
    const fittedItem = this.createElement('div', 'f1-ts-summary-item');
    fittedItem.appendChild(this.createElement('div', 'f1-ts-info-label', 'Currently Fitted'));
    fittedItem.appendChild(this.createElement('div', 'f1-ts-info-value', stats.fitted.toString()));
    statsGrid.appendChild(fittedItem);

    // Compound breakdown
    Object.entries(stats.compounds).forEach(([compound, data]) => {
      const compoundItem = this.createElement('div', 'f1-ts-summary-item');

      const label = this.createElement('div', 'f1-ts-info-label');
      const compoundIcon = this.createTyreIcon(compound);
      if (compoundIcon.children.length > 0) {
        label.appendChild(compoundIcon);
      }
      label.appendChild(document.createTextNode(compound));

      const value = this.createElement('div', 'f1-ts-info-value', `${data.available}/${data.total}`);

      compoundItem.appendChild(label);
      compoundItem.appendChild(value);
      statsGrid.appendChild(compoundItem);
    });

    summary.appendChild(statsGrid);
    return summary;
  }

  render() {
    if (!this.container || !this.tyreData) {
      // Clear container if no data
      if (this.container) {
        this.container.textContent = '';
      }
      return;
    }

    // Clear container
    this.container.textContent = '';

    const tyreSets = this.tyreData['tyre-set-data'];
    const sortedTyreSets = this.sortTyres(tyreSets);
    const stats = this.getAvailabilityStats();

    // Main container
    const mainContainer = this.createElement('div', 'f1-ts-container');

    // Tyre grid (removed title)
    const tyreGrid = this.createElement('div', 'f1-ts-tyre-grid');

    sortedTyreSets.forEach((tyreGroup) => {
      const card = this.createTyreCard(tyreGroup);
      tyreGrid.appendChild(card);
    });

    mainContainer.appendChild(tyreGrid);

    // Summary section
    const summary = this.createSummarySection(stats);
    mainContainer.appendChild(summary);

    // Add to container
    this.container.appendChild(mainContainer);
  }
}
