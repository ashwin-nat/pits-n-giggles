// Function to plot the graph with dark theme, truncated Y-axis values, and 30% excess
function plotGraph(canvas, datasets, xAxisLabel, yAxisLabel, formatAsLapTime = false, limits = null) {
    // Convert data to lap time format if specified
    const excessPerc = 0.2;
    if (formatAsLapTime) {
        datasets.forEach(dataset => {
            dataset.data.forEach(entry => {
                entry.lapTimeString = formatLapTime(entry.y); // Store lap time string for display
            });
        });
    }

    let xData = datasets[0].data.map(entry => entry.x);

    let yMinWithExcess, yMaxWithExcess;
    // Calculate the range of the data
    let yMin = Math.min(...datasets.reduce((acc, dataset) => acc.concat(dataset.data.map(entry => entry.y)), []));
    let yMax = Math.max(...datasets.reduce((acc, dataset) => acc.concat(dataset.data.map(entry => entry.y)), []));

    // Calculate the 30% excess
    let excess = (yMax - yMin) * excessPerc;

    // Adjust the minimum and maximum values for the Y-axis scale with excess
    if (limits !== null) {
        if (!("min" in limits) || limits["min"] === null) {
            yMinWithExcess = yMin - excess;
        } else {
            yMinWithExcess = limits["min"];
        }

        if (!("max" in limits) || limits["max"] === null) {
            yMaxWithExcess = yMax + excess;
        } else {
            yMaxWithExcess = limits["max"];
        }
    }

    let ctx = canvas.getContext('2d');
    let myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: xData,
            datasets: datasets.map(dataset => ({
                ...dataset,
                data: dataset.data.map(entry => entry.y), // Use numerical values for chart
                // label: formatAsLapTime ? dataset.label + " (Lap Time)" : dataset.label // Update label if formatting as lap time
                label: dataset.label
            }))
        },
        options: {
            scales: {
                x: {
                    type: 'linear',
                    scaleLabel: {
                        display: true,
                        labelString: xAxisLabel,
                        fontColor: 'rgba(255, 255, 255, 0.8)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        stepSize: 1, // Ensure each lap number is displayed
                        precision: 0 // Round to whole numbers
                    }
                },
                y: {
                    scaleLabel: {
                        display: true,
                        labelString: yAxisLabel,
                        fontColor: 'rgba(255, 255, 255, 0.8)'
                    },
                    beginAtZero: false,
                    min: yMinWithExcess,
                    max: yMaxWithExcess,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        callback: function (value, index, values) {
                            // Format tick values as lap time if formatting as lap time is enabled
                            return formatAsLapTime ? formatLapTime(value) : value.toFixed(3);
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top', // Place the legend on top
                    labels: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        boxWidth: 20,
                        padding: 15, // Add space between legend items
                        font: {
                            size: 14 // Adjust font size for better readability
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += formatAsLapTime ? formatLapTime(context.parsed.y) : context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            },
            layout: {
                padding: {
                    top: 10,
                    right: 10,
                    bottom: 10,
                    left: 10
                }
            },
            responsive: true
        }
    });
}