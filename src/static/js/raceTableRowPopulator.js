class RaceTableRowPopulator {
    constructor(row, rowData, gameYear) {
        this.row = row;
        this.rowData = rowData;
        this.gameYear = gameYear;
    }

    populate() {
        this.addPositionInfo()
            .addNameInfo()
            // .addDeltaInfo()
            .addErsInfo()
            .addWarningsPensInfo()
            .addBestLapInfo()
            .addLastLapInfo()
            .addCurrTyreInfo()
            .addTyrePredictionInfo()
            .addDamageInfo()
            .addFuelInfo();
    }

    addPositionInfo() {
        let positionCell = this.row.insertCell();
        positionCell.textContent = this.rowData["driver-info"]["position"];
        return this;
    }

    addNameInfo() {
        const index = this.rowData["driver-info"]["index"];
        this.createMultiLineCell([
            this.rowData["driver-info"]["name"],
            getTeamName(this.rowData["driver-info"]["team"]),
        ],  (e) => {
            e.preventDefault();
            console.log("index", index);
            socketio.emit('driver-info', {index: index});
            // window.modalManager.openDriverModal({
            //     "index" : index
            // });
        });
        return this;
    }

    addDeltaInfo() {
        // TODO:
        return this;
    }

    addErsInfo() {
        const ersInfo = this.rowData["ers-info"];
        if (this.gameYear == 23) {
            row.insertCell().textContent = ersInfo["ers-percent"];
        } else {
            this.createMultiLineCell([
                `${ersInfo["ers-percent"]}`,
                `${ersInfo["ers-mode"]}`,
            ]);
        }
        return this;
    }

    addWarningsPensInfo() {
        const warnsPensInfo = this.rowData["warns-pens-info"];
        const dtPlusSg = warnsPensInfo["num-dt"] + "DT + " +
            warnsPensInfo["num-sg"] + "SG";
        this.createMultiLineCell([
            `Pens: ${warnsPensInfo["time-penalties"]} sec`,
            `Warns: ${warnsPensInfo["corner-cutting-warnings"]}`,
            dtPlusSg,
        ]);

        return this;
    }

    // Repeat similar patterns for other add functions
    addBestLapInfo() {
        const isSpectating = this.rowData["driver-info"]["is-spectating"];
        const isPlayer = this.rowData["driver-info"]["is-player"];
        const lapInfo = this.rowData["lap-info-new"]["best-lap"];
        const speedTrapRecord = this.rowData["lap-info-new"]["speed-trap-record-kmph"];
        let cell;
        if (g_pref_bestLapAbsoluteFormat || isSpectating) {
            const lapStr = formatLapTime(lapInfo["lap-time-ms"]);
            if (this.gameYear == 23) {
                cell = this.row.insertCell();
                cell.textContent = lapStr;
            } else {

                let speedTrapValue;
                if (speedTrapRecord != null) {
                    speedTrapValue = formatFloatWithTwoDecimals(speedTrapRecord) + ' kmph';
                } else {
                    speedTrapValue = "---";
                }
                cell = this.createMultiLineCell([
                    lapStr,
                    speedTrapValue,
                ]);
            }
        } else {
            const lapDeltaStr = formatLapDelta(lapInfo["lap-time-ms"],
                    lapInfo["lap-time-ms-player"], isPlayer);
            if (this.gameYear == 23) {
                cell = this.row.insertCell();
                cell.textContent = lapDeltaStr;
            } else {
                let speedTrapValue;
                if (speedTrapRecord != null) {
                    speedTrapValue = formatFloatWithTwoDecimals(speedTrapRecord) + ' kmph';
                } else {
                    speedTrapValue = "---";
                }
                cell = this.createMultiLineCell([
                    lapDeltaStr,
                    speedTrapValue,
                ]);
            }
        }
        if (lapInfo["lap-time-ms"]) {
            this.addSectorInfo(cell, lapInfo["sector-status"]);
        }
        return this;
    }

    addLastLapInfo() {
        const isSpectating = this.rowData["driver-info"]["is-spectating"];
        const isPlayer = this.rowData["driver-info"]["is-player"];
        const lapInfo = this.rowData["lap-info-new"]["last-lap"];
        let cell;
        if (g_pref_bestLapAbsoluteFormat || isSpectating) {
            const lapStr = formatLapTime(lapInfo["lap-time-ms"]);
            cell = this.row.insertCell();
            cell.textContent = lapStr;
        } else {
            const lapDeltaStr = formatLapDelta(lapInfo["lap-time-ms"],
                    lapInfo["lap-time-ms-player"], isPlayer);
            cell = this.row.insertCell();
            cell.textContent = lapDeltaStr;
        }
        if (lapInfo["lap-time-ms"]) {
            this.addSectorInfo(cell, lapInfo["sector-status"]);
        }
        return this;
    }

    addCurrTyreInfo() {
        // const tyreInfoCell = row.insertCell();
        const tyreInfoData = this.rowData["tyre-info"];
        const currTyreWearData = tyreInfoData["current-wear"];
        let tyreWearText = "";
        if (g_pref_tyreWearAverageFormat) {
            if (currTyreWearData) {
                tyreWearText = formatFloatWithTwoDecimals(currTyreWearData["average"]) + "%";
            } else {
                tyreWearText = "N/A";
            }
        } else {
            if (currTyreWearData) {
                const maxTyreWearData = getMaxTyreWear(currTyreWearData);
                tyreWearText = `${maxTyreWearData["max-key"]}: ${formatFloatWithTwoDecimals(maxTyreWearData["max-wear"])}%`
            } else {
                tyreWearText = "N/A";
            }
        }

        const tyreCompound = getTyreCompoundStr(tyreInfoData["visual-tyre-compound"], tyreInfoData["actual-tyre-compound"]);
        this.createMultiLineCell([
            tyreWearText,
            `${tyreInfoData["tyre-age"]} lap(s) ` + `(${tyreInfoData["num-pitstops"]} pit)`,
                tyreCompound,   // TODO, use icon
        ]);
        return this;
    }

    addTyrePredictionInfo() {
        const predictionData = this.rowData["tyre-info"]["wear-prediction"];
        const shouldHidePredictionColumn = false;
        if (!shouldHidePredictionColumn) {
            if (predictionData.length === 0) {
                this.row.insertCell().textContent = "N/A";
            } else {
                const predictionContent = []
                predictionData.forEach((prediction, index) => {
                    const lapNum = prediction["lap-number"];
                    if (g_pref_tyreWearAverageFormat) {
                        predictionContent.push("L" + lapNum + ": " + formatFloatWithTwoDecimals(prediction["average"]) + "%");
                    } else {
                        const maxWearInfo = getMaxTyreWear(prediction);
                        const maxWear = formatFloatWithTwoDecimals(maxWearInfo["max-wear"]);
                        const maxKey = maxWearInfo["max-key"];
                        predictionContent.push("L" + lapNum + ": " + maxKey + " - " + maxWear + "%");
                    }
                });
                this.createMultiLineCell(predictionContent);
            }
        }
        return this;
    }

    addDamageInfo() {
        const damageInfo = this.rowData["damage-info"];
        // Wing damage key will always be present
        const flWingDamage = damageInfo["fl-wing-damage"] == null ? "N/A" :
            formatFloatWithTwoDecimals(damageInfo["fl-wing-damage"]) + "%";
        const frWingDamage = damageInfo["fr-wing-damage"] == null ? "N/A" :
            formatFloatWithTwoDecimals(damageInfo["fr-wing-damage"]) + "%";
        const rearWingDamage = damageInfo["rear-wing-damage"] == null ? "N/A" :
            formatFloatWithTwoDecimals(damageInfo["rear-wing-damage"]) + "%";
        this.createMultiLineCell([
            "FL: " + flWingDamage,
            "FR: " + frWingDamage,
            "RW: " + rearWingDamage
        ]);
        return this;
    }

    addFuelInfo() {
        const fuelInfo = this.rowData["fuel-info"];
        const shouldHideFuelColumn = false;
        if (!shouldHideFuelColumn) {
            // Fuel info
            const currFuelRate = fuelInfo["curr-fuel-rate"] !== null
                ? formatFloatWithTwoDecimals(fuelInfo["curr-fuel-rate"])
                : "N/A";
            const targetFuelRate = fuelInfo["target-fuel-rate"] !== null
                ? formatFloatWithTwoDecimals(fuelInfo["target-fuel-rate"])
                : "N/A";
            const lastLapFuelUsed = fuelInfo["last-lap-fuel-used"] !== null
                ? formatFloatWithTwoDecimals(fuelInfo["last-lap-fuel-used"])
                : "N/A";

            this.createMultiLineCell([
                `Last: ${lastLapFuelUsed}`,
                `Curr: ${currFuelRate}`,
                `Tgt: ${targetFuelRate}`,
            ]);
        }
        return this;
    }

    // Utility
    createMultiLineCell(lines) {
        const cell = this.row.insertCell();
        lines.forEach((line) => {
            const lineElement = document.createElement("div");
            lineElement.textContent = line;
            cell.appendChild(lineElement);
        });
        return cell;
    }

    createMultiLineCell(lines, onClick = null) {
        const cell = this.row.insertCell();
        lines.forEach((line) => {
            const lineElement = document.createElement("div");
            if (onClick) { // If onClick handler is provided
                const link = document.createElement("a");
                link.href = "#";  // Default link to "#"
                link.textContent = line;
                link.addEventListener("click", (event) => {
                    event.preventDefault(); // Prevent the default link navigation
                    onClick(event); // Call the provided onClick function
                });
                lineElement.appendChild(link);
            } else {
                lineElement.textContent = line; // Just add the text if no onClick
            }
            cell.appendChild(lineElement);
        });
        return cell;
    }

    addSectorInfo(cell, sectorStatus) {

        // cell.classList.add('text-center');
        // Create a container div for the sectorBar
        const sectorBar = document.createElement('div');
        sectorBar.classList.add('d-flex', 'w-100', 'p-0');
        sectorBar.style.height = `1rem`; // Set height based on font size

        // Define the color mapping for sector statuses using integers as keys
        //TODO: move away from class to hex code because bg-purple doesnt
        const colorMap = {
            [-1]: 'bg-danger', // Red
            [0]: 'bg-warning', // Yellow
            [1]: 'bg-success', // Green
            [2]: 'bg-purple'   // Purple
        };

        // Create individual segments for each sector and apply the appropriate color
        sectorStatus.forEach(status => {
            const sectorSegment = document.createElement('div');
            sectorSegment.classList.add('flex-fill', 'sector-segment', colorMap[status]);
            sectorBar.appendChild(sectorSegment);
        });

        // Append the sector bar to the cell
        cell.appendChild(sectorBar);
    }

}
