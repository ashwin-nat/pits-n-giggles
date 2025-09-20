// populateRaceControlMessagesTab.js

// Add a small helper to create elements with attributes and children
function createEl(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, val] of Object.entries(props)) {
    if (key === 'class') {
      el.classList.add(...val.split(' '));
    } else if (key === 'style') {
      Object.assign(el.style, val);
    } else if (key.startsWith('on') && typeof val === 'function') {
      el.addEventListener(key.slice(2).toLowerCase(), val);
    } else {
      el.setAttribute(key, val);
    }
  }
  children.forEach(c => el.append(typeof c === 'string' ? document.createTextNode(c) : c));
  return el;
}
function createFilterModal(allTypes, onChange) {
  const getSelected = () =>
    allTypes.filter(t => modal.querySelector(`#filter-${t}`).checked);

  const checkboxes = allTypes.map(type =>
    createEl('div', { class: 'filter-checkbox-container' },
      createEl('input', {
        type: 'checkbox',
        id: `filter-${type}`,
        value: type,
        onChange: () => onChange(getSelected())
      }),
      createEl('label', { for: `filter-${type}` }, type)
    )
  );

  const modal = createEl('div', { class: 'race-control-modal-overlay', style: { display: 'none' } },
    createEl('div', { id: 'raceControlMessageFilters', class: 'race-control-filters-checkboxes' },
      createEl('h3', { style: { color: 'white' } }, 'Message Types'),
      createEl('div', { class: 'filter-button-container' },
        createEl('button', {
          class: 'race-control-action-button',
          onClick: () => { allTypes.forEach(t => modal.querySelector(`#filter-${t}`).checked = true); onChange(allTypes); }
        }, 'Enable All'),
        createEl('button', {
          class: 'race-control-action-button',
          onClick: () => { allTypes.forEach(t => modal.querySelector(`#filter-${t}`).checked = false); onChange([]); }
        }, 'Disable All')
      ),
      createEl('button', {
        class: 'race-control-modal-close-button',
        onClick: () => modal.style.display = 'none'
      }, 'X'),
      ...checkboxes
    )
  );

  modal.addEventListener('click', e => {
    if (e.target === modal) modal.style.display = 'none';
  });

  return {
    overlay: modal,
    open: () => modal.style.display = 'flex',
    update: selected =>
      allTypes.forEach(t => {
        modal.querySelector(`#filter-${t}`).checked = selected.includes(t);
      })
  };
}

function getDriverDetailsStr(driverInfo, brackets=false) {
    if (driverInfo) {
        if (brackets) {
            return `${driverInfo["name"]} (${driverInfo["team"]} ${driverInfo["driver-number"]})`; // Use 'driver-number'
        }
        return `${driverInfo["name"]} - ${driverInfo["team"]} #${driverInfo["driver-number"]}`; // Use 'driver-number'
    } else {
        return "Unknown Driver";
    }
}

// Extract detailRenderers into its own constant (can live at top of file or separate module)
const detailRenderers = {
  SESSION_START: () => 'N/A',
  SESSION_END: () => 'N/A',
  FASTEST_LAP: ({ 'driver-info': d, 'lap-time-ms': ms }) =>
      `Driver: ${getDriverDetailsStr(d ?? null)}, Lap Time: ${formatLapTime(ms)}`,
  RETIREMENT: ({ 'driver-info': d }) =>
      `Driver: ${getDriverDetailsStr(d ?? null)}`,
  DRS_ENABLED: () => 'N/A',
  DRS_DISABLED: ({ reason }) =>
      `Reason: ${reason}`,
  CHEQUERED_FLAG: () => 'N/A',
  RACE_WINNER: ({ 'driver-info': d }) =>
      getDriverDetailsStr(d ?? null),
  PENALTY: ({ 'driver-info': d, 'penalty-type': pt, 'infringement-type': it, 'other-driver-info': od }) => {
    const base = `${getDriverDetailsStr(d, true)}, ${pt} - ${it}`;
    return od ? `${base}, other driver: ${getDriverDetailsStr(od, true)}` : base;
  },
  SPEED_TRAP: ({ 'driver-info': d, speed }) =>
      `Driver: ${getDriverDetailsStr(d ?? null)}, Speed: ${formatFloat(speed)} km/h`,
  START_LIGHTS: ({ 'num-lights': numLights }) =>
      `Number of lights: ${numLights}`,
  LIGHTS_OUT: () => 'N/A',
  DRIVE_THROUGH_SERVED: ({ 'driver-info': d }) =>
      `Driver: ${getDriverDetailsStr(d ?? null)}`,
  STOP_GO_SERVED: ({ 'driver-info': d, 'stop-time': stopTime }) =>
      `Driver: ${getDriverDetailsStr(d ?? null)} - Stop Time: ${formatFloat(stopTime)} s`,
  RED_FLAG: () => 'N/A',
  OVERTAKE: ({ 'overtaker-info': overtaker, 'overtaken-info': overtaken }) =>
      `${getDriverDetailsStr(overtaker ?? null)} overtook ${getDriverDetailsStr(overtaken ?? null)}`,
  SAFETY_CAR: ({ 'sc-type': scType, 'event-type': eventType }) =>
      `${scType} - ${eventType}`,
  COLLISION: ({ 'driver-1-info': d1, 'driver-2-info': d2 }) =>
      `${getDriverDetailsStr(d1 ?? null)} and ${getDriverDetailsStr(d2 ?? null)}`,
  PITTING: ({ 'driver-info': d, 'lap-number': lap }) =>
      `Driver: ${getDriverDetailsStr(d ?? null)}, Lap: ${lap}`,
  CAR_DAMAGE: ({ 'damaged-part': part, 'old-value': oldValue, 'new-value': newValue, 'driver-info': d }) => {
    const partStr = {
        'm_frontLeftWingDamage': 'Front Wing (Left)',
        'm_frontRightWingDamage': 'Front Wing (Right)',
        'm_rearWingDamage': 'Rear Wing',
    }[part] ?? 'Unknown';
    const base = `Part: ${partStr}, Old Value: ${oldValue}, New Value: ${newValue}`;
    return d ? `Driver: ${getDriverDetailsStr(d ?? null)} - ${base}` : base;
  },
  WING_CHANGE: ({ 'driver-info': d, 'lap-number': lap }) =>
      `Driver: ${getDriverDetailsStr(d ?? null)}, Lap: ${lap}`,

  DEFAULT: msg => `Type: ${msg['message-type']} - Placeholder details.`
};

