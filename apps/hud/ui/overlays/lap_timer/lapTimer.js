class LapTimer {
    constructor() {
        this.lastLapEl = document.getElementById('lastLap');
        this.bestLapEl = document.getElementById('bestLap');
        this.currentLapEl = document.getElementById('currentLap');
        this.sector1El = document.getElementById('sector1');
        this.sector2El = document.getElementById('sector2');
        this.sector3El = document.getElementById('sector3');

        this.currSessionUID = null;
        this.currLapNum = null;
        this.isDisplayingCompletedLap = false;
    }

    update(data) {
        const refRow = getRefRow(data);

        if (!refRow) {
            this.#clear();
            return;
        }

        if (this.currSessionUID != data["session-uid"]) {
            this.#clear();
        }
        this.currSessionUID = data["session-uid"];

        const lapInfo = refRow["lap-info"];
        this.updateLastLap(lapInfo["last-lap"]["lap-time-ms"]);
        this.updateBestLap(lapInfo["best-lap"]["lap-time-ms"]);

        const currLap = lapInfo["curr-lap"];
        this.updateCurrLap(currLap["lap-time-ms"]);

        if (this.currLapNum != lapInfo["current-lap"]) {
            // completed a lap
            this.isDisplayingCompletedLap = true;

            // display completed lap first
            this.updateSectorStatus(lapInfo["last-lap"]["sector-status"]);
            this.updateCurrLap(lapInfo["last-lap"]["lap-time-ms"]);

            setTimeout(() => {
                // display new lap after 5s
                this.isDisplayingCompletedLap = false;
                this.updateSectorStatus(currLap["sector-status"]);
                this.updateCurrLap(currLap["lap-time-ms"]);
            }, 5000);

            console.log("LapTimer: completed lap, displaying completed lap sector status for 5s");
        } else {
            if (!this.isDisplayingCompletedLap) {
                this.updateSectorStatus(currLap["sector-status"]);
                this.updateCurrLap(currLap["lap-time-ms"]);
            } else {
                console.log("LapTimer: still displaying completed lap sector status");
            }
        }

        this.currLapNum = lapInfo["current-lap"];
    }

    updateLastLap(timeMs) {
        this.lastLapEl.textContent = formatLapTime(timeMs);
    }

    updateBestLap(timeMs) {
        this.bestLapEl.textContent = formatLapTime(timeMs);
    }

    updateCurrLap(timeMs) {
        this.currentLapEl.textContent = formatLapTime(timeMs);
        requestAnimationFrame(() => this.updateCurrLap(timeMs));
    }

    updateSectorStatus(sectorStatus) {

        this.#updateSectorStatusHelper(this.sector1El, sectorStatus[0]);
        this.#updateSectorStatusHelper(this.sector2El, sectorStatus[1]);
        this.#updateSectorStatusHelper(this.sector3El, sectorStatus[2]);
    }

    #updateSectorStatusHelper(sectorElement, status) {

        sectorElement.classList.remove('purple', 'green', 'yellow', 'red', 'grey');
        const classMap = {
            [-2]: 'grey',
            [-1]: 'red',
            [0]: 'yellow',
            [1]: 'green',
            [2]: 'purple',
        };
        sectorElement.classList.add(classMap[status]);
    }

    #clear() {
        // this.lastLapEl.textContent = '--:--.---';
        // this.bestLapEl.textContent = '--:--.---';
        // this.currentLapEl.textContent = '--:--.---';
        // this.sector1El.className = '';
        // this.sector2El.className = '';
        // this.sector3El.className = '';

        this.currLapNum = null;
        this.currSessionUID = null;
    }
}

const timer = new LapTimer();

// Listen for updates from Python
window.addEventListener('telemetry-update', (event) => {
    timer.update(event.detail);
});

// Wait for utils to be ready before trying to use them
window.addEventListener('utils-ready', async () => {
    console.log('[LapTimer] Utils ready, fetching initial telemetry...');
    test_import(); // TODO: remove

    // Now safe to use utils functions
    try {
        const data = await pywebview.api.get_data();
        timer.update(data);
    } catch (error) {
        console.error('Error getting initial telemetry:', error);
    }
});
