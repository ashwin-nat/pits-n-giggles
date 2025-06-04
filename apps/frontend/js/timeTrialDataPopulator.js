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

    populate(ttPacket, packetFormat) {

        if (packetFormat < 2024) {
            this.clearCells();
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
        this.totalTimeCell.textContent = '---';
        this.s1Cell.textContent = '---';
        this.s2Cell.textContent = '---';
        this.s3Cell.textContent = '---';
        this.validCell.textContent = '---';

        this.tcCell.textContent = '---';
        this.absCell.textContent = '---';
        this.gearboxCell.textContent = '---';
        this.eqPerfCell.textContent = '---';
        this.custSetupCell.textContent = '---';
    }

    populateCells(ttPacket) {

        this.totalTimeCell.textContent = ttPacket["lap-time-str"];
        this.s1Cell.textContent = ttPacket["sector-1-time-str"];
        this.s2Cell.textContent = ttPacket["sector-2-time-str"];
        this.s3Cell.textContent = ttPacket["sector-3-time-str"];
        this.validCell.textContent = (ttPacket["valid"]) ? ('✔️') : ('❌');

        this.tcCell.textContent = (ttPacket["traction-control"] != "OFF") ? ('✔️') : ('❌');
        this.absCell.textContent = (ttPacket["anti-lock-brakes"]) ? ('✔️') : ('❌');

        this.eqPerfCell.textContent = (ttPacket["equal-car-performance"]) ? ('✔️') : ('❌');
        this.custSetupCell.textContent = (ttPacket["custom-setup"]) ? ('✔️') : ('❌');

        let gearBoxStatus;
        switch (ttPacket["gearbox-assist"]) {
            case "Manual":
            case "Manual With Suggested Gear":
                gearBoxStatus = '❌';
                break;
            case "Auto":
                gearBoxStatus = '✔️';
                break;
            default:
                gearBoxStatus = '❔❕';
        }
        this.gearboxCell.textContent = (gearBoxStatus);
    }
}

class TimeTrialDataPopulator {
    constructor() {
        this.timeTrialTable                 = document.getElementById('tt-lap-time-table');

        this.playerSessionBestPopulator     = new TimeTrialTtDataPopulator('ttPlayerSessionBest');
        this.playerPersonalBestPopulator    = new TimeTrialTtDataPopulator('ttPlayerPersonalBest');
        this.rivalSessionBestPopulator      = new TimeTrialTtDataPopulator('ttRivalSessionBest');
    }

    populate(incomingData, packetFormat) {
        this.populateTimeTrialTable(incomingData["session-history"], packetFormat);
        this.populateTimeTrialTtData(incomingData["tt-data"], packetFormat);
    }

    populateTimeTrialTable(incomingData, packetFormat) {
        if (!incomingData || !incomingData["lap-history-data"]) {
            return;
        }

        const lapValidMask = 1;
        const s1ValidMask = 2;
        const s2ValidMask = 4;
        const s3ValidMask = 8;

        const bestLapTimeLapNum = incomingData["best-lap-time-lap-num"];
        const bestS1TimeLapNum  = incomingData["best-sector-1-time-lap-num"];
        const bestS2TimeLapNum  = incomingData["best-sector-2-time-lap-num"];
        const bestS3TimeLapNum  = incomingData["best-sector-3-time-lap-num"];

        // Clear existing rows except the header
        this.timeTrialTable.innerHTML = '';
        const lapHistory = incomingData["lap-history-data"];
        lapHistory.forEach((lap, index) => {
            if (lap["sector-1-time-in-ms"] === 0) {
              return;
            }

            const lapValidBitFlags = lap["lap-valid-bit-flags"];
            const lapNum = index + 1;
            const row = document.createElement('tr');

            const lapCell = document.createElement('td');
            lapCell.textContent = lapNum; // Lap number
            row.appendChild(lapCell);

            const sector1Cell = document.createElement('td');
            sector1Cell.textContent = (lap["sector-1-time-in-ms"]) ? (lap["sector-1-time-str"]) : ('---');
            this.applyColourToCell(sector1Cell, lapNum, bestS1TimeLapNum, lapValidBitFlags & s1ValidMask);
            row.appendChild(sector1Cell);

            const sector2Cell = document.createElement('td');
            sector2Cell.textContent = (lap["sector-2-time-in-ms"]) ? (lap["sector-2-time-str"]) : ('---');
            this.applyColourToCell(sector2Cell, lapNum, bestS2TimeLapNum, lapValidBitFlags & s2ValidMask);
            row.appendChild(sector2Cell);

            const sector3Cell = document.createElement('td');
            sector3Cell.textContent = (lap["sector-3-time-in-ms"]) ? (lap["sector-3-time-str"]) : ('---');
            this.applyColourToCell(sector3Cell, lapNum, bestS3TimeLapNum, lapValidBitFlags & s3ValidMask);
            row.appendChild(sector3Cell);

            const lapTimeCell = document.createElement('td');
            lapTimeCell.textContent = (lap["lap-time-in-ms"]) ? (lap["lap-time-str"]) : ('---');
            this.applyColourToCell(lapTimeCell, lapNum, bestLapTimeLapNum, lapValidBitFlags & lapValidMask);
            row.appendChild(lapTimeCell);

            const topSpeedCell = document.createElement('td');
            topSpeedCell.textContent = lap["top-speed-kmph"] || '---';
            row.appendChild(topSpeedCell);

            this.timeTrialTable.appendChild(row);
        });
    }

    populateTimeTrialTtData(ttData, packetFormat) {

        const playerPersonalBestPacket = (ttData) ? (ttData["personal-best-data-set"]) : (null);
        const playerSessionBestPacket = (ttData) ? (ttData["player-session-best-data-set"]) : (null);
        const rivalSessionBestPacket = (ttData) ? (ttData["rival-session-best-data-set"]) : (null);

        this.playerPersonalBestPopulator.populate(playerPersonalBestPacket, packetFormat);
        this.playerSessionBestPopulator.populate(playerSessionBestPacket, packetFormat);
        this.rivalSessionBestPopulator.populate(rivalSessionBestPacket, packetFormat);
    }

    applyColourToCell(cell, lapNum, pbLapNum, isValid) {
        if (pbLapNum && (lapNum === pbLapNum)) {
            // green time
            cell.classList.add("text-success");
        } else if (!isValid) {
            // red time
            cell.classList.add("text-danger");
        }
    }
}
