class PaceComparison {
    constructor() {
        // Initialize element references
        this.container = document.getElementById('paceComparisonWidget');
        this.prevDriver = document.getElementById('paceComparisonPrev');
        this.nextDriver = document.getElementById('paceComparisonNext');
        this.prevDelta = document.getElementById('paceComparisonPrevDelta');
        this.nextDelta = document.getElementById('paceComparisonNextDelta');

        this.playerName = document.getElementById('paceComparisonPlayerName');
        this.playerLastLapTime = document.getElementById('paceComparisonPlayerLastLapTime');
        this.playerLastS1Time  = document.getElementById('paceComparisonPlayerLastS1Time');
        this.playerLastS2Time  = document.getElementById('paceComparisonPlayerLastS2Time');
        this.playerLastS3Time  = document.getElementById('paceComparisonPlayerLastS3Time');

        this.prevSectors = [
            document.getElementById('prevSector1'),
            document.getElementById('prevSector2'),
            document.getElementById('prevSector3')
        ];
        this.nextSectors = [
            document.getElementById('nextSector1'),
            document.getElementById('nextSector2'),
            document.getElementById('nextSector3')
        ];

        this.prevBatteryLevel       = document.getElementById('prevBatteryLevel');
        this.prevDeployMode         = document.getElementById('prevDeployMode');
        this.prevDeployBar          = document.getElementById('prevDeployBar');
        this.prevHarvestBar        = document.getElementById('prevHarvestBar');

        this.nextBatteryLevel       = document.getElementById('nextBatteryLevel');
        this.nextDeployMode         = document.getElementById('nextDeployMode');
        this.nextDeployBar          = document.getElementById('nextDeployBar');
        this.nextHarvestBar        = document.getElementById('nextHarvestBar');
    }

    #formatDelta(deltaMs) {
        if (!deltaMs && deltaMs !== 0) {
          return '--.-';
        }