/**
 * Populates the Race Control Messages tab with an AG Grid.
 * This function will fetch race control messages and display them in a sortable, paginated grid.
 * It is designed to be easily extensible for new message types.
 */
function populateRaceControlMessagesTab(containerElement, initialRowData) {
    // Clear any existing content in the container
    containerElement.innerHTML = '';

    let gridApi; // Declare gridApi in a higher scope

    // Create the filter button
    const filterButton = document.createElement('button');
    filterButton.textContent = 'Filters';
    filterButton.classList.add('race-control-filter-button');
    // Create the search input for quick filter
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Search messages...';
    searchInput.id = 'raceControlMessageSearchInput';
    searchInput.classList.add('race-control-search-input');
    containerElement.appendChild(filterButton);
    containerElement.appendChild(searchInput);

    // Extract unique message types
    const allMessageTypes = [...new Set(initialRowData.map(row => row['message-type']))].sort();
    console.log('All Message Types:', allMessageTypes);
    let selectedMessageTypes = [...allMessageTypes];

    // Function to update the grid based on selected filters
    const updateGrid = () => { // Removed gridApi parameter
        const filteredRowData = initialRowData.filter(row => selectedMessageTypes.includes(row['message-type']));
        gridApi.setGridOption('rowData', filteredRowData);
    };

    const { overlay: modalOverlay, open: openFilter, update: updateModal } =
        createFilterModal(allMessageTypes, newTypes => {
            selectedMessageTypes = newTypes;
            updateGrid(); // Removed gridApi argument
        });

    containerElement.appendChild(modalOverlay);
    filterButton.addEventListener('click', openFilter);

    // Create the div for the AG Grid
    const gridDiv = document.createElement('div');
    gridDiv.id = 'raceControlMessagesGrid';
    containerElement.appendChild(gridDiv);

    function renderDetailsCell(msg) {
        const fn = detailRenderers[msg['message-type']] || detailRenderers.DEFAULT;
        return fn(msg);
    }

    // Define column definitions for AG Grid
    const columnDefs = [
        { headerName: 'ID', field: 'id', sortable: true, filter: false, width: 80 },
        { headerName: 'Message Type', field: 'message-type', sortable: true, filter: false, width: 150 },
        { headerName: 'Lap Number', field: 'lap-number', sortable: true, filter: false, width: 150 },
        {
            headerName: 'Details',
            field: 'details',
            flex: 1,
            cellRenderer: params => renderDetailsCell(params.data),
            getQuickFilterText: params => renderDetailsCell(params.data)
        }
    ];

    const myTheme = agGrid.themeQuartz
        .withParams({
            backgroundColor: "#1f2836",
            browserColorScheme: "dark",
            chromeBackgroundColor: {
                ref: "foregroundColor",
                mix: 0.07,
                onto: "backgroundColor"
            },
            foregroundColor: "#FFF",
            headerFontSize: 14
        });

    // AG Grid options
    const gridOptions = {
        columnDefs: columnDefs,
        rowData: initialRowData, // Use the initialRowData passed as an argument
        pagination: true, // Enable pagination
        paginationPageSize: 20, // Set default page size
        domLayout: 'autoHeight', // Adjust grid height automatically
        theme: myTheme,
        autoSizeStrategy: {
            type: 'fitGridWidth',
            // Default sizing works well for most cases, no need to specify columnLimits
        },
        defaultColDef: {
            resizable: true,
            // Other default column properties can be added here
        },
        onGridReady: (params) => {
            gridApi = params.api; // Assign gridApi
            updateModal(selectedMessageTypes); // Initialize checkboxes
            updateGrid(); // Removed gridApi argument
            searchInput.addEventListener('input', (event) => {
                const filterText = event.target.value;
                console.log('Search Input:', filterText);
                gridApi.setGridOption( // Use the higher-scoped gridApi
                    "quickFilterText", filterText,
                );
            });
        }
        // Other options can be added here as needed
    };

    // Initialize the AG Grid
    new agGrid.createGrid(gridDiv, gridOptions);
}

// Make the function globally accessible
window.populateRaceControlMessagesTab = populateRaceControlMessagesTab;
