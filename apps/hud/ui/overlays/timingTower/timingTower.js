class F1TimingTower {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.filterFunction = options.filterFunction || (() => true);
        this.gridApi = null;
        this.allDriverData = [];
        this.updateInterval = null;

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
            suppressMovableColumns: true,
            suppressCellFocus: true,
            defaultColDef: {
                sortable: false,
                resizable: false,
                flex: 1
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
                flex: 2
            },
            {
                headerName: 'DELTA',
                field: 'delta',
                flex: 2,
                valueFormatter: params => {
                    if (params.value === null || params.value === undefined) return '--';
                    if (params.value === 0) return 'LEADER';
                    return `+${params.value.toFixed(3)}`;
                }
            },
            {
                headerName: 'TYRE',
                field: 'tyre',
                flex: 1,
                valueFormatter: params => {
                    return (params.value || 'UNKNOWN').toUpperCase();
                }
            },
            {
                headerName: 'ERS',
                field: 'ers',
                flex: 1,
                valueFormatter: params => {
                    const value = params.value || 0;
                    return `${Math.round(value * 100)}%`;
                }
            }
        ];
    }

    update(incomingData) {
        // Store all incoming data
        this.allDriverData = incomingData;

        // Transform and filter data
        const transformedData = incomingData
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

    setFilterFunction(filterFn) {
        this.filterFunction = filterFn;
        // Re-apply with current data
        if (this.allDriverData.length > 0) {
            this.update(this.allDriverData);
        }
    }

    // Dummy data generator for testing
    generateDummyData() {
        const drivers = [
            'VER', 'PER', 'HAM', 'RUS', 'LEC', 'SAI', 'NOR', 'PIA',
            'ALO', 'STR', 'GAS', 'OCO', 'ALB', 'SAR', 'TSU', 'RIC',
            'MAG', 'HUL', 'BOT', 'ZHO'
        ];

        const tyres = ['soft', 'medium', 'hard', 'intermediate', 'wet'];

        return drivers.map((driver, index) => ({
            'driver-info': {
                position: index + 1,
                name: driver
            },
            'delta-info': {
                'delta-to-car-in-front': index === 0 ? 0 : Math.random() * 10
            },
            'tyre-info': {
                'visual-tyre-compound': tyres[Math.floor(Math.random() * tyres.length)]
            },
            'ers-info': {
                'ers-percent-float': Math.random()
            }
        }));
    }

    startDummyUpdates(intervalMs = 1000) {
        // Initial update
        this.update(this.generateDummyData());

        // Periodic updates
        this.updateInterval = setInterval(() => {
            this.update(this.generateDummyData());
        }, intervalMs);
    }

    stopDummyUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
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
timingTower.startDummyUpdates(500);

// Listen for updates from Python
window.addEventListener('telemetry-update', (event) => {
    // timer.update(event.detail);
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
    console.log('[LapTimer] Utils ready, fetching initial telemetry...');
    test_import(); // TODO: remove
});
