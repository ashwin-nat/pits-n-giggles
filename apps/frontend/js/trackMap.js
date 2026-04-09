/**
 * TrackMap — renders driver positions on an SVG track map.
 *
 * Uses lap-progress (0–100%) interpolated onto the SVG polyline to place
 * each driver as a colored circle. Player gets a gold outline, teammate
 * silver, everyone else just their team color.
 *
 * For reverse circuits the polyline points are reversed so that
 * lap-progress still maps correctly (0% = start of reverse layout).
 */

// Mapping from the circuit string delivered by the backend (TrackID.__str__)
// to the SVG filename stem in assets/track-maps/.
// null → no SVG available for this circuit.
const CIRCUIT_TO_SVG = {
    "Melbourne":            "Melbourne",
    "Paul Ricard":          "Paul_Ricard",
    "Shanghai":             "Shanghai",
    "Sakhir":               "Sakhir_Bahrain",
    "Catalunya":            "Catalunya",
    "Monaco":               "Monaco",
    "Montreal":             "Montreal",
    "Silverstone":          "Silverstone",
    "Hockenheim":           null,
    "Hungaroring":          "Hungaroring",
    "Spa":                  "Spa",
    "Monza":                "Monza",
    "Singapore":            "Singapore",
    "Suzuka":               "Suzuka",
    "Abu Dhabi":            "Abu_Dhabi",
    "Texas":                "Texas",
    "Brazil":               "Brazil",
    "Austria":              "Austria",
    "Sochi":                null,
    "Mexico":               "Mexico",
    "Baku":                 "Baku_Azerbaijan",
    "Sakhir Short":         null,
    "Silverstone Short":    null,
    "Texas Short":          null,
    "Suzuka Short":         null,
    "Hanoi":                null,
    "Zandvoort":            "Zandvoort",
    "Imola":                "Imola",
    "Portimao":             "Portimao",
    "Jeddah":               "Jeddah",
    "Miami":                "Miami",
    "Las Vegas":            "Las_Vegas",
    "Losail":               "Losail",
    // Reverse layouts — reuse the base track SVG, polyline gets reversed
    "Silverstone_Reverse":  "Silverstone",
    "Austria_Reverse":      "Austria",
    "Zandvoort_Reverse":    "Zandvoort",
};

const SVG_NS = 'http://www.w3.org/2000/svg';

/** Team → F1 color mapping for driver dots */
function getF1TeamColor(teamName) {
    const teamColors = {
        'Red Bull Racing': 'rgba(54,113,198,1)',
        'Red Bull': 'rgba(54,113,198,1)',
        'VCARB': 'rgba(102,146,255,1)',
        'RB': 'rgba(102,146,255,1)',
        'Mercedes': 'rgba(39,244,210,1)',
        'Ferrari': 'rgba(232,0,45,1)',
        'McLaren': 'rgba(255,128,0,1)',
        'Mclaren': 'rgba(255,128,0,1)',
        'Aston Martin': 'rgba(34,153,113,1)',
        'Alpine': 'rgba(255,135,188,1)',
        'Alpha Tauri': 'rgba(30,40,80,1)',
        'Alfa Romeo': 'rgba(155,0,0,1)',
        'Haas': 'rgba(182,186,189,1)',
        'Williams': 'rgba(100,196,255,1)',
        'Sauber': 'rgba(82,226,82,1)',
    };
    return teamColors[teamName] || '#FFFFFF';
}

class TrackMap {

    constructor(containerSelector) {
        this.container = document.querySelector(containerSelector || '#trackMapContainer');
        this.headerElement = document.getElementById('trackMapHeader');
        this.svgElement = null;
        this.polylinePoints = [];
        this.segmentLengths = [];
        this.totalLength = 0;
        this.currentCircuit = null;
        this.driverDots = new Map(); // index → <circle>
        this.isReverse = false;

        this._createTooltip();
        this._activeTooltipDot = null;

        // ── Pinned popup state ──
        this._pinnedDriver = null;
        this._createPinnedPopup();

        // ── Zoom/Pan state ──
        this._zoom = 1;
        this._panX = 0;
        this._panY = 0;
        this._isPanning = false;
        this._panStartX = 0;
        this._panStartY = 0;
        this._panStartTransX = 0;
        this._panStartTransY = 0;
        this._minZoom = 1;
        this._maxZoom = 8;
        this._zoomStep = 0.15;

        // Touch pinch state
        this._lastPinchDist = 0;

        this._initZoomControls();

        // Dismiss tooltip when tapping outside a driver dot (touch devices)
        document.addEventListener('touchstart', (e) => {
            if (this._activeTooltipDot &&
                !e.target.classList.contains('track-map-driver-dot') &&
                !e.target.classList.contains('track-map-hit-area')) {
                this._hideTooltip();
            }
        });
    }

