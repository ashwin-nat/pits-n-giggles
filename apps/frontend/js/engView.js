let g_engView_predLapNum = null;
function escapeHtml(unsafe) {
    if (typeof unsafe !== "string") {
        return unsafe;
    }
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getShortERSMode(mode) {
    switch (mode) {
        case 'None': return 'NON';
        case 'Medium': return 'MED';
        case 'Hotlap': return 'HOT';
        case 'Overtake': return 'OVR';
    }
    console.error("Unknown ERS mode:", mode);
    return 'N/A';
}

// Class to manage the race table
class CustomHeader {
    init(agGridParams) {
        this.agGridParams = agGridParams;
        this.eGui = document.createElement('div');
        const colDef = agGridParams.column.getColDef();
        const tooltipName = colDef.context.displayName;
        const headerName = colDef.headerName;

        const headerLabelDiv = document.createElement('div');
        headerLabelDiv.classList.add('ag-header-cell-label');
        headerLabelDiv.setAttribute('data-bs-toggle', 'tooltip');
        headerLabelDiv.setAttribute('title', escapeHtml(tooltipName));

        const headerTextSpan = document.createElement('span');
        headerTextSpan.classList.add('ag-header-cell-text');
        headerTextSpan.textContent = escapeHtml(headerName);

        headerLabelDiv.appendChild(headerTextSpan);
        this.eGui.appendChild(headerLabelDiv);

        // Initialize Bootstrap tooltip for this specific header
        this.tooltipInstance = new bootstrap.Tooltip(headerLabelDiv);
    }

    getGui() {
        return this.eGui;
    }

    destroy() {
        // Dispose the tooltip when the header component is destroyed
        if (this.tooltipInstance) {
            this.tooltipInstance.dispose();
        }
    }
}

class CustomNoRowsOverlay {
    init(params) {
        this.eGui = document.createElement('div');
        this.eGui.classList.add('ag-overlay-no-rows-center');
        this.eGui.innerHTML = params.noRowsMessageFunc();
    }

    getGui() {
        return this.eGui;
    }
}

class EngViewRaceTable {
    constructor(iconCache) {
        this.iconCache = iconCache;
        this.gridApi = null;
        this.columnDefs = null;
        this.gridInitialized = false; // Add a flag to track grid initialization
        this.spectatorIndex = null;
        this.currEventType = null;
        this.isSpectating = false;
        this.fastestLapMs = 0;
        this.sessionUID = null;
        this.INVALID_SECTOR = -2;
        this.RED_SECTOR = -1;
        this.YELLOW_SECTOR = 0;
        this.GREEN_SECTOR = 1;
        this.PURPLE_SECTOR = 2;
        this.COLUMN_STATE_LS_KEY = 'eng-view-table-column-state-ag';
        this.TELEMETRY_DISABLED_TEXT = "⌀";
        this.delayedLapData = new Map(); // Stores { oldLapData, timestamp } for each driver
        this.previousTableData = []; // Stores the data from the previous update cycle
        this.refDriverTeam = null; // Team of the reference driver (player or spectated)
        this.INVALID_TEAMS = new Set(["F1 Generic"]);

        // Column visibility pane elements
        this.settingsButton = document.getElementById('settings-btn');
        this.columnVisibilityPane = document.getElementById('column-visibility-pane');
        this.resetVisibilityButton = document.getElementById('reset-visibility-btn');
        this.resetLayoutButton = document.getElementById('reset-layout-btn'); // New button
        this.closePaneButton = document.getElementById('close-pane-btn');
        this.columnVisibilityContainer = document.getElementById('column-visibility-container');

        this.initGrid();
        this.setupSettingsEventListeners();
    }

    saveColumnState() {
        if (this.gridApi) {
            const columnState = this.gridApi.getColumnState();
            try {
                localStorage.setItem(this.COLUMN_STATE_LS_KEY, JSON.stringify(columnState));
                console.debug('Column state saved:', columnState);
                return columnState;
            } catch (error) {
                console.warn('Failed to save column state:', error);
                return null;
            }
        }
    }

    loadColumnState() {
        try {
            const saved = localStorage.getItem(this.COLUMN_STATE_LS_KEY);
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Failed to load column state:', error);
        }
        return null; // Saved data not found
    }

    initGrid() {
        this.columnDefs = this.getColumnDefinitions();
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
            columnDefs: this.columnDefs,
            rowData: [], // Initial empty data
            domLayout: 'normal', // or 'normal' if you want scrolling
            rowHeight: 60, // Add this line - adjust height as needed
            theme: myTheme,
            suppressColumnMoveAnimation: true,
            suppressFieldDotNotation: false, // Allow dots in field names
            defaultColDef: {
                resizable: true,
                sortable: true,
                filter: false,
                headerClass: "eng-view-table-main-header",
                headerComponent: CustomHeader, // Use our custom header component
            },
            noRowsOverlayComponent: CustomNoRowsOverlay,
            noRowsOverlayComponentParams: {
                noRowsMessageFunc: () => "Waiting for data... NOTE: Time Trial is not supported in Engineer View.",
            },
            onGridReady: (params) => {
                this.gridApi = params.api;
                console.debug("AG Grid ready.");

                // Apply saved column state
                const savedColumnState = this.loadColumnState();
                if (savedColumnState) {
                    this.gridApi.applyColumnState({ state: savedColumnState, applyOrder: true });
                    console.debug('Applied saved column state:', savedColumnState);
                }

                // Add event listeners for column state changes
                this.gridApi.addEventListener('columnResized', this.debounceSaveColumnState.bind(this));
                this.gridApi.addEventListener('columnMoved', this.debounceSaveColumnState.bind(this));
                this.gridApi.addEventListener('columnVisible', this.debounceSaveColumnState.bind(this));
                this.gridApi.addEventListener('columnPinned', this.debounceSaveColumnState.bind(this)); // Add this for pinned columns

                const columns = this.fetchGridColumns();
            },
            getRowId: (params) => params.data.id.toString(),
            getRowClass: (params) => {
                const data = params.data;
                if (!data) return;
                const isReferenceDriver = data.isPlayer || data.index === this.spectatorIndex;
                if (isReferenceDriver) {
                    return 'ref-row';
                }
                if ((!this.INVALID_TEAMS.has(data.team)) && (data.team === this.refDriverTeam)) {
                    return 'teammate-row';
                }
                return '';
            },
            onRowClicked: (params) => {
                const data = params.data;
                fetch(`/driver-info?index=${data.index}`)
                    .then(response => response.json())
                    .then(driverData => {
                        window.modalManager.openDriverModal(driverData, this.iconCache);
                    })
                    .catch(err => console.error("Fetch error:", err));
            },
        };

        const gridDiv = document.querySelector("#eng-view-table");
        if (!this.gridInitialized) {
            this.grid = agGrid.createGrid(gridDiv, gridOptions);
            this.gridInitialized = true;
        }
    }

    debounceSaveColumnState() {
        clearTimeout(this.columnStateSaveTimeout);
        this.columnStateSaveTimeout = setTimeout(() => {
            this.saveColumnState();
        }, 500);
    }

    resetColumnState() {
        try {
            localStorage.removeItem(this.COLUMN_STATE_LS_KEY);
            console.debug('Column state reset to default');
            if (this.gridApi) {
                this.gridApi.resetColumnState();
            }
        } catch (error) {
            console.warn('Failed to reset column state:', error);
        }
    }

    createSectorCellRenderer(sectorKey, timeKey, playerTimeKey, isLastLap) {
        return (params) => {
            const driverInfo = params.data;
            const lapInfo = (isLastLap) ? driverInfo["lap-info"]["last-lap"] : driverInfo["lap-info"]["best-lap"];
            const bestLapInfo = driverInfo["lap-info"]["best-lap"];
            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
            const sectorStatus = lapInfo["sector-status"];

            const timeMs = lapInfo[timeKey];
            const formattedTime = sectorKey === 'lap'
                ? formatLapTime(timeMs)
                : formatSectorTime(timeMs);

            let timeClass = '';
            if (sectorStatus) {
                if (sectorKey !== 'lap') {
                    const sectorIndex = parseInt(sectorKey.slice(1)) - 1;
                    if (sectorStatus[sectorIndex] === this.GREEN_SECTOR) {
                        timeClass = 'green-time';
                    } else if (sectorStatus[sectorIndex] === this.PURPLE_SECTOR) {
                        timeClass = 'purple-time';
                    } else if (sectorStatus[sectorIndex] === this.RED_SECTOR) {
                        timeClass = 'red-time';
                    }
                } else if (timeMs) {
                    if (timeMs === this.fastestLapMs) {
                        timeClass = 'purple-time';
                    } else if (timeMs === bestLapInfo[timeKey]) {
                        timeClass = 'green-time';
                    }
                    // Store the computed timeClass directly on the lapInfo object for lap times
                    // This will be used by the comparator
                    lapInfo[`${timeKey}-class`] = timeClass;
                }
            }

            if (isReferenceDriver) {
                return this.createSingleLineCell(formattedTime, {className: timeClass});
            }

            const delta = timeMs - lapInfo[playerTimeKey];
            return this.createMultiLineCell({
                row1: formattedTime,
                row2: ((timeMs) ? (formatDelta(delta)) : ('---')),
                escapeRow1: false,
                row1Class: timeClass // Apply the timeClass to the first row of multiline cell
            });
        };
    }

    createSectorCellRendererCurrLap(sectorKey, timeKey) {
        return (params) => {
            const driverInfo = params.data;
            const driverId = driverInfo.id;
            const delayedData = this.delayedLapData.get(driverId);
            const currentTime = Date.now();
            const CURR_LAP_FREEZE_DURATION = 5000; // 5 sec

            let lapInfo;
            let sectorStatus;

            if (delayedData && (currentTime - delayedData.timestamp < CURR_LAP_FREEZE_DURATION)) {
                // Use delayed data
                lapInfo = delayedData.oldLapData;
                sectorStatus = lapInfo["sector-status"];
            } else {
                // Use current data
                lapInfo = driverInfo["lap-info"]["curr-lap"];
                sectorStatus = lapInfo["sector-status"];
            }

            const timeMs = lapInfo[timeKey];
            let cellText = '';
            const status = lapInfo["driver-status"];
            if (status === "FLYING_LAP" || status === "ON_TRACK" || timeKey !== 'lap-time-ms') {
                cellText = (sectorKey === 'lap')
                    ? formatLapTime(timeMs)
                    : formatSectorTime(timeMs);
            } else {
                cellText = status;
            }

            let timeClass = '';
            if (sectorStatus && sectorKey !== 'lap') {
                  const sectorIndex = parseInt(sectorKey.slice(1)) - 1;
                  if (sectorStatus[sectorIndex] === this.GREEN_SECTOR) {
                      timeClass = 'green-time';
                  } else if (sectorStatus[sectorIndex] === this.PURPLE_SECTOR) {
                      timeClass = 'purple-time';
                  } else if (sectorStatus[sectorIndex] === this.RED_SECTOR) {
                      timeClass = 'red-time';
                  }
            }
            return this.createSingleLineCell(cellText, {className: timeClass});
        };
    }

    createTyreWearCellRenderer(wearField) {
        return (params) => {
            const tyreInfo = params.data["tyre-info"];
            const predictionLap = g_engView_predLapNum;
            const predictedTyreWearInfo = predictionLap
            ? tyreInfo["wear-prediction"]["predictions"].find(p => p["lap-number"] === predictionLap)
            : null;
            const currTyreWearInfo = tyreInfo["current-wear"];

            const driverInfo = params.data;
            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
            if (telemetryPublic) {
                return this.createMultiLineCell({
                    row1: formatFloat(currTyreWearInfo[wearField]) + '%',
                    row2: predictedTyreWearInfo
                        ? formatFloat(predictedTyreWearInfo[wearField]) + '%'
                        : '---'
                });
            } else {
                return this.getTelemetryRestrictedContent();
            }
        };
    }

    getColumnDefinitions() {
        return [
            {
                headerName: "Pos",
                colId: "position",
                context: {displayName: "Position", },
                field: "driver-info",
                flex: 4,
                sortable: true,
                cellRenderer: this.createPositionStatusCellRenderer(),
                equals: this.createPositionEqualsComparator,
                cellClass: 'ag-cell-multiline',
            },
            {
                headerName: "Name",
                colId: "name",
                context: {displayName: "Driver Name", },
                field: "name",
                flex: 12,
                cellRenderer: (params) => {
                    const data = params.data;
                    return this.createMultiLineCell({
                        row1: data.name,
                        row2: data.team
                    });
                },
                sortable: false,
                cellClass: 'ag-cell-multiline',
            },
            {
                headerName: "Delta",
                colId: "delta",
                context: {displayName: "Delta", },
                field: "delta-info",
                flex: 8,
                cellRenderer: (params) => {
                    const data = params.data;
                    const position = data.position;
                    const deltaInfo = data["delta-info"];
                    const deltaToCarInFront = deltaInfo["delta-to-car-in-front"] / 1000;
                    const deltaToLeader = deltaInfo["delta-to-leader"] / 1000;
                    if (position == 1) {
                        return this.createMultiLineCell({
                            row1: 'Interval',
                            row2: 'Leader'
                        });
                    }
                    return this.createMultiLineCell({
                        row1: formatFloat(deltaToCarInFront, { precision: 3, signed: true }),
                        row2: formatFloat(deltaToLeader, { precision: 3, signed: true })
                    });
                },
                sortable: false,
                cellClass: 'ag-cell-multiline',
            },
            {
                headerName: 'Penalties',
                colId: 'penalties',
                context: {displayName: 'Penalties', },
                children: [
                    {
                        headerName: "Track",
                        colId: "track-warnings",
                        context: {displayName: "Track Warnings", },
                        cellRenderer: this.createPenaltyCellRenderer("corner-cutting-warnings"),
                        field: "warns-pens-info.corner-cutting-warnings", flex: 1.5, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: 'Time',
                        colId: 'time-penalties',
                        context: {displayName: "Time Penalties", },
                        cellRenderer: this.createPenaltyCellRenderer("time-penalties"),
                        field: 'warns-pens-info.time-penalties', flex: 1.5, sortable: false, cellClass: 'ag-cell-single-line'
                    },
                    {
                        headerName: 'DT',
                        colId: 'drive-through',
                        context: {displayName: "Drive Through", },
                        field: 'warns-pens-info.num-dt', flex: 1.5, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createPenaltyCellRenderer("num-dt"),
                    },
                    {
                        headerName: 'Serv',
                        colId: 'stop-go',
                        context: {displayName: "Stop Go", },
                        field: 'warns-pens-info.num-sg', flex: 1.5, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createPenaltyCellRenderer("num-sg"),
                    },
                ],
            },
            {
                headerName: 'Best Lap',
                colId: 'best-lap',
                context: {displayName: 'Best Lap', },
                children: [
                    {
                        headerName: "Lap",
                        colId: "best-lap-time",
                        context: {displayName: "Best Lap Time", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRenderer('lap', 'lap-time-ms', 'lap-time-ms-player', false),
                        sortable: false,
                        flex: 2.5,
                        cellClass: (params) => {
                            const driverInfo = params.data;
                            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
                            return isReferenceDriver ? 'ag-cell-single-line' : 'ag-cell-multiline';
                        },
                        equals: this.createLapTimeEqualsComparator('best-lap'),
                    },
                    {
                        headerName: "S1",
                        colId: "best-sector-1",
                        context: {displayName: "Best Sector 1", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRenderer('s1', 's1-time-ms', 's1-time-ms-player', false),
                        sortable: false,
                        flex: 2.5,
                        cellClass: (params) => {
                            const driverInfo = params.data;
                            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
                            return isReferenceDriver ? 'ag-cell-single-line' : 'ag-cell-multiline';
                        },
                        equals: this.createSectorTimeEqualsComparator('best-lap', 's1', 's1-time-ms'),
                    },
                    {
                        headerName: "S2",
                        colId: "best-sector-2",
                        context: {displayName: "Best Sector 2", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRenderer('s2', 's2-time-ms', 's2-time-ms-player', false),
                        sortable: false,
                        flex: 2.5,
                        cellClass: (params) => {
                            const driverInfo = params.data;
                            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
                            return isReferenceDriver ? 'ag-cell-single-line' : 'ag-cell-multiline';
                        },
                        equals: this.createSectorTimeEqualsComparator('best-lap', 's2', 's2-time-ms'),
                    },
                    {
                        headerName: "S3",
                        colId: "best-sector-3",
                        context: {displayName: "Best Sector 3", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRenderer('s3', 's3-time-ms', 's3-time-ms-player', false),
                        sortable: false,
                        flex: 2.5,
                        cellClass: (params) => {
                            const driverInfo = params.data;
                            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
                            return isReferenceDriver ? 'ag-cell-single-line' : 'ag-cell-multiline';
                        },
                        equals: this.createSectorTimeEqualsComparator('best-lap', 's3', 's3-time-ms'),
                    }
                ]
            },
            {
                headerName: 'Last Lap',
                colId: 'last-lap',
                context: {displayName: 'Last Lap', },
                children: [
                    {
                        headerName: "Lap",
                        colId: "last-lap-time",
                        context: {displayName: "Last Lap Time", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRenderer('lap', 'lap-time-ms', 'lap-time-ms-player', true),
                        sortable: false,
                        flex: 2.5,
                        cellClass: (params) => {
                            const driverInfo = params.data;
                            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
                            return isReferenceDriver ? 'ag-cell-single-line' : 'ag-cell-multiline';
                        },
                        equals: this.createLapTimeEqualsComparator('last-lap'),
                    },
                    {
                        headerName: "S1",
                        colId: "last-sector-1",
                        context: {displayName: "Last Sector 1", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRenderer('s1', 's1-time-ms', 's1-time-ms-player', true),
                        sortable: false,
                        flex: 2.5,
                        cellClass: (params) => {
                            const driverInfo = params.data;
                            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
                            return isReferenceDriver ? 'ag-cell-single-line' : 'ag-cell-multiline';
                        },
                        equals: this.createSectorTimeEqualsComparator('last-lap', 's1', 's1-time-ms'),
                    },
                    {
                        headerName: "S2",
                        colId: "last-sector-2",
                        context: {displayName: "Last Sector 2",},
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRenderer('s2', 's2-time-ms', 's2-time-ms-player', true),
                        sortable: false,
                        flex: 2.5,
                        cellClass: (params) => {
                            const driverInfo = params.data;
                            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
                            return isReferenceDriver ? 'ag-cell-single-line' : 'ag-cell-multiline';
                        },
                        equals: this.createSectorTimeEqualsComparator('last-lap', 's2', 's2-time-ms'),
                    },
                    {
                        headerName: "S3",
                        colId: "last-sector-3",
                        context: {displayName: "Last Sector 3", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRenderer('s3', 's3-time-ms', 's3-time-ms-player', true),
                        sortable: false,
                        flex: 2.5,
                        cellClass: (params) => {
                            const driverInfo = params.data;
                            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;
                            return isReferenceDriver ? 'ag-cell-single-line' : 'ag-cell-multiline';
                        },
                        equals: this.createSectorTimeEqualsComparator('last-lap', 's3', 's3-time-ms'),
                    }
                ]
            },
            {
                headerName: 'Current Lap',
                colId: 'curr-lap',
                context: {displayName: 'Curr Lap', },
                children: [
                    {
                        headerName: "Lap",
                        colId: "curr-lap-time",
                        context: {displayName: "Current Lap Time", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRendererCurrLap('lap', 'lap-time-ms'),
                        sortable: false,
                        flex: 2.5,
                        cellClass: 'ag-cell-single-line',
                        // No comparator for current lap time, since no css classes are applied on this column
                    },
                    {
                        headerName: "S1",
                        colId: "curr-sector-1",
                        context: {displayName: "Current Sector 1", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRendererCurrLap('s1', 's1-time-ms'),
                        sortable: false,
                        flex: 2.5,
                        cellClass: 'ag-cell-single-line',
                        equals: this.createSectorTimeEqualsComparator('curr-lap', 's1', 's1-time-ms'),
                    },
                    {
                        headerName: "S2",
                        colId: "curr-sector-2",
                        context: {displayName: "Current Sector 2", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRendererCurrLap('s2', 's2-time-ms'),
                        sortable: false,
                        flex: 2.5,
                        cellClass: 'ag-cell-single-line',
                        equals: this.createSectorTimeEqualsComparator('curr-lap', 's2', 's2-time-ms'),
                    },
                    {
                        headerName: "S3",
                        colId: "curr-sector-3",
                        context: {displayName: "Current Sector 3", },
                        field: `lap-info`,
                        cellRenderer: this.createSectorCellRendererCurrLap('s3', 's3-time-ms'),
                        sortable: false,
                        flex: 2.5,
                        cellClass: 'ag-cell-single-line',
                        equals: this.createSectorTimeEqualsComparator('curr-lap', 's3', 's3-time-ms'),
                    },
                ]
            },
            {
                headerName: 'Speed Trap',
                colId: 'speed-trap',
                context: {displayName: 'Speed Trap', },
                field: "lap-info.speed-trap-record-kmph",
                flex: 8,
                cellRenderer: (params) =>  {
                    const driverInfo = params.data;
                    const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                    if (telemetryPublic) {
                        const speedTrap = driverInfo["lap-info"]["speed-trap-record-kmph"];
                        return this.createSingleLineCell(speedTrap == null ? "N/A" : `${formatFloat(speedTrap)}`);
                    } else {
                        return this.getTelemetryRestrictedContent();
                    }
                },
                sortable: false,
                cellClass: 'ag-cell-single-line',
            },
            {
                headerName: 'Tyre Wear',
                colId: 'tyre-wear',
                context: {displayName: 'Tyre Wear', },
                children: [
                    {
                        headerName: "Comp",
                        colId: "tyre-compound",
                        context: {displayName: "Tyre Compound", },
                        field: "tyre-info.visual-tyre-compound",
                        flex: 4,
                        valueGetter: (params) => {
                            const tyreInfo = params.data["tyre-info"] || {};
                            const compound = tyreInfo["visual-tyre-compound"] ?? "-";
                            const age = tyreInfo["tyre-age"] ?? "-";
                            const pitstops = tyreInfo["num-pitstops"] ?? "-";
                            return `${compound}.${age}.${pitstops}`;
                        },
                        cellRenderer: (params) => {
                            const tyreInfo = params.data["tyre-info"];
                            const tyreIcon = this.iconCache.getIcon(tyreInfo["visual-tyre-compound"]).outerHTML;
                            const agePitInfoStr = `${tyreInfo["tyre-age"]} L (${tyreInfo["num-pitstops"]} pit)`;
                            return this.createMultiLineCell({
                                row1: tyreIcon,
                                row2: agePitInfoStr,
                                escapeRow1: false
                            });
                        },
                        sortable: false,
                        cellClass: 'ag-cell-multiline',
                    },
                    {
                        headerName: "Rejoin",
                        colId: "pit-rejoin-position",
                        context: {displayName: "Pit Rejoin Position", },
                        field: "tyre-info.pit-rejoin-position",
                        flex: 4,
                        cellRenderer: (params) => {
                            const tyreInfo = params.data["tyre-info"];
                            const rejoinPosition = tyreInfo["pit-rejoin-position"] ?? null;
                            const rejoinPositionStr = (rejoinPosition != null)
                                ? `P${tyreInfo["pit-rejoin-position"]}`
                                : "N/A";
                            return this.createSingleLineCell(rejoinPositionStr);
                        },
                        sortable: false,
                        cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "Lap",
                        colId: "tyre-age",
                        context: {displayName: "Tyre Age / Pred. Lap", },
                        field: "tyre-info.tyre-age",
                        flex: 4,
                        cellRenderer: (params) => {
                            const predictionLap = g_engView_predLapNum;
                            return this.createMultiLineCell({
                                row1: "cur",
                                row2: predictionLap ? predictionLap : "---"
                            });
                        },
                        sortable: false,
                        cellClass: 'ag-cell-multiline',
                    },
                    {
                        headerName: "FL",
                        colId: "front-left-wear",
                        context: {displayName: "Front Left Wear", },
                        field: "tyre-info.current-wear.front-left-wear",
                        flex: 2,
                        cellRenderer: this.createTyreWearCellRenderer("front-left-wear"),
                        sortable: false,
                        cellClass: 'ag-cell-multiline',
                    },
                    {
                        headerName: "FR",
                        colId: "front-right-wear",
                        context: {displayName: "Front Right Wear", },
                        field: "tyre-info.current-wear.front-right-wear",
                        flex: 2,
                        cellRenderer: this.createTyreWearCellRenderer("front-right-wear"),
                        sortable: false,
                        cellClass: 'ag-cell-multiline',
                    },
                    {
                        headerName: "RL",
                        colId: "rear-left-wear",
                        context: {displayName: "Rear Left Wear", },
                        field: "tyre-info.current-wear.rear-left-wear",
                        flex: 2,
                        cellRenderer: this.createTyreWearCellRenderer("rear-left-wear"),
                        sortable: false,
                        cellClass: 'ag-cell-multiline',
                    },
                    {
                        headerName: "RR",
                        colId: "rear-right-wear",
                        context: {displayName: "Rear Right Wear", },
                        field: "tyre-info.current-wear.rear-right-wear",
                        flex: 2,
                        cellRenderer: this.createTyreWearCellRenderer("rear-right-wear"),
                        sortable: false,
                        cellClass: 'ag-cell-multiline',
                    },
                ],
            },
            {
                headerName: 'ERS',
                colId: 'ers',
                context: {displayName: 'ERS', },
                children: [
                    {
                        headerName: "Avail", colId: "ers-avail", context: {displayName: "ERS Available", },
                        field: "ers-info.ers-percent", flex: 3.33,
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.createSingleLineCell(`${formatFloat(driverInfo["ers-info"]["ers-percent-float"])}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "Deploy", colId: "ers-deployed", context: {displayName: "ERS Deployed", },
                        field: "ers-info.ers-deployed-this-lap", flex: 3.33,
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.createSingleLineCell(`${formatFloat(driverInfo["ers-info"]["ers-deployed-this-lap"])}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "Mode", colId: "ers-mode", context: {displayName: "ERS Mode", },
                        field: "ers-info.ers-mode", flex: 3.33,
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.createSingleLineCell(getShortERSMode(driverInfo["ers-info"]["ers-mode"]));
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                ],
            },
            {
                headerName: 'Fuel',
                colId: 'fuel',
                context: {displayName: 'Fuel', },
                children: [
                    {
                        headerName: "Total", colId: "fuel-in-tank", context: {displayName: "Fuel In Tank", },
                        field: "fuel-info.fuel-in-tank", flex: 3.33,
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const fuelInTank = driverInfo["fuel-info"]["fuel-in-tank"];
                                const cellContent = fuelInTank == null ? "N/A"
                                    : formatFloat(fuelInTank);
                                return this.createSingleLineCell(cellContent);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "Per Lap", colId: "fuel-per-lap", context: {displayName: "Fuel Per Lap", },
                        field: "fuel-info.curr-fuel-rate", flex: 3.33,
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const currFuelRate = driverInfo["fuel-info"]["curr-fuel-rate"];
                                const cellContent = currFuelRate == null
                                    ? "N/A" : formatFloat(currFuelRate);
                                return this.createSingleLineCell(cellContent);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "Est", colId: "estimated-laps", context: {displayName: "Estimated Laps", },
                        field: "fuel-info.surplus-laps-png", flex: 3.33,
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const surplusLapsPng = driverInfo["fuel-info"]["surplus-laps-png"];
                                const cellContent = surplusLapsPng == null ? "N/A"
                                    : formatFloat(surplusLapsPng, { signed: true });
                                return this.createSingleLineCell(cellContent);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                ],
            },
            {
                headerName: 'Damage',
                colId: 'damage',
                context: {displayName: 'Damage', },
                children: [
                    {
                        headerName: "FL", colId: "fl-wing-damage", context: {displayName: "Front Left Wing", },
                        field: "damage-info.fl-wing-damage", flex: 3.33,
                        cellRenderer: (params) =>  {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const flWingDamage = driverInfo["damage-info"]["fl-wing-damage"];
                                return this.createSingleLineCell(`${formatFloat(flWingDamage)}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "FR", colId: "fr-wing-damage", context: {displayName: "Front Right Wing",},
                        field: "damage-info.fr-wing-damage", flex: 3.33,
                        cellRenderer: (params) =>  {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const frWingDamage = driverInfo["damage-info"]["fr-wing-damage"];
                                return this.createSingleLineCell(`${formatFloat(frWingDamage)}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "RW", colId: "rear-wing-damage", context: {displayName: "Rear Wing", },
                        field: "damage-info.rear-wing-damage", flex: 3.33,
                        cellRenderer: (params) =>  {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const rearWingDamage = driverInfo["damage-info"]["rear-wing-damage"];
                                return this.createSingleLineCell(`${formatFloat(rearWingDamage)}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false, cellClass: 'ag-cell-single-line',
                    },
                ],
            },
        ];
    }

    createPenaltyCellRenderer(penaltyField) {
        return (params) => {
            const driverInfo = params.data;
            const penaltyCount = driverInfo["warns-pens-info"][penaltyField];
            const cellContent = (penaltyCount == null || penaltyCount === 0)
                ? "0"
                : penaltyCount.toString();
            return this.createSingleLineCell(cellContent);
        };
    }

    createPositionStatusCellRenderer() {
        return (params) => {
            const driverInfo = params.data;
            const position = driverInfo.position;
            let statusClass = '';
            let statusText = 'DRS';
            if (driverInfo["driver-info"]["is-pitting"]) {
                statusText = 'PIT';
                statusClass = 'driver-pitting';
            }
            else if (driverInfo["driver-info"]["drs-activated"]) {
                statusClass = 'drs-active';
            } else if (driverInfo["driver-info"]["drs-allowed"] || driverInfo["driver-info"]["drs-distance"]) {
                statusClass = 'drs-available';
            } else {
                statusClass = 'drs-not-available';
            }
            return this.createMultiLineCell({
                row1: position,
                row2: statusText,
                row2Class: statusClass
            });
        };
    }

    createSingleLineCell(value, { escape = true, className = '' } = {}) {
        const processedValue = escape ? escapeHtml(value) : value;
        const classes = `ag-cell-single-line-content ${className}`.trim();
        return `<div class="${classes}">${processedValue}</div>`;
    }

    createMultiLineCell({
        row1,
        row2,
        row1Class = 'eng-view-tyre-row-1',
        row2Class = 'eng-view-tyre-row-2',
        escapeRow1 = true,
        escapeRow2 = true}) {

        const processedRow1 = escapeRow1 ? escapeHtml(row1) : row1;
        const processedRow2 = escapeRow2 ? escapeHtml(row2) : row2;
        return `<div class='${row1Class}'>${processedRow1}</div><div class='${row2Class}'>${processedRow2}</div>`;
    }

    #clear() {
        this.previousTableData = [];
        this.delayedLapData = new Map();
        this.delayedLapDataJustCleared = false;
    }

    update(drivers, isSpectating, eventType, spectatorCarIndex, fastestLapMs, sessionUID, pitTimeLoss) {
        const prevSpectatorIndex = this.spectatorIndex;
        const prevIsSpectating = this.isSpectating;

        this.spectatorIndex = spectatorCarIndex;
        this.isSpectating = isSpectating;
        this.fastestLapMs = fastestLapMs;
        if (this.sessionUID !== sessionUID) {
            // clear the data structures if the session has changed
            this.#clear();
        }
        this.sessionUID = sessionUID;

        if (eventType === "Time Trial") {
            if (this.currEventType !== "Time Trial" && this.gridApi) {
                this.gridApi.setGridOption("rowData", []); // Clear data for Time Trial
                this.gridApi.showNoRowsOverlay();
            }
            return;
        }

        if (this.gridApi) {
            this.gridApi.hideOverlay();
        }

        const refEntry = updateReferenceLapTimes(drivers, (entry) =>
            this.isSpectating ?
            entry["driver-info"]?.["index"] == this.spectatorIndex :
            entry["driver-info"]?.["is-player"]
        );
        if (refEntry) {
            // this.refDriverTeam = refEntry["driver-info"]?.["team"] || '';
            this.refDriverTeam = refEntry["driver-info"]["team"];
        }

        // Sort, compute and insert rejoin positions
        drivers.sort((a, b) => a["driver-info"]["position"] - b["driver-info"]["position"]);
        insertRejoinPositions(drivers, pitTimeLoss);
        const newTableData = drivers.map(driver => ({
            ...driver,
            id: driver['driver-info']['index'],
            position: driver['driver-info']['position'],
            name: driver['driver-info']['name'],
            team: driver['driver-info']['team'],
            isPlayer: driver['driver-info']['is-player'],
            index: driver['driver-info']['index'],
        }));

        if (this.gridApi) {
            const currentTime = Date.now();
            const FIVE_SECONDS_MS = 5000;

            newTableData.forEach(newDriverData => {
                const driverId = newDriverData.id;
                const oldDriverData = this.previousTableData.find(d => d.id === driverId);

                const newLapNum = newDriverData["lap-info"]["curr-lap"]["lap-num"];
                const oldLapNum = oldDriverData ? oldDriverData["lap-info"]["curr-lap"]["lap-num"] : null;

                if (newLapNum !== oldLapNum && oldLapNum !== null) {
                    // Lap number changed, store the old lap data for delay
                    this.delayedLapData.set(driverId, {
                        oldLapData: oldDriverData["lap-info"]["curr-lap"],
                        timestamp: currentTime,
                    });
                } else if (this.delayedLapData.has(driverId)) {
                    // Check if 5 seconds have passed since the lap number change
                    const { timestamp } = this.delayedLapData.get(driverId);
                    if (currentTime - timestamp > FIVE_SECONDS_MS) {
                        this.delayedLapData.delete(driverId); // Clear delayed data
                    }
                }
            });

            if (newTableData && newTableData.length > 0) {
                // Set all row data - AG Grid will handle efficient updates internally
                this.gridApi.setGridOption('rowData', newTableData);
            } else {
                // Clear data if no new data
                this.gridApi.setGridOption('rowData', []);
            }

            this.previousTableData = newTableData; // Store current data for next update cycle

            // If spectator index or spectating status changed, redraw rows to update 'ref-row' class
            if (prevSpectatorIndex !== this.spectatorIndex || prevIsSpectating !== this.isSpectating) {
                this.gridApi.redrawRows();
            }
        }
        this.currEventType = eventType;
    }

    getTelemetryRestrictedContent() {
        return `<div class="telemetry-restricted-text">${this.TELEMETRY_DISABLED_TEXT}</div>`;
    }

    clear() {
        if (this.gridApi) {
            this.gridApi.setGridOption('rowData', []);
        }
    }

    fetchGridColumns() {
        if (this.gridApi) {
            const allColumns = this.gridApi.getColumns();
            const columnNames = allColumns.map(column => column.getColDef().headerName || column.getColDef().field);
            console.log("AG Grid Columns:", columnNames);
            return columnNames;
        }
        console.warn("AG Grid gridApi not available.");
        return [];
    }
    setupSettingsEventListeners() {
        this.settingsButton.addEventListener('click', () => this.toggleColumnVisibilityPane());
        this.closePaneButton.addEventListener('click', () => this.toggleColumnVisibilityPane());
        this.resetVisibilityButton.addEventListener('click', () => this.resetColumnVisibility());
        this.resetLayoutButton.addEventListener('click', () => this.resetColumnLayout()); // New event listener
    }

    toggleColumnVisibilityPane() {
        this.columnVisibilityPane.classList.toggle('open');
        if (this.columnVisibilityPane.classList.contains('open')) {
            this.populateColumnVisibilityToggles();
        }
    }

    resetColumnVisibility() {
        this.resetColumnState(); // Call the existing method to reset AG Grid state
        this.populateColumnVisibilityToggles(); // Re-populate toggles to reflect default state
    }

    populateColumnVisibilityToggles() {
        if (!this.gridApi) {
            console.warn("AG Grid API not available for populating column toggles.");
            return;
        }

        this.columnVisibilityContainer.innerHTML = ''; // Clear existing toggles
        let groupCounter = 0; // synthetic IDs for groups without colId/field

        const createToggle = (colDef, parentColId = null, isGroup = false, initialIsVisible = null) => {
            let colId = colDef.colId;

            // For groups with no id/field, generate synthetic one
            if (!colId && isGroup) {
                colId = `__group_${groupCounter++}`;
            }
            if (!colId) return;

            const column = this.gridApi.getColumn(colId);
            // groups without backing columns won't exist in gridApi
            const isVisible = initialIsVisible !== null ? initialIsVisible : (column ? column.isVisible() : true);

            const displayName = colDef.context?.displayName || colDef.headerName || colDef.field || 'Group';

            const toggleDiv = document.createElement('div');
            toggleDiv.classList.add('form-check', 'form-switch', 'column-toggle');
            if (parentColId) {
                toggleDiv.classList.add('child-column-toggle');
            }

            const input = document.createElement('input');
            input.classList.add('form-check-input');
            input.type = 'checkbox';
            input.id = `toggle-${colId}`;
            input.checked = isVisible;

            const label = document.createElement('label');
            label.classList.add('form-check-label');
            label.htmlFor = `toggle-${colId}`;
            label.textContent = displayName;

            input.addEventListener('change', (event) => {
                const checked = event.target.checked;
                let hasChanged = false;

                if (column) {
                    column.setVisible(checked);
                    hasChanged = true;
                }

                if (colDef.children) {
                    colDef.children.forEach(childColDef => {
                        const childColId = childColDef.colId;
                        if (childColId) {
                            const childColumn = this.gridApi.getColumn(childColId);
                            if (childColumn) {
                                childColumn.setVisible(checked);
                                hasChanged = true;
                            }
                            const childInput = document.getElementById(`toggle-${childColId}`);
                            if (childInput) {
                                childInput.checked = checked;
                            }
                        }
                    });
                }
                if (hasChanged) {
                    const savedColumnState = this.saveColumnState();
                    if (savedColumnState) {
                        this.gridApi.applyColumnState({ state: savedColumnState, applyOrder: true });
                    }
                }
            });

            toggleDiv.appendChild(input);
            toggleDiv.appendChild(label);
            return toggleDiv;
        };

        this.columnDefs.forEach(colDef => {
            if (colDef.children) {
                // column group
                const groupDiv = document.createElement('div');
                groupDiv.classList.add('column-group');

                // Determine initial visibility for the parent group
                const anyChildVisible = colDef.children.some(childColDef => {
                    const childColId = childColDef.colId;
                    const childColumn = childColId ? this.gridApi.getColumn(childColId) : null;
                    return childColumn ? childColumn.isVisible() : false;
                });

                const parentToggle = createToggle(colDef, null, true, anyChildVisible);
                if (parentToggle) {
                    groupDiv.appendChild(parentToggle);
                }

                const childrenContainer = document.createElement('div');
                childrenContainer.classList.add('column-group-children');

                colDef.children.forEach(childColDef => {
                    if (!childColDef.colId && childColDef.field) {
                        childColDef.colId = childColDef.field;
                    }
                    const childToggle = createToggle(childColDef, colDef.colId);
                    if (childToggle) {
                        childrenContainer.appendChild(childToggle);
                    }
                });
                groupDiv.appendChild(childrenContainer);
                this.columnVisibilityContainer.appendChild(groupDiv);
            } else {
                // regular column
                const toggle = createToggle(colDef);
                if (toggle) {
                    this.columnVisibilityContainer.appendChild(toggle);
                }
            }
        });
    }

    resetColumnLayout() {
        if (this.gridApi) {
            // Get the initial column definitions to restore default widths and order
            const initialColumnDefs = this.getColumnDefinitions();
            const initialColumnState = [];

            // Recursively process column definitions to build the initial state
            const processColDefs = (colDefs) => {
                colDefs.forEach(colDef => {
                    if (colDef.children) {
                        processColDefs(colDef.children);
                    } else {
                        initialColumnState.push({
                            colId: colDef.colId,
                            width: colDef.width || colDef.flex ? undefined : null, // Default width if not flex
                            flex: colDef.flex,
                            hide: false, // Ensure visibility is not reset here
                            pinned: colDef.pinned || null,
                        });
                    }
                });
            };
            processColDefs(initialColumnDefs);

            // Get the current column visibility state
            const currentColumnState = this.gridApi.getColumnState();
            const visibilityState = currentColumnState.reduce((acc, col) => {
                acc[col.colId] = col.hide;
                return acc;
            }, {});

            // Merge initial layout with current visibility
            const newState = initialColumnState.map(col => ({
                ...col,
                hide: visibilityState[col.colId] !== undefined ? visibilityState[col.colId] : col.hide,
            }));

            this.gridApi.applyColumnState({ state: newState, applyOrder: true });
            localStorage.removeItem(this.COLUMN_STATE_LS_KEY); // Clear saved state to ensure defaults are used
            console.debug('Column layout (positions and widths) reset to default, visibility preserved.');
        }
    }

    createPositionEqualsComparator(oldDriverInfo, newDriverInfo) {
        // If either value is missing, re-render
        if (!oldDriverInfo || !newDriverInfo) {
            return false;
        }

        // If position changed, definitely re-render
        if (oldDriverInfo["position"] !== newDriverInfo["position"]) {
            return false;
        }

        // re-render if pitting or drs status has changed
        if (oldDriverInfo['is-pitting'] !== newDriverInfo['is-pitting']) {
            return false;
        }

        if (oldDriverInfo['drs-activated'] !== newDriverInfo['drs-activated']) {
            return false;
        }

        if (oldDriverInfo['drs-allowed'] !== newDriverInfo['drs-allowed']) {
            return false;
        }

        return true;
    }

    createLapTimeEqualsComparator(lapType) {
        return (valueA, valueB) => {
            if (!valueA || !valueB) {
                return false;
            }

            const oldLapInfo = valueA[lapType];
            const newLapInfo = valueB[lapType];

            if (!oldLapInfo || !newLapInfo) {
                return false;
            }

            // If lap time changed, re-render
            if (oldLapInfo['lap-time-ms'] !== newLapInfo['lap-time-ms']) {
                return false;
            }

            // Check for overall lap status change (purple/green)
            // This logic needs to be consistent with createSectorCellRenderer
            const fastestLapMs = this.fastestLapMs;
            const pbLapMs = valueB["best-lap"]["lap-time-ms"];
            const oldTimeClass = oldLapInfo[`lap-time-ms-class`];
            let newTimeClass = '';
            const newLapTimeMs = newLapInfo['lap-time-ms'];
            if (newLapTimeMs) {
                if (newLapTimeMs === fastestLapMs) {
                    newTimeClass = 'purple-time';
                } else if (newLapTimeMs === pbLapMs) {
                    newTimeClass = 'green-time';
                }
            }

            if (oldTimeClass !== newTimeClass) {
                return false;
            }

            return true;
        };
    }

    createSectorTimeEqualsComparator(lapType, sectorKey, timeKey) {
        return (valueA, valueB) => {
            if (!valueA || !valueB) {
                return false;
            }

            const oldLapInfo = valueA[lapType];
            const newLapInfo = valueB[lapType];

            if (!oldLapInfo || !newLapInfo) {
                return false;
            }

            // If sector time changed, re-render
            const oldTimeMs = oldLapInfo[timeKey];
            const newTimeMs = newLapInfo[timeKey];
            if (oldTimeMs !== newTimeMs) {
                return false;
            }

            // If sector times are 0, just re-render.
            if ((lapType === 'curr-lap') && (newTimeMs === 0)) {
                return false;
            }

            // If sector status changed, re-render
            const sectorIndex = parseInt(sectorKey.slice(1)) - 1;
            const oldSectorStatus = oldLapInfo["sector-status"] ? oldLapInfo["sector-status"][sectorIndex] : null;
            const newSectorStatus = newLapInfo["sector-status"] ? newLapInfo["sector-status"][sectorIndex] : null;

            if (oldSectorStatus !== newSectorStatus) {
                return false;
            }

            return true;
        };
    }
}
function formatSessionTime(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return [hrs, mins, secs].map(v => String(v).padStart(2, '0')).join(':');
}

class EngViewRaceStatus {
    constructor(iconCache) {
        this.iconCache = iconCache;
        this.sessionTimeElement = document.getElementById('sessionTime');
        this.raceStatusElement = document.getElementById('raceStatus');
        this.raceStatusHeaderElement = document.getElementById('raceStatusHeader');
        this.currentLapElement = document.getElementById('currentLap');
        this.scCountElement = document.getElementById('scCount');
        this.vscCountElement = document.getElementById('vscCount');
        this.trackTempElement = document.getElementById('trackTemp');
        this.airTempElement = document.getElementById('airTemp');
        this.pitTimeLossElement = document.getElementById('pitTimeLoss');
        this.predictionLapInput = document.getElementById('predictionLap');
        this.predictionPitBtn = document.getElementById('predictionPitBtn');
        this.predictionMidBtn = document.getElementById('predictionMidBtn');
        this.predictionLastBtn = document.getElementById('predictionLastBtn');
        this.totalLaps = null;
        this.pitLap = null;
        this.midLap = null;

        this.predictionLapInput.addEventListener('input', (e) => {
            let value = parseInt(e.target.value);
            if (!isNaN(value) && value >= e.target.min && value <= e.target.max) {
                g_engView_predLapNum = value;
                console.debug('Prediction lap changed to:', g_engView_predLapNum);
            } else {
                console.warn('Invalid input: Out of range');
            }
        });

        this.predictionPitBtn.addEventListener('click', () => {
            g_engView_predLapNum = this.pitLap;
            this.#updatePredLapInputBox();
        });

        this.predictionMidBtn.addEventListener('click', () => {
            g_engView_predLapNum = this.midLap;
            this.#updatePredLapInputBox();
        });

        this.predictionLastBtn.addEventListener('click', () => {
            g_engView_predLapNum = this.totalLaps;
            this.#updatePredLapInputBox();
        });

        this.predictionPitBtn.disabled = true;
        this.predictionMidBtn.disabled = true;
        this.predictionLastBtn.disabled = true;
    }

    #updatePredLapInputBox() {
        this.predictionLapInput.value = g_engView_predLapNum;
        console.debug("Updated prediction element value", g_engView_predLapNum);
    }

    #getSCStatusString(scStatus) {
        switch(scStatus) {
            case "NO_SAFETY_CAR":
                return "Racing";
            case "FULL_SAFETY_CAR":
                return "Safety Car";
            case "VIRTUAL_SAFETY_CAR":
                return "VSC";
            case "FORMATION_LAP":
                return "Form. Lap";
            default:
                return "---";
        }
    }

    #getRaceStatusHeaderString(data) {
        const track = data["circuit"]
        const event = data["event-type"];
        if (track === "---" || event === "---") {
            return "Race Status";
        }

        return `${replaceRevSuffix(track)} - ${event}`;
    }

    #getSessionTimeString(data) {
        const sessionType = data["event-type"];
        const eventsWithTimeRemaining = ['Qualifying', 'Practice', 'Sprint Shootout'];
        const showTimeLeft = eventsWithTimeRemaining.some(type => sessionType.includes(type));
        if (showTimeLeft) {
            return formatSessionTime(data["session-time-left"]);
        } else {
            return formatSessionTime(data["session-duration-so-far"]);
        }
    }

    update(data) {

        let shouldUpdatePred = false;
        if (data["total-laps"] != "---" && this.totalLaps != data["total-laps"]) {
            // Set the initial prediction value
            g_engView_predLapNum = data["total-laps"];
            shouldUpdatePred = true;
            this.predictionLastBtn.disabled = false;
        }

        if (this.pitLap == null && data["player-pit-window"]) {
            // If the pit window becomes available
            g_engView_predLapNum = data["player-pit-window"];
            shouldUpdatePred = true;
            this.predictionPitBtn.disabled = false;
        }
        this.totalLaps = data["total-laps"];
        if (data["current-lap"] !== null && this.totalLaps !== null && data["current-lap"] !== 0 && this.totalLaps !== 0) {
            this.midLap = data["current-lap"] + Math.floor((data["total-laps"] - data["current-lap"]) / 2);
            this.predictionMidBtn.disabled = false;
        }

        this.pitLap = data["player-pit-window"];

        this.predictionLapInput.max = this.totalLaps;
        this.sessionTimeElement.textContent = this.#getSessionTimeString(data);
        this.raceStatusElement.textContent = this.#getSCStatusString(data["safety-car-status"]);
        this.raceStatusHeaderElement.textContent = this.#getRaceStatusHeaderString(data);

        let lapText = "";
        if (data['current-lap']) {
            lapText += data['current-lap'].toString();
          }
          if (data['event-type'] != "Time Trial" && ((data['total-laps'] ?? 0) > 1)) {
            lapText += "/" + data['total-laps'].toString();
          }
        this.currentLapElement.textContent = (lapText === "") ? ("---") : (lapText);

        this.scCountElement.textContent = data["num-sc"];
        this.vscCountElement.textContent = data["num-vsc"];
        this.trackTempElement.textContent = data["track-temperature"] + ' °C';
        this.airTempElement.textContent = data["air-temperature"] + ' °C';
        const pitTimeLoss = data["pit-time-loss"] ?? null;
        this.pitTimeLossElement.textContent = (pitTimeLoss != null)
            ? formatFloat(data["pit-time-loss"], { precision: 3 })
            : "N/A";

        if (shouldUpdatePred) {
            this.#updatePredLapInputBox();
        }
    }
}

// Weather table management class
class EngViewWeatherTable {
    constructor() {
        this.tableBody = document.querySelector('.eng-view-weather-table tbody');
    }

    update(weatherData) {
        const sessionWeather = (weatherData.length === 0) ? [] : transformForecast(weatherData)[0];
        // Limit to first 5 entries
        const limitedData = sessionWeather.slice(0, 5);

        // Create weather type row
        const typeRow = document.createElement('tr');
        typeRow.innerHTML = limitedData
            .map(w => `<td>${w["weather"]}</td>`)
            .join('');

        // Create time and probability row
        const timeRow = document.createElement('tr');
        timeRow.innerHTML = limitedData
            .map(w => `<td>+${w["time-offset"]}m (${w["rain-probability"]}%)</td>`)
            .join('');

        // Clear and update table
        this.tableBody.innerHTML = '';
        this.tableBody.appendChild(typeRow);
        this.tableBody.appendChild(timeRow);
    }

    clear() {
        this.tableBody.innerHTML = `
            <tr>${'<td>-</td>'.repeat(5)}</tr>
            <tr>${'<td>-</td>'.repeat(5)}</tr>
        `;
    }
}

let raceTable;
let raceStatus;
let weatherTable;
let iconCache;

// Initialize the dashboard
function initDashboard() {
    iconCache = new IconCache();
    raceTable = new EngViewRaceTable(iconCache);
    raceStatus = new EngViewRaceStatus(iconCache);
    weatherTable = new EngViewWeatherTable(iconCache);

    const driverModal = true;
    const settingsModal = false;
    const raceStatsModal = true;
    window.modalManager = new ModalManager(driverModal, settingsModal, raceStatsModal);

    const connectStart = Date.now();
    const socketio = io(`${location.protocol}//${location.hostname}:${location.port}`, {
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 500,
        reconnectionDelayMax: 3000,
        randomizationFactor: 0.3,
        timeout: 7000,
        transports: ['websocket', 'polling'],
        upgrade: true,
        rememberUpgrade: true,
        secure: location.protocol === 'https:',
    });

    socketio.on('connect', () => {
        socketio.emit('register-client', { type: 'race-table' });
        console.log(`⏱️ Socket connected in ${Date.now() - connectStart}ms`);
    });

    socketio.on('connect_error', (err) => {
        console.warn('❌ Socket connection error:', err.message);
    });

    socketio.on('reconnect_attempt', attempt => {
        console.log(`🔁 Reconnection attempt ${attempt}`);
    });

    socketio.on('race-table-update', (binaryData) => {
        let data;
        try {
            data = window.msgpack.decode(new Uint8Array(binaryData));
        } catch (err) {
            console.error('Failed to decode race-table-update:', err);
            return;
        }

        const {
            "table-entries": tableEntries,
            "is-spectating": isSpectating,
            "event-type": eventType,
            "spectator-car-index": spectatorCarIndex,
            "fastest-lap-overall" : fastestLapMs,
            "session-uid" : sessionUID,
            "pit-time-loss": pitTimeLoss = null // Default to null
        } = data;

        if (tableEntries || eventType === "Time Trial") {
            raceTable.update(tableEntries, isSpectating, eventType, spectatorCarIndex, fastestLapMs, sessionUID, pitTimeLoss);
        }
        raceStatus.update(data);
        weatherTable.update(data["weather-forecast-samples"]);
    });

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Start the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);
