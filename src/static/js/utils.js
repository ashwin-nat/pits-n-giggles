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

    if (playerLapTime === 0 || playerLapTime === null) {
        // player has not set a lap yet. so show absolute value
        return formatLapTime(lapTime);
    }

    return formatDelta(lapTime - playerLapTime);
}

function showToast(message, timeout = 3000) {
    // Select the toast container (create if it doesn't exist)
    const toastContainer = document.querySelector('.toast-container');
    let toastElement = document.getElementById('liveToast');

    if (!toastElement) {
        toastElement = document.createElement('div');
        toastElement.id = 'liveToast';
        toastElement.className = 'toast';
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');
        toastElement.innerHTML = `
        <div class="toast-body"></div>
      `;
        toastContainer.appendChild(toastElement);
    }

    // Update the toast message
    const bodyContent = toastElement.querySelector('.toast-body');
    bodyContent.textContent = message;

    // Apply dark theme styling
    toastElement.style.backgroundColor = '#333'; // Dark background
    bodyContent.style.color = '#fff'; // White text for visibility
    toastElement.style.borderRadius = '20px'; // Rounded corners for Android-like look
    toastElement.style.padding = '10px 20px'; // Some padding for comfort

    // Show the toast with a custom timeout
    const toast = new bootstrap.Toast(toastElement, { delay: timeout });
    toast.show();
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

function getTeamName(teamId) {
    if ("MY_TEAM" == teamId) {
        return g_pref_myTeamName;
    } else {
        return teamId;
    }
}
function textToSpeech(text) {
    // Create a new SpeechSynthesisUtterance object with the provided text
    const speech = new SpeechSynthesisUtterance(text);
    console.log(window.speechSynthesis.getVoices());

    // Optionally, you can customize the speech parameters (e.g., rate, pitch, etc.)
    speech.rate = 1;    // Normal speed
    speech.pitch = 1;   // Normal pitch
    speech.volume = 1;  // Full volume

    // Speak the text out loud
    window.speechSynthesis.speak(speech);
  }