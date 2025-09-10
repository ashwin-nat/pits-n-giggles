class TimeTrialDataPopulator {
    constructor() {
        this.container = document.getElementById('tt-container');
        this.lastData = null;
        this.lapValidMask = 1;
        this.s1ValidMask = 2;
        this.s2ValidMask = 4;
        this.s3ValidMask = 8;
        if (!this.container) {
            throw new Error('Time Trial container not found');
        }
    }

    /**
     * Main method to populate the UI with time trial data
     * @param {Object} data - The time trial data object
     * @param {number} packetFormat - The packet format version
     */
    populate(data, packetFormat) {
        try {
            if (_.isEqual(data, this.lastData)) {
                return;
            }

            this.updateLapHistory(data['session-history']);

            // Only update comparison data if packet format is 2024 or later
            if (packetFormat >= 2024) {
                this.restoreComparisonCards();
                this.updateComparisonData(data['tt-data'], data['tt-setups']);
            } else {
                this.hideComparisonCardsForOlderFormat();
            }

            this.updateIrlPoleLap(data["irl-pole-lap"]);
            this.updateTheoreticalBestAndSessionInfo(data['session-history']);
            this.lastData = data;
        } catch (error) {
            console.error('Error populating time trial data:', error);
        }
    }

    /**
     * Restore comparison cards to their original structure for F1 2024+ format
     */
    restoreComparisonCards() {
        const cardConfigs = [
            { class: 'tt-personal-best', prefix: 'pb', title: 'Personal Best' },
            { class: 'tt-session-best', prefix: 'sb', title: 'Session Best' },
            { class: 'tt-rival-best', prefix: 'rival', title: 'Rival Best' }
        ];

        cardConfigs.forEach(config => {
            const card = document.querySelector(`.${config.class}`);
            if (card) {
                this.restoreCardStructure(card, config);
            }
        });
    }

    /**
     * Restore individual card structure
     */
    restoreCardStructure(card, config) {
        // Clear existing content
        while (card.firstChild) {
            card.removeChild(card.firstChild);
        }

        // Create header
        const cardHeader = document.createElement('div');
        cardHeader.className = 'tt-card-header';

        const headerContent = document.createElement('div');
        headerContent.className = 'tt-card-header-content';

        const title = document.createElement('h6');
        title.className = 'tt-card-title';
        title.textContent = config.title;

        const mainTime = document.createElement('div');
        mainTime.className = 'tt-main-time';
        mainTime.id = `tt-${config.prefix}-time`;
        mainTime.textContent = '--:--:---';

        headerContent.appendChild(title);
        headerContent.appendChild(mainTime);

        const wings = document.createElement('div');
        wings.className = 'tt-wings';
        wings.textContent = 'Wings: ';
        const wingsSpan = document.createElement('span');
        wingsSpan.id = `tt-${config.prefix}-wings`;
        wingsSpan.textContent = '50-50';
        wings.appendChild(wingsSpan);

        cardHeader.appendChild(headerContent);
        cardHeader.appendChild(wings);

        // Create body
        const cardBody = document.createElement('div');
        cardBody.className = 'tt-card-body';

        const sectors = document.createElement('div');
        sectors.className = 'tt-sectors';

        ['s1', 's2', 's3'].forEach(sector => {
            const sectorDiv = document.createElement('div');
            sectorDiv.className = 'tt-sector';
            sectorDiv.textContent = `${sector.toUpperCase()}: `;
            const sectorSpan = document.createElement('span');
            sectorSpan.id = `tt-${config.prefix}-${sector}`;
            sectorSpan.textContent = '--:---';
            sectorDiv.appendChild(sectorSpan);
            sectors.appendChild(sectorDiv);
        });

        const details = document.createElement('div');
        details.className = 'tt-details';

        const assists = document.createElement('div');
        assists.className = 'tt-assists';

        ['tc', 'abs', 'gears'].forEach(assist => {
            const assistSpan = document.createElement('span');
            assistSpan.className = 'tt-assist';
            assistSpan.id = `tt-${config.prefix}-${assist}`;
            assistSpan.textContent = assist === 'tc' ? 'TC: -' : assist === 'abs' ? 'ABS: -' : 'Gears: -';
            assists.appendChild(assistSpan);
        });

        details.appendChild(assists);
        cardBody.appendChild(sectors);
        cardBody.appendChild(details);

        card.appendChild(cardHeader);
        card.appendChild(cardBody);
    }

    /**
     * Hide comparison cards and show unsupported message for older formats
     */
    hideComparisonCardsForOlderFormat() {
        const cards = ['tt-personal-best', 'tt-session-best', 'tt-rival-best'];
        cards.forEach(cardClass => {
            const card = document.querySelector(`.${cardClass}`);
            if (card) {
                this.showUnsupportedMessage(card);
            }
        });
    }

    /**
     * Show unsupported message for a card
     */
    showUnsupportedMessage(card) {
        // Clear existing content
        while (card.firstChild) {
            card.removeChild(card.firstChild);
        }

        // Get the original title from the card class
        let title = 'Feature';
        if (card.classList.contains('tt-personal-best')) title = 'Personal Best';
        else if (card.classList.contains('tt-session-best')) title = 'Session Best';
        else if (card.classList.contains('tt-rival-best')) title = 'Rival Best';

        // Create header with unsupported message
        const cardHeader = document.createElement('div');
        cardHeader.className = 'tt-card-header';

        const headerContent = document.createElement('div');
        headerContent.className = 'tt-card-header-content';

        const titleElement = document.createElement('h6');
        titleElement.className = 'tt-card-title';
        titleElement.textContent = title;

        const mainTime = document.createElement('div');
        mainTime.className = 'tt-main-time';
        mainTime.style.fontSize = '14px';
        mainTime.style.color = '#888';
        mainTime.textContent = 'F1 2024+ Only';

        headerContent.appendChild(titleElement);
        headerContent.appendChild(mainTime);
        cardHeader.appendChild(headerContent);

        // Create body with message
        const cardBody = document.createElement('div');
        cardBody.className = 'tt-card-body';

        const message = document.createElement('div');
        message.style.textAlign = 'center';
        message.style.color = '#888';
        message.style.fontSize = '12px';
        message.style.padding = '10px';
        message.textContent = 'This feature requires F1 2024 or later packet format';

        cardBody.appendChild(message);
        card.appendChild(cardHeader);
        card.appendChild(cardBody);
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

        const bestLapTimeLapNum = sessionHistory["best-lap-time-lap-num"];
        const bestS1TimeLapNum  = sessionHistory["best-sector-1-lap-num"];
        const bestS2TimeLapNum  = sessionHistory["best-sector-2-lap-num"];
        const bestS3TimeLapNum  = sessionHistory["best-sector-3-lap-num"];

        lapData.forEach((lap, index) => {
            const row = document.createElement('tr');
            const lapNum = index + 1;

            const validBitFlags = lap['lap-valid-bit-flags'];
            const isLapValid = validBitFlags & this.lapValidMask;
            const isS1Valid = validBitFlags & this.s1ValidMask;
            const isS2Valid = validBitFlags & this.s2ValidMask;
            const isS3Valid = validBitFlags & this.s3ValidMask;

            const lapCell = document.createElement('td');
            const lapStrong = document.createElement('strong');
            lapStrong.textContent = lapNum;
            lapCell.appendChild(lapStrong);

            const s1Cell = document.createElement('td');
            s1Cell.textContent = (lap["sector-1-time-in-ms"]) ? (lap['sector-1-time-str']) : ('--:---');
            this.applyColourToCell(s1Cell, lapNum, bestS1TimeLapNum, isS1Valid);

            const s2Cell = document.createElement('td');
            s2Cell.textContent = (lap["sector-2-time-in-ms"]) ? (lap['sector-2-time-str']) : ('--:---');
            this.applyColourToCell(s2Cell, lapNum, bestS2TimeLapNum, isS2Valid);

            const s3Cell = document.createElement('td');
            s3Cell.textContent = (lap["sector-3-time-in-ms"]) ? (lap['sector-3-time-str']) : ('--:---');
            this.applyColourToCell(s3Cell, lapNum, bestS3TimeLapNum, isS3Valid);

            const lapTimeCell = document.createElement('td');
            lapTimeCell.textContent = (lap["lap-time-in-ms"]) ? (lap['lap-time-str']) : ('--:---');;
            this.applyColourToCell(lapTimeCell, lapNum, bestLapTimeLapNum, isLapValid);

            const speedCell = document.createElement('td');
            const topSpeed = lap['top-speed-kmph'];
            speedCell.textContent = topSpeed
                ? formatSpeed(topSpeed, {isMetric: g_pref_speedUnitMetric, decimalPlaces: 0, addUnitSuffix: false})
                : '-';

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
     * Apply color based on conditions
     */
    applyColourToCell(cell, lapNum, pbLapNum, isValid) {
        if (pbLapNum && (lapNum === pbLapNum)) {
            // green time
            cell.classList.add("tt-best-time");
        } else if (!isValid) {
            // red time
            cell.classList.add("tt-invalid-lap");
        }
    }

    /**
     * Update comparison data (personal best, session best, rival best)
     */
    updateComparisonData(ttData, ttSetups) {
        if (!ttData) return;

        // Personal Best
        const pbData = ttData['personal-best-data-set'];
        const pbSetup = ttSetups['personal-best-setup'];
        if (pbData) {
            this.updateComparisonCard('pb', pbData, pbSetup);
        }

        // Session Best
        const sbData = ttData['player-session-best-data-set'];
        const sbSetup = ttSetups['player-session-best-setup'];
        if (sbData) {
            this.updateComparisonCard('sb', sbData, sbSetup);
        }

        // Rival Best
        const rivalData = ttData['rival-session-best-data-set'];
        const rivalSetup = ttSetups['rival-session-best-setup'];
        if (rivalData) {
            this.updateComparisonCard('rival', rivalData, rivalSetup);
        }
    }

    /**
     * Update individual comparison card
     */
    updateComparisonCard(prefix, data, setup) {
        const timeElement = document.getElementById(`tt-${prefix}-time`);
        const s1Element = document.getElementById(`tt-${prefix}-s1`);
        const s2Element = document.getElementById(`tt-${prefix}-s2`);
        const s3Element = document.getElementById(`tt-${prefix}-s3`);
        const tcElement = document.getElementById(`tt-${prefix}-tc`);
        const absElement = document.getElementById(`tt-${prefix}-abs`);
        const gearsElement = document.getElementById(`tt-${prefix}-gears`);

        if (timeElement) timeElement.textContent = data['lap-time-str'] || '--:--:---';
        if (s1Element) s1Element.textContent = data['sector-1-time-str'] || '--:---';
        if (s2Element) s2Element.textContent = data['sector-2-time-str'] || '--:---';
        if (s3Element) s3Element.textContent = data['sector-3-time-str'] || '--:---';
        if (tcElement) tcElement.textContent = `TC: ${this.getAssistText(data['traction-control'])}`;
        if (absElement) absElement.textContent = `ABS: ${this.getAssistText(data['anti-lock-brakes'])}`;
        if (gearsElement) gearsElement.textContent = `Gears: ${this.getAssistText(data['gearbox-assist'])}`;

        const wingsElement = document.getElementById(`tt-${prefix}-wings`);
        if (wingsElement && setup && setup['is-valid'] && data['is-valid']) {
            const frontWing = setup['front-wing'];
            const rearWing = setup['rear-wing'];
            wingsElement.textContent = `${frontWing} - ${rearWing}`;
        } else {
            wingsElement.textContent = '-';
        }
    }

    /**
     * Update IRL Pole Lap card
     */
    updateIrlPoleLap(irlPoleLapData) {
        const titleElement = document.getElementById('tt-irl-title');
        const timeElement = document.getElementById('tt-irl-time');
        const s1Element = document.getElementById('tt-irl-s1');
        const s2Element = document.getElementById('tt-irl-s2');
        const s3Element = document.getElementById('tt-irl-s3');

        if (irlPoleLapData) {
            const lapTimeStr = this.formatMillisecondsToLapTime(irlPoleLapData['lap-ms']);
            const s1Str = this.formatMillisecondsToSectorTime(irlPoleLapData['s1-ms']);
            const s2Str = this.formatMillisecondsToSectorTime(irlPoleLapData['s2-ms']);
            const s3Str = this.formatMillisecondsToSectorTime(irlPoleLapData['s3-ms']);

            if (titleElement) titleElement.textContent = `${irlPoleLapData['driver-name']} - ${irlPoleLapData['year']}`;
            if (timeElement) timeElement.textContent = lapTimeStr;
            if (s1Element) s1Element.textContent = s1Str;
            if (s2Element) s2Element.textContent = s2Str;
            if (s3Element) s3Element.textContent = s3Str;
        } else {
            if (titleElement) titleElement.textContent = 'IRL Pole Lap';
            if (timeElement) timeElement.textContent = '--:--:---';
            if (s1Element) s1Element.textContent = '--:---';
            if (s2Element) s2Element.textContent = '--:---';
            if (s3Element) s3Element.textContent = '--:---';
        }
    }

    formatMillisecondsToLapTime(ms) {
        if (!ms) return '--:--:---';
        const minutes = Math.floor(ms / 60000);
        const seconds = Math.floor((ms % 60000) / 1000);
        const milliseconds = ms % 1000;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
    }

    formatMillisecondsToSectorTime(ms) {
        if (!ms) return '--:---';
        const seconds = Math.floor(ms / 1000);
        const milliseconds = ms % 1000;
        return `${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
    }

    getAssistText(assistValue) {
        return assistValue ? '✅' : '❌';
    }

    /**
     * Clears the IRL Pole Lap data from the UI.
     */
    clearIrlPoleLapData() {
        const irlTitleEl = document.getElementById('tt-irl-title');
        const irlTimeEl = document.getElementById('tt-irl-time');
        const irlS1El = document.getElementById('tt-irl-s1');
        const irlS2El = document.getElementById('tt-irl-s2');
        const irlS3El = document.getElementById('tt-irl-s3');
        const irlDetailsAssistsEl = document.getElementById('tt-irl-details-assists');

        if (irlTitleEl) irlTitleEl.textContent = 'IRL Pole Lap';
        if (irlTimeEl) irlTimeEl.textContent = '--:--:---';
        if (irlS1El) irlS1El.textContent = '--:---';
        if (irlS2El) irlS2El.textContent = '--:---';
        if (irlS3El) irlS3El.textContent = '--:---';
        if (irlDetailsAssistsEl) irlDetailsAssistsEl.innerHTML = '';
    }

    /**
     * Update theoretical best time and session info combined
     */
    updateTheoreticalBestAndSessionInfo(sessionHistory) {
        if (!sessionHistory || !sessionHistory['lap-history-data']) {
            return;
        }

        const lapData = sessionHistory['lap-history-data'];
        const s1TimeMs = this.getBestValidSectorTime(lapData, 1, this.s1ValidMask);
        const s2TimeMs = this.getBestValidSectorTime(lapData, 2, this.s2ValidMask);
        const s3TimeMs = this.getBestValidSectorTime(lapData, 3, this.s3ValidMask);
        const theoreticalTimeMs = this.getTheoreticalBestLap(s1TimeMs, s2TimeMs, s3TimeMs);

        // Update theoretical best elements
        const timeElement = document.getElementById('tt-theoretical-time');
        const s1Element = document.getElementById('tt-theoretical-s1');
        const s2Element = document.getElementById('tt-theoretical-s2');
        const s3Element = document.getElementById('tt-theoretical-s3');

        if (timeElement) timeElement.textContent = (theoreticalTimeMs != null) ? (this.formatMillisecondsToLapTime(theoreticalTimeMs)) : ('--:--:---');
        if (s1Element) s1Element.textContent = (s1TimeMs != null) ? (this.formatMillisecondsToSectorTime(s1TimeMs)) : ('--:---');
        if (s2Element) s2Element.textContent = (s2TimeMs != null) ? (this.formatMillisecondsToSectorTime(s2TimeMs)) : ('--:---');
        if (s3Element) s3Element.textContent = (s3TimeMs != null) ? (this.formatMillisecondsToSectorTime(s3TimeMs)) : ('--:---');
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
            const wingsEl = document.getElementById(`tt-${prefix}-wings`);

            if (timeEl) timeEl.textContent = '--:--:---';
            if (s1El) s1El.textContent = '--:---';
            if (s2El) s2El.textContent = '--:---';
            if (s3El) s3El.textContent = '--:---';
            if (tcEl) tcEl.textContent = 'TC: -';
            if (absEl) absEl.textContent = 'ABS: -';
            if (gearsEl) gearsEl.textContent = 'Gears: -';
            if (wingsEl) wingsEl.textContent = '-';
        });

        // Clear IRL Pole Lap data
        this.clearIrlPoleLapData();

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
    }

    /**
     * Finds the best valid sector time across all laps.
     *
     * @param {Array<Object>} laps - List of lap time objects.
     * @param {number} sectorNum - The sector number
     * @param {number} mask - Bitmask to check validity (e.g. s1ValidMask).
     * @returns {number|null} Best valid time in ms, or null if none valid.
     */
    getBestValidSectorTime(laps, sectorNum, mask) {
        let bestTime = null;
        const sectorMinutesKey = `sector-${sectorNum}-time-minutes`;
        const sectorMsKey = `sector-${sectorNum}-time-in-ms`;

        for (const lap of laps) {
            if ((lap["lap-valid-bit-flags"] & mask) !== 0) {
                const minutes = lap[sectorMinutesKey] ?? 0;
                const ms = lap[sectorMsKey] ?? 0;
                const totalMs = minutes * 60000 + ms;
                if (totalMs === 0) continue;

                if (bestTime === null || totalMs < bestTime) {
                    bestTime = totalMs;
                }
            }
        }

        return bestTime;
    }

    /**
     * Computes the theoretical best lap using best valid sector times.
     *
     * @param {number|null} bestS1Ms - Best sector 1 time in ms.
     * @param {number|null} bestS2Ms - Best sector 2 time in ms.
     * @param {number|null} bestS3Ms - Best sector 3 time in ms.
     * @returns {number|null} Best lap time in ms, or null if incomplete.
     */
    getTheoreticalBestLap(bestS1Ms, bestS2Ms, bestS3Ms) {
        if (bestS1Ms === null || bestS2Ms === null || bestS3Ms === null) {
            return null; // not all sectors available
        }

        return bestS1Ms + bestS2Ms + bestS3Ms;
    }

}
