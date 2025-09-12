// populateRaceControlMessagesTab.js

/**
 * Populates the Race Control Messages tab with an AG Grid.
 * This function will fetch race control messages and display them in a sortable, paginated grid.
 * It is designed to be easily extensible for new message types.
 */
function populateRaceControlMessagesTab(containerElement, rowData) {
    // Clear any existing content in the container
    containerElement.innerHTML = '';

    // Create the div for the AG Grid
    const gridDiv = document.createElement('div');
    gridDiv.id = 'raceControlMessagesGrid';
    gridDiv.classList.add('ag-theme-alpine-dark'); // Apply the AG Grid theme class
    containerElement.appendChild(gridDiv);

    // Define column definitions for AG Grid
    const columnDefs = [
        { headerName: 'ID', field: 'id', sortable: true, filter: true, width: 80 },
        { headerName: 'Message Type', field: 'message-type', sortable: true, filter: true, width: 150 },
        // Placeholder for type-dependent fields.
        // These will be dynamically added or handled by a custom cell renderer
        // based on the messageType.
        {
            headerName: 'Details',
            field: 'details',
            flex: 1,
            cellRenderer: (params) => {
                const message = params.data;
                switch (message.messageType) {
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
                        return `Type: ${message.messageType} - Placeholder details.`;
                }
            }
        }
    ];

    // AG Grid options
    const gridOptions = {
        columnDefs: columnDefs,
        rowData: rowData, // Use the rowData passed as an argument
        pagination: true, // Enable pagination
        paginationPageSize: 20, // Set default page size
        domLayout: 'autoHeight', // Adjust grid height automatically
        // Other options can be added here as needed
    };

    // Initialize the AG Grid
    new agGrid.createGrid(gridDiv, gridOptions);
}

// Make the function globally accessible
window.populateRaceControlMessagesTab = populateRaceControlMessagesTab;