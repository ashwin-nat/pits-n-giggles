class F1TimingTower {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.filterFunction = options.filterFunction || (() => true);
        this.gridApi = null;
        this.allDriverData = [];
        this.updateInterval = null;
        this.sessionUid = null;

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
            }
        };

        const gridDiv = document.getElementById(this.containerId);
        this.gridApi = agGrid.createGrid(gridDiv, gridOptions);
    }

    getColumnDefs() {
        return [
            {
                headerName: 'POS',
                field: 'position',
                flex: 1
            },
            {
                headerName: 'DRIVER',
                field: 'name',
                flex: 3
            },
            {
                headerName: 'DELTA',
                field: 'delta',
                flex: 2,
                valueFormatter: params => {
                    if (params.value === null || params.value === undefined) return '--';
                    if (params.value === 0) return 'LEADER';
                    return formatFloat((params.value / 1000), { precision: 3, signed: true });
                }
            },
            {
                headerName: 'TYRE',
                field: 'tyre',
                flex: 2,
                valueFormatter: params => {
                    return (params.value || 'UNKNOWN').toUpperCase();
                }
            },
            {
                headerName: 'ERS',
                field: 'ers',
                flex: 2,
                valueFormatter: params => {
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
        console.log('driversData length', driversData.length);
        if (driversData.length === 0) {
            // TODO: clear table if current table is populated
            return;
        }
        this.allDriverData = driversData;

        // Transform and filter data
        const transformedData = driversData
            .filter(driver => this.filterFunction(driver))
            .map(driver => ({
                position: driver['driver-info']?.position || 0,
                name: driver['driver-info']?.name || 'Unknown',
                delta: driver['delta-info']?.['delta-to-car-in-front'],
                tyre: driver['tyre-info']?.['visual-tyre-compound'] || 'unknown',
                ers: driver['ers-info']?.['ers-percent-float'] || 0
            }))
            .sort((a, b) => a.position - b.position);

        // Update grid
        if (this.gridApi) {
            this.gridApi.setGridOption('rowData', transformedData);
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
        // Re-apply with current data
        if (this.allDriverData.length > 0) {
            this.update(this.allDriverData);
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
    filterFunction: (driverData) => {
        // Show positions 3-7 (P3 to P7)
        const position = driverData['driver-info'].position;
        return position >= 3 && position <= 7;
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

// Wait for utils to be ready before trying to use them
window.addEventListener('utils-ready', async () => {
    console.log('[TimingTower] Utils ready, fetching initial telemetry...');
    test_import(); // TODO: remove
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
