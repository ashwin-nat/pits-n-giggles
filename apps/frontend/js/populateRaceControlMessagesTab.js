// populateRaceControlMessagesTab.js
function createFilterModal(allTypes, onChange) {
    const overlay = document.createElement('div');
    overlay.classList.add('race-control-modal-overlay');
    overlay.style.display = 'none';

    const container = document.createElement('div');
    container.id = 'raceControlMessageFilters';
    container.classList.add('race-control-filters-checkboxes');
    overlay.appendChild(container);

    const title = document.createElement('h3');
    title.textContent = 'Message Types';
    title.style.color = 'white';
    container.appendChild(title);

    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('filter-button-container');

    const enableAllButton = document.createElement('button');
    enableAllButton.textContent = 'Enable All';
    enableAllButton.classList.add('race-control-action-button');
    buttonContainer.appendChild(enableAllButton);

    const disableAllButton = document.createElement('button');
    disableAllButton.textContent = 'Disable All';
    disableAllButton.classList.add('race-control-action-button');
    buttonContainer.appendChild(disableAllButton);
    container.appendChild(buttonContainer);

    const closeButton = document.createElement('button');
    closeButton.textContent = 'X';
    closeButton.classList.add('race-control-modal-close-button');
    container.appendChild(closeButton);

    const checkboxes = {};

    const updateCheckboxes = (selectedTypes) => {
        allTypes.forEach(type => {
            if (checkboxes[type]) {
                checkboxes[type].checked = selectedTypes.includes(type);
            }
        });
    };

    allTypes.forEach(type => {
        const checkboxContainer = document.createElement('div');
        checkboxContainer.classList.add('filter-checkbox-container');

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `filter-${type}`;
        checkbox.value = type;

        const label = document.createElement('label');
        label.htmlFor = `filter-${type}`;
        label.textContent = type;

        checkbox.addEventListener('change', () => {
            const newSelectedTypes = Object.values(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            onChange(newSelectedTypes);
        });

        checkboxContainer.appendChild(checkbox);
        checkboxContainer.appendChild(label);
        container.appendChild(checkboxContainer);
        checkboxes[type] = checkbox;
    });

    enableAllButton.addEventListener('click', () => {
        onChange(allTypes);
    });

    disableAllButton.addEventListener('click', () => {
        onChange([]);
    });

    overlay.addEventListener('click', e => {
        if (e.target === overlay || e.target === closeButton) {
            overlay.style.display = 'none';
        }
    });

    return {
        overlay,
        open: () => { overlay.style.display = 'flex'; },
        update: updateCheckboxes
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

/**
 * Populates the Race Control Messages tab with an AG Grid.
 * This function will fetch race control messages and display them in a sortable, paginated grid.
 * It is designed to be easily extensible for new message types.
 */
function populateRaceControlMessagesTab(containerElement, initialRowData) {
    // Clear any existing content in the container
    containerElement.innerHTML = '';

    // Create the filter button
    const filterButton = document.createElement('button');
    filterButton.textContent = 'Filters';
    filterButton.classList.add('race-control-filter-button');
    containerElement.appendChild(filterButton);

    // Extract unique message types
    const allMessageTypes = [...new Set(initialRowData.map(row => row['message-type']))].sort();
    console.log('All Message Types:', allMessageTypes);
    let selectedMessageTypes = [...allMessageTypes];

    // Function to update the grid based on selected filters
    const updateGrid = (gridApi) => {
        const filteredRowData = initialRowData.filter(row => selectedMessageTypes.includes(row['message-type']));
        gridApi.setGridOption('rowData', filteredRowData);
    };

    const { overlay: modalOverlay, open: openFilter, update: updateModal } =
        createFilterModal(allMessageTypes, newTypes => {
            selectedMessageTypes = newTypes;
            updateGrid(gridApi);
        });

    containerElement.appendChild(modalOverlay);
    filterButton.addEventListener('click', openFilter);

    // Create the div for the AG Grid
    const gridDiv = document.createElement('div');
    gridDiv.id = 'raceControlMessagesGrid';
    containerElement.appendChild(gridDiv);

    // Define detail renderers as a lookup table
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
        PENALTY: (message) => {
            const driverDetails = getDriverDetailsStr(message["driver-info"] ?? null, true);
            const penaltyType = message['penalty-type'];
            const infringementType = message['infringement-type'];
            const otherDriverData = message['other-driver-info'] ?? null;
            if (otherDriverData) {
                const otherDriverDetails = getDriverDetailsStr(otherDriverData, true);
                return `${driverDetails}, ${penaltyType} - ${infringementType}, other driver: ${otherDriverDetails}`;
            }
            return `${driverDetails}, ${penaltyType} - ${infringementType}`;
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
        DEFAULT: (msg) =>
            `Type: ${msg['message-type']} - Placeholder details.`,
    };

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
            cellRenderer: params => renderDetailsCell(params.data)
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
            updateModal(selectedMessageTypes); // Initialize checkboxes
            updateGrid(params.api);
        }
        // Other options can be added here as needed
    };

    // Initialize the AG Grid
    new agGrid.createGrid(gridDiv, gridOptions);
}

// Make the function globally accessible
window.populateRaceControlMessagesTab = populateRaceControlMessagesTab;
