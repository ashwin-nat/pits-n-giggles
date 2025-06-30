class TimeTrialDataPopulator {
    constructor() {
        this.container = document.getElementById('tt-container');
        if (!this.container) {
            throw new Error('Time Trial container not found');
        }
    }

    /**
     * Main method to populate the UI with time trial data
     * @param {Object} data - The time trial data object
     */
    populate(data) {
        try {
            this.updateLapHistory(data['session-history']);
            this.updateComparisonData(data['tt-data']);
            this.updateTheoreticalBestAndSessionInfo(data['session-history']);
        } catch (error) {
            console.error('Error populating time trial data:', error);
        }
    }

    /**
     * Update lap history table
     */
    updateLapHistory(sessionHistory) {
        const tbody = document.getElementById('tt-lap-table-body');
        if (!tbody || !sessionHistory || !sessionHistory['lap-history-data']) {
            return;
        }

        const lapData = sessionHistory['lap-history-data'];
        const bestLapIndex = sessionHistory['best-lap-time-lap-num'] - 1;

        tbody.innerHTML = '';

        lapData.forEach((lap, index) => {
            const row = document.createElement('tr');
            const lapNum = index + 1;
            const isBestLap = index === bestLapIndex;
            const isValid = this.isLapValid(lap['lap-valid-bit-flags']);

            const lapCell = document.createElement('td');
            const lapStrong = document.createElement('strong');
            lapStrong.textContent = lapNum;
            lapCell.appendChild(lapStrong);

            const s1Cell = document.createElement('td');
            s1Cell.textContent = lap['sector-1-time-str'] || '--:---';
            if (!isValid) s1Cell.classList.add('tt-invalid-lap');

            const s2Cell = document.createElement('td');
            s2Cell.textContent = lap['sector-2-time-str'] || '--:---';
            if (!isValid) s2Cell.classList.add('tt-invalid-lap');

            const s3Cell = document.createElement('td');
            s3Cell.textContent = lap['sector-3-time-str'] || '--:---';
            if (!isValid) s3Cell.classList.add('tt-invalid-lap');

            const lapTimeCell = document.createElement('td');
            lapTimeCell.textContent = lap['lap-time-str'] || '--:--:---';
            if (isBestLap) lapTimeCell.classList.add('tt-best-time');
            if (!isValid) lapTimeCell.classList.add('tt-invalid-lap');

            const speedCell = document.createElement('td');
            speedCell.textContent = lap['top-speed-kmph'] || '-';
            if (!isValid) speedCell.classList.add('tt-invalid-lap');

            row.appendChild(lapCell);
            row.appendChild(s1Cell);
            row.appendChild(s2Cell);
            row.appendChild(s3Cell);
            row.appendChild(lapTimeCell);
            row.appendChild(speedCell);

            tbody.appendChild(row);
        });

        // Scroll to bottom to show latest lap
        if (tbody.parentElement) {
            tbody.parentElement.scrollTop = tbody.parentElement.scrollHeight;
        }
    }

    /**
     * Update comparison data (personal best, session best, rival best)
     */
    updateComparisonData(ttData) {
        if (!ttData) return;

        // Personal Best
        const pbData = ttData['personal-best-data-set'];
        if (pbData) {
            this.updateComparisonCard('pb', pbData);
        }

        // Session Best
        const sbData = ttData['player-session-best-data-set'];
        if (sbData) {
            this.updateComparisonCard('sb', sbData);
        }

        // Rival Best
        const rivalData = ttData['rival-session-best-data-set'];
        if (rivalData) {
            this.updateComparisonCard('rival', rivalData);
        }
    }

    /**
     * Update individual comparison card
     */
    updateComparisonCard(prefix, data) {
        const timeElement = document.getElementById(`tt-${prefix}-time`);
        const s1Element = document.getElementById(`tt-${prefix}-s1`);
        const s2Element = document.getElementById(`tt-${prefix}-s2`);
        const s3Element = document.getElementById(`tt-${prefix}-s3`);
        const tcElement = document.getElementById(`tt-${prefix}-tc`);
        const absElement = document.getElementById(`tt-${prefix}-abs`);
        const gearsElement = document.getElementById(`tt-${prefix}-gears`);
        // TODO: Populate wings data from actual data source
        // const wingsElement = document.getElementById(`tt-${prefix}-wings`);

        if (timeElement) timeElement.textContent = data['lap-time-str'] || '--:--:---';
        if (s1Element) s1Element.textContent = data['sector-1-time-str'] || '--:---';
        if (s2Element) s2Element.textContent = data['sector-2-time-str'] || '--:---';
        if (s3Element) s3Element.textContent = data['sector-3-time-str'] || '--:---';
        if (tcElement) tcElement.textContent = `TC: ${data['traction-control'] || '-'}`;
        if (absElement) absElement.textContent = `ABS: ${data['anti-lock-brakes'] ? 'ON' : 'OFF'}`;
        // TODO: Populate gears data from actual data source instead of hardcoding
        if (gearsElement) gearsElement.textContent = `Gears: AUTO`;
    }

    /**
     * Update theoretical best time and session info combined
     */
    updateTheoreticalBestAndSessionInfo(sessionHistory) {
        if (!sessionHistory || !sessionHistory['lap-history-data']) {
            return;
        }

        const lapData = sessionHistory['lap-history-data'];
        let bestS1 = null, bestS2 = null, bestS3 = null;
        let bestS1Time = Infinity, bestS2Time = Infinity, bestS3Time = Infinity;

        // Find best sector times from valid laps
        lapData.forEach(lap => {
            if (this.isLapValid(lap['lap-valid-bit-flags'])) {
                if (lap['sector-1-time-in-ms'] && lap['sector-1-time-in-ms'] < bestS1Time) {
                    bestS1Time = lap['sector-1-time-in-ms'];
                    bestS1 = lap['sector-1-time-str'];
                }
                if (lap['sector-2-time-in-ms'] && lap['sector-2-time-in-ms'] < bestS2Time) {
                    bestS2Time = lap['sector-2-time-in-ms'];
                    bestS2 = lap['sector-2-time-str'];
                }
                if (lap['sector-3-time-in-ms'] && lap['sector-3-time-in-ms'] < bestS3Time) {
                    bestS3Time = lap['sector-3-time-in-ms'];
                    bestS3 = lap['sector-3-time-str'];
                }
            }
        });

        // Calculate theoretical best time
        let theoreticalTimeMs = 0;
        let theoreticalTimeStr = '--:--:---';

        if (bestS1Time !== Infinity && bestS2Time !== Infinity && bestS3Time !== Infinity) {
            theoreticalTimeMs = bestS1Time + bestS2Time + bestS3Time;
            const minutes = Math.floor(theoreticalTimeMs / 60000);
            const seconds = Math.floor((theoreticalTimeMs % 60000) / 1000);
            const milliseconds = theoreticalTimeMs % 1000;
            theoreticalTimeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
        }

        // Update theoretical best elements
        const timeElement = document.getElementById('tt-theoretical-time');
        const s1Element = document.getElementById('tt-theoretical-s1');
        const s2Element = document.getElementById('tt-theoretical-s2');
        const s3Element = document.getElementById('tt-theoretical-s3');

        if (timeElement) timeElement.textContent = theoreticalTimeStr;
        if (s1Element) s1Element.textContent = bestS1 || '--:---';
        if (s2Element) s2Element.textContent = bestS2 || '--:---';
        if (s3Element) s3Element.textContent = bestS3 || '--:---';

        // Update session info
        const bestLapElement = document.getElementById('tt-best-lap-num');
        const bestS1Element = document.getElementById('tt-best-s1-lap');
        const bestS2Element = document.getElementById('tt-best-s2-lap');
        const bestS3Element = document.getElementById('tt-best-s3-lap');

        if (bestLapElement) {
            bestLapElement.textContent = sessionHistory['best-lap-time-lap-num'] || '-';
        }
        if (bestS1Element) {
            bestS1Element.textContent = `Lap ${sessionHistory['best-sector-1-lap-num'] || '-'}`;
        }
        if (bestS2Element) {
            bestS2Element.textContent = `Lap ${sessionHistory['best-sector-2-lap-num'] || '-'}`;
        }
        if (bestS3Element) {
            bestS3Element.textContent = `Lap ${sessionHistory['best-sector-3-lap-num'] || '-'}`;
        }
    }

    /**
     * Check if lap is valid based on bit flags
     */
    isLapValid(validBitFlags) {
        // Assuming valid lap has certain bits set
        // This is a simplified check - adjust based on your data format
        return validBitFlags && validBitFlags > 0;
    }

    /**
     * Clear all data from the UI
     */
    clear() {
        const tbody = document.getElementById('tt-lap-table-body');
        if (tbody) tbody.innerHTML = '';

        // Clear comparison data
        ['pb', 'sb', 'rival'].forEach(prefix => {
            const timeEl = document.getElementById(`tt-${prefix}-time`);
            const s1El = document.getElementById(`tt-${prefix}-s1`);
            const s2El = document.getElementById(`tt-${prefix}-s2`);
            const s3El = document.getElementById(`tt-${prefix}-s3`);
            const tcEl = document.getElementById(`tt-${prefix}-tc`);
            const absEl = document.getElementById(`tt-${prefix}-abs`);
            const gearsEl = document.getElementById(`tt-${prefix}-gears`);

            if (timeEl) timeEl.textContent = '--:--:---';
            if (s1El) s1El.textContent = '--:---';
            if (s2El) s2El.textContent = '--:---';
            if (s3El) s3El.textContent = '--:---';
            if (tcEl) tcEl.textContent = 'TC: -';
            if (absEl) absEl.textContent = 'ABS: -';
            if (gearsEl) gearsEl.textContent = 'Gears: -';
        });

        // Clear theoretical best and session info
        const theoreticalElements = [
            'tt-theoretical-time', 'tt-theoretical-s1', 'tt-theoretical-s2', 'tt-theoretical-s3'
        ];
        theoreticalElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (id === 'tt-theoretical-time') {
                    el.textContent = '--:--:---';
                } else {
                    el.textContent = '--:---';
                }
            }
        });

        const sessionInfoElements = [
            'tt-best-lap-num', 'tt-best-s1-lap', 'tt-best-s2-lap', 'tt-best-s3-lap'
        ];
        sessionInfoElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '-';
        });
    }
}
