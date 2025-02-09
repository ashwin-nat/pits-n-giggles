class TimeTrialTtDataPopulator {
    constructor(sectionPrefix) {

        // For logging purposes
        this.sectionPrefix = sectionPrefix;

        // Init the overall div
        this.sectionDiv     = document.getElementById(`${sectionPrefix}Div`);

        // Init the first table's cells
        this.totalTimeCell  = document.getElementById(`${sectionPrefix}Total`);
        this.s1Cell         = document.getElementById(`${sectionPrefix}S1`);
        this.s2Cell         = document.getElementById(`${sectionPrefix}S2`);
        this.s3Cell         = document.getElementById(`${sectionPrefix}S3`);
        this.validCell      = document.getElementById(`${sectionPrefix}Valid`);

        // Init the second table's cells
        this.tcCell         = document.getElementById(`${sectionPrefix}TC`);
        this.absCell        = document.getElementById(`${sectionPrefix}ABS`);
        this.gearboxCell    = document.getElementById(`${sectionPrefix}Gearbox`);
        this.eqPerfCell     = document.getElementById(`${sectionPrefix}EqualPerformance`);
        this.custSetupCell  = document.getElementById(`${sectionPrefix}CustomSetup`);
    }

    populate(ttPacket, gameYear) {

        if (gameYear < 24) {
            this.showUnsupportedDiv();
            return;
        }

        if (!ttPacket) {
            this.clearCells();
            return;
        }

        this.populateCells(ttPacket);
    }

    showUnsupportedDiv() {
        // console.log("Should render unsupp div", this.sectionPrefix);
        return;
    }

    clearCells() {

        this.totalTimeCell = '---';
        this.s1Cell = '---';
        this.s2Cell = '---';
        this.s3Cell = '---';
        this.validCell = '---';

        this.tcCell = '---';
        this.absCell = '---';
        this.gearboxCell = '---';
        this.eqPerfCell = '---';
        this.custSetupCell = '---';
    }

    populateCells(ttPacket) {

        this.totalTimeCell.textContent = ttPacket["lap-time-str"];
        this.s1Cell.textContent = ttPacket["sector-1-time-str"];
        this.s2Cell.textContent = ttPacket["sector-2-time-str"];
        this.s3Cell.textContent = ttPacket["sector-3-time-str"];
        this.validCell.textContent = (ttPacket["valid"]) ? ('✔️') : ('❌');

        this.tcCell.textContent = (ttPacket["traction-control"] != "OFF") ? ('✔️') : ('❌');
        this.absCell.textContent = (ttPacket["anti-lock-brakes"]) ? ('✔️') : ('❌');
        this.gearboxCell.textContent = (ttPacket["gearbox-assist"] != "MANUAL") ? ('✔️') : ('❌');
        this.eqPerfCell.textContent = (ttPacket["equal-car-performance"]) ? ('✔️') : ('❌');
        this.custSetupCell.textContent = (ttPacket["custom-setup"]) ? ('✔️') : ('❌');
    }
}

class TimeTrialDataPopulator {
    constructor() {
        this.timeTrialTable                 = document.getElementById('tt-lap-time-table');

        this.playerSessionBestPopulator     = new TimeTrialTtDataPopulator('ttPlayerSessionBest');
        this.playerPersonalBestPopulator    = new TimeTrialTtDataPopulator('ttPlayerPersonalBest');
        this.rivalSessionBestPopulator      = new TimeTrialTtDataPopulator('ttRivalSessionBest');
    }

    populate(incomingData, gameYear) {
        this.populateTimeTrialTable(incomingData, gameYear);
        this.populateTimeTrialTtData(incomingData, gameYear);
    }

    populateTimeTrialTable(incomingData, gameYear) {
        if (!incomingData || !incomingData["lap-history"]) {
            return;
        }

        // Clear existing rows except the header
        this.timeTrialTable.innerHTML = '';
        const lapHistory = incomingData["lap-history"];
        lapHistory.forEach((lap, index) => {
            if (lap["sector-1-time-in-ms"] === 0) {
              return;
            }

            const row = document.createElement('tr');

            const lapCell = document.createElement('td');
            lapCell.textContent = index + 1; // Lap number
            row.appendChild(lapCell);

            const sector1Cell = document.createElement('td');
            sector1Cell.textContent = (lap["sector-1-time-in-ms"]) ? (lap["sector-1-time-str"]) : ('---');
            row.appendChild(sector1Cell);

            const sector2Cell = document.createElement('td');
            sector2Cell.textContent = (lap["sector-2-time-in-ms"]) ? (lap["sector-1-time-str"]) : ('---');
            row.appendChild(sector2Cell);

            const sector3Cell = document.createElement('td');
            sector3Cell.textContent = lap["sector-3-time-str"];
            sector3Cell.textContent = (lap["sector-3-time-in-ms"]) ? (lap["sector-3-time-str"]) : ('---');
            row.appendChild(sector3Cell);

            const lapTimeCell = document.createElement('td');
            lapTimeCell.textContent = (lap["lap-time-in-ms"]) ? (lap["lap-time-str"]) : ('---');
            row.appendChild(lapTimeCell);

            const topSpeedCell = document.createElement('td');
            topSpeedCell.textContent = lap["top-speed-kmph"] || '---';
            row.appendChild(topSpeedCell);

            this.timeTrialTable.appendChild(row);
        });
    }

    populateTimeTrialTtData(incomingData, gameYear) {

        const ttPacket = incomingData["tt-packet"];
        const playerPersonalBestPacket = (ttPacket) ? (ttPacket["personal-best-data-set"]) : (null);
        const playerSessionBestPacket = (ttPacket) ? (ttPacket["player-session-best-data-set"]) : (null);
        const rivalSessionBestPacket = (ttPacket) ? (ttPacket["rival-session-best-data-set"]) : (null);

        this.playerPersonalBestPopulator.populate(playerPersonalBestPacket, gameYear);
        this.playerSessionBestPopulator.populate(playerSessionBestPacket, gameYear);
        this.rivalSessionBestPopulator.populate(rivalSessionBestPacket, gameYear);
    }
}