        const seconds = Math.abs(deltaMs) / 1000;
        return (deltaMs > 0 ? '+' : '-') + seconds.toFixed(3);
    }

    #updateElementDelta(element, delta) {
        // Remove existing color classes
        element.classList.remove('text-success', 'text-danger');

        // Add appropriate color class based on delta
        if (delta > 0) {
            element.classList.add('text-danger');
        } else if (delta < 0) {
            element.classList.add('text-success');
        }
    }

    #getDriverName(driver) {
        const name = driver['name'];
        if (name === null) {
            return '---';
        } else {
            return truncateName(driver['name']).toUpperCase();
        }
    }

    #clearPrevData() {
        this.prevDelta.textContent = '---';
        this.prevSectors.forEach(el => el.textContent = '---');
    }

    #clearNextData() {
        this.nextDelta.textContent = '---';
        this.nextSectors.forEach(el => el.textContent = '---');
    }

    #isDataAvailable(data) {
        if (data['last-ms'] !== null && data['sector-1-ms'] !== null &&
            data['sector-2-ms'] !== null && data['sector-3-ms'] !== null) {
            return true;
        } else {
            return false;
        }
    }

    #updateBatteryDisplay(batteryLevelElement, deployModeElement, deployBarElement, harvestBarElement,
        percentage, deployMode, deployPercentage, harvestPercentage) {

        // Update battery level width instead of height
        batteryLevelElement.style.width = `${percentage}%`;

        // Update deploy mode text
        deployModeElement.textContent = deployMode.toUpperCase();

        // Remove all mode classes first
        batteryLevelElement.classList.remove(
            'mode-none',
            'mode-medium',
            'mode-hotlap',
            'mode-overtake'
        );

        // Add appropriate mode class
        batteryLevelElement.classList.add(`mode-${deployMode.toLowerCase()}`);

        // Update the deploy and harvest bars
        deployBarElement.style.width = `${deployPercentage}%`;
        harvestBarElement.style.width = `${harvestPercentage}%`;
    }

    #isERSDataAvailable(ersData) {
        if (!ersData) {
            return false;
        }
        if (ersData['ers-percent'] !== null && ersData['ers-mode'] !== null) {
            return true;
        }
        return false;
    }


    /**
     * Updates the UI with new timing data
     * @param {Object} data - The timing data object containing:
     *   - player-last-lap-ms: number
     *   - prev-last-lap-ms: number
     *   - next-last-lap-ms: number
     *   - prev-driver: string
     *   - next-driver: string
     *   - player-sector-1-ms: number
     *   - player-sector-2-ms: number
     *   - player-sector-3-ms: number
     *   - prev-sector1-ms: number
     *   - prev-sector2-ms: number
     *   - prev-sector3-ms: number
     *   - next-sector1-ms: number
     *   - next-sector2-ms: number
     *   - next-sector3-ms: number
     */
    update(data, eventType) {

        // Hide this in TT mode
        if ("Time Trial" === eventType) {
            this.container.style.display = 'none';
            return;
        } else {
            this.container.style.display = '';
        }

        this.#clearPrevData();
        this.#clearNextData();

        // Fill in the names if available
        if (data['prev']['name'] !== null) {
            this.prevDriver.textContent = this.#getDriverName(data['prev']);
        }
        if (data['next']['name'] !== null) {
            this.nextDriver.textContent = this.#getDriverName(data['next']);
        }

        // Update the players last lap time
        this.playerName.textContent         = this.#getDriverName(data['player']);
        this.playerLastLapTime.textContent  = formatLapTime(data['player']['lap-ms']);
        this.playerLastS1Time.textContent   = formatSectorTime(data['player']['sector-1-ms']);
        this.playerLastS2Time.textContent   = formatSectorTime(data['player']['sector-2-ms']);
        this.playerLastS3Time.textContent   = formatSectorTime(data['player']['sector-3-ms']);

        const isPrevTimingDataAvailable = this.#isDataAvailable(data['prev']);
        const isNextTimingDataAvailable = this.#isDataAvailable(data['next']);

        if (isPrevTimingDataAvailable) {
            const prevDelta = data['player']['lap-ms'] - data['prev']['lap-ms'];
            this.prevDelta.textContent = this.#formatDelta(prevDelta);
            this.#updateElementDelta(this.prevDelta, prevDelta);
        }

        if (isNextTimingDataAvailable) {
            const nextDelta = data['player']['lap-ms'] - data['next']['lap-ms'];
            this.nextDelta.textContent = this.#formatDelta(nextDelta);
            this.#updateElementDelta(this.nextDelta, nextDelta);
        }

        // Update sector times and colors
        for (let i = 0; i < 3; i++) {
            if (isPrevTimingDataAvailable) {
                const prevSectorDelta = data['player'][`sector-${i+1}-ms`] - data['prev'][`sector-${i+1}-ms`];
                this.prevSectors[i].textContent = this.#formatDelta(prevSectorDelta);
                this.#updateElementDelta(this.prevSectors[i], prevSectorDelta);
            }
            if (isNextTimingDataAvailable) {
                const nextSectorDelta = data['player'][`sector-${i+1}-ms`] - data['next'][`sector-${i+1}-ms`];
                this.nextSectors[i].textContent = this.#formatDelta(nextSectorDelta);
                this.#updateElementDelta(this.nextSectors[i], nextSectorDelta);
            }
        }

        // Update the battery stats
        if (this.#isERSDataAvailable(data['prev']['ers'])) {
            const percentage = data['prev']['ers']['ers-percent'];
            const deployMode = data['prev']['ers']['ers-mode'];
            const deployPercentage = data['prev']['ers']['ers-deployed-this-lap'];
            const harvestPercentage = data['prev']['ers']['ers-harvested-by-mguk-this-lap'];
            this.#updateBatteryDisplay(this.prevBatteryLevel, this.prevDeployMode, this.prevDeployBar,
                this.prevHarvestBar, percentage, deployMode, deployPercentage, harvestPercentage);
        }

        if (this.#isERSDataAvailable(data['next']['ers'])) {
            const percentage = data['next']['ers']['ers-percent'];
            const deployMode = data['next']['ers']['ers-mode'];
            const deployPercentage = data['next']['ers']['ers-deployed-this-lap'];
            const harvestPercentage = data['next']['ers']['ers-harvested-by-mguk-this-lap'];
            this.#updateBatteryDisplay(this.nextBatteryLevel, this.nextDeployMode, this.nextDeployBar,
                this.nextHarvestBar, percentage, deployMode, deployPercentage, harvestPercentage);
        }
    }
}
