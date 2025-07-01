class BarChart {
    constructor(container) {
        // Validate container input
        if (!container || !(container instanceof HTMLElement)) {
            throw new Error('Container must be a valid DOM element');
        }

        this.container = container;
        this.chart = null;
        this.canvas = null;
    }

    /**
     * Renders a bar chart with the provided data and options
     * @param {Array} data - Array of data objects [{label: string, value: number, color?: string}]
     * @param {Object} options - Chart configuration options (optional)
     * @param {string} options.title - Chart title (optional)
     * @param {number} options.bufferPercent - Buffer percentage for y-axis (default: 10)
     * @param {string} options.defaultColor - Default bar color (default: '#3498db')
     * @param {Object} options.styling - Additional styling options (optional)
     */
    render(data, options) {
        options = options || {};

        // Validate data input
        if (!data || !Array.isArray(data) || data.length === 0) {
            throw new Error('Data must be a non-empty array');
        }

        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
        }

        // Clear container content
        this.container.innerHTML = '';

        // Set default options
        const config = {
            title: options.title || '',
            bufferPercent: options.bufferPercent || 10,
            defaultColor: options.defaultColor || '#3498db',
            styling: options.styling || {}
        };

        // Merge options into config
        for (const key in options) {
            if (options.hasOwnProperty(key)) {
                config[key] = options[key];
            }
        }

        // Create canvas element
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'bar-chart-canvas';

        // Apply custom styling to canvas if provided
        if (config.styling.canvasStyle) {
            for (var styleKey in config.styling.canvasStyle) {
                if (config.styling.canvasStyle.hasOwnProperty(styleKey)) {
                    this.canvas.style[styleKey] = config.styling.canvasStyle[styleKey];
                }
            }
        }

        this.container.appendChild(this.canvas);

        // Prepare chart data
        const chartData = this._prepareChartData(data, config);

        // Calculate dynamic y-axis range
        const yAxisConfig = this._calculateYAxisRange(data, config.bufferPercent);

        // Create chart configuration
        const chartConfig = {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                categoryPercentage: 0.6, // Make bars less wide
                barPercentage: 0.9, // Make individual bars less wide
                plugins: {
                    title: {
                        display: !!config.title,
                        text: config.title,
                        font: {
                            size: 18,
                            weight: 'bold'
                        },
                        color: config.styling.titleColor || '#ffffff', // White text for visibility
                        padding: {
                            top: 10,
                            bottom: 20
                        }
                    },
                    legend: {
                        display: false // Hide legend for single dataset
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#fff',
                        borderWidth: 1,
                        cornerRadius: 6,
                        displayColors: false,
                        callbacks: {
                            label: function (context) {
                                return 'Value: ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    y: this._mergeObjects(yAxisConfig, {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.2)', // Light grid lines for visibility
                            borderColor: 'rgba(255, 255, 255, 0.5)',
                            lineWidth: 1
                        },
                        ticks: {
                            color: config.styling.axisColor || '#ffffff', // White text
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 8
                        },
                        border: {
                            color: 'rgba(255, 255, 255, 0.5)'
                        }
                    }),
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: config.styling.axisColor || '#ffffff', // White text
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            maxRotation: 45,
                            minRotation: 0,
                            padding: 8
                        },
                        border: {
                            color: 'rgba(255, 255, 255, 0.5)'
                        }
                    }
                },
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        };

        // Apply additional chart options if provided
        if (config.styling.chartOptions) {
            this._mergeDeep(chartConfig.options, config.styling.chartOptions);
        }

        // Create the chart
        this.chart = new Chart(this.canvas, chartConfig);

        return this.chart;
    }

    /**
     * Updates the chart with new data
     * @param {Array} newData - New data array
     * @param {Object} options - Update options (optional)
     */
    updateData(newData, options) {
        options = options || {};

        if (!this.chart) {
            throw new Error('Chart must be rendered before updating data');
        }

        const config = {
            bufferPercent: options.bufferPercent || 10,
            defaultColor: options.defaultColor || '#3498db'
        };

        // Merge options into config
        for (const key in options) {
            if (options.hasOwnProperty(key)) {
                config[key] = options[key];
            }
        }

        // Update chart data
        const chartData = this._prepareChartData(newData, config);
        this.chart.data = chartData;

        // Update y-axis range
        const yAxisConfig = this._calculateYAxisRange(newData, config.bufferPercent);
        this.chart.options.scales.y = this._mergeObjects(this.chart.options.scales.y, yAxisConfig);

        // Update chart
        this.chart.update('active');
    }

    /**
     * Destroys the chart and cleans up resources
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        if (this.canvas) {
            this.canvas.remove();
            this.canvas = null;
        }
    }

    /**
     * Prepares data for Chart.js format
     * @private
     */
    _prepareChartData(data, config) {
        const labels = [];
        const values = [];
        const colors = [];

        for (let i = 0; i < data.length; i++) {
            labels.push(data[i].label);
            values.push(data[i].value);
            colors.push(data[i].color || config.defaultColor);
        }

        const borderColors = [];
        const hoverBackgroundColors = [];
        const hoverBorderColors = [];

        for (let j = 0; j < colors.length; j++) {
            borderColors.push(this._darkenColor(colors[j], 0.2));
            hoverBackgroundColors.push(this._lightenColor(colors[j], 0.1));
            hoverBorderColors.push(this._darkenColor(colors[j], 0.3));
        }

        return {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 4,
                borderSkipped: false,
                hoverBackgroundColor: hoverBackgroundColors,
                hoverBorderColor: hoverBorderColors,
                hoverBorderWidth: 3
            }]
        };
    }

    /**
     * Calculates dynamic y-axis range with buffer
     * @private
     */
    _calculateYAxisRange(data, bufferPercent) {
        const values = [];
        for (let i = 0; i < data.length; i++) {
            values.push(data[i].value);
        }

        const minValue = Math.min.apply(Math, values);
        const maxValue = Math.max.apply(Math, values);

        const range = maxValue - minValue;
        const buffer = range * (bufferPercent / 100);

        // Calculate suggested min and max with buffer
        const suggestedMin = minValue - buffer;
        const suggestedMax = maxValue + buffer;

        // Ensure min doesn't go below 0 if all values are positive
        if (minValue >= 0 && suggestedMin < 0) {
            suggestedMin = 0;
        }

        return {
            beginAtZero: minValue >= 0,
            suggestedMin: suggestedMin,
            suggestedMax: suggestedMax
        };
    }

    /**
     * Darkens a given color by a specified factor.
     *
     * This function uses the tinycolor2 library to parse any valid CSS color input
     * (e.g., hex, rgb, rgba, hsl, named colors) and returns a darker version of that color.
     *
     * @param {string} color - The input color to darken. Can be any valid CSS color string.
     * @param {number} factor - A value between 0 and 1 representing how much to darken the color.
     *                          0 = no change, 1 = full black.
     * @returns {string} A hex color string (e.g., "#335577") representing the darkened color.
     */
    _darkenColor(color, factor) {
        // Create a tinycolor object from the input color
        const tc = tinycolor(color);

        // tinycolor.darken expects a percentage between 0–100,
        // so we multiply our 0–1 factor by 100 to match its API.
        const darkened = tc.darken(factor * 100);

        // Return the resulting color as a 6-digit hex string
        return darkened.toHexString();
    }

    /**
     * Lightens a color by a given factor
     * @private
     */
    _lightenColor(color, factor) {
        var hex = color.replace('#', '');
        var r = parseInt(hex.substr(0, 2), 16);
        var g = parseInt(hex.substr(2, 2), 16);
        var b = parseInt(hex.substr(4, 2), 16);

        var newR = Math.round(r + (255 - r) * factor);
        var newG = Math.round(g + (255 - g) * factor);
        var newB = Math.round(b + (255 - b) * factor);

        return '#' + newR.toString(16).padStart(2, '0') + newG.toString(16).padStart(2, '0') + newB.toString(16).padStart(2, '0');
    }

    /**
     * Merge two objects
     * @private
     */
    _mergeObjects(target, source) {
        var result = {};

        // Copy target properties
        for (var key in target) {
            if (target.hasOwnProperty(key)) {
                result[key] = target[key];
            }
        }

        // Copy source properties (overwriting target)
        for (var key in source) {
            if (source.hasOwnProperty(key)) {
                result[key] = source[key];
            }
        }

        return result;
    }

    /**
     * Deep merge objects
     * @private
     */
    _mergeDeep(target, source) {
        for (var key in source) {
            if (source.hasOwnProperty(key)) {
                if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                    if (!target[key]) target[key] = {};
                    this._mergeDeep(target[key], source[key]);
                } else {
                    target[key] = source[key];
                }
            }
        }
        return target;
    }
}
