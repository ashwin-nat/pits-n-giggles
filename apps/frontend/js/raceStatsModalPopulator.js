class RaceStatsModalPopulator {
    constructor(data, iconCache) {
        this.data = data;
        this.tableClassNames = 'table table-bordered table-striped table-dark table-sm align-middle';
        this.iconCache = iconCache;
        this.defaultColors = [
            'rgba(75, 192, 192, 1)',   // Teal
            'rgba(255, 99, 132, 1)',   // Red
            'rgba(54, 162, 235, 1)',   // Blue
            'rgba(255, 206, 86, 1)',   // Yellow
            'rgba(153, 102, 255, 1)',  // Purple
            'rgba(255, 159, 64, 1)',   // Orange
            'rgba(199, 199, 199, 1)',  // Gray
            'rgba(255, 99, 71, 1)',    // Tomato
            'rgba(60, 179, 113, 1)',   // Medium Sea Green
            'rgba(123, 104, 238, 1)',  // Medium Slate Blue
            'rgba(0, 128, 128, 1)',    // Teal
            'rgba(240, 128, 128, 1)',  // Light Coral
            'rgba(75, 0, 130, 1)',     // Indigo
            'rgba(250, 128, 114, 1)',  // Salmon
            'rgba(34, 139, 34, 1)',    // Forest Green
            'rgba(255, 215, 0, 1)',    // Gold
            'rgba(0, 191, 255, 1)',    // Deep Sky Blue
            'rgba(219, 112, 147, 1)',  // Pale Violet Red
            'rgba(46, 139, 87, 1)',    // Sea Green
            'rgba(139, 69, 19, 1)',    // Saddle Brown
            'rgba(255, 140, 0, 1)',    // Dark Orange
            'rgba(72, 61, 139, 1)'     // Dark Slate Blue
        ];
    }

    // Method to create the navigation tabs
    createNavTabs() {
        const navTabs = document.createElement('ul');
        navTabs.className = 'nav nav-tabs driver-modal-nav inactive';
        navTabs.setAttribute('role', 'tablist');
        navTabs.setAttribute('data-bs-theme', 'dark');

        // Array of tabs with ID and label
        const tabs = [
            { id: 'lap-time-records', label: 'Lap Time Records' },
            { id: 'tyre-stint-records', label: 'Tyre Stint Records' },
            { id: 'custom-markers', label: 'Custom Markers' },
            { id: 'position-history', label: 'Position History' },
            { id: 'tyre-stint-history', label: 'Tyre Stint History' },
            { id: 'speed-trap-records', label: 'Speed Trap Records' },
            { id: 'race-control-messages', label: 'Race Control Messages' },
        ];

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

    createTabContent() {
        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content driver-modal-tab-content h-100'; /* Add h-100 to make it fill height */

        // Array of tabs with ID and method to populate content
        const tabs = [
            { id: 'lap-time-records', method: this.populateLapTimeRecordsTab },
            { id: 'tyre-stint-records', method: this.populateTyreStintRecordsTab },
            { id: 'custom-markers', method: this.populateCustomMarkersTab },
            { id: 'position-history', method: this.populatePositionHistoryTab },
            { id: 'tyre-stint-history', method: this.populateTyreStintHistoryTab },
            { id: 'speed-trap-records', method: this.populateSpeedTrapRecordsTab },
            { id: 'race-control-messages', method: this.populateRaceControlMessagesTabWrapper },
        ];

        // Sort tabs alphabetically based on the label
        tabs.sort((a, b) => a.id.localeCompare(b.id));

        tabs.forEach((tab, index) => {
            const tabPane = document.createElement('div');
            tabPane.className = `tab-pane fade driver-modal-tab-pane ${index === 0 ? 'show active' : ''}`;
            tabPane.id = tab.id;
            tabPane.setAttribute('role', 'tabpanel');
            tabPane.setAttribute('aria-labelledby', `${tab.id}-tab`);

            // Populate the tab content using the respective method
            tab.method.call(this, tabPane);

            tabContent.appendChild(tabPane);
        });

        return tabContent;
    }

    populateLapTimeRecordsTab(tabPane) {

        const containerDiv = document.createElement('div');
        const records = new F1LapSectorRecords(containerDiv);
        records.update(this.data["records"]["fastest"]);
        tabPane.appendChild(containerDiv);
    }

    populateCustomMarkersTab(tabPane) {

        const containerDiv = document.createElement('div');
        containerDiv.className = 'd-flex table-responsive';

        const table = document.createElement('table');
        table.className = this.tableClassNames;

        // Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const headers = [
            'Index',
            'Event',
            'Track',
            'Sector',
            'Lap',
            'Lap Time',
            'Lap Percent',
        ];

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const customMarkersTableBody = document.createElement('tbody');
        if ("custom-markers" in this.data && this.data["custom-markers"].length > 0) {

            this.data["custom-markers"].forEach(function (marker, index) {
                const row = customMarkersTableBody.insertRow();
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${marker["event-type"]}</td>
                    <td>${marker["track"]}</td>
                    <td>${marker["sector"]}</td>
                    <td>${marker["lap"]}</td>
                    <td>${marker["curr-lap-time"]}</td>
                    <td>${marker["curr-lap-percentage"]}</td>
                `;
            });

        } else {
            const row = customMarkersTableBody.insertRow();
            row.innerHTML = '<td colspan="7">Custom Markers data not available</td>';
        }

        table.appendChild(customMarkersTableBody);
        containerDiv.appendChild(table);
        tabPane.appendChild(containerDiv);
    }

    populateTyreStintRecordsTab(tabPane) {

        const containerDiv = document.createElement('div');
        const records = new F1TyreRecords(containerDiv, this.iconCache);
        records.update(this.data["records"]["tyre-stats"]);
        tabPane.appendChild(containerDiv);
    }

    populatePositionHistoryTab(tabPane) {

        const positionHistoryGraphSubDiv = document.createElement('div');

        if ("position-history" in this.data && this.data["position-history"].length > 0) {

            const positionHistoryArray = this.data["position-history"];
            const leaderPositionHistory = positionHistoryArray[0];
            const totalLaps = leaderPositionHistory["driver-position-history"][leaderPositionHistory["driver-position-history"].length - 1]["lap-number"];

            let lapList = [];
            for (let i = 0; i <= totalLaps; i++) {
                lapList.push(i);
            }

            let datasets = [];
            positionHistoryArray.forEach((driverInfo) => {

                const name = driverInfo["name"];
                const team = getTeamName(driverInfo["team"]);
                const driverPositionHistory = driverInfo["driver-position-history"];
                let positionHistoryArray = [];
                driverPositionHistory.forEach((perLapRecord) => {
                    positionHistoryArray.push({ x: perLapRecord["lap-number"], y: perLapRecord["position"] });
                });
                datasets.push({
                    label: getTLA(name),
                    data: positionHistoryArray,
                    borderColor: this.getF1TeamColor(team)
                });
                if (datasets[datasets.length - 1].borderColor === null) {
                    console.log("Could not find colour", driverInfo);
                }
            });

            if (datasets.length > 0) {
                // Create graph canvas
                const graphDiv = document.createElement('div');
                const elementId = 'positionHistoryGraph';
                const graphCanvas = document.createElement('canvas');
                graphDiv.appendChild(graphCanvas);
                graphCanvas.id = elementId;
                graphDiv.classList.add('chart-container');

                // Plot graph
                this.plotGraphPositionHistory(graphCanvas, datasets, 'Lap number', 'Position');
                positionHistoryGraphSubDiv.appendChild(graphDiv);
            }
        }
        tabPane.appendChild(positionHistoryGraphSubDiv);
    }

    populateTyreStintHistoryTab(tabPane) {

        if (this.data["session-info"] == null) {
            this.showDataNotAvailableMessage(tabPane, "Tyre stint history data not available");
            return;
        }

        let data, isNewStyle;
        if ("tyre-stint-history" in this.data && this.data["tyre-stint-history"].length > 0) {
            data = this.data["tyre-stint-history"];
            isNewStyle = false;
        } else if ("tyre-stint-history-v2" in this.data && this.data["tyre-stint-history-v2"].length > 0) {
            data = this.data["tyre-stint-history-v2"];
            isNewStyle = true;
        } else {
            console.log("Tyre Stint History data not available");
            return;
        }
        // Initialize the chart
        const tyreStintHistoryGraphSubDiv = document.createElement('div');
        const chart = new TyreStintChart(tyreStintHistoryGraphSubDiv, {
            height: 25,
            gap: 5,
            padding: 20,
            totalLaps: this.data["session-info"]["total-laps"],
            trackName: this.data["session-info"]["track-id"],
            airTemp: this.data["session-info"]["air-temperature"],
            trackTemp: this.data["session-info"]["track-temperature"],
            isNewStyle: isNewStyle,
            }, this.iconCache);


        chart.updateChart(data);
        tabPane.appendChild(tyreStintHistoryGraphSubDiv);
    }

    populateSpeedTrapRecordsTab(tabPane) {

        const speedTrapRecords = this.data["speed-trap-records"] ?? [];
        if (speedTrapRecords.length == 0) {
            this.showDataNotAvailableMessage(tabPane, "Speed Trap Records data not available");
            return;
        }

        const chartDiv = document.createElement('div');
        chartDiv.className = 'bar-chart-container h-100 d-flex flex-column';
        const chart = new BarChart(chartDiv);
        let chartData = [];
        const unit = g_pref_speedUnitMetric ? "km/h" : "mph";
        this.data["speed-trap-records"].forEach((record) => {
            chartData.push({ label: record["name"], value: this.getSpeedInCustomUnit(record["speed-trap-record-kmph"]),
                             color: this.getF1TeamColor(record["team"]) });
        });
        chart.render(chartData, {
            title: "Speed Trap Records",
            xLabel: "Driver",
             yLabel: `Speed (${unit})`,
        });

        tabPane.appendChild(chartDiv);
    }

    populateRaceControlMessagesTabWrapper(tabPane) {
        const messages = this.data["race-control"] ?? [];
        if (messages.length === 0) {
            this.showDataNotAvailableMessage(tabPane, "Race Control Messages data not available");
            return;
        }

        // Call the globally accessible function, passing the data
        if (window.populateRaceControlMessagesTab) {
            window.populateRaceControlMessagesTab(tabPane, messages);
        } else {
            console.error('populateRaceControlMessagesTab function not found.');
            this.showDataNotAvailableMessage(tabPane, "Race Control Messages grid could not be loaded.");
        }
    }

    // Utils
    populateTableRow(row, cellsData) {
        cellsData.forEach((cellData) => {
            const cell = document.createElement('td');
            cell.textContent = cellData;
            row.appendChild(cell);
        });
    }

    isFastestRecordAvailable(data) {

        if ("records" in data &&
            'fastest' in data["records"] &&
            data["records"]["fastest"]["lap"] != null &&
            data["records"]["fastest"]["s1"] != null &&
            data["records"]["fastest"]["s2"] != null &&
            data["records"]["fastest"]["s3"] != null) {
            return true;
        }
        return false;
    }

    insertFastestRow(data, timesRecordsTableBody, category, searchKey) {

        const fastestLapTime = data["records"]["fastest"][searchKey]["time-str"];
        const fastestLapNum = data["records"]["fastest"][searchKey]["lap-number"];
        const driverName = data["records"]["fastest"][searchKey]["driver-name"];
        const teamName = getTeamName(data["records"]["fastest"][searchKey]["team-id"]);
        const row = timesRecordsTableBody.insertRow();
        row.innerHTML = `
            <td>${category}</td>
            <td>${driverName}</td>
            <td>${teamName}</td>
            <td>${fastestLapNum}</td>
            <td>${fastestLapTime}</td>
        `;
    }

    insertTyreStintRecordRow(tyreStintRecordsTableBody, compound, compoundRecords) {

        const longestTyreStintDriverName = compoundRecords["longest-tyre-stint"]["driver-name"];
        const longestTyreStintLength = compoundRecords["longest-tyre-stint"]["value"];

        const lowestTyreWearPerLapDriverName = compoundRecords["lowest-tyre-wear-per-lap"]["driver-name"];
        const lowestTyreWearPerLap = compoundRecords["lowest-tyre-wear-per-lap"]["value"];

        const highestTyreWearDriverName = compoundRecords["highest-tyre-wear"]["driver-name"];
        const highestTyreWear = compoundRecords["highest-tyre-wear"]["value"];

        const row1 = tyreStintRecordsTableBody.insertRow();
        const compoundCell1 = row1.insertCell();
        compoundCell1.textContent = compound;
        compoundCell1.setAttribute('rowspan', '3'); // Merge cells vertically

        row1.insertCell().textContent = 'Longest Stint';
        row1.insertCell().textContent = longestTyreStintDriverName;
        row1.insertCell().textContent = longestTyreStintLength + " laps";

        const row2 = tyreStintRecordsTableBody.insertRow();
        row2.insertCell().textContent = 'Least Tyre Wear Per Lap';
        row2.insertCell().textContent = lowestTyreWearPerLapDriverName;
        row2.insertCell().textContent = formatFloat(lowestTyreWearPerLap) + "%";

        const row3 = tyreStintRecordsTableBody.insertRow();
        row3.insertCell().textContent = 'Highest Tyre Wear';
        row3.insertCell().textContent = highestTyreWearDriverName;
        row3.insertCell().textContent = formatFloat(highestTyreWear) + "%";
    }

    isObjectEmpty(obj) {
        return obj && Object.keys(obj).length === 0 && obj.constructor === Object;
    }

    getF1TeamColor(teamName) {
        //source: https://www.reddit.com/r/formula1/comments/1avhmjb/f1_2024_hex_codes/
        const teamColors = {
            'Red Bull Racing': 'rgba(54,113,198, 1)',   // Blue
            'Red Bull': 'rgba(54,113,198, 1)',          // Blue

            'VCARB': 'rgba(102,146,255, 1)',            // Blue
            'RB': 'rgba(102,146,255, 1)',              // Blue

            'Mercedes': 'rgba(39,244,210, 1)',          // Teal
            'Ferrari': 'rgba(232,0,45, 1)',             // Red
            'McLaren': 'rgba(255,128,0, 1)',            // Papaya Orange
            'Mclaren': 'rgba(255,128,0, 1)',            // Papaya Orange
            'Aston Martin': 'rgba(34,153,113, 1)',      // Green
            'Alpine': 'rgba(255,135,188, 1)',           // Blue
            'Alpha Tauri': 'rgba(30, 40, 80, 1)',       // Dark Blue
            'Alfa Romeo': 'rgba(155, 0, 0, 1)',         // Dark Red
            'Haas': 'rgba(182,186,189, 1)',             // White/Silver
            'Williams': 'rgba(100,196,255, 1)',         // Blue
            'Sauber': 'rgba(82,226,82,1)',              // Fresh Green
        };


        if (teamName in teamColors) {
            return teamColors[teamName];
        }

        // Fallback: return random default color
        const randomIndex = Math.floor(Math.random() * this.defaultColors.length);
        return this.defaultColors[randomIndex];
    }

    plotGraphPositionHistory(canvas, datasets, xAxisLabel, yAxisLabel) {
        const ctx = canvas.getContext('2d');

        // Find the maximum x value across all datasets
        const maxX = Math.max(...datasets.flatMap(dataset => dataset.data.map(entry => entry.x)));

        // Define a custom plugin for labeling at the end of the line
        const endLabelPlugin = {
            id: 'endLabelPlugin',
            afterDatasetsDraw(chart, args, plugins) {
                const { ctx, data } = chart;
                ctx.save();

                data.datasets.forEach((dataset, index) => {
                    const meta = chart.getDatasetMeta(index);
                    if (!meta.hidden && dataset.data.length > 0) {
                        // Use the last actual data point for label positioning
                        const lastPoint = meta.data[dataset.data.length - 1];

                        // Only draw label if we have valid coordinates
                        if (lastPoint && typeof lastPoint.y === 'number') {
                            // Use the custom line color for the label text or default color
                            ctx.fillStyle = dataset.borderColor;
                            ctx.font = 'bold 16px sans-serif';
                            ctx.textAlign = 'left';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(dataset.label, lastPoint.x + 10, lastPoint.y);
                        }
                    }
                });

                ctx.restore();
            }
        };

        // Process datasets to maintain individual lengths
        const processedDatasets = datasets.map((dataset, index) => ({
            ...dataset,
            data: dataset.data.map(entry => ({x: entry.x, y: entry.y})), // Preserve x,y format
            label: dataset.label,
            borderColor: dataset.borderColor,
            backgroundColor: dataset.backgroundColor || this.defaultColors[index % this.defaultColors.length].replace('1)', '0.2)'),
            borderWidth: 2,
            spanGaps: false, // Don't connect points across gaps
        }));

        // Create the chart with the plugin included
        let myChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: processedDatasets
            },
            options: {
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: xAxisLabel,
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                size: 16
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            stepSize: 1,
                            precision: 0
                        },
                        max: maxX // Set maximum x value
                    },
                    y: {
                        title: {
                            display: true,
                            text: yAxisLabel,
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                size: 16
                            }
                        },
                        beginAtZero: false,
                        min: 0,
                        max: Math.max(...datasets.flatMap(dataset => dataset.data.map(entry => entry.y))) + 1,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.2)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            stepSize: 5,
                            callback: function(value) {
                                return value % 5 === 0 ? value : null;
                            }
                        },
                        reverse: true
                    }
                },
                hover: {
                    mode: 'nearest',
                    intersect: false
                },
                onHover: function(event, activeElements) {
                    const chartArea = myChart.chartArea;
                    const mouseX = event.native.clientX;
                    const mouseY = event.native.clientY;

                    if (mouseX < chartArea.left || mouseX > chartArea.right ||
                        mouseY < chartArea.top || mouseY > chartArea.bottom) {
                        // Reset all lines when mouse leaves the chart area
                        myChart.data.datasets.forEach((dataset) => {
                            dataset.borderWidth = 2;
                            dataset.borderColor = dataset.borderColor.replace('0.3)', '1)');
                            dataset.shadowBlur = 0;
                        });
                        myChart.update();
                        return;
                    }

                    const activeDatasetIndex = activeElements.length ? activeElements[0].datasetIndex : null;

                    myChart.data.datasets.forEach((dataset, index) => {
                        if (index === activeDatasetIndex) {
                            dataset.borderWidth = 6;
                            dataset.borderColor = dataset.borderColor.replace('0.3)', '1)');
                            dataset.shadowBlur = 10;
                            dataset.shadowColor = 'rgba(0, 0, 0, 0.8)';
                        } else {
                            dataset.borderWidth = 2;
                            dataset.borderColor = dataset.borderColor.replace('1)', '0.3)');
                            dataset.shadowBlur = 0;
                        }
                    });

                    myChart.update();
                },
                plugins: {
                    legend: {
                        display: false
                    }
                },
                layout: {
                    padding: {
                        top: 10,
                        right: 75,
                        bottom: 10,
                        left: 10
                    }
                },
                responsive: true,
                maintainAspectRatio: false,
            },
            plugins: [endLabelPlugin]
        });
    }

    showDataNotAvailableMessage(tabPane, text) {
        // Create the alert container
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert d-flex justify-content-center align-items-center text-center mb-3';
        alertDiv.setAttribute('role', 'alert');

        // Create the message span
        const message = document.createElement('span');
        message.textContent = text;

        // Combine icon and message
        alertDiv.appendChild(message);

        // Add to the tab pane
        tabPane.appendChild(alertDiv);
    }

    getSpeedInCustomUnit(speedKmph) {
        return g_pref_speedUnitMetric ? speedKmph : speedKmph * 0.621371;
    }
}