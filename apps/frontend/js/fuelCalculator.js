class FuelCalculator {
    constructor(container, lapsData, options = {}) {
        this.container = container;
        this.lapsData = lapsData;
        this.MIN_FUEL_LEVEL = options.MIN_FUEL_LEVEL || 0.2;
        this.FUEL_SAVING_PERCENT = options.FUEL_SAVING_PERCENT || 3;

        // UI elements that need to be updated
        this.selectedLapsInfo = null;
        this.avgFuelInfo = null;
        this.safetyCarBurnInfo = null;
        this.conservativeStrategy = null;
        this.aggressiveStrategy = null;
        this.inputs = {};
    }

    init() {
        this._render();
        this._bindEvents();
        this._update();
        this._initializeTooltips();
    }

    // Private helper methods for UI creation
    _createInputGroup(labelText, inputConfig, tooltip = null) {
        const group = document.createElement('div');
        group.className = 'fuel-calc-input-group';

        const label = document.createElement('label');
        label.textContent = labelText;
        if (tooltip) {
            label.setAttribute('data-bs-toggle', 'tooltip');
            label.setAttribute('data-bs-placement', 'top');
            label.setAttribute('title', tooltip);
        }

        const input = document.createElement('input');
        input.type = inputConfig.type || 'text';
        input.className = 'form-control form-control-sm';
        input.style.width = inputConfig.width || '70px';

        if (inputConfig.value !== undefined) input.value = inputConfig.value;
        if (inputConfig.min !== undefined) input.min = inputConfig.min;
        if (inputConfig.max !== undefined) input.max = inputConfig.max;
        if (inputConfig.step !== undefined) input.step = inputConfig.step;

        // Add input validation
        input.addEventListener('input', () => {
            const value = parseFloat(input.value);
            const isValidNumber = input.value === '' || (!isNaN(value) && isFinite(value) && input.value.trim() === value.toString());
            if (input.value !== '' && (!isValidNumber || value < 0)) {
                input.classList.add('fuel-calc-invalid');
            } else {
                input.classList.remove('fuel-calc-invalid');
            }
        });

        input.addEventListener('focus', () => {
            input.classList.remove('fuel-calc-invalid');
        });

        input.addEventListener('blur', () => {
            const value = parseFloat(input.value);
            const isValidNumber = input.value === '' || (!isNaN(value) && isFinite(value) && input.value.trim() === value.toString());
            if (input.value !== '' && (!isValidNumber || value < 0)) {
                input.classList.add('fuel-calc-invalid');
            }
        });

        group.appendChild(label);
        group.appendChild(input);
        return { group, input };
    }

    _createButton(text, className = 'btn btn-secondary btn-sm') {
        const button = document.createElement('button');
        button.textContent = text;
        button.className = `${className} fuel-calc-button`;
        return button;
    }

    _createInfoSpan(labelText, valueText = '0', unit = '') {
        const container = document.createElement('span');
        container.className = 'fuel-calc-info-span';

        const label = document.createElement('span');
        label.textContent = labelText;
        label.className = 'fuel-calc-label';

        const value = document.createElement('span');
        value.textContent = valueText;
        value.className = 'fuel-calc-value';

        const unitSpan = document.createElement('span');
        unitSpan.textContent = unit;
        unitSpan.className = 'fuel-calc-unit';

        container.appendChild(label);
        container.appendChild(value);
        container.appendChild(unitSpan);

        return { container, value };
    }

    _createStrategyCard(title, borderColor, tooltip) {
        const card = document.createElement('div');
        card.className = 'card fuel-calc-strategy-card';
        card.style.borderColor = borderColor;

        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';

        const titleElement = document.createElement('h6');
        titleElement.className = 'card-title';
        titleElement.textContent = title;
        if (tooltip) {
            titleElement.setAttribute('data-bs-toggle', 'tooltip');
            titleElement.setAttribute('data-bs-placement', 'top');
            titleElement.setAttribute('title', tooltip);
        }

        const valueSpan = document.createElement('div');
        valueSpan.className = 'fuel-calc-value';
        valueSpan.textContent = '0.00 kg';

        cardBody.appendChild(titleElement);
        cardBody.appendChild(valueSpan);
        card.appendChild(cardBody);

        return { card, valueSpan };
    }

    _createFuelTable(fuelUsageData, tableClassNames) {
        const table = document.createElement('table');
        table.className = tableClassNames;

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
        return table;
    }

    _initializeTooltips() {
        setTimeout(() => {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }, 100);
    }

    _render() {
        // Apply container styles
        this.container.className = 'fuel-calc-left-div-container';

        // Create fuel usage table
        const table = this._createFuelTable(this.lapsData, 'table table-striped table-dark table-sm');
        const tableContainer = document.createElement('div');
        tableContainer.className = 'fuel-calc-table-container';
        tableContainer.style.flex = '1';
        tableContainer.appendChild(table);
        this.container.appendChild(tableContainer);

        // Create fuel calculator header
        const calculatorHeader = document.createElement('div');
        calculatorHeader.className = 'fuel-calc-header';

        const calculatorTitle = document.createElement('h5');
        calculatorTitle.innerHTML = 'Fuel Strategy Calculator <i class="bi bi-chevron-double-up fuel-calc-chevron"></i>';
        calculatorHeader.appendChild(calculatorTitle);

        // Create collapsible wrapper
        const calculatorWrapper = document.createElement('div');
        calculatorWrapper.className = 'fuel-calc-wrapper';
        calculatorWrapper.style.maxHeight = '1000px'; // Start expanded

        // Create calculator container
        const calculatorContainer = document.createElement('div');
        calculatorContainer.className = 'fuel-calc-container';

        // Selection Controls Card
        const selectionCard = this._createSelectionCard();
        calculatorContainer.appendChild(selectionCard);

        // Race Parameters Card
        const paramsCard = this._createParamsCard();
        calculatorContainer.appendChild(paramsCard);

        // Strategies Container
        const strategiesContainer = this._createStrategiesContainer();
        calculatorContainer.appendChild(strategiesContainer);

        calculatorWrapper.appendChild(calculatorContainer);
        this.container.appendChild(calculatorHeader);
        this.container.appendChild(calculatorWrapper);

        // Store references for collapse functionality
        this.calculatorHeader = calculatorHeader;
        this.calculatorWrapper = calculatorWrapper;
        this.calculatorTitle = calculatorTitle;
    }

    _createSelectionCard() {
        const selectionCard = document.createElement('div');
        selectionCard.className = 'card fuel-calc-selection-card';

        const selectionCardBody = document.createElement('div');
        selectionCardBody.className = 'card-body';

        const selectionRow = document.createElement('div');
        selectionRow.className = 'fuel-calc-selection-row';

        const selectAllBtn = this._createButton('Select All');
        const selectNoneBtn = this._createButton('Clear');
        const resetBtn = this._createButton('Reset', 'btn btn-warning btn-sm');

        this.selectedLapsInfo = this._createInfoSpan('Selected: ', '0');
        this.avgFuelInfo = this._createInfoSpan('Avg: ', '0.00', ' kg/lap');
        this.safetyCarBurnInfo = this._createInfoSpan('SC: ', '0.00', ' kg/lap');

        selectionRow.appendChild(selectAllBtn);
        selectionRow.appendChild(selectNoneBtn);
        selectionRow.appendChild(resetBtn);
        selectionRow.appendChild(this.selectedLapsInfo.container);
        selectionRow.appendChild(this.avgFuelInfo.container);
        selectionRow.appendChild(this.safetyCarBurnInfo.container);

        selectionCardBody.appendChild(selectionRow);
        selectionCard.appendChild(selectionCardBody);

        // Store button references
        this.selectAllBtn = selectAllBtn;
        this.selectNoneBtn = selectNoneBtn;
        this.resetBtn = resetBtn;

        return selectionCard;
    }

    _createParamsCard() {
        const paramsCard = document.createElement('div');
        paramsCard.className = 'card fuel-calc-params-card';

        const paramsCardBody = document.createElement('div');
        paramsCardBody.className = 'card-body';

        const paramsRow = document.createElement('div');
        paramsRow.className = 'fuel-calc-params-row';

        // Create input groups
        this.inputs.raceLaps = this._createInputGroup('Race Laps:', { width: '80px', min: '1', step: '1' });
        this.inputs.surplusLaps = this._createInputGroup('Surplus Laps:', { value: '0.25', width: '70px', min: '0', step: '0.1' },
            'Surplus laps of fuel to be accounted for. This is for a safe buffer, recommended 0.25 laps');
        this.inputs.safetyCars = this._createInputGroup('Safety Cars:', { value: '0', width: '60px', min: '0', step: '1' });
        this.inputs.lapsPerSC = this._createInputGroup('Laps Per SC:', { value: '2', width: '60px', min: '1', step: '1' });
        this.inputs.scBurnRate = this._createInputGroup('SC Burn %:', { value: '70', width: '60px', min: '0', max: '100', step: '5' },
            'Safety car fuel burn rate as percentage of normal racing fuel consumption');
        this.inputs.fuelSaving = this._createInputGroup('Aggressive Fuel Saving %:', { value: `${this.FUEL_SAVING_PERCENT}`, width: '60px', min: '0', max: '50', step: '1' },
            'Percentage of fuel saving for aggressive strategy compared to average consumption. ' +
            'Typical fuel saving when lifting/coasting in heavy braking zone in free laps results in ~3%');

        Object.values(this.inputs).forEach(inputGroup => {
            paramsRow.appendChild(inputGroup.group);
        });

        paramsCardBody.appendChild(paramsRow);
        paramsCard.appendChild(paramsCardBody);

        return paramsCard;
    }

    _createStrategiesContainer() {
        const strategiesContainer = document.createElement('div');
        strategiesContainer.className = 'fuel-calc-strategies-container';

        this.conservativeStrategy = this._createStrategyCard('Conservative', '#28a745',
            'Fuel load calculated using current average fuel consumption with safety margins');
        this.aggressiveStrategy = this._createStrategyCard('Aggressive', '#dc3545',
            'Fuel load calculated assuming more efficient driving than current average');

        strategiesContainer.appendChild(this.conservativeStrategy.card);
        strategiesContainer.appendChild(this.aggressiveStrategy.card);

        return strategiesContainer;
    }

    _bindEvents() {
        // Selection button events
        this.selectAllBtn.onclick = () => {
            const checkboxes = document.querySelectorAll('.fuel-calc-checkbox:not(:disabled)');
            checkboxes.forEach(cb => cb.checked = true);
            this._update();
        };

        this.selectNoneBtn.onclick = () => {
            const checkboxes = document.querySelectorAll('.fuel-calc-checkbox');
            checkboxes.forEach(cb => cb.checked = false);
            this._update();
        };

        this.resetBtn.onclick = () => {
            // Reset all inputs to default values
            this.inputs.raceLaps.input.value = '';
            this.inputs.surplusLaps.input.value = '0.25';
            this.inputs.safetyCars.input.value = '0';
            this.inputs.lapsPerSC.input.value = '2';
            this.inputs.scBurnRate.input.value = '70';
            this.inputs.fuelSaving.input.value = `${this.FUEL_SAVING_PERCENT}`;

            // Clear all checkboxes
            const checkboxes = document.querySelectorAll('.fuel-calc-checkbox');
            checkboxes.forEach(cb => cb.checked = false);

            // Reset input validation styles
            Object.values(this.inputs).forEach(inputGroup => {
                inputGroup.input.classList.remove('fuel-calc-invalid');
            });

            this._update();
        };

        // Input change events
        Object.values(this.inputs).forEach(inputGroup => {
            inputGroup.input.addEventListener('input', () => this._update());
        });

        // Checkbox change events (will be bound when table is created)
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('fuel-calc-checkbox')) {
                this._update();
            }
        });

        // Collapse/expand functionality
        let isCollapsed = false;
        this.calculatorHeader.addEventListener('click', () => {
            isCollapsed = !isCollapsed;
            const chevron = this.calculatorTitle.querySelector('i');

            if (isCollapsed) {
                this.calculatorWrapper.style.maxHeight = '0px';
                chevron.className = 'bi bi-chevron-double-right fuel-calc-chevron';
            } else {
                this.calculatorWrapper.style.maxHeight = '1000px';
                chevron.className = 'bi bi-chevron-double-up fuel-calc-chevron';
            }
        });
    }

    _update() {
        const checkedBoxes = document.querySelectorAll('.fuel-calc-checkbox:checked');
        const selectedCount = checkedBoxes.length;
        this.selectedLapsInfo.value.textContent = selectedCount;

        if (selectedCount === 0) {
            this.avgFuelInfo.value.textContent = '0.00';
            this.safetyCarBurnInfo.value.textContent = '0.00';
            this.conservativeStrategy.valueSpan.textContent = '0.00 kg';
            this.aggressiveStrategy.valueSpan.textContent = '0.00 kg';
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
        this.avgFuelInfo.value.textContent = avgFuel.toFixed(2);

        // Calculate safety car fuel burn
        const scBurnRate = parseFloat(this.inputs.scBurnRate.input.value) / 100 || 0.7;
        const safetyCarBurn = avgFuel * scBurnRate;
        this.safetyCarBurnInfo.value.textContent = safetyCarBurn.toFixed(2);

        // Calculate fuel strategies
        const raceLaps = parseInt(this.inputs.raceLaps.input.value) || 0;
        const surplusLaps = parseFloat(this.inputs.surplusLaps.input.value) || 0;
        const numSafetyCars = parseInt(this.inputs.safetyCars.input.value) || 0;
        const lapsPerSC = parseInt(this.inputs.lapsPerSC.input.value) || 2;

        if (raceLaps > 0) {
            // Calculate safety car laps
            const totalSCLaps = numSafetyCars * lapsPerSC;
            const normalLaps = raceLaps - totalSCLaps;

            // Conservative strategy
            const conservativeNormalFuel = normalLaps * avgFuel;
            const conservativeSCFuel = totalSCLaps * safetyCarBurn;
            const conservativeSurplusFuel = surplusLaps * avgFuel;
            const conservativeFuel = conservativeNormalFuel + conservativeSCFuel + conservativeSurplusFuel + this.MIN_FUEL_LEVEL;
            this.conservativeStrategy.valueSpan.textContent = conservativeFuel.toFixed(2) + ' kg';

            // Aggressive strategy
            const fuelSavingPercent = parseFloat(this.inputs.fuelSaving.input.value) || this.FUEL_SAVING_PERCENT;
            const aggressiveFuelPerLap = avgFuel * (1 - fuelSavingPercent / 100);
            const aggressiveNormalFuel = normalLaps * aggressiveFuelPerLap;
            const aggressiveSCFuel = totalSCLaps * (aggressiveFuelPerLap * scBurnRate);
            const aggressiveSurplusFuel = surplusLaps * aggressiveFuelPerLap;
            const aggressiveFuel = aggressiveNormalFuel + aggressiveSCFuel + aggressiveSurplusFuel + this.MIN_FUEL_LEVEL;
            this.aggressiveStrategy.valueSpan.textContent = aggressiveFuel.toFixed(2) + ' kg';
        } else {
            this.conservativeStrategy.valueSpan.textContent = '0.00 kg';
            this.aggressiveStrategy.valueSpan.textContent = '0.00 kg';
        }
    }
}
