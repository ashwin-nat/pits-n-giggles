/**
 * TrackMap — renders driver positions on an SVG + Canvas hybrid track map.
 *
 * Uses SVG track outlines as sharp, infinitely-scalable backgrounds with a
 * transparent Canvas overlay for driver dots. World-coordinate transforms use
 * 6 affine coefficients from svg_transforms.json.
 *
 * Container structure:
 *   #trackMapContainer (position: relative, overflow: hidden)
 *     .track-map-wrapper (CSS transform for zoom/pan)
 *       <img class="track-map-svg"> (SVG source, sharp at any zoom)
 *       <canvas class="track-map-canvas"> (driver dots overlay)
 *     .track-map-zoom-reset button
 *
 * The world->SVG pixel transform is:
 *   svgX = a * worldX + b * worldZ + c
 *   svgY = d * worldX + e * worldZ + f
 */

// Mapping from the circuit string delivered by the backend (TrackID.__str__)
// to the key in svg_transforms.json (and SVG filename stem).
// null -> no track map available for this circuit.
const CIRCUIT_TO_TRANSFORM = {
    "Melbourne":            "Melbourne",
    "Paul Ricard":          null,
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
    // Reverse layouts
    "Silverstone_Reverse":  "Silverstone_Reverse",
    "Austria_Reverse":      "Austria_Reverse",
    "Zandvoort_Reverse":    "Zandvoort_Reverse",
};

// SVG internal coordinate space (all SVGs are 1000x600)
const SVG_W = 1000;
const SVG_H = 600;

// Driver dot radii (in SVG-pixel space)
const DOT_RADIUS      = 10;
const DOT_RADIUS_REF  = 12;
const HIT_RADIUS      = 22;

// Smooth interpolation factor per frame (0-1, higher = snappier)
const LERP_FACTOR = 0.25;

class TrackMap {

    constructor(containerSelector) {
        this.container = document.querySelector(containerSelector || '#trackMapContainer');
        this.headerElement = document.getElementById('trackMapHeader');
        this._wrapper = null;
        this._svgImg = null;
        this.canvas = null;
        this.ctx = null;
        this.currentCircuit = null;

        // Track transform parameters (from JSON) — per game year
        this._transforms = null;  // full JSON object for current game year
        this._currentTf = null;   // active transform for current circuit
        this._gameYear = null;    // currently loaded game year

        // Driver state: Map<driverIndex, {targetX, targetY, currentX, currentY, ...data}>
        this._drivers = new Map();
        this._activeDriverIds = new Set();

        this._createTooltip();
        this._activeTooltipDot = null;

        // -- Pinned popup state --
        this._pinnedDriver = null;
        this._createPinnedPopup();

        // -- Zoom/Pan state --
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

        // -- Rotation state --
        this._rotation = 0;
        this._rotationSliders = [];
        this._rotationInputs = [];
        this._rotationCtrl = null;

        this._initZoomControls();
        this._initRotationControls();

        // rAF loop
        this._rafId = null;
        this._boundRenderLoop = this._renderLoop.bind(this);

        // Sorted driver list cache — rebuilt only when updateDrivers runs
        this._sortedDrivers = [];
        this._driversDirty = false;

        // Dismiss tooltip when tapping outside a driver dot (touch devices)
        this._boundDocTouchStart = (e) => {
            if (this._activeTooltipDot &&
                !this._isDriverHit(e.touches[0].clientX, e.touches[0].clientY)) {
                this._hideTooltip();
            }
        };
        this._boundDocMouseMove = (e) => {
            if (!this._isPanning) return;
            this._panX = this._panStartTransX + (e.clientX - this._panStartX);
            this._panY = this._panStartTransY + (e.clientY - this._panStartY);
            this._clampPan();
            this._applyTransform();
        };
        this._boundDocMouseUp = () => {
            if (this._isPanning) {
                this._isPanning = false;
                this.container.style.cursor = '';
            }
        };
        document.addEventListener('touchstart', this._boundDocTouchStart);
        document.addEventListener('mousemove', this._boundDocMouseMove);
        document.addEventListener('mouseup', this._boundDocMouseUp);

        // Load transforms at construction time
    }

    destroy() {
        this._stopRenderLoop();
        document.removeEventListener('touchstart', this._boundDocTouchStart);
        document.removeEventListener('mousemove', this._boundDocMouseMove);
        document.removeEventListener('mouseup', this._boundDocMouseUp);
        if (this.tooltip) this.tooltip.remove();
        if (this._pinnedPopup) this._pinnedPopup.remove();
    }

