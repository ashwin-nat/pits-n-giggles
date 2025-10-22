class LapTimer {
    constructor() {
        this.lastLapEl = document.getElementById('lastLap');
        this.bestLapEl = document.getElementById('bestLap');
        this.currentLapEl = document.getElementById('currentLap');
        this.sector1El = document.getElementById('sector1');
        this.sector2El = document.getElementById('sector2');
        this.sector3El = document.getElementById('sector3');

        this.startTime = Date.now();
        this.updateCurrentLap();

        // this.simulateDemo();
    }

    formatTime(milliseconds) {
        const totalSeconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const ms = milliseconds % 1000;

        return `${minutes}:${seconds.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    }

    update(data) {
        console.log("LapTimer got data:", data);
    }

    updateLastLap(time) {
        this.lastLapEl.textContent = this.formatTime(time);
    }

    updateBestLap(time) {
        this.bestLapEl.textContent = this.formatTime(time);
    }

    updateCurrentLap() {
        const elapsed = Date.now() - this.startTime;
        this.currentLapEl.textContent = this.formatTime(elapsed);
        requestAnimationFrame(() => this.updateCurrentLap());
    }

    setSectorStatus(sectorNumber, status) {
        const sectorEl = [this.sector1El, this.sector2El, this.sector3El][sectorNumber - 1];

        sectorEl.classList.remove('purple', 'green', 'yellow', 'red');

        if (status !== 'none') {
            sectorEl.classList.add(status);
        }
    }

    simulateDemo() {
        setTimeout(() => {
            this.setSectorStatus(1, 'green');
        }, 2000);

        setTimeout(() => {
            this.setSectorStatus(2, 'purple');
        }, 4000);

        setTimeout(() => {
            this.setSectorStatus(3, 'yellow');
        }, 6000);

        setTimeout(() => {
            this.updateLastLap(87234);
            this.updateBestLap(85678);
            this.startTime = Date.now();
            this.setSectorStatus(1, 'none');
            this.setSectorStatus(2, 'none');
            this.setSectorStatus(3, 'none');
        }, 8000);
    }
}

const timer = new LapTimer();

// Listen for updates from Python
window.addEventListener('telemetry-update', (event) => {
    timer.update(event.detail);
});

// Initial update when ready
window.addEventListener('pywebviewready', async () => {
    try {
        const data = await pywebview.api.get_data();
        timer.update(data);
    } catch (error) {
        console.error('Error getting initial telemetry:', error);
    }
});
