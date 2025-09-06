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
class EngViewRaceTable {
    constructor(iconCache) {
        this.iconCache = iconCache;
        this.gridApi = null;
        this.columnApi = null;
        this.gridInitialized = false; // Add a flag to track grid initialization
        this.spectatorIndex = null;
        this.isSpectating = false;
        this.fastestLapMs = 0;
        this.sessionUID = null;
        this.INVALID_SECTOR = -2;
        this.RED_SECTOR = -1;
        this.YELLOW_SECTOR = 0;
        this.GREEN_SECTOR = 1;
        this.PURPLE_SECTOR = 2;
        this.COLUMN_STATE_LS_KEY = 'eng-view-table-column-state'; // AG Grid combines width, visibility, and order
        this.TELEMETRY_DISABLED_TEXT = "⌀";
        this.initGrid();
    }

    saveColumnState() {
        if (this.gridApi) {
            const columnState = this.gridApi.getColumnState();
            try {
                localStorage.setItem(this.COLUMN_STATE_LS_KEY, JSON.stringify(columnState));
                console.debug('Column state saved:', columnState);
            } catch (error) {
                console.warn('Failed to save column state:', error);
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
        const gridOptions = {
            columnDefs: this.getColumnDefinitions(),
            rowData: [], // Initial empty data
            domLayout: 'normal', // or 'normal' if you want scrolling
            rowHeight: 60, // Add this line - adjust height as needed
            suppressColumnMoveAnimation: true,
            suppressFieldDotNotation: true, // Allow dots in field names
            defaultColDef: {
                resizable: true,
                sortable: true,
                filter: false,
                menuTabs: ['generalMenuTab'],
                headerClass: "eng-view-table-main-header",
            },
            onGridReady: (params) => {
                this.gridApi = params.api;
                this.columnApi = params.columnApi; // Note: columnApi is deprecated in newer versions
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
            },
            getRowId: (params) => params.data.id,
            getRowClass: (params) => {
                const data = params.data;
                if (!data) return;
                const isReferenceDriver = data.isPlayer || data.index === this.spectatorIndex;
                return isReferenceDriver ? 'player-row' : '';
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
                }
            }

            const timeElement = `<div class="single-line-cell ${timeClass}">${formattedTime}</div>`;

            if (isReferenceDriver) {
                return timeElement;
            }

            const delta = timeMs - lapInfo[playerTimeKey];
            return this.createMultiLineCell({
                row1: timeElement,
                row2: formatDelta(delta),
                escapeRow1: false
            });
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

    createSectorColumns(lapType) {
        const isLastLap = lapType === 'last';
        const cellRenderer = this.createSectorCellRenderer.bind(this);

        return [
            {
                headerName: "Lap",
                field: `lap-info.${lapType}-lap.lap-time-ms`,
                cellRenderer: cellRenderer('lap', 'lap-time-ms', 'lap-time-ms-player', isLastLap),
                sortable: false,
            },
            {
                headerName: "S1",
                field: `lap-info.${lapType}-lap.s1-time-ms`,
                cellRenderer: cellRenderer('s1', 's1-time-ms', 's1-time-ms-player', isLastLap),
                sortable: false,
            },
            {
                headerName: "S2",
                field: `lap-info.${lapType}-lap.s2-time-ms`,
                cellRenderer: cellRenderer('s2', 's2-time-ms', 's2-time-ms-player', isLastLap),
                sortable: false,
            },
            {
                headerName: "S3",
                field: `lap-info.${lapType}-lap.s3-time-ms`,
                cellRenderer: cellRenderer('s3', 's3-time-ms', 's3-time-ms-player', isLastLap),
                sortable: false,
            }
        ];
    }

    getColumnDefinitions() {
        return [
            {
                headerName: "Pos",
                field: "position",
                width: 70,
                sortable: true,
                cellRenderer: this.createPositionStatusCellRenderer(),
            },
            {
                headerName: "Name",
                field: "name",
                cellRenderer: (params) => {
                    const data = params.data;
                    return this.createMultiLineCell({
                        row1: data.name,
                        row2: data.team
                    });
                },
                onCellClicked: (params) => {
                    const data = params.data;
                    fetch(`/driver-info?index=${data.index}`)
                        .then(response => response.json())
                        .then(driverData => {
                            window.modalManager.openDriverModal(driverData, this.iconCache);
                        })
                        .catch(err => console.error("Fetch error:", err));
                },
                sortable: false,
            },
            {
                headerName: "Delta",
                field: "delta-info",
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
            },
            {
                headerName: 'Penalties',
                children: [
                    { headerName: "Track", field: "warns-pens-info.corner-cutting-warnings", sortable: false },
                    { headerName: 'Time', field: 'warns-pens-info.time-penalties', sortable: false },
                    { headerName: 'DT', field: 'warns-pens-info.num-dt', sortable: false },
                    { headerName: 'Serv', field: 'warns-pens-info.num-sg', sortable: false },
                ],
            },
            {
                headerName: 'Best Lap',
                children: this.createSectorColumns('best')
            },
            {
                headerName: 'Last Lap',
                children: this.createSectorColumns('last')
            },
            {
                headerName: 'Tyre Wear',
                children: [
                    {
                        headerName: "Comp",
                        field: "tyre-info.visual-tyre-compound",
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
                    },
                    {
                        headerName: "Rejoin",
                        field: "tyre-info.pit-rejoin-position",
                        cellRenderer: (params) => {
                            const tyreInfo = params.data["tyre-info"];
                            const rejoinPosition = tyreInfo["pit-rejoin-position"] ?? null;
                            const rejoinPositionStr = (rejoinPosition != null)
                                ? `P${tyreInfo["pit-rejoin-position"]}`
                                : "N/A";
                            return this.getSingleLineCell(rejoinPositionStr);
                        },
                        sortable: false,
                    },
                    {
                        headerName: "Lap",
                        field: "tyre-info.tyre-age",
                        cellRenderer: (params) => {
                            const predictionLap = g_engView_predLapNum;
                            return this.createMultiLineCell({
                                row1: "cur",
                                row2: predictionLap ? predictionLap : "---"
                            });
                        },
                        sortable: false,
                    },
                    {
                        headerName: "FL",
                        field: "tyre-info.current-wear.front-left-wear",
                        cellRenderer: this.createTyreWearCellRenderer("front-left-wear"),
                        sortable: false,
                    },
                    {
                        headerName: "FR",
                        field: "tyre-info.current-wear.front-right-wear",
                        cellRenderer: this.createTyreWearCellRenderer("front-right-wear"),
                        sortable: false,
                    },
                    {
                        headerName: "RL",
                        field: "tyre-info.current-wear.rear-left-wear",
                        cellRenderer: this.createTyreWearCellRenderer("rear-left-wear"),
                        sortable: false,
                    },
                    {
                        headerName: "RR",
                        field: "tyre-info.current-wear.rear-right-wear",
                        cellRenderer: this.createTyreWearCellRenderer("rear-right-wear"),
                        sortable: false,
                    },
                ],
            },
            {
                headerName: 'ERS',
                children: [
                    { headerName: "Avail", field: "ers-info.ers-percent",
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(params.value);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                    { headerName: "Deploy", field: "ers-info.ers-deployed-this-lap",
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(`${formatFloat(params.value)}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                    { headerName: "Mode", field: "ers-info.ers-mode",
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(getShortERSMode(driverInfo["ers-info"]["ers-mode"]));
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                ],
            },
            {
                headerName: 'Fuel',
                children: [
                    { headerName: "Total", field: "fuel-info.fuel-in-tank",
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const cellContent = params.value == null ? "N/A"
                                    : formatFloat(params.value);
                                return this.getSingleLineCell(cellContent);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                    { headerName: "Per Lap", field: "fuel-info.curr-fuel-rate",
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const cellContent = params.value == null
                                    ? "N/A" : formatFloat(params.value);
                                return this.getSingleLineCell(cellContent);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                    { headerName: "Est", field: "fuel-info.surplus-laps-png",
                        cellRenderer: (params) => {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const cellContent = params.value == null ? "N/A"
                                    : formatFloat(params.value, { signed: true });
                                return this.getSingleLineCell(cellContent);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                ],
            },
            {
                headerName: 'Damage',
                children: [
                    { headerName: "FL", field: "damage-info.fl-wing-damage",
                        cellRenderer: (params) =>  {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(`${params.value}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                    { headerName: "FR", field: "damage-info.fr-wing-damage",
                        cellRenderer: (params) =>  {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(`${params.value}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                    { headerName: "RW", field: "damage-info.rear-wing-damage",
                        cellRenderer: (params) =>  {
                            const driverInfo = params.data;
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(`${params.value}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, sortable: false,
                    },
                ],
            },
        ];
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

    update(drivers, isSpectating, eventType, spectatorCarIndex, fastestLapMs, sessionUID, pitTimeLoss) {
        this.spectatorIndex = spectatorCarIndex;
        this.isSpectating = isSpectating;
        this.fastestLapMs = fastestLapMs;

        if (eventType === "Time Trial") {
            console.warn("Time Trial not supported in Engineer View for AG Grid.");
            if (this.gridApi) {
                this.gridApi.setGridOption('rowData', []); // Clear data for Time Trial
            }
            return;
        }

        updateReferenceLapTimes(drivers, (entry) =>
            this.isSpectating ?
            entry["driver-info"]?.["index"] == this.spectatorIndex :
            entry["driver-info"]?.["is-player"]
        );

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
            if (newTableData && newTableData.length > 0) {
                // Set all row data - AG Grid will handle efficient updates internally
                this.gridApi.setGridOption('rowData', newTableData);
            } else {
                // Clear data if no new data
                this.gridApi.setGridOption('rowData', []);
            }
        }
    }

    getTelemetryRestrictedContent() {
        return this.getSingleLineCell(this.TELEMETRY_DISABLED_TEXT);
    }

    getSingleLineCell(value, escape = true) {
        const processedValue = escape ? escapeHtml(value) : value;
        return `<div class="single-line-cell">${processedValue}</div>`;
    }

    clear() {
        if (this.gridApi) {
            this.gridApi.setGridOption('rowData', []);
        }
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
    const raceStatsModal = false;
    window.modalManager = new ModalManager(driverModal, raceStatsModal, false);

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

    // Column Visibility Pane Logic
    const columnVisibilityPane = document.getElementById('column-visibility-pane');
    const settingsBtn = document.getElementById('settings-btn');
    const closePaneBtn = document.getElementById('close-pane-btn');
    const columnVisibilityContainer = document.getElementById('column-visibility-container');
    const resetVisibilityBtn = document.getElementById('reset-visibility-btn');

    settingsBtn.onclick = function() {
        columnVisibilityPane.classList.add('open');
        populateColumnVisibility();
    }

    closePaneBtn.onclick = function() {
        columnVisibilityPane.classList.remove('open');
    }

    resetVisibilityBtn.onclick = function() {
        // Clear the visibility from local storage so it resets to default
        localStorage.removeItem(raceTable.COLUMN_STATE_LS_KEY); // Changed to COLUMN_STATE_LS_KEY

        // Re-populate the checkboxes which will now be all checked
        populateColumnVisibility();

        // Apply the default visibility to the table
        applyColumnVisibility();
    };

    // Close the pane if clicked outside
    window.addEventListener('click', function(event) {
        if (!columnVisibilityPane.contains(event.target) && !settingsBtn.contains(event.target) && columnVisibilityPane.classList.contains('open')) {
            columnVisibilityPane.classList.remove('open');
        }
    });

    function populateColumnVisibility() {
        columnVisibilityContainer.innerHTML = '';
        // AG Grid: Get all columns from columnApi
        const allColumns = raceTable.columnApi.getColumns();
        const columnState = raceTable.loadColumnState(); // Load saved state

        allColumns.forEach(column => {
            const colDef = column.getColDef();
            const field = colDef.field || colDef.headerName; // Use field or headerName as identifier

            // Check if column is a group
            if (column.isColumnGroup()) {
                createColumnToggle(column, columnVisibilityContainer, columnState, false);
            } else if (field) {
                // Only create toggle for non-group columns with a field/headerName
                createColumnToggle(column, columnVisibilityContainer, columnState, false);
            }
        });
    }

    function createColumnToggle(column, container, columnState, isSub = false) {
        const colDef = column.getColDef();
        const field = colDef.field || colDef.headerName;
        const isVisible = columnState ? columnState.find(s => s.colId === column.getColId())?.hide !== true : true; // Default to visible

        const formCheckDiv = document.createElement('div');
        formCheckDiv.classList.add('form-check', 'form-switch');
        if (isSub) {
            formCheckDiv.classList.add('sub-column');
        }

        const input = document.createElement('input');
        input.classList.add('form-check-input');
        input.type = 'checkbox';
        input.role = 'switch';
        input.id = `toggle-${field}`;
        input.checked = isVisible;
        input.dataset.colId = column.getColId(); // Store colId for AG Grid

        const label = document.createElement('label');
        label.classList.add('form-check-label');
        label.htmlFor = `toggle-${field}`;
        label.textContent = colDef.headerName;

        input.onchange = () => {
            const colId = input.dataset.colId;
            raceTable.columnApi.setColumnVisible(colId, input.checked);
            raceTable.saveColumnState(); // Save state after change

            // Handle parent/child visibility for column groups
            if (column.isColumnGroup()) {
                const children = column.getChildren();
                children.forEach(childCol => {
                    const childInput = columnVisibilityContainer.querySelector(`input[data-col-id="${childCol.getColId()}"]`);
                    if (childInput) {
                        childInput.checked = input.checked;
                        childInput.disabled = !input.checked;
                        raceTable.columnApi.setColumnVisible(childCol.getColId(), input.checked);
                    }
                });
            }
        };

        formCheckDiv.appendChild(input);
        formCheckDiv.appendChild(label);
        container.appendChild(formCheckDiv);

        // Recursively create toggles for children of column groups
        if (column.isColumnGroup()) {
            column.getChildren().forEach(childCol => {
                createColumnToggle(childCol, container, columnState, true);
            });
        }
    }

    function applyColumnVisibility() {
        // Visibility is applied directly by setColumnVisible in onchange handler,
        // and on grid init by applyColumnState. This function might not be strictly needed
        // but can be kept for consistency or if there's a need to re-apply all visibility.
        const savedColumnState = raceTable.loadColumnState();
        if (savedColumnState) {
            raceTable.columnApi.applyColumnState({ state: savedColumnState, applyOrder: true });
        }
    }

    // Apply visibility on initial load
    // This is no longer needed as visibility is applied during table initialization
    // applyColumnVisibility();
}

// Start the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);