    // -- Transform loading -----------------------------------------------

    async _loadTransforms(gameYear) {
        if (!gameYear) return;
        try {
            const resp = await fetch(`/track-maps/f1_${gameYear}/svg_transforms.json`);
            if (!resp.ok) {
                console.error(`Failed to load svg_transforms.json for F1 ${gameYear}:`, resp.status);
                return;
            }
            this._transforms = await resp.json();
            this._gameYear = gameYear;
        } catch (err) {
            console.error(`Failed to fetch svg_transforms.json for F1 ${gameYear}:`, err);
        }
    }

    // -- public API -------------------------------------------------------

    /**
     * Load the SVG track outline for the given circuit name.
     * Creates wrapper with SVG <img> + Canvas overlay.
     * Skips reload if the circuit hasn't changed.
     *
     * @param {string} circuitName  - circuit identifier from backend
     * @param {number} gameYear     - F1 game year (2023, 2024, 2025)
     */
    async loadTrack(circuitName, gameYear) {
        if (circuitName === this.currentCircuit || circuitName === '---') return;

        // F1 packet header sends last two digits (e.g. 25 for 2025)
        if (gameYear && gameYear < 100) gameYear += 2000;

        // Reload transforms if game year changed or not yet loaded
        if (!this._transforms || this._gameYear !== gameYear) {
            await this._loadTransforms(gameYear);
        }

        const tfKey = CIRCUIT_TO_TRANSFORM[circuitName] ?? null;
        if (!tfKey || !this._transforms || !this._transforms[tfKey]) {
            this._showFallback('No track map available');
            return;
        }

        this._currentTf = this._transforms[tfKey];

        try {
            const img = new Image();
            img.crossOrigin = 'anonymous';

            await new Promise((resolve, reject) => {
                img.onload = resolve;
                img.onerror = () => reject(new Error('SVG load failed'));
                img.src = `/track-maps/f1_${gameYear}/` + encodeURIComponent(tfKey + '.svg');
            });

            // Only mark circuit as loaded after successful SVG load
            this.currentCircuit = circuitName;
            this._setupTrackView(img);
            this._startRenderLoop();
        } catch (err) {
            console.error('Failed to load track SVG:', err);
            this._showFallback('Track map not found');
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
        if (!this.canvas || !this._currentTf) return;

        this._activeDriverIds.clear();

        for (const entry of tableEntries) {
            const driverInfo = entry['driver-info'];
            const lapInfo    = entry['lap-info'];
            const ersInfo    = entry['ers-info'];
            const tyreInfo   = entry['tyre-info'];
            const worldPos   = entry['world-pos'];

            const index    = driverInfo['index'];
            const name     = driverInfo['name'];
            const team     = driverInfo['team'];
            const isPlayer = driverInfo['is-player'];

            this._activeDriverIds.add(index);

            // Skip if no world position yet
            if (!worldPos) continue;

            const [worldX, worldZ] = worldPos;
            const { px, py } = this._worldToPixel(worldX, worldZ);

            // Get or create driver state
            let driverState = this._drivers.get(index);
            if (!driverState) {
                driverState = {
                    currentX: px, currentY: py,
                    targetX: px, targetY: py,
                    data: {},
                };
                this._drivers.set(index, driverState);
            }

            // Update target position
            driverState.targetX = px;
            driverState.targetY = py;

            // Determine visual properties
            const isRef = isPlayer || (isSpectating && index === spectatorIndex);
            const isTeammate = !isRef && team === refDriverTeam && team !== 'F1 Generic';

            driverState.data = {
                name, team, index, isRef, isTeammate,
                position:     driverInfo['position'],
                tyreCompound: tyreInfo?.['visual-tyre-compound'] ?? 'N/A',
                ersPercent:   (typeof ersInfo?.['ers-percent-float'] === 'number')
                                ? ersInfo['ers-percent-float'].toFixed(1) : 'N/A',
                ersMode:      ersInfo?.['ers-mode'] ?? 'N/A',
                tyreWearAvg:  this._avgTyreWear(tyreInfo?.['current-wear']),
                teamColor:    getF1TeamColor(team),
            };

            // Update pinned popup content if this driver is pinned
            if (this._pinnedDriver === index) {
                this._updatePinnedPopupContent(driverState.data);
            }
        }

        // Remove stale drivers
        for (const [id] of this._drivers) {
            if (!this._activeDriverIds.has(id)) {
                if (this._pinnedDriver === id) this._unpinPopup();
                this._drivers.delete(id);
            }
        }

        this._driversDirty = true;
    }

    _teardown() {
        this._stopRenderLoop();
        this.container.replaceChildren();
        this._wrapper = null;
        this._svgImg = null;
        this.canvas = null;
        this.ctx = null;
        this._currentTf = null;
        this._drivers.clear();
        this._sortedDrivers = [];
        this._driversDirty = false;
        this._activeTooltipDot = null;
        this._unpinPopup();
        this._resetZoomState();
        this.container.appendChild(this._resetBtn);
    }

    /** Reset internal state (e.g. on session change). */
    clear() {
        this._teardown();
        this.currentCircuit = null;
    }

    // -- Track view setup -------------------------------------------------

    _setupTrackView(svgImg) {
        // Clear previous content
        this.container.replaceChildren();
        this._drivers.clear();
        this._resetZoomState();

        // Create wrapper (receives zoom/pan CSS transform)
        this._wrapper = document.createElement('div');
        this._wrapper.className = 'track-map-wrapper';

        // SVG image (background — sharp at any zoom level)
        this._svgImg = svgImg;
        this._svgImg.className = 'track-map-svg';
        this._svgImg.draggable = false;

        // Canvas overlay (driver dots only, transparent background)
        this.canvas = document.createElement('canvas');
        this.canvas.width = SVG_W;
        this.canvas.height = SVG_H;
        this.canvas.className = 'track-map-canvas';
        this.ctx = this.canvas.getContext('2d');

        this._wrapper.appendChild(this._svgImg);
        this._wrapper.appendChild(this.canvas);
        this.container.appendChild(this._wrapper);
        this.container.appendChild(this._resetBtn);
        if (this._rotationCtrl) {
            this.container.appendChild(this._rotationCtrl);
        }

        // Attach mouse/touch events for interaction
        this._initCanvasInteraction();
    }

    // -- World->SVG pixel transform (affine 6-coefficient) ----------------

    _worldToPixel(worldX, worldZ) {
        const tf = this._currentTf;
        const px = tf.a * worldX + tf.b * worldZ + tf.c;
        const py = tf.d * worldX + tf.e * worldZ + tf.f;
        return { px, py };
    }

    // -- Render loop ------------------------------------------------------

    _startRenderLoop() {
        if (this._rafId) return;
        this._rafId = requestAnimationFrame(this._boundRenderLoop);
    }

    _stopRenderLoop() {
        if (this._rafId) {
            cancelAnimationFrame(this._rafId);
            this._rafId = null;
        }
    }

    _renderLoop() {
        this._rafId = requestAnimationFrame(this._boundRenderLoop);

        const ctx = this.ctx;
        if (!ctx) return;

        // Clear transparent canvas (SVG background is a separate DOM element)
        ctx.clearRect(0, 0, SVG_W, SVG_H);

        // Rebuild sorted list only when driver set changes (not every frame)
        if (this._driversDirty) {
            this._sortedDrivers = [...this._drivers.values()].sort((a, b) => {
                if (a.data.isRef) return 1;
                if (b.data.isRef) return -1;
                if (a.data.isTeammate) return 1;
                if (b.data.isTeammate) return -1;
                return 0;
            });
            this._driversDirty = false;
        }

        for (const driver of this._sortedDrivers) {
            // Smooth interpolation towards target
            driver.currentX += (driver.targetX - driver.currentX) * LERP_FACTOR;
            driver.currentY += (driver.targetY - driver.currentY) * LERP_FACTOR;

            const x = driver.currentX;
            const y = driver.currentY;
            const d = driver.data;

            const radius = d.isRef ? DOT_RADIUS_REF : DOT_RADIUS;

            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fillStyle = d.teamColor || '#888';
            ctx.fill();

            if (d.isRef) {
                ctx.strokeStyle = '#FFD700';
                ctx.lineWidth = 3;
                ctx.stroke();
            } else if (d.isTeammate) {
                ctx.strokeStyle = '#C0C0C0';
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        }

        // Update pinned popup position
        if (this._pinnedDriver !== null) {
            const driver = this._drivers.get(this._pinnedDriver);
            if (driver) {
                this._updatePinnedPopupPosition(driver);
            }
        }
    }

    // -- Canvas interaction (hover, click, touch) -------------------------

    _initCanvasInteraction() {
        // Mouse move -> tooltip on hover
        this.canvas.addEventListener('mousemove', (e) => {
            const hit = this._hitTestDrivers(e.clientX, e.clientY);
            if (hit) {
                if (this._pinnedDriver === hit.data.index) {
                    this._hideTooltip();
                    this.canvas.style.cursor = 'pointer';
                    return;
                }
                this._showTooltip(e, hit.data);
                this.canvas.style.cursor = 'pointer';
            } else {
                this._hideTooltip();
                this.canvas.style.cursor = (this._zoom > 1) ? 'grab' : '';
            }
        });

        this.canvas.addEventListener('mouseleave', () => {
            this._hideTooltip();
        });

        // Click -> pin/unpin popup
        this.canvas.addEventListener('click', (e) => {
            const hit = this._hitTestDrivers(e.clientX, e.clientY);
            if (hit) {
                if (this._pinnedDriver === hit.data.index) {
                    this._unpinPopup();
                } else {
                    this._pinPopup(hit);
                }
            }
        });

        // Touch tap -> toggle tooltip or pin
        this.canvas.addEventListener('touchstart', (e) => {
            if (e.touches.length !== 1) return;
            const touch = e.touches[0];
            const hit = this._hitTestDrivers(touch.clientX, touch.clientY);
            if (hit) {
                e.preventDefault();
                this._toggleTooltipTouch(touch, hit.data);
            }
        }, { passive: false });
    }

    /**
     * Hit-test: find the topmost driver dot at a screen position.
     * Converts screen coords -> SVG-pixel coords via the canvas bounding rect
     * (which already accounts for CSS zoom/pan transforms).
     */
    _hitTestDrivers(clientX, clientY) {
        if (!this.canvas) return null;
        const rect = this.canvas.getBoundingClientRect();

        const svgX = ((clientX - rect.left) / rect.width) * SVG_W;
        const svgY = ((clientY - rect.top) / rect.height) * SVG_H;

        // Check all drivers, find closest within hit radius
        let best = null;
        let bestDist = HIT_RADIUS;

        for (const driver of this._drivers.values()) {
            const dx = svgX - driver.currentX;
            const dy = svgY - driver.currentY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < bestDist) {
                bestDist = dist;
                best = driver;
            }
        }
        return best;
    }

    /** Quick check if a screen position hits any driver (for touch dismiss). */
    _isDriverHit(clientX, clientY) {
        return this._hitTestDrivers(clientX, clientY) !== null;
    }

    // -- tooltip ----------------------------------------------------------

    _createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'track-map-tooltip';
        this.tooltip.style.display = 'none';
        document.body.appendChild(this.tooltip);
    }

