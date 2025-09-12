// populateRaceControlMessagesTab.js

/**
 * Populates the Race Control Messages tab with an AG Grid.
 * This function will fetch race control messages and display them in a sortable, paginated grid.
 * It is designed to be easily extensible for new message types.
 */
function populateRaceControlMessagesTab(containerElement, initialRowData) {
    // Clear any existing content in the container
    containerElement.innerHTML = '';

    // Create the div for the filter controls
    const filterDiv = document.createElement('div');
    filterDiv.id = 'raceControlMessageFilters';
    filterDiv.classList.add('race-control-filters');
    containerElement.appendChild(filterDiv);

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
        filterDiv.innerHTML = '<h3>Filter by Message Type:</h3>';
        allMessageTypes.forEach(type => {
            const checkboxContainer = document.createElement('span');
            checkboxContainer.classList.add('filter-checkbox-container');

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `filter-${type}`;
            checkbox.value = type;
            checkbox.checked = true; // All checked by default

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
            filterDiv.appendChild(checkboxContainer);
        });
    };

    // Define column definitions for AG Grid
    const columnDefs = [
        { headerName: 'ID', field: 'id', sortable: true, filter: false, width: 80 },
        { headerName: 'Message Type', field: 'message-type', sortable: true, filter: false, width: 150 },
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
                    case 'Penalty':
                        return `Driver: ${message.driver}, Type: ${message.penaltyType}, Time: ${message.time}`;
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