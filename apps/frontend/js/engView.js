let g_engView_predLapNum = null;

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
        this.table = null;
        this.spectatorIndex = null;
        this.isSpectating = false;
        this.fastestLapMs = 0;
        this.sessionUID = null;
        this.INVALID_SECTOR = -2;
        this.RED_SECTOR = -1;
        this.YELLOW_SECTOR = 0;
        this.GREEN_SECTOR = 1;
        this.PURPLE_SECTOR = 2;
        this.COLUMN_WIDTHS_KEY = 'eng-view-table-column-widths'; // Storage key
        this.COLUMN_VISIBILITY_KEY = 'eng-view-table-column-visibility'; // Storage key for visibility
        this.COLUMN_ORDER_KEY = 'eng-view-table-column-order'; // Storage key for column order
        this.TELEMETRY_DISABLED_TEXT = "⌀";
        this.initTable();
    }

    // Save column widths to localStorage
    saveColumnWidths() {
        const columns = this.table.getColumns();
        const widths = {};

        columns.forEach(column => {
            const field = column.getField();
            const width = column.getWidth();
            if (field && width) {
                widths[field] = width;
            }
        });

        try {
            localStorage.setItem(this.COLUMN_WIDTHS_KEY, JSON.stringify(widths));
            console.debug('Column widths saved:', widths);
        } catch (error) {
            console.warn('Failed to save column widths:', error);
        }
    }

    // Load column widths from localStorage
    loadColumnWidths() {
        try {
            const saved = localStorage.getItem(this.COLUMN_WIDTHS_KEY);
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Failed to load column widths:', error);
        }
        return {};
    }

    // Apply saved widths to column definitions
    applyColumnWidths(columnDefinitions, savedWidths) {
        const applyWidthsRecursively = (columns) => {
            columns.forEach(col => {
                if (col.field && savedWidths[col.field]) {
                    col.width = savedWidths[col.field];
                }
                if (col.columns) {
                    applyWidthsRecursively(col.columns);
                }
            });
        };

        applyWidthsRecursively(columnDefinitions);
    }

    // Save column order to localStorage
    saveColumnOrder() {
        const columns = this.table.getColumns();
        const order = columns.map(column => column.getField());

        try {
            localStorage.setItem(this.COLUMN_ORDER_KEY, JSON.stringify(order));
            console.debug('Column order saved:', order);
        } catch (error) {
            console.warn('Failed to save column order:', error);
        }
    }

    // Load column order from localStorage
    loadColumnOrder() {
        try {
            const saved = localStorage.getItem(this.COLUMN_ORDER_KEY);
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Failed to load column order:', error);
        }
        return null; // Return null if no order is saved
    }

    initTable() {
        const columnDefinitions = this.getColumnDefinitions();

        // Load and apply saved column widths
        const savedWidths = this.loadColumnWidths();
        console.debug('Saved column widths:', savedWidths);
        this.applyColumnWidths(columnDefinitions, savedWidths);

        // Load and apply column order
        const savedOrder = this.loadColumnOrder();
        if (savedOrder) {
            columnDefinitions.sort((a, b) => {
                const indexA = savedOrder.indexOf(a.field);
                const indexB = savedOrder.indexOf(b.field);
                if (indexA === -1 || indexB === -1) return 0;
                return indexA - indexB;
            });
        }

        function applyHeaderClass(columns) {
            columns.forEach(col => {
                col.cssClass = "eng-view-table-main-header";
                if (col.columns) {
                    applyHeaderClass(col.columns);
                }
            });
        }

        applyHeaderClass(columnDefinitions);

        this.table = new Tabulator("#eng-view-table", {
            layout: "fitColumns",
            placeholder: "No Data Available",
            columnHeaderSortMulti: false,
            movableColumns: true,
            virtualDom: false,
            index: "id",
            initialSort: [
                {column: "position", dir: "asc"}
            ],
            columns: columnDefinitions,
            rowFormatter: (row) => {
                const data = row.getData();
                const isReferenceDriver = data.isPlayer || data.index === this.spectatorIndex;

                if (isReferenceDriver) {
                    row.getElement().classList.add('player-row');
                } else {
                    row.getElement().classList.remove('player-row');
                }
            },
        });

        // Add event listener for column resize
        this.table.on("columnResized", (column) => {
            // Debounce the save operation to avoid too frequent saves
            console.debug("Column resized:", column);
            clearTimeout(this.saveTimeout);
            this.saveTimeout = setTimeout(() => {
                this.saveColumnWidths();
            }, 500); // Save 500ms after the last resize
        });

        // Add event listener for column resize
        this.table.on("columnMoved", (column, columns) => {
            // Debounce the save operation to avoid too frequent saves
            console.debug("Column moved:", column);
            clearTimeout(this.saveTimeout);
            this.saveTimeout = setTimeout(() => {
                this.saveColumnOrder();
            }, 500); // Save 500ms after the last resize
        });
        this.saveColumnOrder();
    }

    // Optional: Method to reset column widths to default
    resetColumnWidths() {
        try {
            localStorage.removeItem(this.COLUMN_WIDTHS_KEY);
            console.debug('Column widths reset to default');
        } catch (error) {
            console.warn('Failed to reset column widths:', error);
        }
    }

    // Load column visibility from localStorage
    loadColumnVisibility() {
        try {
            const saved = localStorage.getItem(this.COLUMN_VISIBILITY_KEY);
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Failed to load column visibility:', error);
        }
        return {}; // Return default if nothing is saved or an error occurs
    }

    // Save column visibility to localStorage
    saveColumnVisibility(visibility) {
        try {
            localStorage.setItem(this.COLUMN_VISIBILITY_KEY, JSON.stringify(visibility));
        } catch (error) {
            console.warn('Failed to save column visibility:', error);
        }
    }

    createSectorFormatter(sectorKey, timeKey, playerTimeKey, isLastLap) {
        return (cell) => {
            const driverInfo = cell.getRow().getData();
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
                row2: formatDelta(delta)
            });
        };
    }

    createLastLapFormatter(sectorKey, timeKey, playerTimeKey, isLastLap) {
        return (cell) => {
            const driverInfo = cell.getRow().getData();
            const lapInfo = driverInfo["lap-info"]["last-lap"];
            const isReferenceDriver = driverInfo.isPlayer || driverInfo.index === this.spectatorIndex;

            if (sectorKey === 'lap') {
                const formattedTime = formatLapTime(lapInfo[timeKey]);
                const bestLapInfo = driverInfo["lap-info"]["best-lap"];
                let timeClass = '';
                if (lapInfo[timeKey] === this.fastestLapMs) {
                    timeClass = 'purple-time';
                } else if (lapInfo[timeKey] === bestLapInfo[timeKey]) {
                    timeClass = 'green-time';
                }
                const timeElement = `<div class="single-line-cell ${timeClass}">${formattedTime}</div>`;

                if (isReferenceDriver) {
                    return timeElement;
                }

                const delta = lapInfo[timeKey] - lapInfo[playerTimeKey];
                return this.createMultiLineCell({
                    row1: timeElement,
                    row2: formatDelta(delta)
                });
            } else {
                // For sectors, use the same logic as best lap
                return this.createSectorFormatter(sectorKey, timeKey, playerTimeKey, isLastLap)(cell);
            }
        };
    }

    createTyreWearFormatter(wearField) {
        return (cell) => {
            const tyreInfo = cell.getRow().getData()["tyre-info"];
            const predictionLap = g_engView_predLapNum;
            const predictedTyreWearInfo = predictionLap
            ? tyreInfo["wear-prediction"]["predictions"].find(p => p["lap-number"] === predictionLap)
            : null;
            const currTyreWearInfo = tyreInfo["current-wear"];

            const driverInfo = cell.getRow().getData();
            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
            if (telemetryPublic) {
                return this.createMultiLineCell({
                    row1: formatFloatWithTwoDecimals(currTyreWearInfo[wearField]) + '%',
                    row2: predictedTyreWearInfo
                        ? formatFloatWithTwoDecimals(predictedTyreWearInfo[wearField]) + '%'
                        : '---'
                });
            } else {
                return this.getTelemetryRestrictedContent();
            }
        };
    }

    createSectorColumns(lapType) {
        const isLastLap = lapType === 'last';
        const formatterMethod = isLastLap ? 'createLastLapFormatter' : 'createSectorFormatter';

        return [
            {
                title: "Lap",
                field: `lap-info.${lapType}-lap.lap-time-ms`,
                formatter: this[formatterMethod]('lap', 'lap-time-ms', 'lap-time-ms-player', isLastLap),
                ...this.getDisableSorting()
            },
            {
                title: "S1",
                field: `lap-info.${lapType}-lap.s1-time-ms`,
                formatter: this[formatterMethod]('s1', 's1-time-ms', 's1-time-ms-player', isLastLap),
                ...this.getDisableSorting()
            },
            {
                title: "S2",
                field: `lap-info.${lapType}-lap.s2-time-ms`,
                formatter: this[formatterMethod]('s2', 's2-time-ms', 's2-time-ms-player', isLastLap),
                ...this.getDisableSorting()
            },
            {
                title: "S3",
                field: `lap-info.${lapType}-lap.s3-time-ms`,
                formatter: this[formatterMethod]('s3', 's3-time-ms', 's3-time-ms-player', isLastLap),
                ...this.getDisableSorting()
            }
        ];
    }

    getDisableSorting() {
        return { headerSort: false };
    }

    getColumnDefinitions() {
        const disableSorting = this.getDisableSorting();
        return [
            {
                title: "Pos",
                field: "position",
                width: 40,
                sorter: "number",
                headerSort: false,
                formatter: (cell) => {
                    const driverInfo = cell.getRow().getData();
                    const position = driverInfo.position;
                    return this.createPositionStatusCell(position, driverInfo["driver-info"]);
                },
                // ...disableSorting
            },
            {
                title: "Name",
                field: "name",
                formatter: (cell, formatterParams, onRendered) => {
                    const data = cell.getRow().getData();
                    return this.createMultiLineCell({
                        row1: data.name,
                        row2: data.team
                    });
                },
                cellClick: (e, cell) => {
                    const data = cell.getRow().getData();
                    fetch(`/driver-info?index=${data.index}`)
                        .then(response => response.json())
                        .then(driverData => {
                            window.modalManager.openDriverModal(driverData, this.iconCache);
                        })
                        .catch(err => console.error("Fetch error:", err));
                },
                ...disableSorting
            },
            {
                title: "Delta",
                field: "delta",
                formatter: (cell) => {
                    const data = cell.getRow().getData();
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
                        row1: formatFloatWithThreeDecimalsSigned(deltaToCarInFront),
                        row2: formatFloatWithThreeDecimalsSigned(deltaToLeader)
                    });
                },
                ...disableSorting
            },
            {
                title: 'Penalties',
                headerSort: false,
                columns: [
                    { title: "Track", field: "warns-pens-info.corner-cutting-warnings", ...disableSorting },
                    { title: 'Time', field: 'warns-pens-info.time-penalties', ...disableSorting },
                    { title: 'DT', field: 'warns-pens-info.num-dt', ...disableSorting },
                    { title: 'Serv', field: 'warns-pens-info.num-sg', ...disableSorting },
                ],
            },
            {
                title: 'Best Lap',
                headerSort: false,
                columns: this.createSectorColumns('best')
            },
            {
                title: 'Last Lap',
                headerSort: false,
                columns: this.createSectorColumns('last')
            },
            {
                title: 'Tyre Wear',
                headerSort: false,
                columns: [
                    {
                        title: "Comp",
                        field: "tyre-info.visual-tyre-compound",
                        formatter: (cell) => {
                            const tyreInfo = cell.getRow().getData()["tyre-info"];
                            const tyreIcon = this.iconCache.getIcon(tyreInfo["visual-tyre-compound"]).outerHTML;
                            const agePitInfoStr = `${tyreInfo["tyre-age"]} L (${tyreInfo["num-pitstops"]} pit)`;
                            return this.createMultiLineCell({
                                row1: tyreIcon,
                                row2: agePitInfoStr
                            });
                        },
                        ...disableSorting
                    },
                    {
                        title: "Lap",
                        field: "tyre-info.tyre-age",
                        formatter: (cell) => {
                            const predictionLap = g_engView_predLapNum;
                            return this.createMultiLineCell({
                                row1: "cur",
                                row2: predictionLap ? predictionLap : "---"
                            });
                        },
                        ...disableSorting
                    },
                    {
                        title: "FL",
                        field: "tyre-info.current-wear.front-left-wear",
                        formatter: this.createTyreWearFormatter("front-left-wear"),
                        ...disableSorting
                    },
                    {
                        title: "FR",
                        field: "tyre-info.current-wear.front-right-wear",
                        formatter: this.createTyreWearFormatter("front-right-wear"),
                        ...disableSorting
                    },
                    {
                        title: "RL",
                        field: "tyre-info.current-wear.rear-left-wear",
                        formatter: this.createTyreWearFormatter("rear-left-wear"),
                        ...disableSorting
                    },
                    {
                        title: "RR",
                        field: "tyre-info.current-wear.rear-right-wear",
                        formatter: this.createTyreWearFormatter("rear-right-wear"),
                        ...disableSorting
                    },
                ],
            },
            {
                title: 'ERS',
                headerSort: false,
                columns: [
                    { title: "Avail", field: "ers-info.ers-percent",
                        formatter: (cell) => {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(cell.getValue());
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        },
                        ...disableSorting },
                    { title: "Deploy", field: "ers-info.ers-deployed-this-lap",
                        formatter: (cell) => {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(`${formatFloatWithTwoDecimals(cell.getValue())}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, ...disableSorting },
                    { title: "Mode", field: "ers-info.ers-mode",
                        formatter: (cell) => {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(getShortERSMode(cell.getValue()));
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, ...disableSorting },
                ],
            },
            {
                title: 'Fuel',
                headerSort: false,
                columns: [
                    { title: "Total", field: "fuel-info.fuel-in-tank",
                        formatter: (cell) => {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const cellContent = cell.getValue() == null ? "N/A"
                                    : formatFloatWithTwoDecimals(cell.getValue());
                                return this.getSingleLineCell(cellContent);
                          } else {
                               return this.getTelemetryRestrictedContent();
                          }
                      }, ...disableSorting },
                  { title: "Per Lap", field: "fuel-info.curr-fuel-rate",
                      formatter: (cell) => {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const cellContent = cell.getValue() == null
                                    ? "N/A" : formatFloatWithTwoDecimals(cell.getValue());
                                return this.getSingleLineCell(cellContent);
                          } else {
                               return this.getTelemetryRestrictedContent();
                          }
                      }, ...disableSorting },
                  { title: "Est", field: "fuel-info.surplus-laps-png",
                      formatter: (cell) => {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                const cellContent = cell.getValue() == null ? "N/A"
                                    : formatFloatWithTwoDecimalsSigned(cell.getValue());
                                return this.getSingleLineCell(cellContent);
                           } else {
                               return this.getTelemetryRestrictedContent();
                           }
                       }, ...disableSorting },
               ],
           },
           {
                title: 'Damage',
                headerSort: false,
                columns: [
                    { title: "FL", field: "damage-info.fl-wing-damage",
                        formatter: (cell) =>  {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(`${cell.getValue()}%`);
                            } else {
                                return this.getTelemetryRestrictedContent();
                            }
                        }, ...disableSorting },
                    { title: "FR", field: "damage-info.fr-wing-damage",
                        formatter: (cell) =>  {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(`${cell.getValue()}%`);
                           } else {
                               return this.getTelemetryRestrictedContent();
                           }
                       }, ...disableSorting },
                   { title: "RW", field: "damage-info.rear-wing-damage",
                       formatter: (cell) =>  {
                            const driverInfo = cell.getRow().getData();
                            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
                            if (telemetryPublic) {
                                return this.getSingleLineCell(`${cell.getValue()}%`);
                           } else {
                               return this.getTelemetryRestrictedContent();
                           }
                       }, ...disableSorting },
               ],
           },
       ];
    }

    createPositionStatusCell(position, driverInfo) {
        let statusClass = '';
        let statusText = 'DRS';
        if (driverInfo["is-pitting"]) {
            statusText = 'PIT';
            statusClass = 'driver-pitting';
        }
        else if (driverInfo["drs-activated"]) {
            statusClass = 'drs-active';
        } else if (driverInfo["drs-allowed"] || driverInfo["drs-distance"]) {
            statusClass = 'drs-available';
        } else {
            statusClass = 'drs-not-available';
        }
        return this.createMultiLineCell({
            row1: position,
            row2: statusText,
            row2Class: statusClass
        })
    }

    createMultiLineCell({
        row1,
        row2,
        row1Class = 'eng-view-tyre-row-1',
        row2Class = 'eng-view-tyre-row-2'}) {

        return `<div class='${row1Class}'>${row1}</div><div class='${row2Class}'>${row2}</div>`;
    }

    update(drivers, isSpectating, eventType, spectatorCarIndex, fastestLapMs, sessionUID) {
        this.spectatorIndex = spectatorCarIndex;
        this.isSpectating = isSpectating;
        this.fastestLapMs = fastestLapMs;

        if (eventType === "Time Trial") {
            this.table.clearData();
            this.table.options.placeholder = "Time Trial not supported in Engineer View";
            return;
        }

        updateReferenceLapTimes(drivers, (entry) =>
            this.isSpectating ?
            entry["driver-info"]?.["index"] == this.spectatorIndex :
            entry["driver-info"]?.["is-player"]
        );

        const newTableData = drivers.map(driver => ({
            ...driver,
            id: driver['driver-info']['index'],
            position: driver['driver-info']['position'],
            name: driver['driver-info']['name'],
            team: driver['driver-info']['team'],
            isPlayer: driver['driver-info']['is-player'],
            index: driver['driver-info']['index'],
        }));

        if (newTableData && newTableData.length > 0) {
            // Store current scroll position
            const scrollPosTop = this.table.rowManager.element.scrollTop;
            const scrollPosLeft = this.table.rowManager.element.scrollLeft;

            // Get current data to compare
            const currentData = this.table.getData();
            const currentDataMap = new Map(currentData.map(row => [row.id, row]));

            // Check if we need to force a full update
            const needsFullUpdate = this.needsFullUpdate(currentData, newTableData, currentDataMap, sessionUID);

            if (needsFullUpdate) {
                // If reference driver changed or new drivers, do full update
                this.table.setData(newTableData).then(() => {
                    // Force sort by position after full update
                    this.table.setSort("position", "asc");

                    setTimeout(() => {
                        this.table.rowManager.element.scrollTop = scrollPosTop;
                        this.table.rowManager.element.scrollLeft = scrollPosLeft;
                    }, 10);
                });
            } else {
                // Find rows that need updates
                const rowsToUpdate = [];
                const newDriverIds = new Set(newTableData.map(d => d.id));

                newTableData.forEach(newRow => {
                    const existingRow = currentDataMap.get(newRow.id);
                    if (!existingRow || this.hasDataChanged(existingRow, newRow)) {
                        rowsToUpdate.push(newRow);
                    }
                });

                // Remove drivers that are no longer in the race
                const rowsToDelete = currentData
                    .filter(row => !newDriverIds.has(row.id))
                    .map(row => row.id);

                // Delete removed rows first
                if (rowsToDelete.length > 0) {
                    this.table.deleteRow(rowsToDelete);
                }

                // Update or add rows that have changed
                if (rowsToUpdate.length > 0) {
                    this.table.updateOrAddData(rowsToUpdate).then(() => {
                        // Force sort by position after update
                        this.table.setSort("position", "asc");

                        // Restore scroll position after a short delay to ensure sorting is complete
                        setTimeout(() => {
                            this.table.rowManager.element.scrollTop = scrollPosTop;
                            this.table.rowManager.element.scrollLeft = scrollPosLeft;
                        }, 10);
                    });
                }
            }
        }
    }

    needsFullUpdate(currentData, newData, currentDataMap, sessionUID) {
        // If different number of drivers, need full update
        if (currentData.length !== newData.length) {
            return true;
        }

        // If session ID has changed, need update
        if (this.sessionUID !== sessionUID) {
            this.sessionUID = sessionUID;
            console.debug("Session UID changed, forcing full update", sessionUID);
            return true;
        }

        // Check if spectator or player reference changed (affects all formatters)
        for (const newRow of newData) {
            const existingRow = currentDataMap.get(newRow.id);
            if (existingRow) {
                // If isPlayer status changed, need full update
                if (existingRow.isPlayer !== newRow.isPlayer) {
                    return true;
                }
            }
        }

        // Check if spectator index changed (affects reference driver calculations)
        const currentReferenceDrivers = currentData.filter(d => d.isPlayer || d.index === this.spectatorIndex);
        const newReferenceDrivers = newData.filter(d => d.isPlayer || d.index === this.spectatorIndex);

        if (currentReferenceDrivers.length !== newReferenceDrivers.length) {
            return true;
        }

        if (currentReferenceDrivers.length > 0 && newReferenceDrivers.length > 0) {
            if (currentReferenceDrivers[0].id !== newReferenceDrivers[0].id) {
                return true;
            }
        }

        return false;
    }

    // Add this method to detect changes in data
    hasDataChanged(oldData, newData) {
        // Compare key fields that would affect display
        const fieldsToCompare = [
            'position',
            'name',
            'team',
            'delta-info',
            'warns-pens-info',
            'lap-info',
            'tyre-info',
            'ers-info',
            'fuel-info',
            'damage-info',
            'driver-info',
            'isPlayer'
        ];

        for (const field of fieldsToCompare) {
            if (JSON.stringify(oldData[field]) !== JSON.stringify(newData[field])) {
                return true;
            }
        }

        // Also check if reference driver status changed (affects formatting)
        const oldIsReference = oldData.isPlayer || oldData.index === this.spectatorIndex;
        const newIsReference = newData.isPlayer || newData.index === this.spectatorIndex;
        if (oldIsReference !== newIsReference) {
            return true;
        }

        return false;
    }


    getTelemetryRestrictedContent() {
        return this.getSingleLineCell(this.TELEMETRY_DISABLED_TEXT);
    }

    getSingleLineCell(value) {
        return `<div class="single-line-cell">${value}</div>`;
    }

    clear() {
        this.table.clearData();
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

        return `${track} - ${event}`;
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
            "session-uid" : sessionUID
        } = data;

        if (tableEntries || eventType === "Time Trial") {
            raceTable.update(tableEntries, isSpectating, eventType, spectatorCarIndex, fastestLapMs, sessionUID);
        }
        raceStatus.update(data);
        weatherTable.update(data["weather-forecast-samples"]);
    });

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Settings Modal Logic
    const settingsModal = document.getElementById('settings-modal');
    const settingsBtn = document.getElementById('settings-btn');
    const closeBtn = settingsModal.querySelector('.close-btn');
    const columnVisibilityContainer = document.getElementById('column-visibility-container');
    const resetVisibilityBtn = document.getElementById('reset-visibility-btn');

    settingsBtn.onclick = function() {
        settingsModal.style.display = 'block';
        populateColumnVisibility();
    }

    closeBtn.onclick = function() {
        settingsModal.style.display = 'none';
    }

    window.onclick = function(event) {
        if (event.target == settingsModal) {
            settingsModal.style.display = 'none';
        }
    }

    resetVisibilityBtn.onclick = function() {
        // Clear the visibility from local storage so it resets to default
        localStorage.removeItem(raceTable.COLUMN_VISIBILITY_KEY);

        // Re-populate the checkboxes which will now be all checked
        populateColumnVisibility();

        // Apply the default visibility to the table
        applyColumnVisibility();
    };

    function populateColumnVisibility() {
        columnVisibilityContainer.innerHTML = '';
        const columns = raceTable.table.getColumns(true);
        const visibility = raceTable.loadColumnVisibility();

        columns.forEach(column => {
            if (column.getDefinition().title) {
                createCheckbox(column, columnVisibilityContainer, visibility);
            }
        });
    }

    function createCheckbox(column, container, visibility, isSub = false) {
        const columnDef = column.getDefinition();
        const field = column.getField() || columnDef.title;
        const label = document.createElement('label');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = visibility[field] !== false; // Default to visible
        checkbox.onchange = () => {
            const newVisibility = raceTable.loadColumnVisibility();
            newVisibility[field] = checkbox.checked;

            // Handle parent/child visibility
            const subColumns = column.getDefinition().columns;
            if (subColumns && subColumns.length > 0) {
                subColumns.forEach(subColumnDef => {
                    const subField = subColumnDef.field || subColumnDef.title;
                    newVisibility[subField] = checkbox.checked;
                    const subCheckbox = columnVisibilityContainer.querySelector(`[data-field="${subField}"]`);
                    if (subCheckbox) {
                        subCheckbox.checked = checkbox.checked;
                        subCheckbox.disabled = !checkbox.checked;
                    }
                });
            }

            raceTable.saveColumnVisibility(newVisibility);
            applyColumnVisibility();
        };

        checkbox.dataset.field = field;
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(` ${columnDef.title}`));
        if (isSub) {
            label.classList.add('sub-column');
        }
        container.appendChild(label);

        const subColumns = column.getDefinition().columns;
        if (subColumns && subColumns.length > 0) {
            // Find the component for the sub-column to pass it to createCheckbox
            const columnComponents = column.getSubColumns();
            columnComponents.forEach(subColumnComponent => {
                createCheckbox(subColumnComponent, container, visibility, true);
            });
        }
    }

    function applyColumnVisibility() {
        const visibility = raceTable.loadColumnVisibility();
        raceTable.table.getColumns().forEach(column => {
            const field = column.getField() || column.getDefinition().title;
            if (visibility[field] === false) {
                column.hide();
            } else {
                column.show();
            }
        });
    }

    // Apply visibility on initial load
    applyColumnVisibility();
}

// Start the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);
