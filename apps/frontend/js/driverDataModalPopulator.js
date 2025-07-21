class DriverModalPopulator {
    constructor(data, iconCache) {
        this.data = data;
        this.tableClassNames = 'table table-bordered table-striped table-dark table-sm align-middle';
        this.iconCache = iconCache;
        this.telemetryEnabled = (this.data?.["participant-data"]?.["telemetry-setting"] === "Public");
        this.tyreWearPredictionsAvailable = this.data?.["tyre-wear-predictions"]?.["status"];
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
            const headers = ['Lap', 'S1', 'S2', 'S3', 'Time', 'Tyre', 'Wear', 'Top Speed'];

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
                const tyreSetInfo = lap["tyre-set-info"];
                const tyreSet = (tyreSetInfo) ? (tyreSetInfo["tyre-set"]) : (null);
                if (tyreSet) {
                    const compound = tyreSet["visual-tyre-compound"];
                    const svgElement = this.iconCache.getIcon(compound);
                    if (svgElement) {
                        tyreCell.appendChild(svgElement);
                    } else {
                        tyreCell.textContent = compound;
                    }
                }
                row.appendChild(tyreCell);

                const wearCell = document.createElement('td');
                wearCell.textContent = tyreSetInfo
                    ? tyreSetInfo["tyre-wear"]["average"].toFixed(2) + '%'
                    : '---';
                row.appendChild(wearCell);

                const topSpeedCell = document.createElement('td');
                const topSpeed = lap["top-speed-kmph"];
                topSpeedCell.textContent = (topSpeed != null) ? (formatSpeed(topSpeed,
                    { isMetric: g_pref_speedUnitMetric, decimalPlaces: 0, addUnitSuffix: false })) : ('---');
                row.appendChild(topSpeedCell);

                tbody.appendChild(row);
            });

            table.appendChild(tbody);
            leftDiv.appendChild(table);
        };

        const rightPanePopulator = (rightDiv) => {

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
        // Minimum fuel level to maintain as buffer
        const MIN_FUEL_LEVEL = 0.2; // kg

        if (!this.telemetryEnabled) {
            this.populateTelemetryDisabledMessage(tabPane);
            return;
        }
        const fuelUsagePerLap = [];

        const leftPanePopulator = (leftDiv) => {
            // Helper function to create input groups
            const createInputGroup = (labelText, inputConfig, tooltip = null) => {
                const group = document.createElement('div');
                group.style.display = 'flex';
                group.style.alignItems = 'center';
                group.style.gap = '5px';

                const label = document.createElement('label');
                label.textContent = labelText;
                label.style.color = '#ffffff';
                label.style.fontSize = '0.85em';
                label.style.marginBottom = '0';
                if (tooltip) {
                    label.title = tooltip;
                    label.style.cursor = 'help';
                }

                const input = document.createElement('input');
                input.type = inputConfig.type || 'number';
                input.className = 'form-control form-control-sm';
                input.style.width = inputConfig.width || '70px';
                input.style.backgroundColor = '#495057';
                input.style.borderColor = '#6c757d';
                input.style.color = '#ffffff';
                input.style.fontSize = '0.85em';
                input.style.appearance = 'textfield';
                input.style.MozAppearance = 'textfield';

                if (inputConfig.value !== undefined) input.value = inputConfig.value;
                if (inputConfig.min !== undefined) input.min = inputConfig.min;
                if (inputConfig.max !== undefined) input.max = inputConfig.max;
                if (inputConfig.step !== undefined) input.step = inputConfig.step;

                group.appendChild(label);
                group.appendChild(input);
                return { group, input };
            };

            // Helper function to create buttons
            const createButton = (text, className = 'btn btn-secondary btn-sm') => {
                const button = document.createElement('button');
                button.textContent = text;
                button.className = className;
                button.style.fontSize = '0.8em';
                return button;
            };

            // Helper function to create info spans
            const createInfoSpan = (labelText, valueText = '0', unit = '') => {
                const container = document.createElement('span');
                container.style.marginLeft = '15px';

                const label = document.createElement('span');
                label.textContent = labelText;
                label.style.color = '#ffffff';
                label.style.fontSize = '0.85em';

                const value = document.createElement('span');
                value.textContent = valueText;
                value.style.fontWeight = 'bold';
                value.style.color = '#ffffff';
                value.style.fontSize = '0.9em';

                const unitSpan = document.createElement('span');
                unitSpan.textContent = unit;
                unitSpan.style.color = '#ffffff';
                unitSpan.style.fontSize = '0.85em';

                container.appendChild(label);
                container.appendChild(value);
                container.appendChild(unitSpan);

                return { container, value };
            };

            // Helper function to create strategy cards
            const createStrategyCard = (title, borderColor, tooltip) => {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.backgroundColor = '#495057';
                card.style.borderColor = borderColor;
                card.style.borderWidth = '2px';
                card.style.width = '140px';

                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                cardBody.style.padding = '8px 12px';
                cardBody.style.textAlign = 'center';

                const titleElement = document.createElement('h6');
                titleElement.className = 'card-title';
                titleElement.textContent = title;
                titleElement.style.color = '#ffffff';
                titleElement.style.fontSize = '0.9em';
                titleElement.style.marginBottom = '5px';
                if (tooltip) {
                    titleElement.title = tooltip;
                    titleElement.style.cursor = 'help';
                }

                const valueSpan = document.createElement('div');
                valueSpan.style.color = '#ffffff';
                valueSpan.style.fontWeight = 'bold';
                valueSpan.style.fontSize = '1.1em';
                valueSpan.textContent = '0.00 kg';

                cardBody.appendChild(titleElement);
                cardBody.appendChild(valueSpan);
                card.appendChild(cardBody);

                return { card, valueSpan };
            };

            // Create fuel usage table
            const table = document.createElement('table');
            table.className = this.tableClassNames;

            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');

            const checkboxHeader = document.createElement('th');
            checkboxHeader.textContent = 'Select';
            headerRow.appendChild(checkboxHeader);

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

                // Add checkbox cell
                const checkboxCell = document.createElement('td');
                checkboxCell.style.textAlign = 'center';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'fuel-calc-checkbox';
                checkbox.dataset.lapIndex = index;
                checkboxCell.appendChild(checkbox);
                row.appendChild(checkboxCell);

                const lapCell = document.createElement('td');
                lapCell.textContent = lapData["lap-number"];
                row.appendChild(lapCell);

                const fuelLoadCell = document.createElement('td');
                fuelLoadCell.textContent = lapData["car-status-data"]["fuel-in-tank"].toFixed(2);
                row.appendChild(fuelLoadCell);

                const usagePerLapCell = document.createElement('td');
                let usagePerLap = 0;
                if (previousFuelLoad !== null) {
                    usagePerLap = previousFuelLoad - lapData["car-status-data"]["fuel-in-tank"];
                    usagePerLapCell.textContent = usagePerLap.toFixed(2);
                    fuelUsagePerLap.push({
                        x: lapData["lap-number"],
                        y: usagePerLap
                    });
                    checkbox.dataset.fuelUsage = usagePerLap.toFixed(4);
                } else {
                    usagePerLapCell.textContent = '-';
                    checkbox.disabled = true;
                }
                row.appendChild(usagePerLapCell);

                const excessLapsCell = document.createElement('td');
                const excessLaps = lapData["car-status-data"]["fuel-remaining-laps"];
                excessLapsCell.textContent = excessLaps.toFixed(2);
                row.appendChild(excessLapsCell);

                const excessLapsDeltaCell = document.createElement('td');
                if (previousExcessLaps !== null) {
                    const excessLapsDelta = excessLaps - previousExcessLaps;
                    excessLapsDeltaCell.textContent = excessLapsDelta.toFixed(2);
                } else {
                    excessLapsDeltaCell.textContent = '-';
                }
                row.appendChild(excessLapsDeltaCell);

                tbody.appendChild(row);

                previousFuelLoad = lapData["car-status-data"]["fuel-in-tank"];
                previousExcessLaps = excessLaps;
            });

            table.appendChild(tbody);

            // Create scrollable table container
            const tableContainer = document.createElement('div');
            tableContainer.style.maxHeight = '400px';
            tableContainer.style.overflowY = 'auto';
            tableContainer.style.position = 'relative';

            thead.style.position = 'sticky';
            thead.style.top = '0';
            thead.style.zIndex = '10';

            tableContainer.appendChild(table);
            leftDiv.appendChild(tableContainer);

            // Create fuel calculator header
            const calculatorHeader = document.createElement('div');
            calculatorHeader.style.marginTop = '20px';
            calculatorHeader.style.marginBottom = '15px';
            calculatorHeader.style.padding = '10px 15px';
            calculatorHeader.style.backgroundColor = '#495057';
            calculatorHeader.style.borderLeft = '4px solid #17a2b8';
            calculatorHeader.style.borderRadius = '4px';

            const calculatorTitle = document.createElement('h5');
            calculatorTitle.textContent = 'Fuel Strategy Calculator';
            calculatorTitle.style.color = '#ffffff';
            calculatorTitle.style.margin = '0';
            calculatorTitle.style.fontSize = '1.1em';
            calculatorTitle.style.fontWeight = 'bold';

            calculatorHeader.appendChild(calculatorTitle);
            leftDiv.appendChild(calculatorHeader);

            // Create fuel calculator container
            const calculatorContainer = document.createElement('div');
            calculatorContainer.style.marginTop = '15px';
            calculatorContainer.style.padding = '15px';
            calculatorContainer.style.backgroundColor = '#343a40';
            calculatorContainer.style.borderRadius = '6px';
            calculatorContainer.style.border = '1px solid #495057';
            calculatorContainer.style.display = 'flex';
            calculatorContainer.style.flexDirection = 'column';
            calculatorContainer.style.gap = '10px';

            // Selection Controls Card
            const selectionCard = document.createElement('div');
            selectionCard.className = 'card';
            selectionCard.style.backgroundColor = '#495057';
            selectionCard.style.borderColor = '#6c757d';

            const selectionCardBody = document.createElement('div');
            selectionCardBody.className = 'card-body';
            selectionCardBody.style.padding = '8px 12px';

            const selectionRow = document.createElement('div');
            selectionRow.style.display = 'flex';
            selectionRow.style.alignItems = 'center';
            selectionRow.style.gap = '10px';
            selectionRow.style.flexWrap = 'wrap';

            const selectAllBtn = createButton('Select All');
            const selectNoneBtn = createButton('Clear');

            const selectedLapsInfo = createInfoSpan('Selected: ', '0');
            const avgFuelInfo = createInfoSpan('Avg: ', '0.00', ' kg/lap');
            const safetyCarBurnInfo = createInfoSpan('SC: ', '0.00', ' kg/lap');

            selectionRow.appendChild(selectAllBtn);
            selectionRow.appendChild(selectNoneBtn);
            selectionRow.appendChild(selectedLapsInfo.container);
            selectionRow.appendChild(avgFuelInfo.container);
            selectionRow.appendChild(safetyCarBurnInfo.container);

            selectionCardBody.appendChild(selectionRow);
            selectionCard.appendChild(selectionCardBody);

            // Race Parameters Card
            const paramsCard = document.createElement('div');
            paramsCard.className = 'card';
            paramsCard.style.backgroundColor = '#495057';
            paramsCard.style.borderColor = '#6c757d';

            const paramsCardBody = document.createElement('div');
            paramsCardBody.className = 'card-body';
            paramsCardBody.style.padding = '8px 12px';

            const paramsRow = document.createElement('div');
            paramsRow.style.display = 'flex';
            paramsRow.style.alignItems = 'center';
            paramsRow.style.gap = '15px';
            paramsRow.style.flexWrap = 'wrap';

            // Create input groups
            const raceLapsGroup = createInputGroup('Race Laps:', { width: '80px', min: '1', step: '1' });
            const surplusLapsGroup = createInputGroup('Surplus Laps:', { value: '0.2', width: '70px', min: '0', step: '0.1' });
            const safetyCarsGroup = createInputGroup('Safety Cars:', { value: '0', width: '60px', min: '0', step: '1' });
            const lapsPerSCGroup = createInputGroup('Laps Per SC:', { value: '2', width: '60px', min: '1', step: '1' });
            const scBurnRateGroup = createInputGroup('SC Burn %:', { value: '70', width: '60px', min: '0', max: '100', step: '5' }, 'Safety car fuel burn rate as percentage of normal racing fuel consumption');

            paramsRow.appendChild(raceLapsGroup.group);
            paramsRow.appendChild(surplusLapsGroup.group);
            paramsRow.appendChild(safetyCarsGroup.group);
            paramsRow.appendChild(lapsPerSCGroup.group);
            paramsRow.appendChild(scBurnRateGroup.group);
            paramsCardBody.appendChild(paramsRow);
            paramsCard.appendChild(paramsCardBody);

            // Strategies Container
            const strategiesContainer = document.createElement('div');
            strategiesContainer.style.display = 'flex';
            strategiesContainer.style.gap = '10px';

            const conservativeStrategy = createStrategyCard('Conservative', '#28a745', 'Fuel load calculated using current average fuel consumption with safety margins');
            const aggressiveStrategy = createStrategyCard('Aggressive', '#dc3545', 'Fuel load calculated assuming 5% more efficient driving than current average');

            strategiesContainer.appendChild(conservativeStrategy.card);
            strategiesContainer.appendChild(aggressiveStrategy.card);

            // Update calculations function
            const updateCalculations = () => {
                const checkedBoxes = leftDiv.querySelectorAll('.fuel-calc-checkbox:checked');
                const selectedCount = checkedBoxes.length;
                selectedLapsInfo.value.textContent = selectedCount;

                if (selectedCount === 0) {
                    avgFuelInfo.value.textContent = '0.00';
                    safetyCarBurnInfo.value.textContent = '0.00';
                    conservativeStrategy.valueSpan.textContent = '0.00 kg';
                    aggressiveStrategy.valueSpan.textContent = '0.00 kg';
                    return;
                }

                let totalFuelUsage = 0;
                checkedBoxes.forEach(checkbox => {
                    const fuelUsage = parseFloat(checkbox.dataset.fuelUsage);
                    if (!isNaN(fuelUsage)) {
                        totalFuelUsage += fuelUsage;
                    }
                });

                const avgFuel = totalFuelUsage / selectedCount;
                avgFuelInfo.value.textContent = avgFuel.toFixed(2);

                // Calculate safety car fuel burn
                const scBurnRate = parseFloat(scBurnRateGroup.input.value) / 100 || 0.7;
                const safetyCarBurn = avgFuel * scBurnRate;
                safetyCarBurnInfo.value.textContent = safetyCarBurn.toFixed(2);

                // Calculate fuel strategies
                const raceLaps = parseInt(raceLapsGroup.input.value) || 0;
                const surplusLaps = parseFloat(surplusLapsGroup.input.value) || 0;
                const numSafetyCars = parseInt(safetyCarsGroup.input.value) || 0;
                const lapsPerSC = parseInt(lapsPerSCGroup.input.value) || 2;

                if (raceLaps > 0) {
                    // Calculate safety car laps
                    const totalSCLaps = numSafetyCars * lapsPerSC;
                    const normalLaps = raceLaps - totalSCLaps;

                    // Conservative strategy
                    const conservativeNormalFuel = normalLaps * avgFuel;
                    const conservativeSCFuel = totalSCLaps * safetyCarBurn;
                    const conservativeSurplusFuel = surplusLaps * avgFuel;
                    const conservativeFuel = conservativeNormalFuel + conservativeSCFuel + conservativeSurplusFuel + MIN_FUEL_LEVEL;
                    conservativeStrategy.valueSpan.textContent = conservativeFuel.toFixed(2) + ' kg';

                    // Aggressive strategy
                    const aggressiveFuelPerLap = avgFuel * 0.95;
                    const aggressiveNormalFuel = normalLaps * aggressiveFuelPerLap;
                    const aggressiveSCFuel = totalSCLaps * (aggressiveFuelPerLap * scBurnRate);
                    const aggressiveSurplusFuel = surplusLaps * aggressiveFuelPerLap;
                    const aggressiveFuel = aggressiveNormalFuel + aggressiveSCFuel + aggressiveSurplusFuel + MIN_FUEL_LEVEL;
                    aggressiveStrategy.valueSpan.textContent = aggressiveFuel.toFixed(2) + ' kg';
                } else {
                    conservativeStrategy.valueSpan.textContent = '0.00 kg';
                    aggressiveStrategy.valueSpan.textContent = '0.00 kg';
                }
            };

            // Add event listeners
            selectAllBtn.onclick = () => {
                const checkboxes = leftDiv.querySelectorAll('.fuel-calc-checkbox:not(:disabled)');
                checkboxes.forEach(cb => cb.checked = true);
                updateCalculations();
            };

            selectNoneBtn.onclick = () => {
                const checkboxes = leftDiv.querySelectorAll('.fuel-calc-checkbox');
                checkboxes.forEach(cb => cb.checked = false);
                updateCalculations();
            };

            const checkboxes = leftDiv.querySelectorAll('.fuel-calc-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.addEventListener('change', updateCalculations);
            });

            // Add event listeners for all inputs
            [raceLapsGroup, surplusLapsGroup, safetyCarsGroup, lapsPerSCGroup, scBurnRateGroup].forEach(group => {
                group.input.addEventListener('input', updateCalculations);
            });

            // Append all calculator components
            calculatorContainer.appendChild(selectionCard);
            calculatorContainer.appendChild(paramsCard);
            calculatorContainer.appendChild(strategiesContainer);
            leftDiv.appendChild(calculatorContainer);
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

            const canvas = document.createElement('canvas');
            rightDiv.appendChild(canvas);
            rightDiv.classList.add('chart-container');
            plotGraph(canvas, datasets, 'Lap', 'Fuel used (kg)');
        };

        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
    }

    populateTyreStintHistoryTab(tabPane) {
        if (!this.telemetryEnabled) {
            this.populateTelemetryDisabledMessage(tabPane);
            return;
        }

        const graphDataFL = [];
        const graphDataFR = [];
        const graphDataRL = [];
        const graphDataRR = [];
        const leftPanePopulator = (leftDiv) => {
            const tyreSetsHistoryData = this.data["tyre-set-history"];
            const table = document.createElement('table');
            table.className = this.tableClassNames;

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
                    const collapseId = `collapse-stint-${stintId}`;

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

                    // Make row clickable and add Bootstrap collapse attributes
                    row.style.cursor = 'pointer';
                    row.setAttribute('data-bs-toggle', 'collapse');
                    row.setAttribute('data-bs-target', `#${collapseId}`);
                    row.setAttribute('aria-expanded', 'false');
                    row.setAttribute('aria-controls', collapseId);

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

                    // Create collapsible sub-row for lap-by-lap data
                    if ("tyre-wear-history" in stintData && stintData["tyre-wear-history"].length > 0) {
                        const collapseRow = tbody.insertRow();
                        const collapseCell = collapseRow.insertCell();
                        collapseCell.colSpan = 7;
                        collapseCell.style.padding = '0';
                        collapseCell.style.border = 'none';

                        const collapseDiv = document.createElement('div');
                        collapseDiv.className = 'collapse';
                        collapseDiv.id = collapseId;

                        const subTable = document.createElement('table');
                        subTable.className = this.tableClassNames + ' mb-0';
                        subTable.style.backgroundColor = '#f8f9fa';

                        // Create sub-table header
                        const subThead = document.createElement('thead');
                        const subHeaderRow = document.createElement('tr');
                        const subHeaders = ['Lap', 'Front Left', 'Front Right', 'Rear Left', 'Rear Right'];

                        subHeaders.forEach(headerText => {
                            const th = document.createElement('th');
                            th.textContent = headerText;
                            th.style.fontSize = '0.9em';
                            th.style.padding = '0.5rem';
                            subHeaderRow.appendChild(th);
                        });

                        subThead.appendChild(subHeaderRow);
                        subTable.appendChild(subThead);

                        // Create sub-table body
                        const subTbody = document.createElement('tbody');
                        const wearHistory = stintData["tyre-wear-history"];

                        wearHistory.forEach(wearData => {
                            const subRow = subTbody.insertRow();
                            subRow.style.fontSize = '0.9em';

                            const lapCell = subRow.insertCell();
                            lapCell.textContent = wearData["lap-number"];
                            lapCell.style.padding = '0.5rem';

                            const flCell = subRow.insertCell();
                            flCell.textContent = formatFloatWithTwoDecimals(wearData["front-left-wear"]) + '%';
                            flCell.style.padding = '0.5rem';

                            const frCell = subRow.insertCell();
                            frCell.textContent = formatFloatWithTwoDecimals(wearData["front-right-wear"]) + '%';
                            frCell.style.padding = '0.5rem';

                            const rlCell = subRow.insertCell();
                            rlCell.textContent = formatFloatWithTwoDecimals(wearData["rear-left-wear"]) + '%';
                            rlCell.style.padding = '0.5rem';

                            const rrCell = subRow.insertCell();
                            rrCell.textContent = formatFloatWithTwoDecimals(wearData["rear-right-wear"]) + '%';
                            rrCell.style.padding = '0.5rem';
                        });

                        subTable.appendChild(subTbody);
                        collapseDiv.appendChild(subTable);
                        collapseCell.appendChild(collapseDiv);
                    }

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
                row.innerHTML = '<td colspan="7">Tyre Stint History data not yet available</td>';
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
        if (!this.telemetryEnabled) {
            this.populateTelemetryDisabledMessage(tabPane);
            return;
        }

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
        if (!this.telemetryEnabled) {
            this.populateTelemetryDisabledMessage(tabPane);
            return;
        }
        this.showRawDataInTable(tabPane, this.data["car-damage"], "Car damage data not available");
    }

    populateTyreWearPredictionTab(tabPane) {
        if (!this.telemetryEnabled) {
            this.populateTelemetryDisabledMessage(tabPane);
            return;
        }
        if (!this.data.hasOwnProperty("tyre-wear-predictions")) {
            // no need to even create this tab
            return;
        }
        const selectedPitStop = this.data["tyre-wear-predictions"]["selected-pit-stop-lap"];
        const predictions = this.data["tyre-wear-predictions"]["predictions"];
        const graphDataFL = [];
        const graphDataFR = [];
        const graphDataRL = [];
        const graphDataRR = [];

        const leftPanePopulator = (leftDiv) => {
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
            if (predictions.length > 0) {
                predictions.forEach((predictionData) => {
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

                    // update the graph data
                    graphDataFL.push({ x: parseFloat(currentLapNum), y: predictionData["front-left-wear"], desc: predictionData["desc"] });
                    graphDataFR.push({ x: parseFloat(currentLapNum), y: predictionData["front-right-wear"], desc: predictionData["desc"] });
                    graphDataRL.push({ x: parseFloat(currentLapNum), y: predictionData["rear-left-wear"], desc: predictionData["desc"] });
                    graphDataRR.push({ x: parseFloat(currentLapNum), y: predictionData["rear-right-wear"], desc: predictionData["desc"] });
                });
            } else {
                const row = tbody.insertRow();
                row.innerHTML = '<td colspan="6">Tyre wear prediction data not available</td>';
            }

            table.appendChild(tbody);
            leftDiv.appendChild(table);
        };

        /* Now create and populate the graph */
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

        if (!this.telemetryEnabled) {
            this.populateTelemetryDisabledMessage(tabPane);
            return;
        }

        // Create manager with required parameters
        const manager = new F1TyreManager(tabPane, this.iconCache);

        // Update with data when available
        manager.updateData(this.data["tyre-sets"]);
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

    populatePlayerInfoTab(tabPane) {

        // Left pane - Participant data
        const leftPanePopulator = (leftDiv) => {
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table body
            const tbody = document.createElement('tbody');
            const participantData = this.data["participant-data"];
            if (participantData) {

                this.populateTableRows(tbody, [
                    ["AI controlled", participantData["ai-controlled"]],
                    ["Driver ID (Not the driver's race number)", participantData["driver-id"]],
                    ["Team", participantData["team-id"]],
                    ["Name", participantData["name"]],
                    ["Nationality", participantData["nationality"]],
                    ["Network ID", participantData["network-id"]],
                    ["Is Paused", this.data?.["car-status"]?.["network-paused"] ?? "Unknown"],
                    ["Platform", participantData["platform"]],
                    ["Race Number", participantData["race-number"]],
                    ["Show Online Names", participantData["show-online-names"]],
                    ["Tech Level", participantData["tech-level"]],
                    ["Telemetry Setting", participantData["telemetry-setting"]],
                ]);
            } else {
                const row = tbody.insertRow();
                row.innerHTML = '<td colspan="2">No participant data</td>';
            }

            table.appendChild(tbody);
            leftDiv.appendChild(table);
        };

        // Right pane - Assists info
        const rightPanePopulator = (rightDiv) => {
            const table = document.createElement('table');
            table.className = this.tableClassNames ;

            // Create table body
            const tbody = document.createElement('tbody');
            const carStatusData = this.data["car-status"];
            if (carStatusData) {

                this.populateTableRows(tbody, [
                    ["Anti Lock Brakes", carStatusData["anti-lock-brakes"]],
                    ["Traction Control", carStatusData["traction-control"]],
                ]);
            } else {
                const row = tbody.insertRow();
                row.innerHTML = '<td colspan="2">No assists data</td>';
            }

            table.appendChild(tbody);
            rightDiv.appendChild(table);
        };

        this.createModalDivElelements(tabPane, leftPanePopulator, rightPanePopulator);
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
            { id: 'warns-pens-info', label: 'Warns/Pens' },
            { id: 'collisions-info', label: 'Collisions' },
            { id: 'tyre-sets', label: 'Tyre Sets' },
            { id: 'player-info', label: 'Player Info' },
        ];

        if ('car-setup' in this.data) {
            tabs.push({ id: 'car-setup', label: 'Car Setup' });
        }

        if (this.tyreWearPredictionsAvailable) {
            tabs.push({ id: 'tyre-wear-prediction', label: 'Tyre Wear Prediction' });
        }

        // Sort tabs alphabetically based on the label
        tabs.sort((a, b) => a.id.localeCompare(b.id));

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
            { id: 'warns-pens-info', method: this.populateWarnsPensInfoTab },
            { id: 'collisions-info', method: this.populateCollisionsInfoTab },
            { id: 'tyre-sets', method: this.populateTyreSetsInfoTab },
            { id: 'player-info', method: this.populatePlayerInfoTab },
        ];

        if ('car-setup' in this.data) {
          tabs.push({ id: 'car-setup', method: this.populateCarSetupTab });
        }

        if (this.tyreWearPredictionsAvailable) {
            tabs.push({ id: 'tyre-wear-prediction', method: this.populateTyreWearPredictionTab });
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

    populateTableRows(tbody, rowsData) {
        rowsData.forEach((cellsData) => {
            const row = tbody.insertRow();
            this.populateTableRow(row, cellsData);
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
        rightDiv.className = 'w-50 border border-light-subtle rounded overflow-auto'; // Half width
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

    populateTelemetryDisabledMessage(tabPane) {
        // Create the alert container
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert d-flex justify-content-center align-items-center text-center mb-3';
        alertDiv.setAttribute('role', 'alert');

        // Create the icon
        const icon = document.createElement('i');
        icon.className = 'bi bi-exclamation-triangle-fill me-2';

        // Create the message span
        const message = document.createElement('span');
        message.textContent = 'Telemetry has been set to Restricted';

        // Combine icon and message
        alertDiv.appendChild(icon);
        alertDiv.appendChild(message);

        // Add to the tab pane
        tabPane.appendChild(alertDiv);
    }
}
