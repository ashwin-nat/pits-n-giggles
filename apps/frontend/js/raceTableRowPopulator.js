class RaceTableRowPopulator {
    constructor(row, rowData, packetFormat, isLiveDataMode, iconCache, raceEnded, spectatorIndex) {
        this.row = row;
        this.rowData = rowData;
        this.packetFormat = packetFormat;
        this.isLiveDataMode = isLiveDataMode;
        this.iconCache = iconCache;
        this.raceEnded = raceEnded;
        this.spectatorIndex = spectatorIndex;
    }

    populate() {
        const isTelemetryPublic = this.rowData["driver-info"]["telemetry-setting"] === "Public";

        this.addPositionInfo()
            .addNameInfo()
            .addDeltaInfo()
            .addErsInfo()
            .addWarningsPensInfo()
            .addBestLapInfo()
            .addLastLapInfo()
            .addCurrTyreInfo();

        if (isTelemetryPublic) {
            this.addTyrePredictionInfo()
                .addDamageInfo()
                .addFuelInfo();
        } else {
            this.addTelemetryRestrictedColspan();
        }
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
        ], (e) => {
            e.preventDefault();
            fetch(`/driver-info?index=${index}`)
                .then(response => {
                    if (!response.ok) throw new Error("Network response was not ok");
                    return response.json(); // or .text() if you expect plain text
                })
                .then(data => {
                    window.modalManager.openDriverModal(data, this.iconCache);
                })
                .catch(err => {
                    console.error("Fetch error:", err);
                });
        });
        return this;
    }

    addDeltaInfo() {
        if (this.isLiveDataMode) {
            return this;
        }
        const deltaInfo = this.rowData["delta-info"];
        const deltaCell = this.row.insertCell();
        if (g_pref_relativeDelta) {
            deltaCell.textContent = formatDelta(deltaInfo["delta"]);
        } else {
            deltaCell.textContent = formatDelta(deltaInfo["delta-to-leader"]);
        }
        return this;
    }

    addErsInfo() {
        const ersInfo = this.rowData["ers-info"];
        const cell = this.createMultiLineCell([
            `${ersInfo["ers-mode"].toUpperCase()}`,
            `${ersInfo["ers-percent"]}`,
        ]);
        this.addErsBar(cell, ersInfo["ers-percent-float"]);
        return this;
    }

    addWarningsPensInfo() {
        const warnsPensInfo = this.rowData["warns-pens-info"];
        const dtPlusSg = warnsPensInfo["num-dt"] + "DT + " +
            warnsPensInfo["num-sg"] + "Serv";
        this.createMultiLineCell([
            `Pens: ${warnsPensInfo["time-penalties"]} sec`,
            `Warns: ${warnsPensInfo["corner-cutting-warnings"]}`,
            dtPlusSg,
        ]);

        return this;
    }

    // Repeat similar patterns for other add functions
    addBestLapInfo() {
        const isPlayer = this.rowData["driver-info"]["is-player"];
        const lapInfo = this.rowData["lap-info"]["best-lap"];
        const index = this.rowData["driver-info"]["index"];
        const speedTrapRecord = this.rowData["lap-info"]["speed-trap-record-kmph"];
        let cell;
        const lapContent = getFormattedLapTimeStr({
            lapTimeMs: lapInfo["lap-time-ms"],
            lapTimeMsPlayer: lapInfo["lap-time-ms-player"],
            isPlayer,
            index,
            spectatorIndex: this.spectatorIndex,
            showAbsoluteFormat: g_pref_bestLapAbsoluteFormat
        });

        const speedTrapValue = speedTrapRecord != null
            ? formatSpeed(speedTrapRecord, { isMetric: g_pref_speedUnitMetric, decimalPlaces: 2, addUnitSuffix: true })
            : "---";

        // Game-specific layout:
        // - In F1 23, use a single-line cell with just the lap content
        // - in F1 24+, use a multi-line cell with lap content and speed trap info
        if (this.packetFormat == 2023) {
            cell = this.row.insertCell();
            cell.textContent = lapContent;
        } else {
            cell = this.createMultiLineCell([
                lapContent,
                speedTrapValue
            ]);
        }

        if (lapInfo["lap-time-ms"]) {
            this.addSectorInfo(cell, lapInfo["sector-status"]);
        }
        return this;
    }

    addLastLapInfo() {
        const isPlayer = this.rowData["driver-info"]["is-player"];
        const index = this.rowData["driver-info"]["index"];
        const lapInfo = this.rowData["lap-info"]["last-lap"];
        const cellContent = [];
        if (this.packetFormat > 2023) {
            // one line to pad against speed trap record
            cellContent.push(null);
        }

        const lapTimeContent = getFormattedLapTimeStr({
            lapTimeMs: lapInfo["lap-time-ms"],
            lapTimeMsPlayer: lapInfo["lap-time-ms-player"],
            isPlayer,
            index,
            spectatorIndex: this.spectatorIndex,
            showAbsoluteFormat: g_pref_lastLapAbsoluteFormat
        });
        cellContent.push(lapTimeContent);

        const cell = this.createMultiLineCell(cellContent);
        if (lapInfo["lap-time-ms"]) {
            this.addSectorInfo(cell, lapInfo["sector-status"]);
        }
        return this;
    }

    addCurrTyreInfo() {
        const tyreInfoData = this.rowData["tyre-info"];
        const currTyreWearData = tyreInfoData["current-wear"];
        let tyreWearText = "";
        if (g_pref_tyreWearAverageFormat) {
            tyreWearText = currTyreWearData
                ? formatFloat(currTyreWearData["average"]) + "%"
                : "N/A";
        } else {
            tyreWearText = currTyreWearData
                ? (() => {
                    const maxTyreWearData = getMaxTyreWear(currTyreWearData);
                    return `${maxTyreWearData["max-key"]}: ${formatFloat(maxTyreWearData["max-wear"])}%`;
                })()
                : "N/A";
        }

        const cell = this.row.insertCell();

        const firstRow = document.createElement("div");
        const icon = this.iconCache.getIcon(tyreInfoData["visual-tyre-compound"]);
        const tyreCompound = getTyreCompoundStr(tyreInfoData["visual-tyre-compound"], tyreInfoData["actual-tyre-compound"]);

        if (icon) {
            firstRow.appendChild(icon);
            firstRow.appendChild(document.createTextNode(" " + tyreWearText));
        } else {
            firstRow.textContent = `${tyreCompound} ${tyreWearText}`;
        }

        const secondRow = document.createElement("div");
        secondRow.textContent = `${tyreInfoData["tyre-age"]} lap(s) (${tyreInfoData["num-pitstops"]} pit)`;
        cell.appendChild(firstRow);
        cell.appendChild(secondRow);

        if (!this.raceEnded && this.isLiveDataMode) {
            const thirdRow = document.createElement("div");
            const rejoin = tyreInfoData["pit-rejoin-position"];
            thirdRow.textContent = `Pit rejoin: ${rejoin ? "P" + rejoin : "N/A"}`;
            cell.appendChild(thirdRow);
        }

        return this;
    }

    #getPitStopPrediction(data) {
        if (data["selected-pit-stop-lap"] > 0) {
            return data.predictions.find(
                p => p["lap-number"] === data["selected-pit-stop-lap"]
            ) || null;
        }
        return null;
    }

    #getWearPredictions(data, currentLap) {
        // If status is false or no predictions, return empty array
        if (!data.status || !data.predictions?.length) {
            return [];
        }

        const {predictions} = data;
        const lastPrediction = predictions[predictions.length - 1];

        // If selected pit stop lap is non-zero and exists in predictions
        const pitPrediction = this.#getPitStopPrediction(data);
        if (pitPrediction) {
            return [pitPrediction, lastPrediction];
        }

        // Calculate midpoint between current lap and last predicted lap
        const midLapNumber = Math.floor((currentLap + lastPrediction["lap-number"]) / 2);
        // If midpoint equals the final lap, return only the last prediction
        if (midLapNumber === lastPrediction["lap-number"]) {
            return [lastPrediction];
        }

        // Find the first prediction that is at or after the midpoint
        const midPointPrediction = predictions.find(
            pred => pred["lap-number"] >= midLapNumber
        );

        return midPointPrediction ? [midPointPrediction, lastPrediction] : [lastPrediction];
    }
    addTyrePredictionInfo() {
        const currentLap = this.rowData["lap-info"]["current-lap"];
        const predictionData = this.#getWearPredictions(this.rowData["tyre-info"]["wear-prediction"], currentLap);

        const shouldHidePredictionColumn = false;
        if (!shouldHidePredictionColumn) {
            if (predictionData.length === 0) {
                this.row.insertCell().textContent = "N/A";
            } else {
                const predictionContent = []
                predictionData.forEach((prediction, index) => {
                    const lapNum = prediction["lap-number"];
                    if (g_pref_tyreWearAverageFormat) {
                        predictionContent.push("L" + lapNum + ": " + formatFloat(prediction["average"]) + "%");
                    } else {
                        const maxWearInfo = getMaxTyreWear(prediction);
                        const maxWear = formatFloat(maxWearInfo["max-wear"]);
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
            formatFloat(damageInfo["fl-wing-damage"]) + "%";
        const frWingDamage = damageInfo["fr-wing-damage"] == null ? "N/A" :
            formatFloat(damageInfo["fr-wing-damage"]) + "%";
        const rearWingDamage = damageInfo["rear-wing-damage"] == null ? "N/A" :
            formatFloat(damageInfo["rear-wing-damage"]) + "%";
        this.createMultiLineCell([
            "FL: " + flWingDamage,
            "FR: " + frWingDamage,
            "RW: " + rearWingDamage
        ]);
        return this;
    }

    #computeFuelMetrics(fuelInfo, raceEnded) {
        if (raceEnded) {
          const currFuelRate = fuelInfo["curr-fuel-rate"] !== null
            ? formatFloat(fuelInfo["curr-fuel-rate"])
            : "N/A";
          const lastLapFuelUsed = fuelInfo["last-lap-fuel-used"] !== null
            ? formatFloat(fuelInfo["last-lap-fuel-used"])
            : "N/A";
          const remainingFuel = fuelInfo["remaining-fuel"] !== null
            ? formatFloat(fuelInfo["fuel-in-tank"])
            : "N/A";
          return [
            `Last: ${lastLapFuelUsed}`,
            `Rate: ${currFuelRate}`,
            `Rem: ${remainingFuel}`
          ];
        } else {
          const targetFuelRateAverage = fuelInfo["target-fuel-rate-average"] !== null
            ? formatFloat(fuelInfo["target-fuel-rate-average"])
            : "N/A";
          const targetFuelRateNextLap = fuelInfo["target-fuel-rate-next-lap"] !== null
            ? formatFloat(fuelInfo["target-fuel-rate-next-lap"])
            : "N/A";
          const lastLapFuelUsed = fuelInfo["last-lap-fuel-used"] !== null
            ? formatFloat(fuelInfo["last-lap-fuel-used"])
            : "N/A";
          const surplusLapsPng = fuelInfo["surplus-laps-png"] !== null
            ? formatFloat(fuelInfo["surplus-laps-png"], { signed: true })
            : "N/A";
          const surplusLapsGame = fuelInfo["surplus-laps-game"] !== null
            ? formatFloat(fuelInfo["surplus-laps-game"], { signed: true })
            : "N/A";

          const laps = g_pref_fuelSurplusLapsPng ? surplusLapsPng : surplusLapsGame;
          const tgt = g_pref_fuelTargetAverageFormat ? targetFuelRateAverage : targetFuelRateNextLap;
          return [
            `Last: ${lastLapFuelUsed}`,
            `Laps: ${laps}`,
            `Tgt: ${tgt}`
          ];
        }
    }

    addFuelInfo() {
        if (!this.isLiveDataMode) {
          return this;
        }
        const fuelInfo = this.rowData["fuel-info"];
        const shouldHideFuelColumn = false;
        if (!shouldHideFuelColumn) {
          const metrics = this.#computeFuelMetrics(fuelInfo, this.raceEnded);
          this.createMultiLineCell(metrics);
        }
        return this;
      }

    addTelemetryRestrictedColspan() {
        const cell = this.row.insertCell();
        cell.colSpan = 3;
        cell.style.textAlign = "center";
        cell.style.verticalAlign = "middle";

        const message = document.createElement("div");
        message.textContent = "Driver has telemetry set to Restricted";
        message.style.fontStyle = "italic"; // Make the text italic
        cell.appendChild(message);

        return this;
    }

    createMultiLineCell(lines, onClick = null) {
        const cell = this.row.insertCell();
        lines.forEach((line) => {
            const lineElement = document.createElement("div");

            if (line === null) {
                const lineBreak = document.createElement("br");
                lineElement.appendChild(lineBreak);
            }
            else if (line instanceof SVGElement) { // Check if the line is an SVG element
                lineElement.appendChild(line); // Directly append the SVG icon
            }
            else if (onClick) { // If onClick handler is provided
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

        // Create a container div for the sectorBar
        const sectorBar = document.createElement('div');
        sectorBar.classList.add('d-flex', 'w-100', 'p-0');
        sectorBar.style.height = `1rem`; // Set height based on font size

        // Define the color mapping for sector statuses using integers as keys
        const colorMap = {
            [-2]: 'bg-secondary', // grey
            [-1]: 'bg-danger', // Red
            [0]: 'bg-warning', // Yellow
            [1]: 'bg-success', // Green
            [2]: 'bg-purple'   // Purple
        };

        // Create individual segments for each sector and apply the appropriate color
        sectorStatus.forEach((status, index) => {
            const sectorSegment = document.createElement('div');
            sectorSegment.classList.add('flex-fill', 'sector-segment', colorMap[status]);
            if (index < sectorStatus.length - 1) {
                // Add black border to the right, except for the last segment
                sectorSegment.classList.add('border-end', 'border-dark');
            }
            sectorBar.appendChild(sectorSegment);
        });

        // Append the sector bar to the cell
        cell.appendChild(sectorBar);
    }

    addErsBar(cell, ersPerc) {
        if (ersPerc == null) return;
        if (ersPerc < 0.0 || ersPerc > 100.0) {
            console.error(`ERS percentage is out of range: ${ersPerc}`);
            return;
        }

        const levelClass = ersPerc > 15 ? 'normal' : 'low';

        const bar = document.createElement('div');
        bar.className = 'ers-bar';

        const fill = document.createElement('div');
        fill.className = `ers-bar__fill ers-bar__fill--${levelClass}`;
        fill.style.width = `${ersPerc}%`;

        bar.append(fill);
        cell.append(bar);
    }

}