    // ── public API ──────────────────────────────────────────────────

    /**
     * Load the track SVG for the given circuit name.
     * Skips reload if the circuit hasn't changed.
     */
    async loadTrack(circuitName) {
        if (circuitName === this.currentCircuit || circuitName === '---') return;
        this.currentCircuit = circuitName;

        this.isReverse = circuitName.endsWith('_Reverse');
        const svgStem = CIRCUIT_TO_SVG[circuitName] ?? null;

        if (!svgStem) {
            this._showFallback('No track map available');
            return;
        }

        try {
            const response = await fetch(`/track-maps/${encodeURIComponent(svgStem)}.svg`);
            if (!response.ok) {
                this._showFallback('Track map not found');
                return;
            }
            const svgText = await response.text();
            this._injectSVG(svgText);
        } catch (err) {
            console.error('Failed to load track map:', err);
            this._showFallback('Failed to load track map');
        }
    }

    /**
     * Update driver dot positions from the race-table data.
     *
     * @param {Array}   tableEntries   - driver row objects from race-table-update
     * @param {boolean} isSpectating   - true when in spectator mode
     * @param {number}  spectatorIndex - car index of the spectated driver
     * @param {string}  refDriverTeam  - team name of the reference driver (for teammate detection)
     */
    updateDrivers(tableEntries, isSpectating, spectatorIndex, refDriverTeam) {
        if (!this.svgElement || this.polylinePoints.length === 0) return;

        const activeIds = new Set();

        for (const entry of tableEntries) {
            const driverInfo = entry['driver-info'];
            const lapInfo    = entry['lap-info'];
            const ersInfo    = entry['ers-info'];
            const tyreInfo   = entry['tyre-info'];

            const index    = driverInfo['index'];
            const progress = lapInfo['lap-progress'] ?? 0;
            const name     = driverInfo['name'];
            const team     = driverInfo['team'];
            const isPlayer = driverInfo['is-player'];

            activeIds.add(index);

            const pos = this._getPositionAtProgress(progress);

            // Get or create the driver circle
            let dot = this.driverDots.get(index);
            if (!dot) {
                dot = this._createDriverDot();
                this.driverDots.set(index, dot);
            }

            // Position (CSS transitions on cx/cy give smooth movement)
            dot.setAttribute('cx', pos.x);
            dot.setAttribute('cy', pos.y);
            if (dot._hitArea) {
                dot._hitArea.setAttribute('cx', pos.x);
                dot._hitArea.setAttribute('cy', pos.y);
            }

            // Team color fill
            dot.setAttribute('fill', getF1TeamColor(team));

            // Highlight: gold for player/spectated, silver for teammate
            const isRef = isPlayer || (isSpectating && index === spectatorIndex);
            const isTeammate = !isRef && team === refDriverTeam && team !== 'F1 Generic';

            if (isRef) {
                dot.setAttribute('stroke', '#FFD700');
                dot.setAttribute('stroke-width', '3');
            } else if (isTeammate) {
                dot.setAttribute('stroke', '#C0C0C0');
                dot.setAttribute('stroke-width', '2');
            } else {
                dot.setAttribute('stroke', 'none');
                dot.setAttribute('stroke-width', '0');
            }

            // Data attributes for hover tooltip & pinned popup
            dot.dataset.driverName   = name;
            dot.dataset.driverTeam   = team;
            dot.dataset.driverIndex  = index;
            dot.dataset.position     = driverInfo['position'];
            dot.dataset.tyreCompound = tyreInfo?.['visual-tyre-compound'] ?? 'N/A';
            dot.dataset.ersPercent   = (typeof ersInfo?.['ers-percent-float'] === 'number')
                                        ? ersInfo['ers-percent-float'].toFixed(1) : 'N/A';
            dot.dataset.ersMode      = ersInfo?.['ers-mode'] ?? 'N/A';
            dot.dataset.tyreWearAvg  = this._avgTyreWear(tyreInfo?.['current-wear']);

            // Update pinned popup if this driver is pinned
            if (this._pinnedDriver === index) {
                this._updatePinnedPopupPosition(dot);
                this._updatePinnedPopupContent(dot);
            }
        }

        // Remove stale dots (driver retired / left session)
        this.driverDots.forEach((dot, id) => {
            if (!activeIds.has(id)) {
                if (this._pinnedDriver === id) this._unpinPopup();
                if (dot._hitArea) dot._hitArea.remove();
                dot.remove();
                this.driverDots.delete(id);
            }
        });
    }

