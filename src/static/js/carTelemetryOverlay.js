export class CarTelemetryWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container with id '${containerId}' not found`);
        }
        this.initializeElements();
        this.initializeChart();
    }

    initializeElements() {
        this.elements = {
            throttle: document.getElementById('throttleBar'),
            brake: document.getElementById('brakeBar'),
            steering: document.getElementById('steeringBar'),
            chart: document.getElementById('throttleBrakeChart')
        };
    }

    initializeChart() {
        const maxDataPoints = 50;
        const defaultData = Array(maxDataPoints).fill(0);

        this.chart = new Chart(this.elements.chart, {
            type: 'line',
            data: {
                labels: Array(maxDataPoints).fill(''),
                datasets: [
                    {
                        // throttle
                        data: [...defaultData],
                        borderColor: 'rgb(0, 255, 0)', // Green for throttle
                        tension: 0.4,
                        fill: false,
                        pointRadius: 0, // Removes the points (circles)
                        hoverRadius: 0, // Removes the hover effect on points
                        hoverBackgroundColor: 'transparent', // Ensure no hover color is shown
                        yAxisID: 'y1', // Use the first Y-axis for throttle
                    },
                    {
                        // brake
                        data: [...defaultData],
                        borderColor: 'rgb(255, 0, 0)', // Red for brake
                        tension: 0.4,
                        fill: false,
                        pointRadius: 0,
                        hoverRadius: 0,
                        hoverBackgroundColor: 'transparent',
                        yAxisID: 'y1', // Use the first Y-axis for brake
                    },
                    {
                        // steering
                        data: [...defaultData],
                        borderColor: 'rgb(255, 205, 86)', // Yellow for steering
                        tension: 0.4,
                        fill: false,
                        pointRadius: 0,
                        hoverRadius: 0,
                        hoverBackgroundColor: 'transparent',
                        yAxisID: 'y2', // Use the second Y-axis for steering
                    }
                ]
            },
            options: {
                responsive: true,
                animation: { duration: 0 },
                scales: {
                    y1: {
                        min: 0,
                        max: 100,
                        position: 'left',
                        grid: { display: false },
                        ticks: { display: false }
                    },
                    y2: {
                        min: -100,
                        max: 100,
                        position: 'right',
                        grid: { display: false },
                        ticks: { display: false }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }, // Disable the tooltip plugin
                },
                interaction: {
                    mode: null, // Disables interaction
                    intersect: false, // Prevents hover interactions
                },
                elements: {
                    line: {
                        tension: 0.4 // Ensures the line has a smooth curve
                    }
                }
            }
        });
    }

    updateChart(data) {
        this.chart.data.datasets.forEach((dataset, index) => {
            dataset.data.shift();
            dataset.data.push(
                index === 0 ? data.throttle :
                    index === 1 ? data.brake :
                        data.steering
            );
        });
        this.chart.update('none');
    }

    updateBars(data) {
        this.elements.throttle.style.height = `${data.throttle}%`;
        this.elements.brake.style.height = `${data.brake}%`;
        const barWidth = this.elements.steering.offsetWidth;
        // Subtract half the bar width to align its center with the center line
        const steeringOffset = (data.steering / 100) * 50 - (barWidth / 2);
        this.elements.steering.style.transform = `translateX(${steeringOffset}px)`;
    }


    update(data) {
        this.updateChart(data);
        this.updateBars(data);
    }
}
