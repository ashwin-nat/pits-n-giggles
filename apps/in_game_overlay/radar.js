class F1Radar {
    constructor(element) {
        this.element = element;
        this.width = element.offsetWidth;
        this.height = element.offsetHeight;
        this.centerX = this.width / 2;
        this.centerY = this.height / 2;
        this.carElements = {};

        this.init();
        this.setupResizeObserver();

        // For demo - remove this when integrating with real data
        // this.startDemo();
    }

    init() {
        this.element.innerHTML = '';
        this.createRadarGrid();
    }

    createRadarGrid() {
        const gridElement = document.createElement('div');
        gridElement.className = 'radar-grid';

        // Create circles
        for (let i = 1; i <= 4; i++) {
            const circle = document.createElement('div');
            circle.className = 'radar-grid-circle';
            const size = (i / 4) * 100;
            circle.style.width = `${size}%`;
            circle.style.height = `${size}%`;
            circle.style.top = `${(100 - size) / 2}%`;
            circle.style.left = `${(100 - size) / 2}%`;
            gridElement.appendChild(circle);
        }

        // Add crosshair
        const horizontal = document.createElement('div');
        horizontal.className = 'radar-grid-line';
        horizontal.style.width = '100%';
        horizontal.style.height = '1px';
        horizontal.style.top = '50%';

        const vertical = document.createElement('div');
        vertical.className = 'radar-grid-line';
        vertical.style.width = '1px';
        vertical.style.height = '100%';
        vertical.style.left = '50%';

        gridElement.appendChild(horizontal);
        gridElement.appendChild(vertical);
        this.element.appendChild(gridElement);
    }

    updatePositions(data) {
        // if no data or in spectator mode, do nothing
        if (!data || !data.cars || data.cars.length === 0) {
            return; // No cars to display
        }

        const scale = this.width / 100; // 100 meters fits in view
        const playerIndex = data["player-index"];
        data.cars.forEach((car, index) => {
            const carId = `car-${index}`;
            let carElement = this.carElements[carId];

            if (!carElement) {
                carElement = document.createElement('div');
                carElement.id = carId;
                const isPlayer = index === playerIndex;
                carElement.className = `radar-car ${isPlayer ? 'player-car' : 'opponent-car'}`;

                const velocityIndicator = document.createElement('div');
                velocityIndicator.className = 'velocity-indicator';
                carElement.appendChild(velocityIndicator);

                this.element.appendChild(carElement);
                this.carElements[carId] = carElement;
            }

            // Position relative to center
            const screenX = this.centerX + (car["world-position"].x * scale);
            const screenY = this.centerY - (car["world-position"].z * scale);

            carElement.style.left = `${screenX}px`;
            carElement.style.top = `${screenY}px`;
            carElement.style.transform = `translate(-50%, -50%) rotate(${car["orientation"].yaw}rad)`;

            // Update velocity indicator
            const velocity = Math.sqrt(car["world-verlocity"].x * car["world-verlocity"].x + car["world-verlocity"].z * car["world-verlocity"].z);
            const velocityScale = Math.min(velocity / 100, 1);
            carElement.querySelector('.velocity-indicator').style.height = `${velocityScale * 100}%`;
        });
    }

    setupResizeObserver() {
        const resizeObserver = new ResizeObserver(entries => {
            for (const entry of entries) {
                if (entry.target === this.element) {
                    this.width = entry.contentRect.width;
                    this.height = entry.contentRect.height;
                    this.centerX = this.width / 2;
                    this.centerY = this.height / 2;
                }
            }
        });

        resizeObserver.observe(this.element);
    }
/*
    {
        "world-position": {
            "x": -271.3988037109375,
            "y": 14.724800109863281,
            "z": -723.61767578125
        },
        "world-velocity": {
            "x": 0.0001811655383789912,
            "y": -0.0009959058370441198,
            "z": -0.0006909227231517434
        },
        "world-forward-dir": {
            "x": -17666,
            "y": 258,
            "z": -27595
        },
        "world-right-dir": {
            "x": 27596,
            "y": 200,
            "z": -17665
        },
        "g-force": {
            "lateral": 7.5122088674106635e-06,
            "longitudinal": 9.615591807232704e-06,
            "vertical": -1.4028184523340315e-05
        },
        "orientation": {
            "yaw": -2.572145938873291,
            "pitch": -0.007882237434387207,
            "roll": -0.006111640017479658
        }
    }
*/

    // Demo code - remove this when integrating with real data
    startDemo() {
        const demoData = {
            "player-index": 0,
            cars: [
                {
                    "world-position": { x: 0, y: 0, z: 0 },
                    "world-velocity": { x: 0, y: 0, z: 50 },
                    "orientation": { yaw: 0, pitch: 0, roll: 0 }
                },
                {
                    "world-position": { x: 0, y: 0, z: 30 },
                    "world-velocity": { x: 0, y: 0, z: 48 },
                    "orientation": { yaw: 0, pitch: 0, roll: 0 }
                },
                {
                    "world-position": { x: 15, y: 0, z: 10 },
                    "world-velocity": { x: 0, y: 0, z: 45 },
                    "orientation": { yaw: 0, pitch: 0, roll: 0 }
                },
                {
                    "world-position": { x: -5, y: 0, z: -20 },
                    "world-velocity": { x: 0, y: 0, z: 52 },
                    "orientation": { yaw: 0, pitch: 0, roll: 0 }
                },
            ]
        };

        const updateDemo = () => {
            demoData.cars.forEach(car => {
                car["world-position"].x += (Math.random() - 0.5) * 2;
                car["world-position"].z += (Math.random() - 0.5) * 2;
                car["orientation"].yaw += (Math.random() - 0.5) * 0.1;
            });

            this.updatePositions(demoData);
        };

        setInterval(updateDemo, 50);
    }
}

// Initialize the radar
const radar = new F1Radar(document.getElementById('f1-radar'));

// Wait for the page to fully load
document.addEventListener("DOMContentLoaded", function () {
    setTimeout(initWebChannel, 100); // Small delay to ensure everything is ready
});

function initWebChannel() {
    console.log("Initializing WebChannel...");
    new QWebChannel(qt.webChannelTransport, function (channel) {
        console.log("Channel created, available objects:", Object.keys(channel.objects));
        const {backend} = channel.objects;

        if (!backend) {
            console.error("Backend not available!");
            return;
        }

        if (!backend.dataChanged) {
            console.error("dataChanged signal not available!");
            return;
        }

        backend.dataChanged.connect(function (jsonData) {
            try {
                // Parse the JSON string back to an object
                const data = JSON.parse(jsonData);
                console.log("Data received:", data);

                if (!data) {
                    console.error("Received null data!");
                    return;
                }
                radar.updatePositions(data);
            } catch (error) {
                console.error("Error parsing JSON data:", error, jsonData);
            }
        });

        console.log("QWebChannel connected successfully!");
    });
}

// Also initialize if the document is already loaded
if (document.readyState !== "loading") {
    console.log("Document already loaded, initializing WebChannel...");
    setTimeout(initWebChannel, 100);
}
