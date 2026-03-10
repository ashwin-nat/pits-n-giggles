function initializeSocketIO(clientType, clientId) {
    const connectStart = Date.now();
    const eventHandlers = new Map();
    const pollTimers = [];
    const eventSources = [];
    let pollingStarted = false;
    let frontendUpdatePollingStarted = false;
    let sseStarted = false;
    let socketio = null;
    let lastFrontendUpdateId = null;

    function addHandler(event, handler) {
        if (!eventHandlers.has(event)) {
            eventHandlers.set(event, []);
        }
        eventHandlers.get(event).push(handler);
    }

    function emitLocal(event, payload) {
        const handlers = eventHandlers.get(event) || [];
        handlers.forEach((handler) => {
            try {
                handler(payload);
            } catch (err) {
                console.error(`Handler for ${event} failed:`, err);
            }
        });
    }

    function jsonToBinaryPayload(data) {
        return window.msgpack.encode(data).buffer;
    }

    function addSseListener(eventSource, eventName) {
        eventSource.addEventListener(eventName, (message) => {
            try {
                emitLocal(eventName, jsonToBinaryPayload(JSON.parse(message.data)));
            } catch (err) {
                console.error(`SSE payload decode failed for ${eventName}:`, err);
            }
        });
    }

    function startSseFallback() {
        if (sseStarted || typeof EventSource !== 'function') {
            return false;
        }

        let eventSourceConfigs = null;
        if (clientType === 'race-table') {
            eventSourceConfigs = [
                {
                    endpoint: '/events/race-table',
                    events: ['race-table-update']
                },
                {
                    endpoint: '/events/frontend-updates',
                    events: ['frontend-update']
                }
            ];
        } else if (clientType === 'player-stream-overlay') {
            eventSourceConfigs = [{
                endpoint: '/events/stream-overlay',
                events: ['stream-overlay-update']
            }];
        } else {
            return false;
        }

        sseStarted = true;
        console.warn(`Using SSE live updates for ${clientType}/${clientId}`);

        eventSourceConfigs.forEach((eventSourceConfig) => {
            const eventSource = new EventSource(eventSourceConfig.endpoint);
            eventSourceConfig.events.forEach((eventName) => addSseListener(eventSource, eventName));
            eventSource.onopen = () => {
                console.log(`SSE connected to ${eventSourceConfig.endpoint} in ${Date.now() - connectStart}ms`);
            };
            eventSource.onerror = () => {
                console.warn(`SSE connection degraded for ${eventSourceConfig.endpoint}`);
                eventSource.close();
                if (eventSourceConfig.endpoint === '/events/frontend-updates') {
                    startFrontendUpdatePollingFallback();
                } else if (eventSourceConfig.endpoint === '/events/race-table' || eventSourceConfig.endpoint === '/events/stream-overlay') {
                    startPollingFallback();
                }
            };
            eventSources.push(eventSource);
        });
        return true;
    }

    async function pollJson(endpoint, eventName) {
        try {
            const response = await fetch(endpoint, { cache: 'no-store' });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            emitLocal(eventName, jsonToBinaryPayload(data));
        } catch (err) {
            console.warn(`Polling ${endpoint} failed:`, err.message);
        }
    }

    async function pollFrontendUpdates() {
        try {
            const endpoint = lastFrontendUpdateId === null
                ? '/frontend-updates'
                : `/frontend-updates?after=${lastFrontendUpdateId}`;
            const response = await fetch(endpoint, { cache: 'no-store' });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            const entries = Array.isArray(data.entries) ? data.entries : [];
            entries.forEach((entry) => {
                lastFrontendUpdateId = entry.id;
                emitLocal('frontend-update', jsonToBinaryPayload(entry.payload));
            });
        } catch (err) {
            console.warn('Polling /frontend-updates failed:', err.message);
        }
    }

    function startFrontendUpdatePollingFallback() {
        if (frontendUpdatePollingStarted || clientType !== 'race-table') {
            return;
        }
        frontendUpdatePollingStarted = true;
        pollTimers.push(setInterval(() => pollFrontendUpdates(), 500));
        pollFrontendUpdates();
    }

    function startPollingFallback() {
        if (pollingStarted) {
            return;
        }
        pollingStarted = true;
        console.warn(`Falling back to HTTP polling for ${clientType}/${clientId}`);

        if (clientType === 'race-table') {
            pollTimers.push(setInterval(() => pollJson('/telemetry-info', 'race-table-update'), 250));
            pollJson('/telemetry-info', 'race-table-update');
            startFrontendUpdatePollingFallback();
        } else if (clientType === 'player-stream-overlay') {
            pollTimers.push(setInterval(() => pollJson('/stream-overlay-info', 'stream-overlay-update'), 100));
            pollJson('/stream-overlay-info', 'stream-overlay-update');
        }
    }

    const wrapper = {
        on(event, handler) {
            addHandler(event, handler);
            if (socketio) {
                socketio.on(event, handler);
            }
            return wrapper;
        },
        emit(event, payload) {
            if (socketio && socketio.connected) {
                socketio.emit(event, payload);
            }
            return wrapper;
        },
        connect() {
            if (startSseFallback()) {
                return wrapper;
            }
            if (socketio) {
                socketio.connect();
            } else {
                startPollingFallback();
            }
            return wrapper;
        },
        disconnect() {
            pollTimers.forEach((timer) => clearInterval(timer));
            eventSources.forEach((eventSource) => eventSource.close());
            if (socketio) {
                socketio.disconnect();
            }
            return wrapper;
        }
    };

    if (startSseFallback()) {
        return wrapper;
    }

    if (typeof io !== 'function') {
        console.warn('Socket.IO client unavailable, using polling fallback');
        startPollingFallback();
        return wrapper;
    }

    socketio = io(`${location.protocol}//${location.hostname}:${location.port}`, {
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        randomizationFactor: 0.3,
        timeout: 1500,
        transports: ['websocket', 'polling'],
        upgrade: true,
        rememberUpgrade: true,
        secure: location.protocol === 'https:',
    });

    console.log('SocketIO initialized');

    socketio.on('connect', () => {
        socketio.emit('register-client', { type: clientType, id: clientId });
        console.log(`Socket connected in ${Date.now() - connectStart}ms`);
    });

    socketio.on('connect_error', (err) => {
        console.warn('Socket connection error:', err.message);
        startPollingFallback();
    });

    socketio.on('reconnect_attempt', (attempt) => {
        console.log(`Reconnection attempt ${attempt}`);
    });

    socketio.on('reconnect', (attemptNumber) => {
        console.log(`Reconnected after ${attemptNumber} attempts`);
    });

    socketio.on('disconnect', (reason) => {
        console.log('Disconnected:', reason);
        if (reason === 'io server disconnect') {
            socketio.connect();
        }
    });

    socketio.on('reconnect_failed', () => {
        console.error('Socket reconnection failed, enabling polling fallback');
        startPollingFallback();
    });

    setTimeout(() => {
        if (!socketio.connected) {
            startPollingFallback();
        }
    }, 1500);

    return wrapper;
}
