class CarTelemetryWidget {
    constructor() {
        this.initializeElements();
        this.initializeGraph();
    }

    initializeElements() {
        this.elements = {
            throttle: document.getElementById('throttleBar'),
            brake: document.getElementById('brakeBar'),
            steering: document.getElementById('steeringBar')
        };
    }

    initializeGraph() {
        const ctx = document.getElementById('inputGraph').getContext('2d');
        const maxDataPoints = 100;

        this.graphData = {
            throttle: Array(maxDataPoints).fill(0),
            brake: Array(maxDataPoints).fill(0),
            steering: Array(maxDataPoints).fill(0)
        };

        this.graph = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array(maxDataPoints).fill(''),
                datasets: [
                    {
                        label: 'Throttle',
                        data: this.graphData.throttle,
                        borderColor: '#00ff00',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: 'Brake',
                        data: this.graphData.brake,
                        borderColor: '#ff0000',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: 'Steering',
                        data: this.graphData.steering,
                        borderColor: '#ffff00',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {
                    mode: 'none',
                    enabled: false
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: true,
                        min: -100,
                        max: 100,
                        grid: {
                            color: context => {
                                const value = context.tick.value;
                                if (value === 0 || value === -50 || value === 50) {
                                    return 'rgba(255, 255, 255, 0.1)';
                                }
                                return 'transparent';
                            }
                        },
                        ticks: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            }
        });
    }

    updateGraph(data) {
        // Update data arrays
        this.graphData.throttle.push(this.#transformValue(data.throttle));
        this.graphData.throttle.shift();
        this.graphData.brake.push(this.#transformValue(data.brake));
        this.graphData.brake.shift();
        this.graphData.steering.push(data.steering);
        this.graphData.steering.shift();

        // Update chart datasets
        this.graph.data.datasets[0].data = [...this.graphData.throttle];
        this.graph.data.datasets[1].data = [...this.graphData.brake];
        this.graph.data.datasets[2].data = [...this.graphData.steering];

        this.graph.update('none');
    }

    updateBars(data) {
        // Update pedal bars
        this.elements.throttle.style.height = `${data.throttle}%`;
        this.elements.brake.style.height = `${data.brake}%`;

        // Update steering bar
        const barWidth = this.elements.steering.offsetWidth;
        const containerWidth = this.elements.steering.parentElement.offsetWidth;
        const maxOffset = (containerWidth - barWidth) / 2;
        const steeringOffset = (data.steering / 100) * maxOffset;
        this.elements.steering.style.transform = `translateX(calc(-50% + ${steeringOffset}%))`;
    }

    update(data) {
        this.updateBars(data);
        this.updateGraph(data);
    }

    #transformValue(value) {
        return (value * 2) - 100;
    }
}
