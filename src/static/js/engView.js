let g_engView_pitLapNum = null;

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

// Class to handle table row creation and updates
class EngViewRaceTableRow {
    constructor(driver, isSpectating, iconCache, eventType) {
        this.driver = driver;
        this.isSpectating = isSpectating;
        this.iconCache = iconCache;
        this.element = document.createElement('tr');
        if (eventType === "Time Trial") {
            this.renderTT();
        } else {
            this.render();
        }
    }

    createMultiLineCell(row1, row2) {
        return `
            <div class="eng-view-tyre-row-1">${row1}</div>
            <div class="eng-view-tyre-row-2">${row2}</div>
        `;
    }

    createLapInfoCell(row1, row2, sectorStatus) {
        const redSector     = -1;
        const greenSector   = 1;
        const purpleSector  = 2;

        let sectorClass = '';
        if (sectorStatus === greenSector) {
            sectorClass = 'green-time';
        } else if (sectorStatus === purpleSector) {
            sectorClass = 'purple-time';
        } else if (sectorStatus === redSector) {
            sectorClass = 'red-time';
        }

        // Apply 'eng-view-tyre-row-1' and conditionally add sectorClass to row1
        return `
            <div class="eng-view-tyre-row-1 ${sectorClass}">${row1}</div>
            <div class="eng-view-tyre-row-2">${row2}</div>
        `;
    }

    createPositionDrsCell(position, driverInfo) {
        let drsClass = '';
        if (driverInfo["drs-activated"]) {
            drsClass = 'drs-active';
        } else if (driverInfo["drs-available"]) {
            drsClass = 'drs-available';
        } else {
            drsClass = 'drs-not-available';
        }
        return `
            <div class="eng-view-tyre-row-1">${position}</div>
            <div class="${drsClass}">${"DRS"}</div>
        `;
    }

    createMultiLineCellOnClick(row1Content, row2Content, onClick) {
        const container = document.createElement("div");

        const row1 = document.createElement("div");
        row1.className = "eng-view-tyre-row-1";
        row1.textContent = row1Content;
        row1.addEventListener("click", onClick);

        const row2 = document.createElement("div");
        row2.className = "eng-view-tyre-row-2";
        row2.textContent = row2Content;
        row2.addEventListener("click", onClick);

        container.appendChild(row1);
        container.appendChild(row2);

        return container;
    }

    createIconTextCell(iconSvg, text) {
        return `
            <div class="eng-view-icon-row">
                <div class="eng-view-icon">${iconSvg.outerHTML}</div>
                <div class="eng-view-tyre-row-2">${text}</div>
            </div>
        `;
    }

    getDriverInfoCells() {
        const driverInfo = this.driver["driver-info"];
        return [
            {value: this.createPositionDrsCell(driverInfo["position"], driverInfo), border: true},
            {value: this.createMultiLineCellOnClick(driverInfo["name"], driverInfo["team"], () => {
                console.log("Sending driver info request", driverInfo["name"], driverInfo["index"]);
                socketio.emit('driver-info', { index: driverInfo["index"] });
            }), border: true},
        ];
    }

    getDeltaInfoCells() {

        const deltaInfo  = this.driver["delta-info"];
        const position   = this.driver["driver-info"]["position"]
        return [
            {
                value: this.createMultiLineCell(
                    (position == 1) ? ("Interval") :
                        (formatFloatWithThreeDecimalsSigned(deltaInfo["delta-to-car-in-front"]/1000)),
                    (position == 1) ? ("Leader") :
                        (formatFloatWithThreeDecimalsSigned(deltaInfo["delta-to-leader"]/1000))),
                border: true
            },
        ]
    }

    getPenaltyCells() {
        const warnsPensInfo = this.driver["warns-pens-info"];
        return [
            { value: warnsPensInfo["corner-cutting-warnings"] },
            { value: warnsPensInfo["time-penalties"] },
            { value: warnsPensInfo["num-dt"] },
            { value: warnsPensInfo["num-sg"], border: true }
        ];
    }