    _buildTooltipContent(data) {
        const name    = escapeHtml(data.name || '');
        const abbr    = escapeHtml(this._getTeamAbbreviation(data.team));
        const ers     = escapeHtml(data.ersPercent  || 'N/A');
        const ersMode = escapeHtml(data.ersMode     || 'N/A');
        const wear    = escapeHtml(data.tyreWearAvg || 'N/A');

        this.tooltip.replaceChildren();
        const strong = document.createElement('strong');
        strong.textContent = name + ' (' + abbr + ')';
        this.tooltip.appendChild(strong);
        this.tooltip.appendChild(document.createElement('br'));
        this.tooltip.appendChild(document.createTextNode('ERS: ' + ers + '% (' + ersMode + ')'));
        this.tooltip.appendChild(document.createElement('br'));
        this.tooltip.appendChild(document.createTextNode('Tyre Wear: ' + wear + '%'));
        this.tooltip.style.display = 'block';
        this._activeTooltipDot = data.index;
    }

    _showTooltip(event, data) {
        this._buildTooltipContent(data);
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

    _toggleTooltipTouch(touch, data) {
        if (this._activeTooltipDot === data.index) {
            this._hideTooltip();
        } else {
            this._buildTooltipContent(data);
            this.tooltip.style.left = (touch.pageX + 12) + 'px';
            this.tooltip.style.top  = (touch.pageY - 28) + 'px';
        }
    }

    // -- pinned popup -----------------------------------------------------

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

    _pinPopup(driverState) {
        const index = driverState.data.index;
        this._pinnedDriver = index;
        this._pinnedPopup.style.display = 'block';
        this._updatePinnedPopupContent(driverState.data);
        this._updatePinnedPopupPosition(driverState);
        // Hide hover tooltip to avoid duplication
        this._hideTooltip();
    }

    _unpinPopup() {
        this._pinnedDriver = null;
        this._pinnedPopup.style.display = 'none';
    }

    /** Position the pinned popup next to the driver dot (screen coords). */
    _updatePinnedPopupPosition(driverState) {
        if (!this.canvas) return;
        const rect = this.canvas.getBoundingClientRect();

        // Convert SVG-pixel -> screen pixel (rect already includes CSS transforms)
        const screenX = rect.left + (driverState.currentX / SVG_W) * rect.width;
        const screenY = rect.top  + (driverState.currentY / SVG_H) * rect.height;

        this._pinnedPopup.style.left = (screenX + window.scrollX + 12) + 'px';
        this._pinnedPopup.style.top  = (screenY + window.scrollY - 10) + 'px';
    }

    _updatePinnedPopupContent(data) {
        const name     = escapeHtml(data.name || '');
        const team     = data.team || '';
        const abbr     = escapeHtml(this._getTeamAbbreviation(team));
        const pos      = escapeHtml(String(data.position || ''));
        const ers      = escapeHtml(data.ersPercent || 'N/A');
        const ersMode  = escapeHtml(data.ersMode || 'N/A');
        const wear     = escapeHtml(data.tyreWearAvg || 'N/A');
        const compound = escapeHtml(data.tyreCompound || 'N/A');

        this._pinnedPopup.replaceChildren();
        const closeSpan = document.createElement('span');
        closeSpan.className = 'pinned-popup-close';
        closeSpan.textContent = '\u00d7';
        this._pinnedPopup.appendChild(closeSpan);
        const strong = document.createElement('strong');
        strong.textContent = name + ' (' + abbr + ')';
        this._pinnedPopup.appendChild(strong);
        this._pinnedPopup.appendChild(document.createElement('br'));
        this._pinnedPopup.appendChild(document.createTextNode('P' + pos + ' \u00b7 ' + compound));
        this._pinnedPopup.appendChild(document.createElement('br'));
        this._pinnedPopup.appendChild(document.createTextNode('ERS: ' + ers + '% (' + ersMode + ')'));
        this._pinnedPopup.appendChild(document.createElement('br'));
        this._pinnedPopup.appendChild(document.createTextNode('Wear: ' + wear + '%'));
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

    // -- helpers ----------------------------------------------------------

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
        this._teardown();
        const fallback = document.createElement('div');
        fallback.className = 'track-map-fallback';
        fallback.textContent = message;
        // Insert before the reset button
        this.container.insertBefore(fallback, this._resetBtn);
    }

    // -- Zoom & Pan -------------------------------------------------------

    _initZoomControls() {
        // Create reset button
        this._resetBtn = document.createElement('button');
        this._resetBtn.className = 'track-map-zoom-reset';
        this._resetBtn.textContent = '\u21ba';
        this._resetBtn.title = 'Reset zoom';
        this._resetBtn.style.display = 'none';
        this._resetBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.resetZoom();
        });
        this.container.appendChild(this._resetBtn);

