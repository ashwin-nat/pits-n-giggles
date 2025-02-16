// Data structure for a driver
class Driver {
    constructor(position, name) {
        this.position = position;
        this.name = name;
        this.delta = '0.000';
        this.penalties = { track: 0, time: 0, dt: 0, serv: 0 };
        this.lastLap = {
            total: '0.000',
            s1: '0.000',
            s2: '0.000',
            s3: '0.000'
        };
        this.bestLap = {
            total: '0.000',
            s1: '0.000',
            s2: '0.000',
            s3: '0.000'
        };
        this.tyreWear = {
            current: { lap: 'curr', fl: 100, fr: 100, rl: 100, rr: 100 },
            prediction: { lap: 0, fl: 100, fr: 100, rl: 100, rr: 100 }
        };
        this.ers = { available: 100, deploy: 0, mode: 1 };
        this.fuel = { total: 100, perLap: 2.5, estimate: 95 };
        this.damage = { fl: 0, fr: 0, rw: 0 };
    }
}

// Global race state
const raceState = {
    currentLap: 1,
    totalLaps: 58,
    status: 'Racing',
    scCount: 0,
    vscCount: 0,
    predictionLap: 1,
    weather: [
        { time: '+10m', type: 'Clear', probability: 0 },
        { time: '+20m', type: 'Clear', probability: 10 },
        { time: '+30m', type: 'Cloudy', probability: 30 },
        { time: '+40m', type: 'Light Rain', probability: 60 },
        { time: '+50m', type: 'Rain', probability: 80 }
    ]
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

// Class to handle table row creation and updates
class EngViewRaceTableRow {
    constructor(driver) {
        this.driver = driver;
        this.element = document.createElement('tr');
        this.render();
    }

    createTyreWearCell(current, prediction) {
        return `
            <div class="eng-view-tyre-row-1">${current}</div>
            <div class="eng-view-tyre-row-2">${prediction}</div>
        `;
    }

    getDriverInfoCells() {
        const driverInfo = this.driver["driver-info"];
        const deltaInfo  = this.driver["delta-info"];

        // TODO: first row show the mode - interval/leader
        return [
            {value: driverInfo["position"], border: true},
            {value: driverInfo["name"], border: true},
            {value: formatFloatWithThreeDecimalsSigned(deltaInfo["delta-to-car-in-front"]/1000), border: true},
        ];
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

    getTyreWearCells() {
        const currTyreWearInfo = this.driver["tyre-info"]["current-wear"];
        const predictedTyreWearInfo = this.driver["tyre-info"]["current-wear"]; // TODO: fix
        console.log("currTyreWearInfo", currTyreWearInfo);
        const predictionLap = 1;
        return [
            { value: this.createTyreWearCell("cur", predictionLap) },
            { value: this.createTyreWearCell(formatFloatWithTwoDecimals(currTyreWearInfo["front-left-wear"]) + '%',
                formatFloatWithTwoDecimals(predictedTyreWearInfo["front-left-wear"]) + '%') },
            { value: this.createTyreWearCell(formatFloatWithTwoDecimals(currTyreWearInfo["front-right-wear"]) + '%',
                formatFloatWithTwoDecimals(predictedTyreWearInfo["front-right-wear"]) + '%') },
            { value: this.createTyreWearCell(formatFloatWithTwoDecimals(currTyreWearInfo["rear-left-wear"]) + '%',
                formatFloatWithTwoDecimals(predictedTyreWearInfo["rear-left-wear"]) + '%') },
            { value: this.createTyreWearCell(formatFloatWithTwoDecimals(currTyreWearInfo["rear-right-wear"]) + '%',
                formatFloatWithTwoDecimals(predictedTyreWearInfo["rear-right-wear"]) + '%'), border: true }
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
        const cells = [
            ...this.getDriverInfoCells(),
            ...this.getPenaltyCells(),
            ...this.getLapTimeCells(),
            ...this.getTyreWearCells(),
            ...this.getErsCells(),
            ...this.getFuelCells(),
            ...this.getDamageCells()
        ];

        this.element.innerHTML = cells.map(cell =>
            `<td${cell.border ? ' class="eng-view-col-border"' : ''}>${cell.value}</td>`
        ).join('');
    }

    update(driver) {
        this.driver = driver;
        this.render();
    }
}

// Class to manage the race table
class EngViewRaceTable {
    constructor() {
        this.tableBody = document.getElementById('engViewRaceTableBody');
        this.rows = new Map();
    }

    updateDriver(driver) {
        if (!this.rows.has(driver.position)) {
            const row = new EngViewRaceTableRow(driver);
            this.rows.set(driver.position, row);
            this.tableBody.appendChild(row.element);
        } else {
            this.rows.get(driver.position).update(driver);
        }
    }

    clear() {
        this.tableBody.innerHTML = '';
        this.rows.clear();
    }

    update(drivers) {
        // Clear the existing table body
        this.clear();

        // Repopulate the table with the new driver data
        drivers.forEach(driver => {
            const row = new EngViewRaceTableRow(driver);
            this.rows.set(driver.position, row);
            this.tableBody.appendChild(row.element);
        });
    }
}

function formatSessionTime(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return [hrs, mins, secs].map(v => String(v).padStart(2, '0')).join(':');
}

class EngViewRaceStatus {
    constructor() {
        this.raceTimeElement = document.getElementById('raceTime');
        this.raceStatusElement = document.getElementById('raceStatus');
        this.currentLapElement = document.getElementById('currentLap');
        this.scCountElement = document.getElementById('scCount');
        this.vscCountElement = document.getElementById('vscCount');
        this.predictionLapInput = document.getElementById('predictionLap');

        this.predictionLapInput.addEventListener('input', (e) => {
            const newValue = parseInt(e.target.value);
            if (newValue >= 1 && newValue <= raceState.totalLaps) {
                raceState.predictionLap = newValue;
                // You can add your callback function here
                console.log('Prediction lap changed to:', newValue);
            }
        });
    }

    update(data) {
        this.raceTimeElement.textContent = formatSessionTime(data["session-duration"]);
        this.raceStatusElement.textContent = data["safety-car-status"];
        this.currentLapElement.textContent = `${data["current-lap"]}/${data["total-laps"]}`;
        this.scCountElement.textContent = data["num-sc"];
        this.vscCountElement.textContent = data["num-vsc"];
    }
}

// Update race time and status
function updateRaceStatus() {
    const raceTimeElement = document.getElementById('raceTime');
    const raceStatusElement = document.getElementById('raceStatus');
    const currentLapElement = document.getElementById('currentLap');
    const scCountElement = document.getElementById('scCount');
    const vscCountElement = document.getElementById('vscCount');
    const predictionLapInput = document.getElementById('predictionLap');

    let seconds = 0;

    // Set up prediction lap input
    predictionLapInput.min = 1;
    predictionLapInput.max = raceState.totalLaps;
    predictionLapInput.value = raceState.predictionLap;

    predictionLapInput.addEventListener('input', (e) => {
        const newValue = parseInt(e.target.value);
        if (newValue >= 1 && newValue <= raceState.totalLaps) {
            raceState.predictionLap = newValue;
            // You can add your callback function here
            console.log('Prediction lap changed to:', newValue);
        }
    });

    setInterval(() => {
        seconds++;
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        raceTimeElement.textContent =
            `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        raceStatusElement.textContent = raceState.status;
        currentLapElement.textContent = `${raceState.currentLap}/${raceState.totalLaps}`;
        scCountElement.textContent = raceState.scCount;
        vscCountElement.textContent = raceState.vscCount;
    }, 1000);
}

let raceTable;
let raceStatus;
// Initialize the dashboard
function initDashboard() {
    raceTable = new EngViewRaceTable();
    raceStatus = new EngViewRaceStatus();
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

function clearSocketIoRequestTimeout() {
    awaitingResponse = false;
    clearInterval(timeoutIntervalId);
}

socketio.on('connect', function () {
    socketio.emit('register-client', { type: 'race-table' });
});

// Receive details from server
socketio.on('race-table-update', function (data) {

    const tableEntries = data["table-entries"];
    if (tableEntries) {
        raceTable.update(tableEntries);
    }
    raceStatus.update(data);
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