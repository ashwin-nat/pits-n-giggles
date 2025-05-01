class GForceDisplay {
    constructor(containerId) {
        this.initializeElements(containerId);
    }

    initializeElements(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container with id '${containerId}' not found`);
        }

        this.dot = document.getElementById('gforce-dot');
        this.netGForceElement = document.getElementById('net-gforce');
    }

    update(gForceData) {
        this.updateDotPosition(gForceData);
        this.updateGForceValues(gForceData);
    }

    updateDotPosition(gForceData) {
        const maxG = 4;
        const radius = 50;

        const { scaledLat, scaledLong } = this.calculateDotPosition(gForceData, maxG, radius);
        // Apply translation from the centered position
        this.dot.style.transform = `translate(${scaledLat}px, ${-scaledLong}px)`;
    }

    updateGForceValues(gForceData) {
        const netGForce = this.calculateNetGForce(gForceData);
        this.netGForceElement.textContent = netGForce.toFixed(2) + " G";
    }

    calculateNetGForce(gForceData) {
        return Math.sqrt(
            Math.pow(gForceData.lat, 2) +
            Math.pow(gForceData.long, 2) +
            Math.pow(gForceData.vert, 2)
        );
    }

    calculateDotPosition(gForceData, maxG, radius) {
        const scaledLat = (gForceData.lat / maxG) * radius;
        const scaledLong = (gForceData.long / maxG) * radius;

        return { scaledLat, scaledLong };
    }
}