        // Wheel zoom
        this.container.addEventListener('wheel', (e) => {
            if (!this.canvas) return;
            e.preventDefault();
            const rect = this.container.getBoundingClientRect();
            const cursorX = e.clientX - rect.left;
            const cursorY = e.clientY - rect.top;
            const delta = e.deltaY > 0 ? -this._zoomStep : this._zoomStep;
            this._applyZoom(delta, cursorX, cursorY);
        }, { passive: false });

        // Double-click reset
        this.container.addEventListener('dblclick', (e) => {
            if (!this.canvas) return;
            e.preventDefault();
            this.resetZoom();
        });

        // Mouse drag pan
        this.container.addEventListener('mousedown', (e) => {
            if (!this.canvas || this._zoom <= 1) return;
            // Don't start pan if clicking on a driver dot
            if (this._hitTestDrivers(e.clientX, e.clientY)) return;
            e.preventDefault();
            this._isPanning = true;
            this._panStartX = e.clientX;
            this._panStartY = e.clientY;
            this._panStartTransX = this._panX;
            this._panStartTransY = this._panY;
            this.container.style.cursor = 'grabbing';
        });

        // mousemove and mouseup are registered on document in the constructor
        // so they can be removed via destroy().

        // Touch: pinch-to-zoom + pan
        this.container.addEventListener('touchstart', (e) => {
            if (!this.canvas) return;
            if (e.touches.length === 2) {
                e.preventDefault();
                this._lastPinchDist = this._getTouchDist(e.touches);
            } else if (e.touches.length === 1 && this._zoom > 1) {
                const touch = e.touches[0];
                if (this._hitTestDrivers(touch.clientX, touch.clientY)) return;
                this._isPanning = true;
                this._panStartX = touch.clientX;
                this._panStartY = touch.clientY;
                this._panStartTransX = this._panX;
                this._panStartTransY = this._panY;
            }
        }, { passive: false });

