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

// Format lap time from milliseconds to "s.ms" format
function formatLapTime(ms) {
    return (ms / 1000).toFixed(3);
}

// Format float values to 2 decimal places
function formatFloat(value) {
    return Number(value).toFixed(2);
}

// Class to handle table row creation and updates
class RaceTableRow {
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

    render() {
        const cells = [
            { value: this.driver.position, border: true },
            { value: this.driver.name, border: true },
            { value: formatLapTime(this.driver.delta), border: true },
            // Penalties
            { value: this.driver.penalties.track },
            { value: this.driver.penalties.time },
            { value: this.driver.penalties.dt },
            { value: this.driver.penalties.serv, border: true },
            // Last Lap
            { value: formatLapTime(this.driver.lastLap.total) },
            { value: formatLapTime(this.driver.lastLap.s1) },
            { value: formatLapTime(this.driver.lastLap.s2) },
            { value: formatLapTime(this.driver.lastLap.s3), border: true },
            // Best Lap
            { value: formatLapTime(this.driver.bestLap.total) },
            { value: formatLapTime(this.driver.bestLap.s1) },
            { value: formatLapTime(this.driver.bestLap.s2) },
            { value: formatLapTime(this.driver.bestLap.s3), border: true },
            // Tyre Wear
            { value: this.createTyreWearCell(this.driver.tyreWear.current.lap, this.driver.tyreWear.prediction.lap) },
            { value: this.createTyreWearCell(formatFloat(this.driver.tyreWear.current.fl) + '%', formatFloat(this.driver.tyreWear.prediction.fl) + '%') },
            { value: this.createTyreWearCell(formatFloat(this.driver.tyreWear.current.fr) + '%', formatFloat(this.driver.tyreWear.prediction.fr) + '%') },
            { value: this.createTyreWearCell(formatFloat(this.driver.tyreWear.current.rl) + '%', formatFloat(this.driver.tyreWear.prediction.rl) + '%') },
            { value: this.createTyreWearCell(formatFloat(this.driver.tyreWear.current.rr) + '%', formatFloat(this.driver.tyreWear.prediction.rr) + '%'), border: true },
            // ERS
            { value: formatFloat(this.driver.ers.available) + '%' },
            { value: formatFloat(this.driver.ers.deploy) + '%' },
            { value: this.driver.ers.mode, border: true },
            // Fuel
            { value: formatFloat(this.driver.fuel.total) + 'kg' },
            { value: formatFloat(this.driver.fuel.perLap) + 'kg' },
            { value: formatFloat(this.driver.fuel.estimate) + 'kg', border: true },
            // Damage
            { value: formatFloat(this.driver.damage.fl) + '%' },
            { value: formatFloat(this.driver.damage.fr) + '%' },
            { value: formatFloat(this.driver.damage.rw) + '%' }
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
class RaceTable {
    constructor() {
        this.tableBody = document.getElementById('raceTableBody');
        this.rows = new Map();
    }

    updateDriver(driver) {
        if (!this.rows.has(driver.position)) {
            const row = new RaceTableRow(driver);
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

// Initialize the dashboard
function initDashboard() {
    const raceTable = new RaceTable();

    // Create 22 drivers with realistic names
    const driverNames = [
        'VER', 'HAM', 'PER', 'LEC', 'SAI', 'RUS',
        'NOR', 'PIA', 'ALO', 'STR', 'GAS', 'OCO',
        'ALB', 'BOT', 'HUL', 'ZHO', 'TSU', 'MAG',
        'SAR', 'LAW', 'BEA', 'VES'
    ];

    const drivers = driverNames.map((name, index) => new Driver(index + 1, name));

    // Initial update
    drivers.forEach(driver => raceTable.updateDriver(driver));
    updateRaceStatus();

    // Simulate random updates
    setInterval(() => {
        drivers.forEach(driver => {
            // Update lap times
            const lastLapTime = Math.random() * 2000 + 80000; // 80-82s lap time
            driver.lastLap.total = lastLapTime;
            driver.lastLap.s1 = lastLapTime * 0.3;
            driver.lastLap.s2 = lastLapTime * 0.35;
            driver.lastLap.s3 = lastLapTime * 0.35;

            if (!driver.bestLap.total || lastLapTime < driver.bestLap.total) {
                driver.bestLap = { ...driver.lastLap };
            }

            driver.delta = Math.random() * 2000;
            driver.tyreWear.current.lap = 'curr';
            driver.tyreWear.prediction.lap = Math.floor(Math.random() * 20 + 30);
            driver.tyreWear.current.fl = Math.max(0, 100 - Math.random() * 50);
            driver.tyreWear.prediction.fl = Math.max(0, driver.tyreWear.current.fl - 20);
            driver.ers.available = Math.max(0, Math.min(100, driver.ers.available + (Math.random() * 2 - 1)));
            driver.fuel.total = Math.max(0, driver.fuel.total - Math.random() * 0.1);

            raceTable.updateDriver(driver);
        });

        // Occasionally update race status
        if (Math.random() < 0.05) {
            const statuses = ['Racing', 'SC', 'VSC'];
            const newStatus = statuses[Math.floor(Math.random() * statuses.length)];
            if (newStatus !== raceState.status) {
                if (newStatus === 'SC') raceState.scCount++;
                if (newStatus === 'VSC') raceState.vscCount++;
                raceState.status = newStatus;
            }
        }

        // Update lap number
        if (Math.random() < 0.1 && raceState.currentLap < raceState.totalLaps) {
            raceState.currentLap++;
        }
    }, 1000);
}

// Start the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);
