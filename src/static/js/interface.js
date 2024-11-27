socket.on('connect', function () {
    socket.emit('register-client', { type: 'race-table' });
});

// Receive details from server
socket.on('race-table-update', function (data) {
    displayData(data);
});

socket.on('race-info-response', function (data) {
    clearSocketIoRequestTimeout();
    if (!('error' in data)) {
        openRaceInfoModal(data);
    } else {
        console.log("Received error for race-info request", data);
    }
});

socket.on('driver-info-response', function (data) {
    clearSocketIoRequestTimeout();
    if (!('error' in data)) {
        openDriverInfoModal(data);
    } else {
        console.log("Received error for driver-info request", data);
        showToast("Received error for driver info request");
    }
});