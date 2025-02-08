class DriverModalPopulator {
    constructor(data, iconCache) {
        this.data = data;
        this.tableClassNames = 'table table-bordered table-striped table-dark table-sm align-middle';
        this.iconCache = iconCache;
    }

    populateLapTimesTab(tabPane) {
        const lapTimeHistory = this.data["lap-time-history"];
        const lapHistoryData = lapTimeHistory["lap-history-data"];

        const leftPanePopulator = (leftDiv) => {

            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            const headers = ['Lap', 'S1', 'S2', 'S3', 'Time', 'Tyre', 'Wear'];

            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table body
            const tbody = document.createElement('tbody');

            lapHistoryData.forEach((lap, index) => {
                const row = document.createElement('tr');

                const lapCell = document.createElement('td');
                lapCell.textContent = index + 1; // Lap number
                row.appendChild(lapCell);

                const sector1Cell = document.createElement('td');
                sector1Cell.textContent = lap["sector-1-time-str"];
                row.appendChild(sector1Cell);

                const sector2Cell = document.createElement('td');
                sector2Cell.textContent = lap["sector-2-time-str"];
                row.appendChild(sector2Cell);

                const sector3Cell = document.createElement('td');
                sector3Cell.textContent = lap["sector-3-time-str"];
                row.appendChild(sector3Cell);

                const lapTimeCell = document.createElement('td');
                lapTimeCell.textContent = lap["lap-time-str"];
                row.appendChild(lapTimeCell);

                const tyreCell = document.createElement('td');
                const compound = lap["tyre-set-info"]["tyre-set"]["visual-tyre-compound"];
                const svgElement = this.iconCache.getIcon(compound);
                if (svgElement) {
                    tyreCell.appendChild(svgElement);
                } else {
                    tyreCell.textContent = compound;
                }
                row.appendChild(tyreCell);

                const wearCell = document.createElement('td');
                wearCell.textContent = lap["tyre-set-info"]["tyre-wear"]["average"].toFixed(2) + '%';
                row.appendChild(wearCell);

                tbody.appendChild(row);
            });

            table.appendChild(tbody);
            leftDiv.appendChild(table);
        };

        const rightPanePopulator = (rightDiv) => {
            // Prepare data for the graph
            // const sector1Data = lapHistoryData.map((lap, index) => ({
            //     x: index + 1, // Lap number (index + 1)
            //     y: lap["sector-1-time-in-ms"] // Time in milliseconds
            // }));
            // const sector2Data = lapHistoryData.map((lap, index) => ({
            //     x: index + 1, // Lap number (index + 1)
            //     y: lap["sector-2-time-in-ms"] // Time in milliseconds
            // }));
            // const sector3Data = lapHistoryData.map((lap, index) => ({
            //     x: index + 1, // Lap number (index + 1)
            //     y: lap["sector-3-time-in-ms"] // Time in milliseconds
            // }));
            // const totalTimeData = lapHistoryData.map((lap, index) => ({
            //     x: index + 1, // Lap number (index + 1)
            //     y: lap["lap-time-in-ms"] // Total lap time in milliseconds
            // }));

            const sector1Data = lapHistoryData
                .filter(lap => lap["sector-1-time-in-ms"] > 0)
                .map((lap, index) => ({
                    x: index + 1,
                    y: lap["sector-1-time-in-ms"]
                }));

            const sector2Data = lapHistoryData
                .filter(lap => lap["sector-2-time-in-ms"] > 0)
                .map((lap, index) => ({
                    x: index + 1,
                    y: lap["sector-2-time-in-ms"]
                }));

            const sector3Data = lapHistoryData
                .filter(lap => lap["sector-3-time-in-ms"] > 0)
                .map((lap, index) => ({
                    x: index + 1,
                    y: lap["sector-3-time-in-ms"]
                }));

            const totalTimeData = lapHistoryData
                .filter(lap => lap["lap-time-in-ms"] > 0)
                .map((lap, index) => ({
                    x: index + 1,
                    y: lap["lap-time-in-ms"]
                }));

            const datasets = [
                {
                    label: "S1",
                    data: sector1Data,
                    borderColor: 'red',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    fill: false
                },
                {
                    label: "S2",
                    data: sector2Data,
                    borderColor: 'blue',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: false
                },
                {
                    label: "S3",
                    data: sector3Data,
                    borderColor: 'cyan',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    fill: false
                },
                {
                    label: "Lap",
                    data: totalTimeData,
                    borderColor: 'purple',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    fill: false
                }
            ];

            // Pass the graph data to plotGraph function
            const canvas = document.createElement('canvas');

            rightDiv.appendChild(canvas);
            rightDiv.classList.add('chart-container');
            plotGraph(canvas, datasets, 'Lap', 'Lap Time (ms)', true);
        };

        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
    }

    populateFuelUsageTab(tabPane) {
        const fuelUsagePerLap = [];

        const leftPanePopulator = (leftDiv) => {
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            const headers = ['Lap', 'Fuel Load (kg)', 'Usage Per Lap (kg)', 'Excess Laps', 'Excess Laps Delta'];

            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table body
            const tbody = document.createElement('tbody');

            let previousFuelLoad = null;
            let previousExcessLaps = null;

            const fuelUsageData = this.data["per-lap-info"];
            fuelUsageData.forEach((lapData, index) => {
                const row = document.createElement('tr');

                const lapCell = document.createElement('td');
                lapCell.textContent = lapData["lap-number"]; // Lap number
                row.appendChild(lapCell);

                const fuelLoadCell = document.createElement('td');
                fuelLoadCell.textContent = lapData["car-status-data"]["fuel-in-tank"].toFixed(2); // Fuel load (kg)
                row.appendChild(fuelLoadCell);

                const usagePerLapCell = document.createElement('td');
                if (previousFuelLoad !== null) {
                    const usagePerLap = previousFuelLoad - lapData["car-status-data"]["fuel-in-tank"];
                    usagePerLapCell.textContent = usagePerLap.toFixed(2); // Usage per lap (kg)
                    fuelUsagePerLap.push({
                        x: lapData["lap-number"],
                        y: usagePerLap
                    });
                } else {
                    usagePerLapCell.textContent = '-'; // First lap, no previous value to calculate
                }
                row.appendChild(usagePerLapCell);

                const excessLapsCell = document.createElement('td');
                const excessLaps = lapData["car-status-data"]["fuel-remaining-laps"];
                excessLapsCell.textContent = excessLaps.toFixed(2); // Excess laps
                row.appendChild(excessLapsCell);

                const excessLapsDeltaCell = document.createElement('td');
                if (previousExcessLaps !== null) {
                    const excessLapsDelta = excessLaps - previousExcessLaps;
                    excessLapsDeltaCell.textContent = excessLapsDelta.toFixed(2); // Excess laps delta
                } else {
                    excessLapsDeltaCell.textContent = '-'; // First lap, no previous value to calculate
                }
                row.appendChild(excessLapsDeltaCell);

                tbody.appendChild(row);

                // Update previous values for next iteration
                previousFuelLoad = lapData["car-status-data"]["fuel-in-tank"];
                previousExcessLaps = excessLaps;
            });

            table.appendChild(tbody);
            leftDiv.appendChild(table);
        };

        const rightPanePopulator = (rightDiv) => {
            const datasets = [
                {
                    label: "Fuel Usage",
                    data: fuelUsagePerLap,
                    borderColor: 'red',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    fill: false
                }
            ];

            // Pass the graph data to plotGraph function
            const canvas = document.createElement('canvas');

            rightDiv.appendChild(canvas);
            rightDiv.classList.add('chart-container');
            plotGraph(canvas, datasets, 'Lap', 'Fuel used (kg)');
        };

        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
    }

    populateTyreStintHistoryTab(tabPane) {

        const graphDataFL = [];
        const graphDataFR = [];
        const graphDataRL = [];
        const graphDataRR = [];
        const leftPanePopulator = (leftDiv) => {
            const tyreSetsHistoryData = this.data["tyre-set-history"];
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            const headers = [
                'Stint',
                'Start Lap',
                'End Lap',
                'Length',
                'Tyre',
                'Tyre Wear',
                'Tyre Wear/Lap',
            ];

            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table body and populate
            const tbody = document.createElement('tbody');
            if (tyreSetsHistoryData.length > 0) {
                let count = 0;
                tyreSetsHistoryData.forEach((stintData, index) => {

                    const stintStartLap = stintData["start-lap"];
                    const stintEndLap = stintData["end-lap"];
                    const stintLength = `${stintData["stint-length"]} lap(s)`;

                    // backward compatibility for files saved with invalid first stint history record bug
                    if ((stintData["stint-length"] == 0) || (stintData["start-lap"] < "stint-history"["end-lap"])) {
                        console.debug("Skipping row with invalid data", stintData, index);
                        return;
                    }

                    const row = tbody.insertRow();
                    const stintId = count + 1;

                    let compound = "---";
                    let tyreWear = "---";
                    let tyreWearPerLap = "---";
                    let icon;

                    if ("tyre-set-data" in stintData && stintData["tyre-set-data"] != null) {
                        const tyreSetData = stintData["tyre-set-data"];
                        const tyreSetIndex = stintData["fitted-index"];

                        const actualCompound = tyreSetData["actual-tyre-compound"];
                        const tyreSetId = `${actualCompound} - ${tyreSetIndex}`;
                        icon = this.iconCache.getIcon(tyreSetData["visual-tyre-compound"]);
                        compound = tyreSetData["visual-tyre-compound"] + " (" + tyreSetId + ")";
                        tyreWear = `${formatFloatWithTwoDecimals(tyreSetData["wear"])}%`;

                        // Use parseFloat to ensure numerical calculation
                        const wearPerLap = parseFloat(tyreSetData["wear"]) / parseFloat(stintData["stint-length"]);
                        tyreWearPerLap = formatFloatWithTwoDecimals(wearPerLap) + "%";
                    }

                    // Populate table
                    this.populateTableRow(row, [
                        stintId,
                        stintStartLap,
                        stintEndLap,
                        stintLength,
                        icon || compound,
                        tyreWear,
                        tyreWearPerLap,
                    ]);

                    // Populate graph data set
                    if ("tyre-wear-history" in stintData && stintData["tyre-wear-history"].length > 0) {
                        const wearHistory = stintData["tyre-wear-history"];
                        wearHistory.forEach(wearData => {
                            graphDataFL.push({
                                x: wearData["lap-number"],
                                y: formatFloatWithTwoDecimals(wearData["front-left-wear"]),
                                desc: wearData["desc"],
                            });
                            graphDataFR.push({
                                x: wearData["lap-number"],
                                y: formatFloatWithTwoDecimals(wearData["front-right-wear"]),
                                desc: wearData["desc"],
                            });
                            graphDataRL.push({
                                x: wearData["lap-number"],
                                y: formatFloatWithTwoDecimals(wearData["rear-left-wear"]),
                                desc: wearData["desc"],
                            });
                            graphDataRR.push({
                                x: wearData["lap-number"],
                                y: formatFloatWithTwoDecimals(wearData["rear-right-wear"]),
                                desc: wearData["desc"],
                            });
                        });
                    }
                    count++;
                });
            } else {
                const row = tbody.insertRow();
                row.innerHTML = '<td colspan="8">Tyre Stint History data not yet available</td>';
            }

            table.appendChild(tbody);
            leftDiv.appendChild(table);
        };
        const rightPanePopulator = (rightDiv) => {
            const datasets = [
                {
                    label: 'FL',
                    data: graphDataFL
                },
                {
                    label: 'FR',
                    data: graphDataFR
                },
                {
                    label: 'RL',
                    data: graphDataRL
                },
                {
                    label: 'RR',
                    data: graphDataRR
                }
            ];
            const limits = {
                min: 0,
            }

            // Pass the graph data to plotGraph function
            const canvas = document.createElement('canvas');
            rightDiv.classList.add('chart-container');
            plotGraph(canvas, datasets, 'Lap', 'Tyre Wear %', false, limits);
            rightDiv.appendChild(canvas);
        };

        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
    }

    populateERSHistoryTab(tabPane) {

        const graphDataDeployed = [];
        const graphDataRemaining = [];
        const graphDataHarvested = [];
        const leftPanePopulator = (leftDiv) => {
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            const headers = [
                'Lap',
                'Remaining',
                'Deployed',
                'Harv MGU-H',
                'Harv MGU-K',
                'Harvested',
            ];

            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table body
            const tbody = document.createElement('tbody');
            const perLapInfo = this.data["per-lap-info"];
            if (perLapInfo.length > 0) {
                perLapInfo.forEach((lapInfo) => {
                    const row = tbody.insertRow();
                    const currentLapNum = lapInfo["lap-number"];
                    if (currentLapNum == 0) {
                        // Skip lap 0 for ERS, we want that only for fuel
                        // If this is the only lap info available, print the standard error message
                        if (perLapInfo.length == 1) {
                            row.innerHTML = '<td colspan="6">ERS data not available</td>';
                        }
                        return;
                    }

                    let ersRemainingPerc = "---";
                    let ersDeployedPerc = "---";
                    let ersHarvestedMguHPerc = "---";
                    let ersHarvestedMguKPerc = "---";
                    let ersHarvestedTotalPerc = "---";
                    if ("car-status-data" in lapInfo) {
                        const maxErsCapacity = lapInfo["car-status-data"]["ers-max-capacity"];
                        const ersRemainingVal = lapInfo["car-status-data"]["ers-store-energy"];
                        const ersDeployedThisLapVal = lapInfo["car-status-data"]["ers-deployed-this-lap"];
                        const ersHarvestedThisLapMguHVal = lapInfo["car-status-data"]["ers-harvested-this-lap-mguh"];
                        const ersHarvestedThisLapMguKVal = lapInfo["car-status-data"]["ers-harvested-this-lap-mguk"];

                        ersRemainingPerc = formatFloatWithTwoDecimals(
                            (ersRemainingVal / maxErsCapacity) * 100) + "%";
                        ersDeployedPerc = formatFloatWithTwoDecimals(
                            (ersDeployedThisLapVal / maxErsCapacity) * 100) + "%";
                        ersHarvestedMguHPerc = formatFloatWithTwoDecimals(
                            (ersHarvestedThisLapMguHVal / maxErsCapacity) * 100) + "%";
                        ersHarvestedMguKPerc = formatFloatWithTwoDecimals(
                            (ersHarvestedThisLapMguKVal / maxErsCapacity) * 100) + "%";
                        ersHarvestedTotalPerc = formatFloatWithTwoDecimals(
                            ((ersHarvestedThisLapMguHVal + ersHarvestedThisLapMguKVal) / maxErsCapacity)
                            * 100) + "%";

                        graphDataDeployed.push({ x: parseFloat(currentLapNum), y: ((ersDeployedThisLapVal / maxErsCapacity) * 100) });
                        graphDataRemaining.push({ x: parseFloat(currentLapNum), y: ((ersRemainingVal / maxErsCapacity) * 100) });
                        graphDataHarvested.push({ x: parseFloat(currentLapNum), y: (((ersHarvestedThisLapMguHVal + ersHarvestedThisLapMguKVal) / maxErsCapacity) * 100) });
                    }

                    this.populateTableRow(row, [
                        currentLapNum,
                        ersRemainingPerc,
                        ersDeployedPerc,
                        ersHarvestedMguHPerc,
                        ersHarvestedMguKPerc,
                        ersHarvestedTotalPerc,
                    ]);
                });
            } else {
                const row = tbody.insertRow();
                row.innerHTML = '<td colspan="6">ERS data not available</td>';
            }

            table.appendChild(tbody);
            leftDiv.appendChild(table);
        };

        const rightPanePopulator = (rightDiv) => {
            // Plot graph
            const datasets = [
                {
                    label: 'Deployed',
                    data: graphDataDeployed
                },
                {
                    label: 'Remaining',
                    data: graphDataRemaining
                },
                {
                    label: 'Harvested',
                    data: graphDataHarvested
                }
            ];
            const limits = {
                min: 0,
            }

            // Pass the graph data to plotGraph function
            const canvas = document.createElement('canvas');
            rightDiv.classList.add('chart-container');
            plotGraph(canvas, datasets, 'Lap', 'ERS %', false, limits);
            rightDiv.appendChild(canvas);
        };

        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
    }

    populateCarDamageTab(tabPane) {
        this.showRawDataInTable(tabPane, this.data["car-damage"], "Car damage data not available");
    }

    populateTyreWearPredictionTab(tabPane) {
        if (!this.data.hasOwnProperty("tyre-wear-predictions")) {
            // no need to even create this tab
            return;
        }
        const selectedPitStop = this.data["tyre-wear-predictions"]["selected-pit-stop-lap"];
        const predictions = this.data["tyre-wear-predictions"]["predictions"];
        const { firstHalf, secondHalf } = splitArray(predictions);

        const panePopulator = (divElement, tableData) => {
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            const headers = [
                'Lap',
                'FL',
                'FR',
                'RL',
                'RR',
                'Average'
            ];

            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table body
            const tbody = document.createElement('tbody');
            if (tableData.length > 0) {
                tableData.forEach((predictionData) => {
                    const currentLapNum = predictionData["lap-number"];
                    const flWear = formatFloatWithTwoDecimals(predictionData["front-left-wear"]) + "%";
                    const frWear = formatFloatWithTwoDecimals(predictionData["front-right-wear"]) + "%";
                    const rlWear = formatFloatWithTwoDecimals(predictionData["rear-left-wear"]) + "%";
                    const rrWear = formatFloatWithTwoDecimals(predictionData["rear-right-wear"]) + "%";
                    const average = formatFloatWithTwoDecimals(predictionData["average"]) + "%";
                    const row = tbody.insertRow();
                    this.populateTableRow(row, [
                        currentLapNum,
                        flWear,
                        frWear,
                        rlWear,
                        rrWear,
                        average
                    ]);

                    if (currentLapNum == selectedPitStop) {
                        row.classList.add('border', 'border-white');
                    }
                });
            } else {
                const row = tbody.insertRow();
                row.innerHTML = '<td colspan="6">Tyre wear prediction data not available</td>';
            }

            table.appendChild(tbody);
            divElement.appendChild(table);
        };

        const leftPanePopulator = (leftDiv) => {
            panePopulator(leftDiv, firstHalf);
        };
        const rightPanePopulator = (rightDiv) => {
            panePopulator(rightDiv, secondHalf);
        };
        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
    }

    populateWarnsPensInfoTab(tabPane) {

        const leftPanePopulator = (leftDiv) => {
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table body
            const tbody = document.createElement('tbody');
            const lapData = this.data["lap-data"];
            if (lapData) {
                const numPenalties = lapData["penalties"];
                const totalWarnings = lapData["total-warnings"];
                const numCornerCuttingWarnings = lapData["corner-cutting-warnings"];
                const numUnservedDriveThroughPens = lapData["num-unserved-drive-through-pens"];
                const numUnservedStopGoPens = lapData["num-unserved-stop-go-pens"];
                let row;

                row = tbody.insertRow();
                this.populateTableRow(row, [
                    "Time Penalties",
                    numPenalties
                ]);

                row = tbody.insertRow();
                this.populateTableRow(row, [
                    "Total Warnings",
                    totalWarnings
                ]);

                row = tbody.insertRow();
                this.populateTableRow(row, [
                    "Corner Cutting Warnings",
                    numCornerCuttingWarnings
                ]);

                row = tbody.insertRow();
                this.populateTableRow(row, [
                    "Unserved Drive Through Penalties",
                    numUnservedDriveThroughPens
                ]);

                row = tbody.insertRow();
                this.populateTableRow(row, [
                    "Unserved Stop Go Penalties",
                    numUnservedStopGoPens
                ]);
            }

            table.appendChild(tbody);
            leftDiv.appendChild(table);
        };

        const rightPanePopulator = (rightDiv) => {
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            const headers = [
                'Lap',
                'Sector',
                'Lap %',
                'Type',
                'Old val',
                'New val'
            ];

            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table body
            const tbody = document.createElement('tbody');
            const warningsPenaltyHistoryList = this.data["warning-penalty-history"];
            if (warningsPenaltyHistoryList.length) {
                warningsPenaltyHistoryList.forEach(data => {
                    const entryType = data["entry-type"];
                    const oldValue = data["old-value"];
                    const newValue = data["new-value"];
                    const lapNumber = data["lap-number"];
                    const sectorNumber = data["sector-number"];
                    const lapProgressPercent = data["lap-progress-percent"];
                    const row = tbody.insertRow();
                    this.populateTableRow(row, [
                        lapNumber,
                        sectorNumber,
                        formatFloatWithTwoDecimals(lapProgressPercent) + "%",
                        entryType,
                        oldValue,
                        newValue
                    ]);
                });
            } else {
                const row = tbody.insertRow();
                row.innerHTML = '<td colspan="6">No Warnings or Penalites</td>';
            }

            table.appendChild(tbody);
            rightDiv.appendChild(table);
        };

        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
    }

    populateCollisionsInfoTab(tabPane) {

        const table = document.createElement('table');
        table.className = this.tableClassNames ;

        // Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const headers = [
          'ID',
          'Colliding driver',
          'Lap',
        ];

        headers.forEach(headerText => {
          const th = document.createElement('th');
          th.textContent = headerText;
          headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const tbody = document.createElement('tbody');
        const playerIndex = this.data["index"];

        let records;
        if (!("collisions" in this.data && "records" in this.data["collisions"])) {
            records = [];
        } else {
            records = this.data["collisions"]["records"];
        }
        records.forEach((record, index) => {
            const otherDriverName = this.getCollisionOtherDriverName(playerIndex, record);
            const lapNum = this.getCollisionLapNumber(playerIndex, record);
            const row = tbody.insertRow();
            this.populateTableRow(row, [
                index+1,
                otherDriverName,
                lapNum
            ]);
        });

        table.appendChild(tbody);
        tabPane.appendChild(table);
    }

    populateTyreSetsInfoTab(tabPane) {

        const tyreSets = this.sanitizeTyreSetData(this.data['tyre-sets']['tyre-set-data']);
        // Create the accordion container
        const accordionContainer = document.createElement('div');
        accordionContainer.className = 'accordion bg-dark';
        accordionContainer.id = 'tyreSetsAccordion';

        // Generate accordion items
        tyreSets.forEach((tyreSetGroup, index) => {
            // Create an accordion item (group)
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item accordion-flush bg-dark border-secondary';

            // Accordion header (the clickable row)
            const accordionHeader = document.createElement('h2');
            accordionHeader.className = 'accordion-header';
            accordionHeader.id = `heading${index}`;

            const icon = this.iconCache.getIcon(tyreSetGroup["visual-tyre-compound"]);
            const accordionButton = document.createElement('button');
            accordionButton.className = 'accordion-button bg-dark text-white collapsed';
            accordionButton.type = 'button';
            accordionButton.setAttribute('data-bs-toggle', 'collapse');
            accordionButton.setAttribute('data-bs-target', `#collapse${index}`);
            accordionButton.setAttribute('aria-expanded', 'false');
            accordionButton.setAttribute('aria-controls', `collapse${index}`);

            if (icon) {
                accordionButton.textContent = `${tyreSetGroup["visual-tyre-compound"]}  `;
                accordionButton.appendChild(icon);
            } else {
                accordionButton.textContent = tyreSetGroup["actual-tyre-compound"] + " - " +
                    tyreSetGroup["visual-tyre-compound"];
            }

            accordionHeader.appendChild(accordionButton);

            // Accordion body (the collapsible content area)
            const accordionCollapse = document.createElement('div');
            accordionCollapse.id = `collapse${index}`;
            accordionCollapse.className = 'accordion-collapse collapse';
            accordionCollapse.setAttribute('aria-labelledby', `heading${index}`);
            accordionCollapse.setAttribute('data-bs-parent', '#tyreSetsAccordion');

            // Accordion body content
            const accordionBody = document.createElement('div');
            accordionBody.className = 'accordion-body bg-dark text-light';
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            const headers = [
                'Index',
                'Wear %',
                'Lifespan',
                'Delta'
            ];

            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table body
            const tbody = document.createElement('tbody');

            const currTyreSets = tyreSetGroup["tyre-sets"];
            currTyreSets.forEach((record) => {
                const tyreSetIndex = record["index"];
                const wear = record["wear"];
                const lifespan = record["life-span"];
                const delta = formatFloatWithTwoDecimalsSigned(record["lap-delta-time"] / 1000) + "s";
                const row = tbody.insertRow();
                this.populateTableRow(row, [
                    tyreSetIndex,
                    wear,
                    lifespan,
                    delta
                ]);
            });

            table.appendChild(tbody);

            accordionBody.appendChild(table);
            accordionCollapse.appendChild(accordionBody);

            // Append header and body to the accordion item
            accordionItem.appendChild(accordionHeader);
            accordionItem.appendChild(accordionCollapse);

            // Append the accordion item to the main container
            accordionContainer.appendChild(accordionItem);
        });

        // Append the accordion container to the body (or any other container)
        tabPane.appendChild(accordionContainer);
    }

    populateCarSetupTab(tabPane) {

        if (this.data["car-setup"]) {
            if (this.data["car-setup"]["is-valid"]) {
                // remove this key, no need to display
                delete this.data["car-setup"]["is-valid"];
            } else {
                // setup data will be full of 0's. Don't show
                this.data["car-setup"] = null;
            }
        }
        this.showRawDataInTable(tabPane, this.data["car-setup"], "Car setup data not available");
    }

    // Method to create the navigation tabs
    createNavTabs() {
        const navTabs = document.createElement('ul');
        navTabs.className = 'nav nav-tabs driver-modal-nav inactive';
        navTabs.setAttribute('role', 'tablist');
        navTabs.setAttribute('data-bs-theme', 'dark');

        // Array of tabs with ID and label
        const tabs = [
            { id: 'lap-times', label: 'Lap Times' },
            { id: 'fuel-usage', label: 'Fuel Usage History' },
            { id: 'tyre-stint-history', label: 'Tyre Stint History' },
            { id: 'ers-history', label: 'ERS Usage History' },
            { id: 'car-damage', label: 'Car Damage' },
            { id: 'tyre-wear-prediction', label: 'Tyre Wear Prediction' },
            { id: 'warns-pens-info', label: 'Warns/Pens' },
            { id: 'collisions-info', label: 'Collisions' },
            { id: 'tyre-sets', label: 'Tyre Sets' },
        ];

        if ('car-setup' in this.data) {
            tabs.push({ id: 'car-setup', label: 'Car Setup' });
        }

        // Sort tabs alphabetically based on the label
        tabs.sort((a, b) => a.label.localeCompare(b.label));

        tabs.forEach((tab, index) => {
            const navItem = document.createElement('li');
            navItem.className = 'nav-item';
            navItem.setAttribute('role', 'presentation');

            const navLink = document.createElement('button');
            navLink.className = `nav-link driver-modal-nav-link ${index === 0 ? 'active' : ''}`;
            navLink.id = `${tab.id}-tab`;
            navLink.setAttribute('data-bs-toggle', 'tab');
            navLink.setAttribute('data-bs-target', `#${tab.id}`);
            navLink.setAttribute('type', 'button');
            navLink.setAttribute('role', 'tab');
            navLink.setAttribute('aria-controls', tab.id);
            navLink.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
            navLink.textContent = tab.label;

            navItem.appendChild(navLink);
            navTabs.appendChild(navItem);
        });

        return navTabs;
    }

    // Method to create the tab content container
    createTabContent() {
        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content driver-modal-tab-content flex-grow-1 overflow-hidden';

        // Array of tabs with ID and method to populate content
        const tabs = [
            { id: 'lap-times', method: this.populateLapTimesTab },
            { id: 'fuel-usage', method: this.populateFuelUsageTab },
            { id: 'tyre-stint-history', method: this.populateTyreStintHistoryTab },
            { id: 'ers-history', method: this.populateERSHistoryTab },
            { id: 'car-damage', method: this.populateCarDamageTab },
            { id: 'tyre-wear-prediction', method: this.populateTyreWearPredictionTab },
            { id: 'warns-pens-info', method: this.populateWarnsPensInfoTab },
            { id: 'collisions-info', method: this.populateCollisionsInfoTab },
            { id: 'tyre-sets', method: this.populateTyreSetsInfoTab },
        ];

        if ('car-setup' in this.data) {
          tabs.push({ id: 'car-setup', method: this.populateCarSetupTab });
        }


        // Sort tabs alphabetically based on the label
        tabs.sort((a, b) => a.id.localeCompare(b.id));

        tabs.forEach((tab, index) => {
            const tabPane = document.createElement('div');
            tabPane.className = `tab-pane fade driver-modal-tab-pane ${index === 0 ? 'show active' : ''} h-100`;
            tabPane.id = tab.id;
            tabPane.setAttribute('role', 'tabpanel');
            tabPane.setAttribute('aria-labelledby', `${tab.id}-tab`);

            // Populate the tab content using the respective method
            tab.method.call(this, tabPane);

            tabContent.appendChild(tabPane);
        });

        return tabContent;
    }

    populateTableRow(row, cellsData) {
        cellsData.forEach((cellData) => {
            const cell = document.createElement('td');

            if (cellData instanceof SVGElement) { // Check if cellData is an SVG element
                cell.appendChild(cellData); // Directly append the SVG icon
            } else {
                cell.textContent = cellData; // Fallback to text content for other types
            }

            row.appendChild(cell);
        });
    }

    createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator) {

        // Split the tab content into two vertical halves
        const containerDiv = document.createElement('div');
        containerDiv.className = 'd-flex';
        // containerDiv.style.height = '100vh';

        // Left half: Create the fuel usage table
        const leftDiv = document.createElement('div');
        leftDiv.className = 'w-50 border border-light-subtle rounded overflow-auto'; // Half width
        leftPanePopulator(leftDiv);

        // Right half: Empty for now
        const rightDiv = document.createElement('div');
        rightDiv.className = 'w-50 border border-light-subtle rounded overflow-auto'; // Half width, empty for now
        rightPanePopulator(rightDiv);

        containerDiv.appendChild(leftDiv);
        containerDiv.appendChild(rightDiv);

        tabPane.appendChild(containerDiv);
    }

    getCollisionOtherDriverName(index, data) {

        if (index == data["driver-1-index"]) {
            return data["driver-2-name"];
        } else {
            return data["driver-1-name"];
        }
    }

    getCollisionLapNumber(index, data) {

        if (index == data["driver-1-index"]) {
            return data["driver-1-lap"];
        } else {
            return data["driver-2-lap"];
        }
    }

    sanitizeTyreSetData(tyreSetData) {
        // Step 1: Filter out unavailable tyres
        const availableTyres = tyreSetData
            .filter(tyre => tyre.available === true)
            .map((tyre, index) => ({ ...tyre, index }));

        // Step 2: Group tyres by both "actual-tyre-compound" and "visual-tyre-compound"
        const groupedTyres = availableTyres.reduce((acc, tyre) => {
            const { "actual-tyre-compound": actualCompound, "visual-tyre-compound": visualCompound } = tyre;

            // Ensure the actual-tyre-compound group exists
            if (!acc[actualCompound]) {
                acc[actualCompound] = {};
            }

            // Ensure the visual-tyre-compound group exists within the actual-tyre-compound group
            if (!acc[actualCompound][visualCompound]) {
                acc[actualCompound][visualCompound] = [];
            }

            // Add the tyre to the appropriate group
            acc[actualCompound][visualCompound].push(tyre);

            return acc; // Return the accumulator for the next iteration
        }, {}); // Start with an empty object

        // Step 3: Convert the grouped object into the desired array structure
        return Object.keys(groupedTyres).map(actualCompound => {
            return Object.keys(groupedTyres[actualCompound]).map(visualCompound => ({
                "actual-tyre-compound": actualCompound,
                "visual-tyre-compound": visualCompound,
                "tyre-sets": groupedTyres[actualCompound][visualCompound]
            }));
        }).flat();
    }

    showRawDataInTable(tabPane, data, errorMessage) {
        if (data === null) {

            // Create the container div
            const containerDiv = document.createElement('div');
            containerDiv.className = 'd-flex';

            // Create a paragraph element
            const paragraph = document.createElement('p');

            // Set the text content of the paragraph
            paragraph.textContent = errorMessage;

            // Append the paragraph to the container div
            containerDiv.appendChild(paragraph);

            // Optionally, you can append the containerDiv to the body or any other parent element
            tabPane.appendChild(containerDiv);
            return;
        }

        const { firstHalf, secondHalf } = splitJsonObject(flattenJsonObject(data));
        const panePopulator = (divElement, tableData) => {
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            const headers = [
                'Field',
                'Value',
            ];

            headers.forEach(headerText => {
                const th = document.createElement('th');
                th.textContent = headerText;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table body
            const tbody = document.createElement('tbody');
            if (Object.keys(tableData).length > 0) {
                for (const key in tableData) {
                    const value = tableData[key];
                    const row = tbody.insertRow();
                    this.populateTableRow(row, [kebabToTitleCase(key),
                        typeof value === 'number' && !Number.isInteger(value) ?
                            formatFloatWithTwoDecimals(value) : value]);
                }
            } else {
                const row = tbody.insertRow();
                row.innerHTML = `<td colspan="2">${errorMessage}</td>`;
            }

            table.appendChild(tbody);
            divElement.appendChild(table);
        };

        const leftPanePopulator = (leftDiv) => {
            panePopulator(leftDiv, firstHalf);
        }
        const rightPanePopulator = (rightDiv) => {
            panePopulator(rightDiv, secondHalf);
        }

        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
    }
}
