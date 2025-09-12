// populateRaceControlMessagesTab.js

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

    // Create the modal overlay
    const modalOverlay = document.createElement('div');
    modalOverlay.classList.add('race-control-modal-overlay');
    modalOverlay.style.display = 'none'; // Hidden by default, controlled by class in CSS
    containerElement.appendChild(modalOverlay);

    // Create the modal content box
    const filterCheckboxesContainer = document.createElement('div');
    filterCheckboxesContainer.id = 'raceControlMessageFilters';
    filterCheckboxesContainer.classList.add('race-control-filters-checkboxes');
    modalOverlay.appendChild(filterCheckboxesContainer);

    // Create the div for the AG Grid
    const gridDiv = document.createElement('div');
    gridDiv.id = 'raceControlMessagesGrid';
    gridDiv.classList.add('ag-theme-alpine-dark'); // Apply the AG Grid theme class
    containerElement.appendChild(gridDiv);

    // Extract unique message types
    const allMessageTypes = [...new Set(initialRowData.map(row => row['message-type']))]; // Use 'message-type'
    console.log('All Message Types:', allMessageTypes); // Console log for verification
    let selectedMessageTypes = [...allMessageTypes]; // All selected by default

    // Function to update the grid based on selected filters
    const updateGrid = (gridApi) => {
        const filteredRowData = initialRowData.filter(row => selectedMessageTypes.includes(row['message-type'])); // Use 'message-type'
        gridApi.setGridOption('rowData', filteredRowData);
    };

    // Populate filter checkboxes
    const populateFilters = (gridApi) => {
        // Clear existing content using proper DOM API
        while (filterCheckboxesContainer.firstChild) {
            filterCheckboxesContainer.removeChild(filterCheckboxesContainer.firstChild);
        }

        const title = document.createElement('h3');
        title.textContent = 'Message Types';
        filterCheckboxesContainer.appendChild(title);

        // Add a close button to the modal
        const closeButton = document.createElement('button');
        closeButton.textContent = 'X';
        closeButton.classList.add('race-control-modal-close-button');
        closeButton.addEventListener('click', () => {
            modalOverlay.style.display = 'none';
        });
        filterCheckboxesContainer.appendChild(closeButton);

        allMessageTypes.forEach(type => {
            const checkboxContainer = document.createElement('div');
            checkboxContainer.classList.add('filter-checkbox-container');

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `filter-${type}`;
            checkbox.value = type;
            checkbox.checked = true;

            const label = document.createElement('label');
            label.htmlFor = `filter-${type}`;
            label.textContent = type;

            checkbox.addEventListener('change', (event) => {
                if (event.target.checked) {
                    selectedMessageTypes.push(type);
                } else {
                    selectedMessageTypes = selectedMessageTypes.filter(t => t !== type);
                }
                updateGrid(gridApi);
            });

            checkboxContainer.appendChild(checkbox);
            checkboxContainer.appendChild(label);
            filterCheckboxesContainer.appendChild(checkboxContainer);
        });

        // Toggle filter checkboxes visibility
        filterButton.addEventListener('click', () => {
            modalOverlay.style.display = 'flex'; // Show the modal
        });

        // Close modal when clicking outside
        modalOverlay.addEventListener('click', (event) => {
            if (event.target === modalOverlay) {
                modalOverlay.style.display = 'none';
            }
        });
    };

    // Define column definitions for AG Grid
    const columnDefs = [
        { headerName: 'ID', field: 'id', sortable: true, filter: false, width: 80 },
        { headerName: 'Message Type', field: 'message-type', sortable: true, filter: false, width: 150 },
        { headerName: 'Lap Number', field: 'lap-number', sortable: true, filter: false, width: 150 },
        // Placeholder for type-dependent fields.
        // These will be dynamically added or handled by a custom cell renderer
        // based on the message-type.
        {
            headerName: 'Details',
            field: 'details',
            flex: 1,
            cellRenderer: (params) => {
                const message = params.data;
                switch (message['message-type']) { // Use 'message-type' here
                    case 'SESSION_START':
                        return `N/A`;
                    case 'SESSION_END':
                        return `N/A`;
                    case 'FASTEST_LAP':
                        let driverDetails;
                        const driverInfo = message["driver-info"] ?? null;
                        if (driverInfo) {
                            driverDetails = `${driverInfo["name"]} - ${driverInfo["team"]} #${driverInfo["driver-number"]}`;
                        } else {
                            driverDetails = "Unknown Driver";
                        }
                        return `Driver: ${driverDetails}, Lap Time: ${formatLapTime(message['lap-time-ms'])}`;
                    case 'Warning':
                        return `Driver: ${message.driver}, Reason: ${message.reason}`;
                    case 'SafetyCar':
                        return `Status: ${message.status}`;
                    case 'VirtualSafetyCar':
                        return `Status: ${message.status}`;
                    case 'TrackLimitsWarning':
                        return `Driver: ${message.driver}, Warnings: ${message.warnings}`;
                    case 'OvertakeAllowed':
                        return `Status: ${message.status}`;
                    case 'OvertakeForbidden':
                        return `Status: ${message.status}`;
                    case 'RaceStewardDecision':
                        return `Driver: ${message.driver}, Decision: ${message.decision}`;
                    case 'ChequeredFlag':
                        return `Status: ${message.status}`;
                    case 'StartLights':
                        return `Lights: ${message.lights}`;
                    default:
                        return `Type: ${message['message-type']} - Placeholder details.`; // Use 'message-type' here
                }
            }
        }
    ];

    // AG Grid options
    const gridOptions = {
        columnDefs: columnDefs,
        rowData: initialRowData, // Use the initialRowData passed as an argument
        pagination: true, // Enable pagination
        paginationPageSize: 20, // Set default page size
        domLayout: 'autoHeight', // Adjust grid height automatically
        onGridReady: (params) => {
            populateFilters(params.api);
            updateGrid(params.api);
        }
        // Other options can be added here as needed
    };

    // Initialize the AG Grid
    new agGrid.createGrid(gridDiv, gridOptions);
}

// Make the function globally accessible
window.populateRaceControlMessagesTab = populateRaceControlMessagesTab;