    getLapTimeCells() {
        const lastLapInfo = this.driver["lap-info"]["last-lap"];
        const bestLapInfo = this.driver["lap-info"]["best-lap"];
        const isPlayer = this.driver["driver-info"]["is-player"];

        // in spectator mode, there is no need for delta
        if (this.isSpectating || isPlayer) {
            return [
                // Last Lap
                { value: formatLapTime(lastLapInfo["lap-time-ms"]) },
                { value: formatSectorTime(lastLapInfo["s1-time-ms"]) },
                { value: formatSectorTime(lastLapInfo["s2-time-ms"]) },
                { value: formatSectorTime(lastLapInfo["s3-time-ms"]), border: true },
                // Best Lap
                { value: formatLapTime(bestLapInfo["lap-time-ms"]) },
                { value: formatSectorTime(bestLapInfo["s1-time-ms"]) },
                { value: formatSectorTime(bestLapInfo["s2-time-ms"]) },
                { value: formatSectorTime(bestLapInfo["s3-time-ms"]), border: true },
            ];
        }

        const yellowSector = 0;
        return [
            // Last Lap
            {
                value: this.createLapInfoCell(formatLapTime(lastLapInfo["lap-time-ms"]),
                    formatDelta(lastLapInfo["lap-time-ms-player"] - lastLapInfo["lap-time-ms"]), yellowSector),
                border: false
            },
            {
                value: this.createLapInfoCell(formatSectorTime(lastLapInfo["s1-time-ms"]),
                    formatDelta(lastLapInfo["s1-time-ms-player"] - lastLapInfo["s1-time-ms"]), lastLapInfo["sector-status"][0]),
                border: false
            },
            {
                value: this.createLapInfoCell(formatSectorTime(lastLapInfo["s2-time-ms"]),
                    formatDelta(lastLapInfo["s2-time-ms-player"] - lastLapInfo["s2-time-ms"]), lastLapInfo["sector-status"][1]),
                border: false
            },
            {
                value: this.createLapInfoCell(formatSectorTime(lastLapInfo["s3-time-ms"]),
                    formatDelta(lastLapInfo["s3-time-ms-player"] - lastLapInfo["s3-time-ms"]), lastLapInfo["sector-status"][2]),
                border: true
            },

            // Best Lap
            {
                value: this.createLapInfoCell(formatLapTime(bestLapInfo["lap-time-ms"]),
                    formatDelta(bestLapInfo["lap-time-ms-player"] - bestLapInfo["lap-time-ms"]), yellowSector),
                border: false
            },
            {
                value: this.createLapInfoCell(formatSectorTime(bestLapInfo["s1-time-ms"]),
                    formatDelta(bestLapInfo["s1-time-ms-player"] - bestLapInfo["s1-time-ms"]), bestLapInfo["sector-status"][0]),
                border: false
            },
            {
                value: this.createLapInfoCell(formatSectorTime(bestLapInfo["s2-time-ms"]),
                    formatDelta(bestLapInfo["s2-time-ms-player"] - bestLapInfo["s2-time-ms"]), bestLapInfo["sector-status"][1]),
                border: false
            },
            {
                value: this.createLapInfoCell(formatSectorTime(bestLapInfo["s3-time-ms"]),
                    formatDelta(bestLapInfo["s3-time-ms-player"] - bestLapInfo["s3-time-ms"]), bestLapInfo["sector-status"][2]),
                border: true
            },
        ];
    }

    getTyreWearCells() {
        const tyreInfoData = this.driver["tyre-info"];
        const currTyreWearInfo = tyreInfoData["current-wear"];
        const tyreIcon = this.iconCache.getIcon(tyreInfoData["visual-tyre-compound"]);
        const agePitInfoStr = `${tyreInfoData["tyre-age"]} L (${tyreInfoData["num-pitstops"]} pit)`;
        const predictionLap = g_engView_pitLapNum;
        const predictedTyreWearInfo = tyreInfoData["wear-prediction"]["predictions"].find(
            p => p["lap-number"] === predictionLap);
        return [
            { value: this.createIconTextCell(tyreIcon, agePitInfoStr)},
            { value: this.createMultiLineCell("cur", predictionLap) },
            { value: this.createMultiLineCell(formatFloatWithTwoDecimals(currTyreWearInfo["front-left-wear"]) + '%',
                (predictedTyreWearInfo) ? (formatFloatWithTwoDecimals(predictedTyreWearInfo["front-left-wear"]) + '%') : ('---')) },
            { value: this.createMultiLineCell(formatFloatWithTwoDecimals(currTyreWearInfo["front-right-wear"]) + '%',
                (predictedTyreWearInfo) ? (formatFloatWithTwoDecimals(predictedTyreWearInfo["front-right-wear"]) + '%') : ('---')) },
            { value: this.createMultiLineCell(formatFloatWithTwoDecimals(currTyreWearInfo["rear-left-wear"]) + '%',
                (predictedTyreWearInfo) ? (formatFloatWithTwoDecimals(predictedTyreWearInfo["rear-left-wear"]) + '%') : ('---')) },
            { value: this.createMultiLineCell(formatFloatWithTwoDecimals(currTyreWearInfo["rear-right-wear"]) + '%',
                (predictedTyreWearInfo) ? (formatFloatWithTwoDecimals(predictedTyreWearInfo["rear-right-wear"]) + '%') : ('---')),
                border: true },
        ];
    }