    /** Reset internal state (e.g. on session change). */
    clear() {
        this.container.innerHTML = '';
        this.svgElement = null;
        this.polylinePoints = [];
        this.segmentLengths = [];
        this.totalLength = 0;
        this.currentCircuit = null;
        this.driverDots.clear();
        this._activeTooltipDot = null;
        this._unpinPopup();
        this._resetZoomState();
        // Re-append reset button
        this.container.appendChild(this._resetBtn);
    }

    // ── SVG parsing ─────────────────────────────────────────────────

    _injectSVG(svgText) {
        this.container.innerHTML = '';
        this.driverDots.clear();
        this._resetZoomState();

        const doc = new DOMParser().parseFromString(svgText, 'image/svg+xml');
        this.svgElement = doc.querySelector('svg');
        if (!this.svgElement) {
            this._showFallback('Invalid SVG');
            return;
        }

        // Make the SVG scale to fit its container while preserving aspect ratio
        const origW = this.svgElement.getAttribute('width')  || '1000';
        const origH = this.svgElement.getAttribute('height') || '600';
        this.svgElement.setAttribute('viewBox', `0 0 ${origW} ${origH}`);
        this.svgElement.removeAttribute('width');
        this.svgElement.removeAttribute('height');
        this.svgElement.classList.add('track-map-svg');

        this.container.appendChild(this.svgElement);
        this.container.appendChild(this._resetBtn);

        // Parse polyline
        const polyline = this.svgElement.querySelector('polyline');
        if (!polyline) {
            this._showFallback('No polyline in SVG');
            return;
        }

        this.polylinePoints = polyline.getAttribute('points')
            .trim()
            .split(/\s+/)
            .map(p => {
                const [x, y] = p.split(',').map(Number);
                return { x, y };
            });

        // For reverse circuits, reverse the points so 0% is the reverse-layout start
        if (this.isReverse) {
            this.polylinePoints.reverse();
        }

        this._computeSegmentLengths();
    }

    _computeSegmentLengths() {
        this.segmentLengths = [];
        this.totalLength = 0;

        for (let i = 1; i < this.polylinePoints.length; i++) {
            const dx = this.polylinePoints[i].x - this.polylinePoints[i - 1].x;
            const dy = this.polylinePoints[i].y - this.polylinePoints[i - 1].y;
            const len = Math.sqrt(dx * dx + dy * dy);
            this.segmentLengths.push(len);
            this.totalLength += len;
        }
    }

    // ── position interpolation ──────────────────────────────────────

    /**
     * Interpolate a position on the polyline at the given progress (0–100 %).
     * Returns { x, y } in SVG coordinate space.
     */
    _getPositionAtProgress(progress) {
        const clamped = Math.max(0, Math.min(progress, 100));
        let target = (clamped / 100) * this.totalLength;

        let accumulated = 0;
        for (let i = 0; i < this.segmentLengths.length; i++) {
            const segLen = this.segmentLengths[i];
            if (accumulated + segLen >= target) {
                const frac = (segLen > 0) ? (target - accumulated) / segLen : 0;
                const p1 = this.polylinePoints[i];
                const p2 = this.polylinePoints[i + 1];
                return {
                    x: p1.x + (p2.x - p1.x) * frac,
                    y: p1.y + (p2.y - p1.y) * frac,
                };
            }
            accumulated += segLen;
        }

        // Edge case: return the last point
        const last = this.polylinePoints[this.polylinePoints.length - 1];
        return { x: last.x, y: last.y };
    }

    // ── driver dots ─────────────────────────────────────────────────

