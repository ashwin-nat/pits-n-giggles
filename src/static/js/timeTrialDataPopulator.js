class TimeTrialDataPopulator {
    constructor() {
        this.timeTrialTableDiv = document.getElementById('time-trial-table-div');
        this.timeTrialTable = document.getElementById('tt-lap-time-table');
        this.timeTrialTtDataDiv = document.getElementById('time-trial-tt-data-div');
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

        // This data is available only on F1 24 onwards
        if (gameYear < 24) {
            return;
        }

        ;
    }
}