    getErsCells() {
        const ersInfo = this.driver["ers-info"];
        return [
            { value: ersInfo["ers-percent"] }, // this is already a string
            { value: formatFloatWithTwoDecimals(ersInfo["ers-deployed-this-lap"]) + '%' },
            { value: getShortERSMode(ersInfo["ers-mode"]), border: true }
        ];
    }

    getFuelCells() {
        const fuelInfo = this.driver["fuel-info"];
        return [
            { value: fuelInfo["fuel-in-tank"] == null ? "N/A" : formatFloatWithTwoDecimals(fuelInfo["fuel-in-tank"]) },
            { value: fuelInfo["curr-fuel-rate"] == null ? "N/A" : formatFloatWithTwoDecimals(fuelInfo["curr-fuel-rate"]) },
            { value: fuelInfo["curr-fuel-rate"] == null ? "N/A" : formatFloatWithTwoDecimals(fuelInfo["curr-fuel-rate"]), border: true } // TODO: fix
        ];
    }

    getDamageCells() {
        const damageInfo = this.driver["damage-info"];
        return [
            { value: damageInfo["fl-wing-damage"] + '%' },
            { value: damageInfo["fr-wing-damage"] + '%' },
            { value: damageInfo["rear-wing-damage"] + '%', border: true }
        ];
    }

    render() {
        // Add the player-row class if this is the player's row
        if (this.driver["driver-info"]["is-player"]) {
            this.element.classList.add('player-row');
        } else {
            this.element.classList.remove('player-row');
        }

        // Clear previous content
        this.element.innerHTML = "";

        const cells = [
            ...this.getDriverInfoCells(),
            ...this.getDeltaInfoCells(),
            ...this.getPenaltyCells(),
            ...this.getLapTimeCells(),
            ...this.getTyreWearCells(),
            ...this.getErsCells(),
            ...this.getFuelCells(),
            ...this.getDamageCells()
        ];

        // Iterate through cells and append them correctly
        cells.forEach(cell => {
            const td = document.createElement("td");
            if (cell.border) {
                td.classList.add("eng-view-col-border");
            }

            if (cell.value instanceof HTMLElement) {
                td.appendChild(cell.value);  // Append the element properly
            } else {
                td.innerHTML = cell.value;   // Use innerHTML for string values
            }

            this.element.appendChild(td);
        });
    }

    renderTT() {
        // Clear existing content and display a message spanning all columns
        this.element.innerHTML = `
            <td colspan="100%" class="text-center">
                Time Trial not supported in Engineer View
            </td>
        `;
    }

    update(driver) {
        this.driver = driver;
        this.render();
    }
}

// Class to manage the race table
class EngViewRaceTable {
    constructor(iconCache) {
        this.tableBody = document.getElementById('engViewRaceTableBody');
        this.rows = new Map();
        this.iconCache = iconCache;
    }

    clear() {
        this.tableBody.innerHTML = '';
        this.rows.clear();
    }

