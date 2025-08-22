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

// Class to manage the race table
class EngViewRaceTable {
    constructor(iconCache) {
        this.iconCache = iconCache;
        this.table = null;
        this.spectatorIndex = null;
        this.isSpectating = false;
        this.initTable();
    }

    initTable() {
        this.table = new Tabulator("#eng-view-table", {
            layout: "fitColumns",
            placeholder: "No Data Available",
            columnHeaderSortMulti: false,
            virtualDom: false,
            index: "id",
            columns: this.getColumnDefinitions(),
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
    }

    getColumnDefinitions() {
        const disableSorting = { headerSort: false };
        return [
            { title: "Pos", field: "position", width: 40, ...disableSorting },
            {
                title: "Name",
                field: "name",
                formatter: (cell, formatterParams, onRendered) => {
                    const data = cell.getRow().getData();
                    return `${data.name}<br><span class="text-muted">${data.team}</span>`;
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
                        return `Interval<br>Leader`;
                    }
                    return `${formatFloatWithThreeDecimalsSigned(deltaToCarInFront)}<br>${formatFloatWithThreeDecimalsSigned(deltaToLeader)}`;
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
                columns: [
                    { title: "Lap", field: "lap-info.best-lap.lap-time-ms", formatter: (cell) => formatLapTime(cell.getValue()), ...disableSorting },
                    { title: "S1", field: "lap-info.best-lap.s1-time-ms", formatter: (cell) => formatSectorTime(cell.getValue()), ...disableSorting },
                    { title: "S2", field: "lap-info.best-lap.s2-time-ms", formatter: (cell) => formatSectorTime(cell.getValue()), ...disableSorting },
                    { title: "S3", field: "lap-info.best-lap.s3-time-ms", formatter: (cell) => formatSectorTime(cell.getValue()), ...disableSorting },
                ],
            },
            {
                title: 'Last Lap',
                headerSort: false,
                columns: [
                    { title: "Lap", field: "lap-info.last-lap.lap-time-ms", formatter: (cell) => formatLapTime(cell.getValue()), ...disableSorting },
                    { title: "S1", field: "lap-info.last-lap.s1-time-ms", formatter: (cell) => formatSectorTime(cell.getValue()), ...disableSorting },
                    { title: "S2", field: "lap-info.last-lap.s2-time-ms", formatter: (cell) => formatSectorTime(cell.getValue()), ...disableSorting },
                    { title: "S3", field: "lap-info.last-lap.s3-time-ms", formatter: (cell) => formatSectorTime(cell.getValue()), ...disableSorting },
                ],
            },
            {
                title: 'Tyre Wear',
                headerSort: false,
                columns: [
                    { title: "Comp", field: "tyre-info.visual-tyre-compound", formatter: (cell) => this.iconCache.getIcon(cell.getValue()).outerHTML, ...disableSorting },
                    { title: "Lap", field: "tyre-info.tyre-age", ...disableSorting },
                    { title: "FL", field: "tyre-info.current-wear.front-left-wear", formatter: (cell) => `${formatFloatWithTwoDecimals(cell.getValue())}%`, ...disableSorting },
                    { title: "FR", field: "tyre-info.current-wear.front-right-wear", formatter: (cell) => `${formatFloatWithTwoDecimals(cell.getValue())}%`, ...disableSorting },
                    { title: "RL", field: "tyre-info.current-wear.rear-left-wear", formatter: (cell) => `${formatFloatWithTwoDecimals(cell.getValue())}%`, ...disableSorting },
                    { title: "RR", field: "tyre-info.current-wear.rear-right-wear", formatter: (cell) => `${formatFloatWithTwoDecimals(cell.getValue())}%`, ...disableSorting },
                ],
            },
            {
                title: 'ERS',
                headerSort: false,
                columns: [
                    { title: "Avail", field: "ers-info.ers-percent", ...disableSorting },
                    { title: "Deploy", field: "ers-info.ers-deployed-this-lap", formatter: (cell) => `${formatFloatWithTwoDecimals(cell.getValue())}%`, ...disableSorting },
                    { title: "Mode", field: "ers-info.ers-mode", formatter: (cell) => getShortERSMode(cell.getValue()), ...disableSorting },
                ],
            },
            {
                title: 'Fuel',
                headerSort: false,
                columns: [
                    { title: "Total", field: "fuel-info.fuel-in-tank", formatter: (cell) => cell.getValue() == null ? "N/A" : formatFloatWithTwoDecimals(cell.getValue()), ...disableSorting },
                    { title: "Per Lap", field: "fuel-info.curr-fuel-rate", formatter: (cell) => cell.getValue() == null ? "N/A" : formatFloatWithTwoDecimals(cell.getValue()), ...disableSorting },
                    { title: "Est", field: "fuel-info.surplus-laps-png", formatter: (cell) => cell.getValue() == null ? "N/A" : formatFloatWithTwoDecimalsSigned(cell.getValue()), ...disableSorting },
                ],
            },
            {
                title: 'Damage',
                headerSort: false,
                columns: [
                    { title: "FL", field: "damage-info.fl-wing-damage", formatter: (cell) => `${cell.getValue()}%`, ...disableSorting },
                    { title: "FR", field: "damage-info.fr-wing-damage", formatter: (cell) => `${cell.getValue()}%`, ...disableSorting },
                    { title: "RW", field: "damage-info.rear-wing-damage", formatter: (cell) => `${cell.getValue()}%`, ...disableSorting },
                ],
            },
        ];
    }

    update(drivers, isSpectating, eventType, spectatorCarIndex) {
        this.spectatorIndex = spectatorCarIndex;
        this.isSpectating = isSpectating;

        if (eventType === "Time Trial") {
            this.table.clearData();
            this.table.placeholder = "Time Trial not supported in Engineer View";
            return;
        }

        updateReferenceLapTimes(drivers, (entry) =>
            this.isSpectating ?
            entry["driver-info"]?.["index"] == this.spectatorIndex :
            entry["driver-info"]?.["is-player"]
        );

        const tableData = drivers.map(driver => ({
            ...driver,
            id: driver['driver-info']['index'],
            position: driver['driver-info']['position'],
            name: driver['driver-info']['name'],
            team: driver['driver-info']['team'],
            isPlayer: driver['driver-info']['is-player'],
            index: driver['driver-info']['index'],
        }));

        if (tableData && tableData.length > 0) {
            const scrollPos = this.table.rowManager.element.scrollTop;
            this.table.setData(tableData).then(() => {
                this.table.rowManager.element.scrollTop = scrollPos;
            });
        }
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
    const settingsModal = false;
    window.modalManager = new ModalManager(driverModal, raceStatsModal, settingsModal);
}

// Start the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);

let awaitingResponse = false;
let timeoutIntervalId;
let timeoutIntervalMs = 3000;
let socketio;

const connectStart = Date.now();
socketio = io(`${location.protocol}//${location.hostname}:${location.port}`, {
    reconnection: true,
    reconnectionAttempts: 5,         // increased for flakier networks
    reconnectionDelay: 500,          // base delay
    reconnectionDelayMax: 3000,      // allow more time for retries
    randomizationFactor: 0.3,        // more jitter helps on bad links
    timeout: 7000,                   // wait a bit longer before timing out
    transports: ['websocket', 'polling'], // try WS, fallback to polling
    upgrade: true,
    rememberUpgrade: true,
    secure: location.protocol === 'https:', // optional: makes intent explicit
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
    console.log(`⏱️ Socket connected in ${Date.now() - connectStart}ms`);
});

socketio.on('connect_error', (err) => {
    console.warn('❌ Socket connection error:', err.message);
});

socketio.on('reconnect_attempt', attempt => {
    console.log(`🔁 Reconnection attempt ${attempt}`);
});

// Receive details from server
socketio.on('race-table-update', function (binaryData) {

    let data;
    try {
        data = window.msgpack.decode(new Uint8Array(binaryData));
    } catch (err) {
        console.error('Failed to decode race-table-update:', err);
        return;
    }

    const tableEntries      = data["table-entries"];
    const isSpectating      = data["is-spectating"];
    const eventType         = data["event-type"];
    const spectatorCarIndex = data["spectator-car-index"];
    if (tableEntries) {
        raceTable.update(tableEntries, isSpectating, eventType, spectatorCarIndex);
    } else if (eventType === "Time Trial") {
        raceTable.update(tableEntries, isSpectating, eventType, spectatorCarIndex);
    }
    raceStatus.update(data);
    weatherTable.update(data["weather-forecast-samples"]);
});