        this.container.addEventListener('touchmove', (e) => {
            if (!this.canvas) return;
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

    _initRotationControls() {
        const { sliders, inputs, ctrl } = this._findOrCreateRotationControls();
        this._rotationSliders = sliders;
        this._rotationInputs = inputs;
        this._rotationCtrl = ctrl || null;
        this._wireRotationControls();
    }

    _findOrCreateRotationControls() {
        // Prefer controls already in the HTML (eng-view card header + drawer header).
        // Fall back to creating them in the container (fullscreen page).
        if (document.getElementById('trackMapRotationCtrl')) {
            return {
                ctrl: null,
                sliders: [
                    document.getElementById('trackMapRotationSlider'),
                    document.getElementById('trackMapDrawerRotationSlider'),
                ].filter(Boolean),
                inputs: [
                    document.getElementById('trackMapRotationInput'),
                    document.getElementById('trackMapDrawerRotationInput'),
                ].filter(Boolean),
            };
        }

        const ctrl = document.createElement('div');
        ctrl.className = 'track-map-rotation-ctrl';

        const label = document.createElement('i');
        label.className = 'bi bi-arrow-repeat track-map-rotation-label';

        const slider = document.createElement('input');
        slider.type = 'range';
        slider.className = 'track-map-rotation-slider';
        slider.min = 0;
        slider.max = 359;
        slider.value = 0;
        slider.step = 1;

        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'track-map-rotation-input';
        input.min = 0;
        input.max = 359;
        input.value = 0;
        input.step = 1;

        ctrl.appendChild(label);
        ctrl.appendChild(slider);
        ctrl.appendChild(input);

        return { ctrl, sliders: [slider], inputs: [input] };
    }

    _wireRotationControls() {
        const syncAll = (deg) => {
            this._rotation = deg;
            this._rotationSliders.forEach(s => s.value = deg);
            this._rotationInputs.forEach(i => i.value = deg);
            this._applyTransform();
            if (this._resetBtn) {
                this._resetBtn.style.display = deg !== 0 ? '' : 'none';
            }
        };

        this._rotationSliders.forEach(slider => {
            slider.addEventListener('input', () => {
                syncAll(parseInt(slider.value, 10));
            });
        });

        this._rotationInputs.forEach(input => {
            input.addEventListener('input', () => {
                const v = parseInt(input.value, 10);
                if (!Number.isNaN(v)) {
                    syncAll(((v % 360) + 360) % 360);
                }
            });
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
        if (!this._wrapper) return;
        const ww = this._wrapper.offsetWidth;
        const wh = this._wrapper.offsetHeight;
        const maxPanX = (this._zoom - 1) * ww / 2;
        const maxPanY = (this._zoom - 1) * wh / 2;
        this._panX = Math.max(-maxPanX, Math.min(maxPanX, this._panX));
        this._panY = Math.max(-maxPanY, Math.min(maxPanY, this._panY));
    }

    _applyTransform() {
        if (!this._wrapper) return;
        this._wrapper.style.transform =
            'translate(' + this._panX + 'px, ' + this._panY + 'px) rotate(' + this._rotation + 'deg) scale(' + this._zoom + ')';
    }

    _resetZoomState() {
        this._zoom = 1;
        this._panX = 0;
        this._panY = 0;
        this._rotation = 0;
        if (this._resetBtn) this._resetBtn.style.display = 'none';
        if (this._rotationSliders) this._rotationSliders.forEach(s => s.value = 0);
        if (this._rotationInputs) this._rotationInputs.forEach(i => i.value = 0);
    }

    /** Reset zoom and pan to default. */
    resetZoom() {
        this._resetZoomState();
        this._applyTransform();
    }
}
