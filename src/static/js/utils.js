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
        console.trace(); // Log the call stack
        return null;
    }

    // Use toFixed to round to two decimal places and convert to string
    return floatNumber.toFixed(2);
}

function formatFloatWithTwoDecimalsSigned(floatNumber) {
    if (typeof floatNumber !== 'number' || isNaN(floatNumber)) {
        console.error('Invalid input. Please provide a valid number.');
        console.trace(); // Log the call stack
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
function textToSpeech(text, volume=g_pref_ttsVolume) {
    // Create a new SpeechSynthesisUtterance object with the provided text
    const speech = new SpeechSynthesisUtterance(text);

    // Retrieve the list of available voices
    const voices = window.speechSynthesis.getVoices();

    // Use the variable g_pref_ttsVoice to select the voice
    const preferredVoiceName = g_pref_ttsVoice; // Replace this with your preferred voice variable
    const preferredVoice = voices.find(voice => voice.name === preferredVoiceName);

    if (preferredVoice) {
        speech.voice = preferredVoice; // Assign the preferred voice to the utterance
    } else {
        console.warn(`Voice "${preferredVoiceName}" not found. Using the default voice.`);
    }

    // Optionally, you can customize the speech parameters
    speech.rate = 1;    // Normal speed
    speech.pitch = 1;   // Normal pitch
    speech.volume = (g_pref_ttsVolume / 100);  // Full volume

    // Speak the text out loud
    window.speechSynthesis.speak(speech);
}


function flattenJsonObject(obj) {
    const result = {};
    const suffixes = ["rl", "rr", "fl", "fr"];
    const stack = [{ currentObj: obj, currentKey: "" }];

    while (stack.length > 0) {
        const { currentObj, currentKey } = stack.pop();

        for (const key in currentObj) {
            const value = currentObj[key];
            const newKey = currentKey ? `${currentKey}.${key}` : key;

            if (Array.isArray(value)) {
                // Unroll the array with specific suffixes
                value.forEach((element, index) => {
                    if (index < suffixes.length) {
                        result[`${newKey}-${suffixes[index]}`] = element;
                    }
                });
            } else if (typeof value === 'object' && value !== null) {
                // Push nested objects onto the stack for further processing
                stack.push({ currentObj: value, currentKey: newKey });
            } else {
                // Assign the value to the result
                result[newKey] = value;
            }
        }
    }

    return result;
}

function splitJsonObject(obj) {
    const keys = Object.keys(obj);
    const mid = Math.ceil(keys.length / 2);

    const firstHalf = {};
    const secondHalf = {};

    keys.forEach((key, index) => {
        if (index < mid) {
            firstHalf[key] = obj[key];
        } else {
            secondHalf[key] = obj[key];
        }
    });

    return { firstHalf, secondHalf };
}

function kebabToTitleCase(str) {
    return str
        .split('-')          // Split the string by the hyphen
        .map(word => word.charAt(0).toUpperCase() + word.slice(1)) // Capitalize the first letter of each word
        .join(' ');          // Join the words with a space
}

function splitArray(array) {
    const mid = Math.ceil(array.length / 2); // Find the midpoint
    const firstHalf = array.slice(0, mid); // Elements from index 0 to mid (not inclusive)
    const secondHalf = array.slice(mid);   // Elements from mid to the end

    return { firstHalf, secondHalf };
}

function clearTable(tableElement, clearHeader = false) {
    const minTableRowsCount = clearHeader ? 0 : 1;

    // Remove rows starting from the last row
    while (tableElement.rows.length > minTableRowsCount) {
        tableElement.deleteRow(tableElement.rows.length - 1); // Always delete the last row
    }
}

function getTyreIconSpan(tyreCompound) {

    // Get the first letter of the compound or an empty string if compound is empty
    const firstLetter = tyreCompound.charAt(0);  // Get the first letter of the compound

    // Create a span element to hold the first letter
    const span = document.createElement('span');
    span.textContent = firstLetter;

    // Apply class for styling
    span.classList.add('tyre-icon');

    switch (tyreCompound) {
        case "Soft":
            span.classList.add('soft-tyre');
            break;
        case "Medium":
            span.classList.add('medium-tyre');
            break;
        case "Hard":
            span.classList.add('hard-tyre');
            break;
        case "Inters":
            span.classList.add('intermediate-tyre');
            break;
        case "Wet":
            span.classList.add('wet-tyre');
            break;
    }

    return span;
}

function formatSecondsToMMSS(seconds) {
    // Ensure the input is a number
    if (typeof seconds !== 'number' || seconds < 0) {
        throw new Error('Input should be a non-negative integer representing seconds.');
    }

    // Calculate minutes and remaining seconds
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    // Format minutes and seconds with leading zeros if necessary
    const formattedMinutes = String(minutes).padStart(2, '0');
    const formattedSeconds = String(remainingSeconds).padStart(2, '0');

    // Return formatted time string
    return `${formattedMinutes}:${formattedSeconds}`;
}