    update(drivers, isSpectating, eventType) {
        // Clear the existing table body
        this.clear();

        // Time trial not supported
        if (eventType === "Time Trial") {
            const row = new EngViewRaceTableRow(null, isSpectating, this.iconCache, eventType);
            this.rows.set(1, row);
            this.tableBody.appendChild(row.element);
        } else {
            // Repopulate the table with the new driver data
            drivers.forEach(driver => {
                const row = new EngViewRaceTableRow(driver, isSpectating, this.iconCache, eventType);
                this.rows.set(driver.position, row);
                this.tableBody.appendChild(row.element);
            });
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
        this.raceTimeElement = document.getElementById('raceTime');
        this.raceStatusElement = document.getElementById('raceStatus');
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
                g_engView_pitLapNum = value;
                console.log('Prediction lap changed to:', g_engView_pitLapNum);
            } else {
                console.warn('Invalid input: Out of range');
            }
        });

        this.predictionPitBtn.addEventListener('click', () => {
            g_engView_pitLapNum = this.pitLap;
            this.#updatePredLapInputBox();
        });

        this.predictionMidBtn.addEventListener('click', () => {
            g_engView_pitLapNum = this.midLap;
            this.#updatePredLapInputBox();
        });

        this.predictionLastBtn.addEventListener('click', () => {
            g_engView_pitLapNum = this.totalLaps;
            this.#updatePredLapInputBox();
        });

        this.predictionPitBtn.disabled = true;
        this.predictionMidBtn.disabled = true;
        this.predictionLastBtn.disabled = true;
    }

    #updatePredLapInputBox() {
        this.predictionLapInput.value = g_engView_pitLapNum;
        console.log("Updated prediction element value", g_engView_pitLapNum);
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

    update(data) {

        let shouldUpdatePred = false;
        if (data["total-laps"] != "---" && this.totalLaps != data["total-laps"]) {
            // Set the initial prediction value
            g_engView_pitLapNum = data["total-laps"];
            shouldUpdatePred = true;
            this.predictionLastBtn.disabled = false;
        }

        if (this.pitLap == null && data["player-pit-window"]) {
            // If the pit window becomes available
            g_engView_pitLapNum = data["player-pit-window"];
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
        this.raceTimeElement.textContent = formatSessionTime(data["session-duration-so-far"]);
        this.raceStatusElement.textContent = this.#getSCStatusString(data["safety-car-status"]);

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
        // Limit to first 5 entries
        const limitedData = weatherData.slice(0, 5);

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
    const settingsModal = false;
    window.modalManager = new ModalManager(driverModal, raceStatsModal, settingsModal);
}

// Start the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);

let awaitingResponse = false;
let timeoutIntervalId;
let timeoutIntervalMs = 3000;
let socketio;

socketio = io.connect('http://' + location.hostname + ':' + location.port, {
    reconnection: true,           // Enables reconnection
    reconnectionAttempts: Infinity, // Number of attempts before giving up (Infinity means never stop trying)
    reconnectionDelay: 1000,      // Initial delay before reconnection (in ms)
    reconnectionDelayMax: 5000,   // Maximum delay between reconnections (in ms)
    randomizationFactor: 0.5,     // Randomization factor to prevent reconnection storms
    timeout: 20000                // Connection timeout before giving up (in ms)
});
console.log("SocketIO initialized");

// Init tooltips
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

function clearSocketIoRequestTimeout() {
    awaitingResponse = false;
    clearInterval(timeoutIntervalId);
}

socketio.on('connect', function () {
    socketio.emit('register-client', { type: 'race-table' });
});

// Receive details from server
socketio.on('race-table-update', function (data) {

    const tableEntries  = data["table-entries"];
    const isSpectating  = data["is-spectating"];
    const eventType     = data["event-type"];
    if (tableEntries) {
        raceTable.update(tableEntries, isSpectating, eventType);
    } else if (eventType === "Time Trial") {
        raceTable.update(tableEntries, isSpectating, eventType);
    }
    raceStatus.update(data);
    weatherTable.update(data["weather-forecast-samples"]);
});

socketio.on('race-info-response', function (data) {
    clearSocketIoRequestTimeout();
    console.log("Received race-info-response", data);
    // if (!('error' in data)) {
    //     if ('__dummy' in data) {
    //         // this request is meant for a synchronous listener, ignore
    //         console.debug("Ignoring race-info-response in main listener");
    //     } else {
    //         window.modalManager.openRaceStatsModal(data);
    //     }
    // } else {
    //     console.error("Received error for race-info request", data);
    // }
});

socketio.on('driver-info-response', function (data) {
    clearSocketIoRequestTimeout();
    console.log("Received driver-info-response", data);
    if (!('error' in data)) {
        if ('__dummy' in data) {
            // this request is meant for a synchronous listener, ignore
            console.debug("Ignoring driver-info-response in main listener");
        } else {
            window.modalManager.openDriverModal(data, iconCache);
        }
    } else {
        console.error("Received error for driver-info request", data);
        // showToast("Received error for driver info request");
    }
});

socketio.on('frontend-update', function (data) {
    console.log("frontend-update", data);
    // switch (data['message-type']) {
    //     case 'custom-marker':
    //         processCustomMarkerMessage(data['message']);
    //         break;
    //     case 'tyre-delta':
    //         processTyreDeltaMessage(data['message']);
    //         break;
    //     default:
    //         console.error("received unsupported message type in frontend-update");
    // }
});

// Generic function to handle any request-response via socket events
async function sendSynchronousRequest(requestEvent, requestData, responseEvent) {
    return new Promise((resolve, reject) => {
        // Send the request event with data
        socketio.emit(requestEvent, requestData);

        // Listen for the response event
        socketio.once(responseEvent, (response) => {
            resolve(response);  // Resolve the promise with the response
        });

        // Optional: Timeout after 5 seconds (adjust as needed)
        setTimeout(() => {
            reject(new Error(`Timeout waiting for response event: ${responseEvent}`));
        }, 5000);  // 5 seconds timeout
    });
}
