class F1TimingTower {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.filterFunction = options.filterFunction || (() => []);
        this.gridApi = null;
        this.allDriverData = [];
        this.updateInterval = null;
        this.sessionUid = null;
        this.allowedPositions = [];

        this.initGrid();
    }

    initGrid() {
        const myTheme = agGrid.themeQuartz
            .withParams({
                backgroundColor: "#15151E",
                borderColor: "#333333",
                browserColorScheme: "dark",
                chromeBackgroundColor: {
                    ref: "foregroundColor",
                    mix: 0.07,
                    onto: "backgroundColor"
                },
                columnBorder: true,
                fontSize: 16,
                foregroundColor: "#FFF",
                headerBackgroundColor: "#0C0C12",
                headerFontSize: 14,
                oddRowBackgroundColor: "#1F1F2B",
                rowHeight: 30,
                rowHoverColor: "#2D2D3D",
                selectedRowBackgroundColor: "#2D2D3D"
            });
        const gridOptions = {
            columnDefs: this.getColumnDefs(),
            rowData: [],
            domLayout: 'normal',
            theme: myTheme,
            headerHeight: 0,  // Disable header
            suppressMovableColumns: true,
            suppressCellFocus: true,
            defaultColDef: {
                sortable: false,
                resizable: false,
            },
            isExternalFilterPresent: () => true,
            doesExternalFilterPass: (node) => {
                const position = node.data['driver-info']?.position;
                if (!position) return false;
                return this.allowedPositions.includes(position);
            },
            initialState: {
                columns: {
                    columnGroup: [
                        { colId: 'driver-info.position', sort: 'asc' }
                    ]
                }
            }
        };

        const gridDiv = document.getElementById(this.containerId);
        this.gridApi = agGrid.createGrid(gridDiv, gridOptions);
    }

    getColumnDefs() {
        return [
            {
                headerName: 'POS',
                field: 'driver-info.position',
                flex: 1,
                sort: 'asc',
                comparator: (a, b) => {
                    const numA = parseInt(a, 10);
                    const numB = parseInt(b, 10);
                    if (isNaN(numA) && isNaN(numB)) return 0;
                    if (isNaN(numA)) return 1;
                    if (isNaN(numB)) return -1;
                    return numA - numB;
                },
                valueGetter: params => params.data['driver-info']?.position || 0
            },
            {
                headerName: 'DRIVER',
                field: 'driver-info.name',
                flex: 3,
                valueGetter: params => params.data['driver-info']?.name || 'Unknown'
            },
            {
                headerName: 'DELTA',
                field: 'delta-info.delta-to-car-in-front',
                flex: 2,
                valueGetter: params => params.data['delta-info']?.['delta-to-car-in-front'],
                cellRenderer: params => {
                    if (params.value === null || params.value === undefined) return '--';
                    if (params.value === 0) return 'LEADER';
                    return formatFloat((params.value / 1000), { precision: 3, signed: true });
                }
            },
            {
                headerName: 'TYRE',
                field: 'tyre-info.visual-tyre-compound',
                flex: 2,
                valueGetter: params => params.data['tyre-info']?.['visual-tyre-compound'] || 'unknown',
                cellRenderer: params => {
                    return (params.value || 'UNKNOWN').toUpperCase();
                }
            },
            {
                headerName: 'ERS',
                field: 'ers-info.ers-percent-float',
                flex: 2,
                valueGetter: params => params.data['ers-info']?.['ers-percent-float'] || 0,
                cellRenderer: params => {
                    const value = params.value || 0;
                    return `${formatFloat(value, { precision: 0, signed: false })}%`;
                }
            }
        ];
    }

    update(incomingData) {

        if (this.sessionUid !== incomingData['session-uid']) {
            // clear the data structures if the session has changed
            this.sessionUid = incomingData['session-uid'];
            this.#clear();
        }

        // Store all incoming data
        const driversData = incomingData['table-entries'];
        if (driversData.length === 0) {
            // TODO: clear table if current table is populated
            return;
        }
        this.allDriverData = driversData;

        // Compute allowed positions once per update
        this.allowedPositions = this.filterFunction(incomingData);

        // Update grid with all data - ag-grid will handle filtering
        if (this.gridApi) {
            this.gridApi.setGridOption('rowData', driversData);
        }
    }

    #clear() {
        this.allDriverData = [];
        if (this.gridApi) {
            this.gridApi.setGridOption('rowData', []);
        }
    }

    setFilterFunction(filterFn) {
        this.filterFunction = filterFn;
        // Trigger ag-grid to re-evaluate the external filter
        if (this.gridApi) {
            this.gridApi.onFilterChanged();
        }
    }

    destroy() {
        this.stopDummyUpdates();
        if (this.gridApi) {
            this.gridApi.destroy();
        }
    }
}

// Initialize the timing tower
const timingTower = new F1TimingTower('timingGrid', {
    filterFunction: (incomingData) => {
        const playerPosition = getPlayerPosition(incomingData);
        const totalCars = incomingData["table-entries"].length;
        const numAdjacentCars = 2;
        return getAdjacentPositions(playerPosition, totalCars, numAdjacentCars);
    }
});

// Start periodic updates with dummy data
// timingTower.startDummyUpdates(500);

// Listen for updates from Python
window.addEventListener('telemetry-update', (event) => {
    timingTower.update(event.detail);
});

window.addEventListener('lock-state-change', (event) => {
    const locked = event.detail['new-value'];
    console.log('lock-state-change', event.detail);

    if (locked) {
        // Lock/disable column resizing
    } else {
        // Unlock/enable column resizing
    }
});

window.addEventListener('utils-ready', async () => {
    console.log('[TimingTower] Utils ready, fetching initial telemetry...');
    test_import(); // TODO: remove

    // Now safe to use utils functions
    try {
        const data = await pywebview.api.get_data();
        timingTower.update(data);
    } catch (error) {
        console.error('Error getting initial telemetry:', error);
    }
});
