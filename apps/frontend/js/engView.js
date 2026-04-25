let g_engView_predLapNum = null;

// Tyre surface temperature thresholds per compound (°C).
// Source: EA F1 tyre model data (F1 23/24/25 — identical across versions).
// Color zones derived from these: blue (<min), yellow (min to optimal-5),
// green (optimal ±5), orange (optimal+5 to max), red (>max).
const TYRE_TEMP_THRESHOLDS = {
    "C1":     { min:  90, optimal: 100, max: 115 },
    "C2":     { min:  85, optimal:  95, max: 115 },
    "C3":     { min:  80, optimal:  90, max: 105 },
    "C4":     { min:  75, optimal:  85, max: 100 },
    "C5":     { min:  70, optimal:  80, max:  90 },
    "Inters": { min:  60, optimal:  70, max:  80 },
    "Wet":    { min:  50, optimal:  60, max:  70 },
};
// Fallback for unknown/F2/classic compounds — uses C3 range as reasonable midpoint
const TYRE_TEMP_THRESHOLDS_DEFAULT = TYRE_TEMP_THRESHOLDS["C3"];

// Responsive column presets — columns visible at each breakpoint.
// null (desktop) = all columns visible via gridApi.resetColumnState().
const RESPONSIVE_COLUMN_PRESETS = {
    desktop: null,
    laptop: [
        'position', 'name', 'delta',
        'last-lap-time', 'last-sector-1', 'last-sector-2', 'last-sector-3',
        'speed-trap',
        'tyre-compound',
        'front-left-wear', 'front-right-wear', 'rear-left-wear', 'rear-right-wear',
        'tyre-inner-fl', 'tyre-inner-fr', 'tyre-inner-rl', 'tyre-inner-rr',
        'fuel-in-tank',
    ],
    tablet: [
        'position', 'name', 'delta',
        'last-lap-time',
        'tyre-compound', 'tyre-wear-agg',
        'tyre-inner-fl', 'tyre-inner-fr', 'tyre-inner-rl', 'tyre-inner-rr',
        'fuel-in-tank',
    ],
    compact: [
        'position', 'name', 'delta',
        'last-lap-time',
        'tyre-compound',
        'tyre-inner-fl', 'tyre-inner-fr', 'tyre-inner-rl', 'tyre-inner-rr',
    ],
};

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
        this.eGui.textContent = params.noRowsMessageFunc();
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
        this.COLUMN_PROFILES_LS_KEY = 'eng-view-table-column-profiles';
        this.COLUMN_ACTIVE_PROFILE_LS_KEY = 'eng-view-table-active-profile';
        this.DEFAULT_PROFILE_ID = '__default__';
        this.TELEMETRY_DISABLED_TEXT = "⌀";
        this.delayedLapData = new Map(); // Stores { oldLapData, timestamp } for each driver
        this.previousTableData = []; // Stores the data from the previous update cycle
        this.refDriverTeam = null; // Team of the reference driver (player or spectated)
        this.INVALID_TEAMS = new Set(["F1 Generic"]);
        this.MANUAL_REF_LS_KEY = 'eng-view-manual-ref-driver';
        this.manualRefDriverIndex = null;

        // Column visibility pane elements
        this.settingsButton = document.getElementById('settings-btn');
        this.columnVisibilityPane = document.getElementById('column-visibility-pane');
        this.resetVisibilityButton = document.getElementById('reset-visibility-btn');
        this.resetLayoutButton = document.getElementById('reset-layout-btn');
        this.closePaneButton = document.getElementById('close-pane-btn');
        this.autoFitColumnsButton = document.getElementById('autoFitColumnsBtn');
        this.columnVisibilityContainer = document.getElementById('column-visibility-container');
        this.columnProfileSelect = document.getElementById('column-profile-select');
        this.renameProfileBtn = document.getElementById('rename-profile-btn');
        this.newProfileBtn = document.getElementById('new-profile-btn');
        this.deleteProfileBtn = document.getElementById('delete-profile-btn');

        this.initGrid();
        this.setupSettingsEventListeners();
        this.#loadManualRef();
    }

    saveColumnState() {
        if (!this.gridApi) return null;

        const activeProfile = this.getActiveProfileId();
        if (activeProfile === this.DEFAULT_PROFILE_ID) {
            // Default is always all-columns-visible with library defaults — never persist changes
            return null;
        }

        const columnState = this.gridApi.getColumnState();
        try {
            localStorage.setItem(this.COLUMN_STATE_LS_KEY, JSON.stringify(columnState));
            console.debug('Column state saved:', columnState);

            const profiles = this.loadProfiles();
            if (profiles[activeProfile]) {
                profiles[activeProfile].state = columnState;
                this.saveProfiles(profiles);
            }

            return columnState;
        } catch (error) {
            console.warn('Failed to save column state:', error);
            return null;
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

    // --- Profile management ---

    loadProfiles() {
        try {
            const raw = localStorage.getItem(this.COLUMN_PROFILES_LS_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch {
            return {};
        }
    }

    saveProfiles(profiles) {
        try {
            localStorage.setItem(this.COLUMN_PROFILES_LS_KEY, JSON.stringify(profiles));
        } catch (error) {
            console.warn('Failed to save column profiles:', error);
        }
    }

    getActiveProfileId() {
        return localStorage.getItem(this.COLUMN_ACTIVE_PROFILE_LS_KEY) || this.DEFAULT_PROFILE_ID;
    }

    setActiveProfileId(profileId) {
        localStorage.setItem(this.COLUMN_ACTIVE_PROFILE_LS_KEY, profileId);
    }

    applyProfile(profileId) {
        this.setActiveProfileId(profileId);

        let state = null;
        if (profileId === this.DEFAULT_PROFILE_ID) {
            // Clear saved state so grid defaults apply on next load; apply defaults now
            localStorage.removeItem(this.COLUMN_STATE_LS_KEY);
        } else {
            const profiles = this.loadProfiles();
            state = profiles[profileId]?.state || null;
            if (state) {
                try {
                    localStorage.setItem(this.COLUMN_STATE_LS_KEY, JSON.stringify(state));
                } catch { /* ignore */ }
            }
        }

        if (this.gridApi) {
            if (state) {
                this.gridApi.applyColumnState({ state, applyOrder: true });
            } else {
                this.gridApi.resetColumnState();
            }
        }

        this.populateColumnVisibilityToggles();
    }


    createProfile(name) {
        if (!this.gridApi) return null;
        const profiles = this.loadProfiles();
        // Generate a unique ID
        const id = 'profile_' + Date.now();
        profiles[id] = { name, state: this.gridApi.getColumnState() };
        this.saveProfiles(profiles);
        return id;
    }

    deleteProfile(profileId) {
        if (profileId === this.DEFAULT_PROFILE_ID) return;
        const profiles = this.loadProfiles();
        delete profiles[profileId];
        this.saveProfiles(profiles);
    }

    populateProfileSelect() {
        const select = this.columnProfileSelect;
        const activeId = this.getActiveProfileId();
        select.innerHTML = '';

        const defaultOpt = document.createElement('option');
        defaultOpt.value = this.DEFAULT_PROFILE_ID;
        defaultOpt.textContent = 'Default';
        select.appendChild(defaultOpt);

        const profiles = this.loadProfiles();
        for (const [id, profile] of Object.entries(profiles)) {
            const opt = document.createElement('option');
            opt.value = id;
            opt.textContent = profile.name;
            select.appendChild(opt);
        }

        select.value = activeId;
        // Fall back to default if active profile was deleted
        if (!select.value) {
            select.value = this.DEFAULT_PROFILE_ID;
            this.setActiveProfileId(this.DEFAULT_PROFILE_ID);
        }

        this.updateProfileButtons();
    }

    updateProfileButtons() {
        const isDefault = this.columnProfileSelect.value === this.DEFAULT_PROFILE_ID;
        this.deleteProfileBtn.disabled = isDefault;
        this.renameProfileBtn.disabled = isDefault;
    }

    getCurrentBreakpoint() {
        const width = window.innerWidth;
        if (width >= 1440) return 'desktop';
        if (width >= 1024) return 'laptop';
        if (width >= 768)  return 'tablet';
        return 'compact';
    }

    applyBreakpointPreset(breakpoint) {
        const preset = RESPONSIVE_COLUMN_PRESETS[breakpoint];
        const isTouch = (breakpoint === 'tablet' || breakpoint === 'compact');
        this.gridApi.setGridOption('defaultColDef', {
            ...this.gridApi.getGridOption('defaultColDef'),
            resizable: !isTouch,
        });
        if (!preset) {
            this.gridApi.resetColumnState();
            return;
        }
        const visibleSet = new Set(preset);
        const allColumns = this.gridApi.getColumns();
        const newState = allColumns.map(col => ({
            colId: col.getColId(),
            hide: !visibleSet.has(col.getColId()),
        }));
        this.gridApi.applyColumnState({ state: newState });
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

                // Apply saved column state (skip for Default — library defaults apply)
                if (this.getActiveProfileId() !== this.DEFAULT_PROFILE_ID) {
                    const savedColumnState = this.loadColumnState();
                    if (savedColumnState) {
                        this.gridApi.applyColumnState({ state: savedColumnState, applyOrder: true });
                        console.debug('Applied saved column state:', savedColumnState);
                    }
                } else {
                    const breakpoint = this.getCurrentBreakpoint();
                    this.applyBreakpointPreset(breakpoint);
                    console.debug('Applied breakpoint preset:', breakpoint);
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
                const isReferenceDriver = this.#isRefDriver(data.index, data.isPlayer);
                if (isReferenceDriver) {
                    return 'ref-row';
                }
                if ((!this.INVALID_TEAMS.has(data.team)) && (data.team === this.refDriverTeam)) {
                    return 'teammate-row';
                }
                return '';
            },
            onRowClicked: (params) => {
                if (params.event?.target?.closest('.pin-ref-btn')) return;
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

        gridDiv.addEventListener('click', (e) => {
            const btn = e.target.closest('.pin-ref-btn');
            if (btn) {
                e.stopPropagation();
                this.#setManualRef(parseInt(btn.dataset.driverIndex, 10));
            }
        });
    }

    debounceSaveColumnState() {
        clearTimeout(this.columnStateSaveTimeout);
        this.columnStateSaveTimeout = setTimeout(() => {
            this.saveColumnState();
        }, 500);
    }

    createSectorCellRenderer(sectorKey, timeKey, playerTimeKey, isLastLap) {
        return (params) => {
            const driverInfo = params.data;
            const lapInfo = (isLastLap) ? driverInfo["lap-info"]["last-lap"] : driverInfo["lap-info"]["best-lap"];
            const bestLapInfo = driverInfo["lap-info"]["best-lap"];
            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
            const lapInfo = this.getCurrentLapInfo(params.data);
            const sectorStatus = lapInfo["sector-status"];

            const timeMs = lapInfo[timeKey];
            const cellText = (sectorKey === 'lap')
                ? formatLapTime(timeMs)
                : formatSectorTime(timeMs);

            let timeClass = '';
            if (sectorStatus && sectorKey !== 'lap' && sectorKey !== 'delta') {
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

    getCurrentLapInfo(driverInfo) {
        const driverId = driverInfo.id;
        const delayedData = this.delayedLapData.get(driverId);
        const currentTime = Date.now();
        const CURR_LAP_FREEZE_DURATION = 5000; // 5 sec

        if (delayedData && (currentTime - delayedData.timestamp < CURR_LAP_FREEZE_DURATION)) {
            return delayedData.oldLapData;
        }

        return driverInfo["lap-info"]["curr-lap"];
    }

    createStatusCellRendererCurrLap() {
        return (params) => {
            const lapInfo = this.getCurrentLapInfo(params.data);
            const status = lapInfo["driver-status"] ?? "---";
            return this.createSingleLineCell(status);
        };
    }

    createDeltaCellRendererCurrLap() {
        return (params) => {
            const driverInfo = params.data;
            const currLapInfo = driverInfo["lap-info"]["curr-lap"];
            const delta = currLapInfo["delta-ms"];
            const formattedTime = (delta !== null) ? formatFloat(delta/1000, { precision: 3, signed: true }) : '---';
            return this.createSingleLineCell(formattedTime);
        };
    }

    createTempCellRenderer(section, wheel) {
        return (params) => {
            const driverInfo = params.data;
            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
            if (!telemetryPublic) {
                return this.getTelemetryRestrictedContent();
            }
            const temps = driverInfo["tyre-info"][section];
            const val = temps?.[wheel];
            if (val == null) return this.createSingleLineCell("N/A");
            if (section === "inner-temps") {
                const compound = driverInfo["tyre-info"]["actual-tyre-compound"] ?? "";
                const th = TYRE_TEMP_THRESHOLDS[compound] ?? TYRE_TEMP_THRESHOLDS_DEFAULT;
                const tempClass = this.#getTyreTempClass(val, th);
                // escape: false is safe here — tempClass comes from #getTyreTempClass, never user input
                return this.createSingleLineCell(`${val}°`, { escape: false, className: tempClass });
            }
            return this.createSingleLineCell(`${val}°`);
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

    createAggregatedTyreWearCellRenderer() {
        return (params) => {
            const driverInfo = params.data;
            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
            if (!telemetryPublic) {
                return this.getTelemetryRestrictedContent();
            }
            const tyreInfo = driverInfo["tyre-info"];
            const currWear = tyreInfo["current-wear"];
            const wearValues = [
                currWear["front-left-wear"],
                currWear["front-right-wear"],
                currWear["rear-left-wear"],
                currWear["rear-right-wear"],
            ];
            const worstCurrentWear = Math.max(...wearValues);

            const predictionLap = g_engView_predLapNum;
            const predictedWearInfo = predictionLap
                ? tyreInfo["wear-prediction"]["predictions"].find(p => p["lap-number"] === predictionLap)
                : null;

            let worstPredictedWear = null;
            if (predictedWearInfo) {
                const predictedValues = [
                    predictedWearInfo["front-left-wear"],
                    predictedWearInfo["front-right-wear"],
                    predictedWearInfo["rear-left-wear"],
                    predictedWearInfo["rear-right-wear"],
                ];
                worstPredictedWear = Math.max(...predictedValues);
            }

            return this.createMultiLineCell({
                row1: formatFloat(worstCurrentWear) + '%',
                row2: worstPredictedWear != null
                    ? formatFloat(worstPredictedWear) + '%'
                    : '---'
            });
        };
    }

    #getTyreTempClass(temp, thresholds) {
        const greenLow = thresholds.optimal - 5;
        const greenHigh = thresholds.optimal + 5;
        if (temp < thresholds.min) return 'eng-temp-cold';
        if (temp < greenLow) return 'eng-temp-warmup';
        if (temp <= greenHigh) return 'eng-temp-optimal';
        if (temp <= thresholds.max) return 'eng-temp-hot';
        return 'eng-temp-overheat';
    }

    #getEngDamageClass(damage) {
        if (damage == null || damage === 0) return '';
        if (damage <= 20) return 'eng-dmg-light';
        if (damage <= 50) return 'eng-dmg-moderate';
        return 'eng-dmg-severe';
    }

    createDamageCellRenderer(damageField) {
        return (params) => {
            const driverInfo = params.data;
            const telemetryPublic = driverInfo["driver-info"]["telemetry-setting"] === "Public";
            if (!telemetryPublic) {
                return this.getTelemetryRestrictedContent();
            }
            const damage = driverInfo["damage-info"][damageField];
            const text = `${formatFloat(damage)}%`;
            const dmgClass = this.#getEngDamageClass(damage);
            // escape: false is safe here — dmgClass comes from #getEngDamageClass, never user input
            return this.createSingleLineCell(text, { escape: false, className: dmgClass });
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
                    const isPinned = this.manualRefDriverIndex === data.index;
                    const starIcon = isPinned ? 'bi-star-fill' : 'bi-star';
                    const starStyle = isPinned ? 'color:#ffd700;' : '';
                    return `<div class="driver-name-cell">` +
                        `<div class="driver-name-cell-text">` +
                            this.createMultiLineCell({ row1: data.name, row2: data.team }) +
                        `</div>` +
                        `<button class="pin-ref-btn" data-driver-index="${data.index}" title="Set as reference driver">` +
                            `<i class="bi ${starIcon}" style="${starStyle}"></i>` +
                        `</button>` +
                    `</div>`;
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
                            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
                            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
                            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
                            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
                            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
                            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
                            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
                            const isReferenceDriver = this.#isRefDriver(driverInfo.index, driverInfo.isPlayer);
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
                    {
                        headerName: "Status",
                        colId: "curr-lap-status",
                        context: {displayName: "Driver Status", },
                        field: `lap-info`,
                        cellRenderer: this.createStatusCellRendererCurrLap(),
                        sortable: false,
                        flex: 2.5,
                        cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "Delta",
                        colId: "curr-lap-delta",
                        context: {displayName: "Delta", },
                        field: `lap-info`,
                        cellRenderer: this.createDeltaCellRendererCurrLap(),
                        sortable: false,
                        flex: 2.5,
                        cellClass: 'ag-cell-single-line',
                        equals: this.createSectorTimeEqualsComparator('curr-lap', null, 'delta-ms'),
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
                    {
                        headerName: "Wear",
                        colId: "tyre-wear-agg",
                        context: { displayName: "Tyre Wear (Worst)" },
                        field: "tyre-info",
                        flex: 3,
                        hide: true,
                        cellRenderer: this.createAggregatedTyreWearCellRenderer(),
                        sortable: false,
                        cellClass: 'ag-cell-multiline',
                        equals: (val1, val2) => {
                            if (!val1 || !val2) return val1 === val2;
                            const wear1 = val1["current-wear"];
                            const wear2 = val2["current-wear"];
                            if (!wear1 || !wear2) return wear1 === wear2;
                            return wear1["front-left-wear"] === wear2["front-left-wear"]
                                && wear1["front-right-wear"] === wear2["front-right-wear"]
                                && wear1["rear-left-wear"] === wear2["rear-left-wear"]
                                && wear1["rear-right-wear"] === wear2["rear-right-wear"];
                        },
                    },
                ],
            },
            {
                headerName: 'Surf T',
                colId: 'tyre-surf-temps',
                context: {displayName: 'Tyre Surface Temps'},
                children: [
                    {
                        headerName: "FL", colId: "tyre-surf-fl", context: {displayName: "Surface Temp FL"},
                        field: "tyre-info.surface-temps.fl", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("surface-temps", "fl"),
                    },
                    {
                        headerName: "FR", colId: "tyre-surf-fr", context: {displayName: "Surface Temp FR"},
                        field: "tyre-info.surface-temps.fr", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("surface-temps", "fr"),
                    },
                    {
                        headerName: "RL", colId: "tyre-surf-rl", context: {displayName: "Surface Temp RL"},
                        field: "tyre-info.surface-temps.rl", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("surface-temps", "rl"),
                    },
                    {
                        headerName: "RR", colId: "tyre-surf-rr", context: {displayName: "Surface Temp RR"},
                        field: "tyre-info.surface-temps.rr", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("surface-temps", "rr"),
                    },
                ],
            },
            {
                headerName: 'Inner T',
                colId: 'tyre-inner-temps',
                context: {displayName: 'Tyre Inner Temps'},
                children: [
                    {
                        headerName: "FL", colId: "tyre-inner-fl", context: {displayName: "Inner Temp FL"},
                        field: "tyre-info.inner-temps.fl", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("inner-temps", "fl"),
                    },
                    {
                        headerName: "FR", colId: "tyre-inner-fr", context: {displayName: "Inner Temp FR"},
                        field: "tyre-info.inner-temps.fr", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("inner-temps", "fr"),
                    },
                    {
                        headerName: "RL", colId: "tyre-inner-rl", context: {displayName: "Inner Temp RL"},
                        field: "tyre-info.inner-temps.rl", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("inner-temps", "rl"),
                    },
                    {
                        headerName: "RR", colId: "tyre-inner-rr", context: {displayName: "Inner Temp RR"},
                        field: "tyre-info.inner-temps.rr", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("inner-temps", "rr"),
                    },
                ],
            },
            {
                headerName: 'Brake T',
                colId: 'brake-temps',
                context: {displayName: 'Brake Temps'},
                children: [
                    {
                        headerName: "FL", colId: "brake-fl", context: {displayName: "Brake Temp FL"},
                        field: "tyre-info.brakes-temps.fl", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("brakes-temps", "fl"),
                    },
                    {
                        headerName: "FR", colId: "brake-fr", context: {displayName: "Brake Temp FR"},
                        field: "tyre-info.brakes-temps.fr", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("brakes-temps", "fr"),
                    },
                    {
                        headerName: "RL", colId: "brake-rl", context: {displayName: "Brake Temp RL"},
                        field: "tyre-info.brakes-temps.rl", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("brakes-temps", "rl"),
                    },
                    {
                        headerName: "RR", colId: "brake-rr", context: {displayName: "Brake Temp RR"},
                        field: "tyre-info.brakes-temps.rr", flex: 2, sortable: false, cellClass: 'ag-cell-single-line',
                        cellRenderer: this.createTempCellRenderer("brakes-temps", "rr"),
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
                        headerName: "FLW", colId: "fl-wing-damage", context: {displayName: "Front Left Wing", },
                        field: "damage-info.fl-wing-damage", flex: 3.33,
                        cellRenderer: this.createDamageCellRenderer("fl-wing-damage"),
                        sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "FRW", colId: "fr-wing-damage", context: {displayName: "Front Right Wing",},
                        field: "damage-info.fr-wing-damage", flex: 3.33,
                        cellRenderer: this.createDamageCellRenderer("fr-wing-damage"),
                        sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "RW", colId: "rear-wing-damage", context: {displayName: "Rear Wing", },
                        field: "damage-info.rear-wing-damage", flex: 3.33,
                        cellRenderer: this.createDamageCellRenderer("rear-wing-damage"),
                        sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "Floor", colId: "floor-damage", context: {displayName: "Floor", },
                        field: "damage-info.floor-damage", flex: 3.33,
                        cellRenderer: this.createDamageCellRenderer("floor-damage"),
                        sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "DF", colId: "diffuser-damage", context: {displayName: "Diffuser", },
                        field: "damage-info.diffuser-damage", flex: 3.33,
                        cellRenderer: this.createDamageCellRenderer("diffuser-damage"),
                        sortable: false, cellClass: 'ag-cell-single-line',
                    },
                    {
                        headerName: "SP", colId: "sidepod-damage", context: {displayName: "Sidepod", },
                        field: "damage-info.sidepod-damage", flex: 3.33,
                        cellRenderer: this.createDamageCellRenderer("sidepod-damage"),
                        sortable: false, cellClass: 'ag-cell-single-line',
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
            const dnfStatus = driverInfo["driver-info"]["dnf-status"];
            if (dnfStatus === 'DNF' || dnfStatus === 'DSQ') {
                statusText = dnfStatus;
                statusClass = 'driver-dnf';
            }
            else if (driverInfo["driver-info"]["is-pitting"]) {
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

    #loadManualRef() {
        const saved = localStorage.getItem(this.MANUAL_REF_LS_KEY);
        if (saved !== null) {
            const parsed = parseInt(saved, 10);
            this.manualRefDriverIndex = isNaN(parsed) ? null : parsed;
        }
        document.getElementById('clear-ref-driver-btn')?.addEventListener('click', () => this.#clearManualRef());
    }


    #setManualRef(index) {
        if (this.manualRefDriverIndex === index) {
            this.#clearManualRef();
            return;
        }
        this.manualRefDriverIndex = index;
        localStorage.setItem(this.MANUAL_REF_LS_KEY, index.toString());
        if (this.gridApi) this.gridApi.redrawRows();
    }

    #clearManualRef() {
        this.manualRefDriverIndex = null;
        localStorage.removeItem(this.MANUAL_REF_LS_KEY);
        if (this.gridApi) this.gridApi.redrawRows();
    }

    #isRefDriver(index, isPlayer) {
        if (this.manualRefDriverIndex !== null) {
            return index === this.manualRefDriverIndex;
        }
        return isPlayer || index === this.spectatorIndex;
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

        // If the manually-pinned driver is no longer in the session, clear the override
        if (this.manualRefDriverIndex !== null) {
            const stillPresent = drivers.some(d => d["driver-info"]["index"] === this.manualRefDriverIndex);
            if (!stillPresent) {
                this.manualRefDriverIndex = null;
                localStorage.removeItem(this.MANUAL_REF_LS_KEY);
            }
        }

        const refEntry = updateReferenceLapTimes(drivers, (entry) => {
            if (this.manualRefDriverIndex !== null) {
                return entry["driver-info"]?.["index"] === this.manualRefDriverIndex;
            }
            return this.isSpectating
                ? entry["driver-info"]?.["index"] == this.spectatorIndex
                : entry["driver-info"]?.["is-player"];
        });
        if (refEntry) {
            // this.refDriverTeam = refEntry["driver-info"]?.["team"] || '';
            this.refDriverTeam = refEntry["driver-info"]["team"];
        }

        // Sort, compute and insert rejoin positions
        drivers.sort((a, b) => a["driver-info"]["position"] - b["driver-info"]["position"]);
        const refIndex = this.manualRefDriverIndex ?? refEntry?.["driver-info"]?.["index"] ?? null;
        insertRejoinPositions(drivers, pitTimeLoss, refIndex);
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
        this.resetLayoutButton.addEventListener('click', () => this.resetColumnLayout());

        this.columnProfileSelect.addEventListener('change', () => {
            this.applyProfile(this.columnProfileSelect.value);
            this.updateProfileButtons();
        });

        this.renameProfileBtn.addEventListener('click', () => {
            const profileId = this.columnProfileSelect.value;
            if (profileId === this.DEFAULT_PROFILE_ID) return;
            const profiles = this.loadProfiles();
            const currentName = profiles[profileId]?.name || '';
            const newName = prompt('Enter a new name for this profile:', currentName);
            if (!newName || !newName.trim() || newName.trim() === currentName) return;
            profiles[profileId].name = newName.trim();
            this.saveProfiles(profiles);
            this.populateProfileSelect();
        });

        this.newProfileBtn.addEventListener('click', () => {
            const name = prompt('Enter a name for the new profile:');
            if (!name || !name.trim()) return;
            const id = this.createProfile(name.trim());
            if (id) {
                this.populateProfileSelect();
                this.columnProfileSelect.value = id;
                this.setActiveProfileId(id);
                this.updateProfileButtons();
            }
        });

        this.deleteProfileBtn.addEventListener('click', () => {
            const profileId = this.columnProfileSelect.value;
            if (profileId === this.DEFAULT_PROFILE_ID) return;
            const profiles = this.loadProfiles();
            const name = profiles[profileId]?.name || profileId;
            if (!confirm(`Delete profile "${name}"?`)) return;
            this.deleteProfile(profileId);
            this.applyProfile(this.DEFAULT_PROFILE_ID);
            this.populateProfileSelect();
        });

        this.autoFitColumnsButton?.addEventListener('click', () => {
            if (this.gridApi) {
                this.gridApi.autoSizeAllColumns();
            }
        });
    }

    toggleColumnVisibilityPane() {
        if (window.drawerManager) {
            window.drawerManager.closeAllDrawers();
        }
        this.columnVisibilityPane.classList.toggle('open');
        if (this.columnVisibilityPane.classList.contains('open')) {
            this.populateProfileSelect();
            this.populateColumnVisibilityToggles();
        }
    }

    resetColumnVisibility() {
        this.resetColumnState();
        // If on a named profile, update its stored state after reset
        const activeProfile = this.getActiveProfileId();
        if (activeProfile !== this.DEFAULT_PROFILE_ID && this.gridApi) {
            const profiles = this.loadProfiles();
            if (profiles[activeProfile]) {
                profiles[activeProfile].state = this.gridApi.getColumnState();
                this.saveProfiles(profiles);
            }
        } else {
            // For default profile, apply responsive breakpoint
            localStorage.removeItem(this.COLUMN_STATE_LS_KEY);
            const breakpoint = this.getCurrentBreakpoint();
            this.applyBreakpointPreset(breakpoint);
        }
        this.populateColumnVisibilityToggles();
    }

    populateColumnVisibilityToggles() {
        if (!this.gridApi) {
            console.warn("AG Grid API not available for populating column toggles.");
            return;
        }

        this.columnVisibilityContainer.textContent = ''; // Clear existing toggles
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

                // Collect all colIds to toggle (leaf column + children)
                const colIdsToToggle = [];
                if (column) {
                    colIdsToToggle.push(colId);
                }
                if (colDef.children) {
                    colDef.children.forEach(childColDef => {
                        const childColId = childColDef.colId;
                        if (childColId && this.gridApi.getColumn(childColId)) {
                            colIdsToToggle.push(childColId);
                            const childInput = document.getElementById(`toggle-${childColId}`);
                            if (childInput) {
                                childInput.checked = checked;
                            }
                        }
                    });
                }
                if (colIdsToToggle.length > 0) {
                    this.gridApi.setColumnsVisible(colIdsToToggle, checked);
                    hasChanged = true;
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
            // Capture current visibility before resetting
            const visibilityState = this.gridApi.getColumnState().reduce((acc, col) => {
                acc[col.colId] = col.hide;
                return acc;
            }, {});

            // Let the library restore its true defaults (order, widths, flex)
            this.gridApi.resetColumnState();

            // Re-apply visibility so columns the user hid stay hidden
            const restoredState = this.gridApi.getColumnState().map(col => ({
                colId: col.colId,
                hide: visibilityState[col.colId] !== undefined ? visibilityState[col.colId] : col.hide,
            }));
            this.gridApi.applyColumnState({ state: restoredState });

            localStorage.removeItem(this.COLUMN_STATE_LS_KEY);
            console.debug('Column layout (positions and widths) reset to default, visibility preserved.');

            // If on a named profile, update its stored state after layout reset
            const activeProfile = this.getActiveProfileId();
            if (activeProfile !== this.DEFAULT_PROFILE_ID) {
                const profiles = this.loadProfiles();
                if (profiles[activeProfile]) {
                    profiles[activeProfile].state = this.gridApi.getColumnState();
                    this.saveProfiles(profiles);
                }
            }
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

            if (!sectorKey) {
                return true;
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

        // Collapse elements
        this.collapseBtn = document.getElementById('raceStatusCollapseBtn');
        this.raceStatusBody = document.getElementById('raceStatusBody');
        this.summaryLap = document.getElementById('summaryLap');
        this.summaryTrackTemp = document.getElementById('summaryTrackTemp');
        this.summaryAirTemp = document.getElementById('summaryAirTemp');
        this.summarySC = document.getElementById('summarySC');
        this.summaryVSC = document.getElementById('summaryVSC');
        this.LS_COLLAPSE_KEY = 'raceStatusCollapsed';
        this._collapseMediaQuery = window.matchMedia('(max-width: 1439px)');

        this._initCollapse();

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

    _initCollapse() {
        // Toggle button click
        this.collapseBtn.addEventListener('click', () => {
            const isCollapsed = this.raceStatusBody.classList.toggle('rs-collapsed');
            this.collapseBtn.classList.toggle('rs-open', !isCollapsed);
            localStorage.setItem(this.LS_COLLAPSE_KEY, isCollapsed ? 'true' : 'false');
        });

        // Restore state from localStorage (only meaningful < 1440px)
        const applyCollapse = () => {
            if (this._collapseMediaQuery.matches) {
                const saved = localStorage.getItem(this.LS_COLLAPSE_KEY);
                // Default to collapsed when narrow
                const shouldCollapse = saved !== 'false';
                this.raceStatusBody.classList.toggle('rs-collapsed', shouldCollapse);
                this.collapseBtn.classList.toggle('rs-open', !shouldCollapse);
            } else {
                // Wide screen — always show body, remove collapse state
                this.raceStatusBody.classList.remove('rs-collapsed');
                this.collapseBtn.classList.remove('rs-open');
            }
        };

        applyCollapse();
        this._collapseMediaQuery.addEventListener('change', applyCollapse);
    }

    #updateSummary(data) {
        let lapText = '';
        if (data['current-lap']) {
            lapText += data['current-lap'].toString();
        }
        if (data['event-type'] !== 'Time Trial' && ((data['total-laps'] ?? 0) > 1)) {
            lapText += '/' + data['total-laps'].toString();
        }
        this.summaryLap.textContent = lapText || '—';
        this.summaryTrackTemp.textContent = data['track-temperature'] + ' °C';
        this.summaryAirTemp.textContent = data['air-temperature'] + ' °C';
        this.summarySC.textContent = data['num-sc'] ?? '0';
        this.summaryVSC.textContent = data['num-vsc'] ?? '0';
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

        this.#updateSummary(data);
    }
}

// Weather table management class
class EngViewWeatherTable {
    constructor(weatherGraph) {
        this.tableBody = document.querySelector('.eng-view-weather-table tbody');
        this.sessionNameElement = document.getElementById('weatherSessionName');
        document.getElementById('weatherSessionPrevBtn').addEventListener('click', () => this.cycleSessionBackward());
        document.getElementById('weatherSessionNextBtn').addEventListener('click', () => this.cycleSessionForward());
        this.currSessionIndex = 0;
        this.numSessions = 0;
        this.numDisplayedSamples = 0;
        this.sessionUID = 0;
        this.weatherGraph = weatherGraph;
        this.weatherBySession = [];
    }

    cycleSessionForward() {
        if (this.numSessions === 0) return;
        this.currSessionIndex = (this.currSessionIndex + 1) % this.numSessions;
        this.#updateGraph();
    }

    cycleSessionBackward() {
        if (this.numSessions === 0) return;
        this.currSessionIndex =
            (this.currSessionIndex - 1 + this.numSessions) % this.numSessions;
        this.#updateGraph();
    }

    #updateGraph() {
        if (!this.weatherGraph || this.weatherBySession.length === 0) return;
        const currSession = this.weatherBySession[this.currSessionIndex];
        if (currSession) {
            const sessionKey = `${currSession["session_type"]}_${this.currSessionIndex}`;
            this.weatherGraph.update(currSession["items"], sessionKey);
        }
    }

    update(incomingData, incomingSessionUID) {
        if (incomingData.length === 0) {
            this.clear();
            return;
        }

        if (incomingSessionUID != this.sessionUID) {
            this.currSessionIndex = 0;
            this.sessionUID = incomingSessionUID
        }

        this.weatherBySession = groupWeatherSamplesBySessionType(incomingData);
        this.numSessions = this.weatherBySession.length;
        if (this.currSessionIndex < 0 ||
            this.currSessionIndex >= this.weatherBySession.length) {
            console.debug('Invalid session index. Resetting to 0.');
            this.currSessionIndex = 0;
        }

        const currSession = this.weatherBySession[this.currSessionIndex];
        const sessionType = currSession["session_type"];
        this.sessionNameElement.textContent = `${sessionType} (${this.currSessionIndex + 1}/${this.numSessions})`;

        const sessionWeather = currSession["items"];
        const limitedData = sessionWeather.slice(0, 5);

        // Create weather type row
        const typeRow = document.createElement('tr');
        limitedData.forEach(w => {
            const cell = typeRow.insertCell();
            cell.textContent = w["weather"];
        });

        // Create time and probability row
        const timeRow = document.createElement('tr');
        limitedData.forEach(w => {
            const cell = timeRow.insertCell();
            cell.textContent = `+${w["time-offset"]}m (${w["rain-probability"]}%)`;
        });

        // Clear and update table
        this.tableBody.textContent = '';
        this.tableBody.appendChild(typeRow);
        this.tableBody.appendChild(timeRow);
        this.numDisplayedSamples = limitedData.length;

        this.#updateGraph();
    }

    clear() {
        if (!this.numDisplayedSamples) return;
        this.tableBody.innerHTML = `
            <tr>${'<td>-</td>'.repeat(5)}</tr>
            <tr>${'<td>-</td>'.repeat(5)}</tr>
        `;
        this.currSessionIndex = 0;
        this.numSessions = 0;
        this.sessionUID = 0;
        this.numDisplayedSamples = 0;
        this.weatherBySession = [];
        if (this.weatherGraph) this.weatherGraph.update([], null);
    }
}

let raceTable;
let raceStatus;
let weatherTable;
let weatherGraph;
let iconCache;
let trackMap;

// Weather display mode toggle (table / graph / both)
function initWeatherDisplayToggle() {
    const LS_KEY = 'weatherDisplayMode';
    const VALID_MODES = ['table', 'graph', 'both'];
    const toggleGroup = document.getElementById('weatherDisplayToggle');
    const tableWrapper = document.getElementById('weatherTableWrapper');
    const graphContainer = document.getElementById('weatherGraphContainer');

    function applyMode(mode) {
        toggleGroup.querySelectorAll('button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.value === mode);
        });
        tableWrapper.style.display = (mode === 'graph') ? 'none' : '';
        graphContainer.style.display = (mode === 'table') ? 'none' : '';
    }

    const saved = localStorage.getItem(LS_KEY);
    applyMode(VALID_MODES.includes(saved) ? saved : 'both');

    toggleGroup.addEventListener('click', (e) => {
        const btn = e.target.closest('button[data-value]');
        if (!btn || !VALID_MODES.includes(btn.dataset.value)) return;
        localStorage.setItem(LS_KEY, btn.dataset.value);
        applyMode(btn.dataset.value);
    });
}

// ── Card Collapse Toggles (Weather + TrackMap at laptop breakpoint) ──

function initCardCollapseToggles() {
    const cards = [
        { col: '.weather-col',   key: 'engViewWeatherCollapsed' },
        { col: '.track-map-col', key: 'engViewTrackMapCollapsed' },
    ];

    for (const { col, key } of cards) {
        const colEl = document.querySelector(col);
        if (!colEl) continue;
        const card = colEl.querySelector('.card');
        const header = colEl.querySelector('.card-header');
        const body = colEl.querySelector('.card-body');
        if (!card || !header || !body) continue;

        // Create toggle button
        const btn = document.createElement('button');
        btn.className = 'btn card-collapse-toggle';
        btn.title = 'Toggle collapse';
        const icon = document.createElement('i');
        icon.classList.add('bi', 'bi-chevron-down');
        btn.appendChild(icon);
        header.appendChild(btn);

        // Restore saved state
        const saved = localStorage.getItem(key);
        if (saved === 'true') {
            body.classList.add('card-body-collapsed');
            icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
        }

        btn.addEventListener('click', () => {
            const isCollapsed = body.classList.toggle('card-body-collapsed');
            const icon = btn.querySelector('i');
            if (isCollapsed) {
                icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
            } else {
                icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
            }
            localStorage.setItem(key, isCollapsed);
        });
    }
}

// ── Upper Section Accordion ──────────────────────────────────────

function initUpperSectionAccordion() {
    const LS_KEY = 'engViewUpperSectionCollapsed';
    const header = document.getElementById('upperSectionAccordionHeader');
    const body   = document.getElementById('upperSectionAccordionBody');

    const apply = (collapsed) => {
        header.classList.toggle('collapsed', collapsed);
        body.classList.toggle('collapsed', collapsed);
    };

    const saved = localStorage.getItem(LS_KEY);
    apply(saved === 'true');

    header.addEventListener('click', () => {
        const nowCollapsed = !body.classList.contains('collapsed');
        apply(nowCollapsed);
        localStorage.setItem(LS_KEY, nowCollapsed);
    });
}

// Initialize the dashboard
function initDashboard() {
    iconCache = new IconCache();
    raceTable = new EngViewRaceTable(iconCache);
    raceStatus = new EngViewRaceStatus(iconCache);
    weatherGraph = new WeatherGraph(document.getElementById('weatherGraphContainer'));
    weatherTable = new EngViewWeatherTable(weatherGraph);
    trackMap = new TrackMap();
    initUpperSectionAccordion();
    initWeatherDisplayToggle();
    initCardCollapseToggles();
    window.drawerManager = new DrawerManager();

    const driverModal = true;
    const settingsModal = false;
    const raceStatsModal = true;
    window.modalManager = new ModalManager(driverModal, settingsModal, raceStatsModal);

    const socketio = initializeSocketIO('race-table', 'eng-view');

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
        weatherTable.update(data["weather-forecast-samples"], sessionUID);

        // Track Map: load circuit SVG (no-op if already loaded) then update driver dots
        const circuit = data["circuit"];
        const gameYear = data["f1-game-year"];
        if (circuit && gameYear) {
            trackMap.loadTrack(circuit, gameYear);
        }
        if (tableEntries && tableEntries.length > 0) {
            const effectiveSpectating = isSpectating || (raceTable.manualRefDriverIndex !== null);
            const effectiveRefIndex = raceTable.manualRefDriverIndex ?? spectatorCarIndex;
            trackMap.updateDrivers(
                tableEntries,
                effectiveSpectating,
                effectiveRefIndex,
                raceTable.refDriverTeam
            );
        }
    });

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Start the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);

// ── Drawer Manager ──────────────────────────────────────────────

class DrawerManager {
    constructor() {
        this.backdrop = document.getElementById('drawer-backdrop');
        this.columnVisibilityPane = document.getElementById('column-visibility-pane');
        this._drawerMediaQuery = window.matchMedia('(max-width: 1023px)');

        // Inline content parents (for DOM-move)
        this.weatherInlineParent = document.querySelector('.weather-col .card-body');
        this.trackMapInlineParent = document.querySelector('.track-map-col .card-body');

        // Drawer bodies
        this.weatherDrawerBody = document.getElementById('weatherDrawerBody');
        this.trackMapDrawerBody = document.getElementById('trackMapDrawerBody');

        // Build drawer map
        this.drawers = new Map();
        document.querySelectorAll('.context-drawer').forEach(container => {
            const id = container.id;
            const body = container.querySelector('.context-drawer-body');
            const toggleBtn = document.querySelector(`.drawer-toggle-btn[data-drawer="${id}"]`);
            this.drawers.set(id, { container, body, toggleBtn });
        });

        // Toggle buttons
        document.querySelectorAll('.drawer-toggle-btn').forEach(btn => {
            btn.addEventListener('click', () => this.toggleDrawer(btn.dataset.drawer));
        });

        // Close buttons inside drawers
        document.querySelectorAll('.context-drawer-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeDrawer(btn.dataset.drawer));
        });

        // Backdrop click
        this.backdrop.addEventListener('click', () => this.closeAllDrawers());

        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeAllDrawers();
        });

        // Observer: moves track map content to drawer when injected at < 1024px
        this._trackMapObserver = new MutationObserver(() => {
            if (this._drawerMediaQuery.matches && this.trackMapInlineParent.firstChild) {
                // Clear stale content (old canvas / fallback) before moving fresh content.
                // Guard: only act when inline has content — the move itself triggers
                // a second observer callback (removal from inline) which must be a no-op.
                this.trackMapDrawerBody.replaceChildren();
                while (this.trackMapInlineParent.firstChild) {
                    this.trackMapDrawerBody.appendChild(this.trackMapInlineParent.firstChild);
                }
            }
        });

        // MediaQuery listener
        this._drawerMediaQuery.addEventListener('change', () => this._onBreakpointChange());

        // Initial state
        this._onBreakpointChange();
    }

    toggleDrawer(drawerId) {
        const drawer = this.drawers.get(drawerId);
        if (!drawer) return;

        if (drawer.container.classList.contains('open')) {
            this.closeDrawer(drawerId);
            return;
        }

        // Close everything else first
        this.closeAllDrawers();

        // Close Column Visibility Pane if open
        if (this.columnVisibilityPane.classList.contains('open')) {
            this.columnVisibilityPane.classList.remove('open');
        }

        // Open this drawer
        drawer.container.classList.add('open');
        this.backdrop.classList.add('active');
        if (drawer.toggleBtn) drawer.toggleBtn.classList.add('active');
    }

    closeDrawer(drawerId) {
        const drawer = this.drawers.get(drawerId);
        if (!drawer) return;
        drawer.container.classList.remove('open');
        if (drawer.toggleBtn) drawer.toggleBtn.classList.remove('active');

        // Hide backdrop if no drawer is open
        const anyOpen = [...this.drawers.values()].some(d => d.container.classList.contains('open'));
        if (!anyOpen) this.backdrop.classList.remove('active');
    }

    closeAllDrawers() {
        for (const [, drawer] of this.drawers) {
            drawer.container.classList.remove('open');
            if (drawer.toggleBtn) drawer.toggleBtn.classList.remove('active');
        }
        this.backdrop.classList.remove('active');
    }

    _moveContentToDrawers() {
        while (this.weatherInlineParent.firstChild) {
            this.weatherDrawerBody.appendChild(this.weatherInlineParent.firstChild);
        }
        while (this.trackMapInlineParent.firstChild) {
            this.trackMapDrawerBody.appendChild(this.trackMapInlineParent.firstChild);
        }
        this._trackMapObserver.observe(this.trackMapInlineParent, { childList: true });
    }

    _moveContentToInline() {
        this._trackMapObserver.disconnect();
        while (this.weatherDrawerBody.firstChild) {
            this.weatherInlineParent.appendChild(this.weatherDrawerBody.firstChild);
        }
        while (this.trackMapDrawerBody.firstChild) {
            this.trackMapInlineParent.appendChild(this.trackMapDrawerBody.firstChild);
        }
    }

    _onBreakpointChange() {
        if (this._drawerMediaQuery.matches) {
            this._moveContentToDrawers();
        } else {
            this.closeAllDrawers();
            this._moveContentToInline();
        }
    }
}
