function formatLapTime(milliseconds) {
    // Check if the input is 0 or null
    if (milliseconds === 0 || milliseconds === null) {
        return "---";
    }
    let minutes = Math.floor(milliseconds / 60000);
    let seconds = Math.floor((milliseconds % 60000) / 1000);
    let millisecondsPart = milliseconds % 1000;
    return minutes.toString().padStart(2, '0') + ":" +
        seconds.toString().padStart(2, '0') + "." +
        millisecondsPart.toString().padStart(3, '0'); // Ensure it's 3 digits
}

function formatLapDelta(lapTime, playerLapTime, isPlayer) {
    function formatDelta(delta) {
        // Determine the sign
        const sign = delta >= 0 ? '+' : '-';

        // Get the absolute value of delta for formatting
        const absDelta = Math.abs(delta);

        // Calculate seconds and milliseconds
        const seconds = Math.floor(absDelta / 1000);
        const milliseconds = absDelta % 1000;

        // Format the string as "±seconds.milliseconds"
        return sign + seconds + '.' + milliseconds.toString().padStart(3, '0'); // Ensure milliseconds are 3 digits
    }

    if (isPlayer) {
        return formatLapTime(playerLapTime);
    }

    if (lapTime === 0 || lapTime === null) {
        return "---";
    }

    if(playerLapTime === 0 || playerLapTime === null) {
        // player has not set a lap yet. so show absolute value
        return formatLapTime(lapTime);
    }

    return formatDelta(lapTime - playerLapTime);
}

function showToast(message) {
    // Create a new div element for the toast
    let toast = document.createElement('div');
    toast.classList.add('toast');

    // Set the message content
    toast.innerText = message;

    // Append the toast to the document body
    document.body.appendChild(toast);

    // Show the toast
    toast.style.opacity = 1;

    // Hide the toast after 3 seconds
    setTimeout(function() {
        toast.style.opacity = 0;
        // Remove the toast from the document after it fades out
        setTimeout(function() {
        document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

function formatFloatWithTwoDecimals(floatNumber) {
    if (typeof floatNumber !== 'number' || isNaN(floatNumber)) {
        console.error('Invalid input. Please provide a valid number.');
        return null;
    }

    // Use toFixed to round to two decimal places and convert to string
    return floatNumber.toFixed(2);
}

function formatFloatWithTwoDecimalsSigned(floatNumber) {
    if (typeof floatNumber !== 'number' || isNaN(floatNumber)) {
        console.error('Invalid input. Please provide a valid number.');
        return null;
    }

    // Use toFixed to round to two decimal places and convert to string
    const floatStr = floatNumber.toFixed(2);
    if (floatNumber >= 0.0) {
        return '+' + floatStr;
    } else {
        return floatStr;
    }
}

function getTyreCompoundStr(visualTyreCompound, actualTyreCompound) {

    if (visualTyreCompound == "Inters" || visualTyreCompound == "Wet") {
        return visualTyreCompound;
    } else {
        return actualTyreCompound + " - " + visualTyreCompound;
    }
}

function getMaxTyreWear(wearData) {
    const relevantKeys = {
        "front-left-wear": "FL",
        "front-right-wear": "FR",
        "rear-left-wear": "RL",
        "rear-right-wear": "RR"
    };

    let maxKey = null;
    let maxValue = -Infinity;

    // Iterate only through relevant keys
    for (const key in relevantKeys) {
        if (key in wearData && wearData[key] > maxValue) {
            maxValue = wearData[key];
            maxKey = key;
        }
    }

    // Return the result as a JSON object with max-key shortened and max-wear
    return {
        "max-key": relevantKeys[maxKey],  // Use the shortened version
        "max-wear": maxValue
    };
}

function showToast(message) {
    // Create a new div element for the toast
    let toast = document.createElement('div');
    toast.classList.add('toast');

    // Set the message content
    toast.innerText = message;

    // Append the toast to the document body
    document.body.appendChild(toast);

    // Show the toast
    toast.style.opacity = 1;

    // Hide the toast after 3 seconds
    setTimeout(function() {
        toast.style.opacity = 0;
        // Remove the toast from the document after it fades out
        setTimeout(function() {
        document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

function getTeamName(teamId) {
    if ("MY_TEAM" == teamId) {
        return g_pref_myTeamName;
    } else {
        return teamId;
    }
}