    _createDriverDot() {
        // Invisible larger hit-area for touch devices
        const hitArea = document.createElementNS(SVG_NS, 'circle');
        hitArea.setAttribute('r', '16');
        hitArea.setAttribute('fill', 'transparent');
        hitArea.setAttribute('stroke', 'none');
        hitArea.classList.add('track-map-hit-area');

        const circle = document.createElementNS(SVG_NS, 'circle');
        circle.setAttribute('r', '8');
        circle.classList.add('track-map-driver-dot');

        // Mouse events (desktop)
        circle.addEventListener('mouseenter', (e) => this._showTooltip(e, circle));
        circle.addEventListener('mouseleave', ()  => this._hideTooltip());
        circle.addEventListener('mousemove',  (e) => this._positionTooltip(e));

        // Click to pin/unpin popup
        const handlePinClick = () => {
            if (this._pinnedDriver === parseInt(circle.dataset.driverIndex)) {
                this._unpinPopup();
            } else {
                this._pinPopup(circle);
            }
        };
        circle.addEventListener('click', handlePinClick);
        hitArea.addEventListener('click', handlePinClick);

        // Touch events on hit-area (tap to toggle tooltip)
        hitArea.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this._toggleTooltipTouch(e, circle);
        });

        this.svgElement.appendChild(hitArea);
        this.svgElement.appendChild(circle);

        // Link hit-area to circle for position sync
        circle._hitArea = hitArea;
        return circle;
    }

    // ── tooltip ─────────────────────────────────────────────────────

    _createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'track-map-tooltip';
        this.tooltip.style.display = 'none';
        document.body.appendChild(this.tooltip);
    }

    _showTooltip(event, dot) {
        if (this._pinnedDriver === parseInt(dot.dataset.driverIndex)) return;

        const name    = escapeHtml(dot.dataset.driverName || '');
        const team    = dot.dataset.driverTeam || '';
        const abbr    = escapeHtml(this._getTeamAbbreviation(team));
        const ers     = escapeHtml(dot.dataset.ersPercent  || 'N/A');
        const ersMode = escapeHtml(dot.dataset.ersMode     || 'N/A');
        const wear    = escapeHtml(dot.dataset.tyreWearAvg || 'N/A');

        this.tooltip.innerHTML =
            `<strong>${name} (${abbr})</strong><br>` +
            `ERS: ${ers}% (${ersMode})<br>` +
            `Tyre Wear: ${wear}%`;
        this.tooltip.style.display = 'block';
        this._positionTooltip(event);
    }

    _positionTooltip(event) {
        this.tooltip.style.left = (event.pageX + 12) + 'px';
        this.tooltip.style.top  = (event.pageY - 10) + 'px';
    }

    _hideTooltip() {
        this.tooltip.style.display = 'none';
        this._activeTooltipDot = null;
    }

    _toggleTooltipTouch(event, dot) {
        if (this._activeTooltipDot === dot) {
            this._hideTooltip();
        } else {
            const touch = event.touches[0];
            const name    = escapeHtml(dot.dataset.driverName || '');
            const team    = dot.dataset.driverTeam || '';
            const abbr    = escapeHtml(this._getTeamAbbreviation(team));
            const ers     = escapeHtml(dot.dataset.ersPercent  || 'N/A');
            const ersMode = escapeHtml(dot.dataset.ersMode     || 'N/A');
            const wear    = escapeHtml(dot.dataset.tyreWearAvg || 'N/A');

            this.tooltip.innerHTML =
                `<strong>${name} (${abbr})</strong><br>` +
                `ERS: ${ers}% (${ersMode})<br>` +
                `Tyre Wear: ${wear}%`;
            this.tooltip.style.display = 'block';
            this.tooltip.style.left = (touch.pageX + 12) + 'px';
            this.tooltip.style.top  = (touch.pageY - 28) + 'px';
            this._activeTooltipDot = dot;
        }
    }

    // ── pinned popup ────────────────────────────────────────────────

    _createPinnedPopup() {
        this._pinnedPopup = document.createElement('div');
        this._pinnedPopup.className = 'track-map-pinned-popup';
        this._pinnedPopup.style.display = 'none';
        this._pinnedPopup.addEventListener('click', (e) => {
            if (e.target.classList.contains('pinned-popup-close')) {
                this._unpinPopup();
            }
        });
        document.body.appendChild(this._pinnedPopup);
    }

    _pinPopup(dot) {
        const index = parseInt(dot.dataset.driverIndex);
        this._pinnedDriver = index;
        this._pinnedPopup.style.display = 'block';
        this._updatePinnedPopupContent(dot);
        this._updatePinnedPopupPosition(dot);
        // Hide hover tooltip to avoid duplication
        this._hideTooltip();
    }

    _unpinPopup() {
        this._pinnedDriver = null;
        this._pinnedPopup.style.display = 'none';
    }

    _updatePinnedPopupPosition(dot) {
        const rect = dot.getBoundingClientRect();
        this._pinnedPopup.style.left = (rect.right + window.scrollX + 8) + 'px';
        this._pinnedPopup.style.top  = (rect.top + window.scrollY - 10) + 'px';
    }

    _updatePinnedPopupContent(dot) {
        const name     = escapeHtml(dot.dataset.driverName || '');
        const team     = dot.dataset.driverTeam || '';
        const abbr     = escapeHtml(this._getTeamAbbreviation(team));
        const pos      = escapeHtml(dot.dataset.position || '');
        const ers      = escapeHtml(dot.dataset.ersPercent || 'N/A');
        const ersMode  = escapeHtml(dot.dataset.ersMode || 'N/A');
        const wear     = escapeHtml(dot.dataset.tyreWearAvg || 'N/A');
        const compound = escapeHtml(dot.dataset.tyreCompound || 'N/A');

        this._pinnedPopup.innerHTML =
            `<span class="pinned-popup-close">&times;</span>` +
            `<strong>${name} (${abbr})</strong><br>` +
            `P${pos} \u00b7 ${compound}<br>` +
            `ERS: ${ers}% (${ersMode})<br>` +
            `Wear: ${wear}%`;
        this._pinnedPopup.style.borderColor = getF1TeamColor(team);
    }

    _getTeamAbbreviation(teamName) {
        const map = {
            'Red Bull Racing': 'RBR',
            'McLaren':         'MCL',
            'Ferrari':         'FER',
            'Mercedes':        'MER',
            'Aston Martin':    'AMR',
            'Alpine':          'ALP',
            'Williams':        'WIL',
            'Haas':            'HAS',
            'RB':              'RB',
            'Kick Sauber':     'SAU',
            'Cadillac':        'CAD',
        };
        return map[teamName] || (teamName || '').slice(0, 3).toUpperCase();
    }

    // ── helpers ──────────────────────────────────────────────────────

    _avgTyreWear(wearData) {
        if (!wearData) return 'N/A';
        const vals = [
            wearData['front-left-wear'],
            wearData['front-right-wear'],
            wearData['rear-left-wear'],
            wearData['rear-right-wear'],
        ].filter(v => typeof v === 'number');
        if (vals.length === 0) return 'N/A';
        return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
    }

    _showFallback(message) {
        this.container.innerHTML =
            `<div class="track-map-fallback">${escapeHtml(message)}</div>`;
        this.svgElement = null;
        this.polylinePoints = [];
        this.segmentLengths = [];
        this.totalLength = 0;
        this.driverDots.clear();
        this._unpinPopup();
        this._resetZoomState();
        // Re-append reset button (innerHTML wiped it)
        this.container.appendChild(this._resetBtn);
    }

    // ── Zoom & Pan ──────────────────────────────────────────────────

    _initZoomControls() {
        // Create reset button
        this._resetBtn = document.createElement('button');
        this._resetBtn.className = 'track-map-zoom-reset';
        this._resetBtn.textContent = '↺';
        this._resetBtn.title = 'Reset zoom';
        this._resetBtn.style.display = 'none';
        this._resetBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.resetZoom();
        });
        this.container.appendChild(this._resetBtn);

        // Wheel zoom
        this.container.addEventListener('wheel', (e) => {
            if (!this.svgElement) return;
            e.preventDefault();
            const rect = this.container.getBoundingClientRect();
            const cursorX = e.clientX - rect.left;
            const cursorY = e.clientY - rect.top;
            const delta = e.deltaY > 0 ? -this._zoomStep : this._zoomStep;
            this._applyZoom(delta, cursorX, cursorY);
        }, { passive: false });

        // Double-click reset
        this.container.addEventListener('dblclick', (e) => {
            if (!this.svgElement) return;
            e.preventDefault();
            this.resetZoom();
        });

        // Mouse drag pan
        this.container.addEventListener('mousedown', (e) => {
            if (!this.svgElement || this._zoom <= 1) return;
            if (e.target.classList.contains('track-map-driver-dot') ||
                e.target.classList.contains('track-map-hit-area')) return;
            e.preventDefault();
            this._isPanning = true;
            this._panStartX = e.clientX;
            this._panStartY = e.clientY;
            this._panStartTransX = this._panX;
            this._panStartTransY = this._panY;
            this.container.style.cursor = 'grabbing';
        });

        document.addEventListener('mousemove', (e) => {
            if (!this._isPanning) return;
            this._panX = this._panStartTransX + (e.clientX - this._panStartX);
            this._panY = this._panStartTransY + (e.clientY - this._panStartY);
            this._clampPan();
            this._applyTransform();
        });

        document.addEventListener('mouseup', () => {
            if (this._isPanning) {
                this._isPanning = false;
                this.container.style.cursor = '';
            }
        });

        // Touch: pinch-to-zoom + pan
        this.container.addEventListener('touchstart', (e) => {
            if (!this.svgElement) return;
            if (e.touches.length === 2) {
                e.preventDefault();
                this._lastPinchDist = this._getTouchDist(e.touches);
            } else if (e.touches.length === 1 && this._zoom > 1) {
                const touch = e.touches[0];
                if (touch.target.classList.contains('track-map-driver-dot') ||
                    touch.target.classList.contains('track-map-hit-area')) return;
                this._isPanning = true;
                this._panStartX = touch.clientX;
                this._panStartY = touch.clientY;
                this._panStartTransX = this._panX;
                this._panStartTransY = this._panY;
            }
        }, { passive: false });

        this.container.addEventListener('touchmove', (e) => {
            if (!this.svgElement) return;
            if (e.touches.length === 2) {
                e.preventDefault();
                const dist = this._getTouchDist(e.touches);
                if (this._lastPinchDist > 0) {
                    const rect = this.container.getBoundingClientRect();
                    const cx = ((e.touches[0].clientX + e.touches[1].clientX) / 2) - rect.left;
                    const cy = ((e.touches[0].clientY + e.touches[1].clientY) / 2) - rect.top;
                    const scale = dist / this._lastPinchDist;
                    const delta = (scale - 1) * 0.5;
                    this._applyZoom(delta, cx, cy);
                }
                this._lastPinchDist = dist;
            } else if (e.touches.length === 1 && this._isPanning) {
                e.preventDefault();
                const touch = e.touches[0];
                this._panX = this._panStartTransX + (touch.clientX - this._panStartX);
                this._panY = this._panStartTransY + (touch.clientY - this._panStartY);
                this._clampPan();
                this._applyTransform();
            }
        }, { passive: false });

        this.container.addEventListener('touchend', (e) => {
            if (e.touches.length < 2) this._lastPinchDist = 0;
            if (e.touches.length === 0) this._isPanning = false;
        });
    }

    _getTouchDist(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    /** Zoom towards a point (cursorX/Y relative to container). */
    _applyZoom(delta, cursorX, cursorY) {
        const oldZoom = this._zoom;
        this._zoom = Math.min(this._maxZoom, Math.max(this._minZoom, this._zoom + delta));
        if (this._zoom === oldZoom) return;

        // Adjust pan so the point under cursor stays fixed
        const ratio = this._zoom / oldZoom;
        this._panX = cursorX - ratio * (cursorX - this._panX);
        this._panY = cursorY - ratio * (cursorY - this._panY);

        this._clampPan();
        this._applyTransform();
        this._resetBtn.style.display = this._zoom > 1.01 ? '' : 'none';
    }

    _clampPan() {
        const w = this.container.clientWidth;
        const h = this.container.clientHeight;
        const maxPanX = (this._zoom - 1) * w / 2;
        const maxPanY = (this._zoom - 1) * h / 2;
        this._panX = Math.max(-maxPanX, Math.min(maxPanX, this._panX));
        this._panY = Math.max(-maxPanY, Math.min(maxPanY, this._panY));
    }

    _applyTransform() {
        if (!this.svgElement) return;
        this.svgElement.style.transform = `translate(${this._panX}px, ${this._panY}px) scale(${this._zoom})`;

        // Update pinned popup position after transform change
        if (this._pinnedDriver !== null) {
            const dot = this.driverDots.get(this._pinnedDriver);
            if (dot) {
                requestAnimationFrame(() => this._updatePinnedPopupPosition(dot));
            }
        }
    }

    _resetZoomState() {
        this._zoom = 1;
        this._panX = 0;
        this._panY = 0;
        if (this._resetBtn) this._resetBtn.style.display = 'none';
    }

    /** Reset zoom and pan to default. */
    resetZoom() {
        this._resetZoomState();
        this._applyTransform();
    }
}
