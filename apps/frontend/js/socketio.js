function initializeSocketIO(clientType, clientId) {
    const connectStart = Date.now();

    const socketio = io(`${location.protocol}//${location.hostname}:${location.port}`, {
        reconnection: true,
        reconnectionAttempts: Infinity,  // keep trying indefinitely
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        randomizationFactor: 0.3,
        timeout: 10000,
        transports: ['websocket', 'polling'],
        upgrade: true,
        rememberUpgrade: true,
        secure: location.protocol === 'https:',
    });

    console.log("SocketIO initialized");

    // Connection successful
    socketio.on('connect', () => {
        socketio.emit('register-client', { type: clientType, id: clientId });
        console.log(`⏱️ Socket connected in ${Date.now() - connectStart}ms`);
    });

    // Connection error
    socketio.on('connect_error', (err) => {
        console.warn('❌ Socket connection error:', err.message);
    });

    // Reconnection attempts
    socketio.on('reconnect_attempt', (attempt) => {
        console.log(`🔁 Reconnection attempt ${attempt}`);
    });

    // Successful reconnection
    socketio.on('reconnect', (attemptNumber) => {
        console.log(`✅ Reconnected after ${attemptNumber} attempts`);
    });

    // Disconnection
    socketio.on('disconnect', (reason) => {
        console.log('✗ Disconnected:', reason);

        // Server forcefully disconnected - manually reconnect
        if (reason === 'io server disconnect') {
            console.log('Server disconnected - attempting manual reconnect...');
            socketio.connect();
        }
    });

    // Reconnection failed
    socketio.on('reconnect_failed', () => {
        console.error('❌ Reconnection failed after all attempts');
    });

    return socketio;
}
