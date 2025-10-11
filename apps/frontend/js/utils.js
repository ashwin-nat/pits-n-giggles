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

function formatSectorTime(milliseconds) {
    // Check if the input is 0 or null
    if (milliseconds === 0 || milliseconds === null) {
        return "--.---";
    }
    return (milliseconds / 1000).toFixed(3);
}

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

function formatLapDelta(lapTime, playerLapTime, isPlayer) {

    if (isPlayer) {
        return formatLapTime(lapTime);
    }

    if (lapTime === 0 || lapTime === null) {
        return "---";
    }

    if (playerLapTime === 0 || playerLapTime === null) {
        // player has not set a lap yet. so show absolute value
        return formatLapTime(lapTime);
    }

    return formatDelta(playerLapTime - lapTime);
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

function formatFloat(floatNumber, { precision = 2, signed = false } = {}) {
    if (typeof floatNumber !== 'number' || isNaN(floatNumber)) {
        console.error('Invalid input. Please provide a valid number.', floatNumber);
        console.trace();
        return null;
    }

    const floatStr = floatNumber.toFixed(precision);

    if (signed && floatNumber >= 0) {
        return '+' + floatStr;
    }

    return floatStr;
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

function randomInRange(min, max) {
    return Math.random() * (max - min) + min;
}

function shootConfetti(durationMs) {
    const animationEnd = Date.now() + durationMs;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    const interval = setInterval(function() {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
            return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / durationMs);

        // since particles fall down, start a bit higher than random
        confetti(
            Object.assign({}, defaults, {
            particleCount,
            origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
            })
        );
        confetti(
            Object.assign({}, defaults, {
                particleCount,
                origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
            }));
    }, 250);
}

/**
 * mutate the input JSON and inserts reference lap times into every driver object
 * @param {Array} tableEntriesJson - Array of table entry objects.
 * @param {Function} matchFn - Function to identify the reference entry.
 * @returns {Array} New array with updated lap times.
 */
function updateReferenceLapTimes(tableEntriesJson, matchFn = (entry) => entry["driver-info"]?.["is-player"]) {
  const referenceEntry = tableEntriesJson.find(matchFn);

  if (referenceEntry) {
    const refLastLap = referenceEntry["lap-info"]["last-lap"];
    const refBestLap = referenceEntry["lap-info"]["best-lap"];
    const referenceIndex = referenceEntry["driver-info"]?.["index"];

    tableEntriesJson.forEach((tableEntry) => {
      const isReference = tableEntry["driver-info"]?.["index"] === referenceIndex;

      const lastLap = tableEntry["lap-info"]["last-lap"];
      const bestLap = tableEntry["lap-info"]["best-lap"];

      if (isReference) {
        // Copy from self
        lastLap["lap-time-ms-player"] = lastLap["lap-time-ms"];
        lastLap["s1-time-ms-player"] = lastLap["s1-time-ms"];
        lastLap["s2-time-ms-player"] = lastLap["s2-time-ms"];
        lastLap["s3-time-ms-player"] = lastLap["s3-time-ms"];

        bestLap["lap-time-ms-player"] = bestLap["lap-time-ms"];
        bestLap["s1-time-ms-player"] = bestLap["s1-time-ms"];
        bestLap["s2-time-ms-player"] = bestLap["s2-time-ms"];
        bestLap["s3-time-ms-player"] = bestLap["s3-time-ms"];
      } else {
        // Copy from reference
        lastLap["lap-time-ms-player"] = refLastLap["lap-time-ms"];
        lastLap["s1-time-ms-player"] = refLastLap["s1-time-ms"];
        lastLap["s2-time-ms-player"] = refLastLap["s2-time-ms"];
        lastLap["s3-time-ms-player"] = refLastLap["s3-time-ms"];

        bestLap["lap-time-ms-player"] = refBestLap["lap-time-ms"];
        bestLap["s1-time-ms-player"] = refBestLap["s1-time-ms"];
        bestLap["s2-time-ms-player"] = refBestLap["s2-time-ms"];
        bestLap["s3-time-ms-player"] = refBestLap["s3-time-ms"];
      }
    });
  }
}

function getFormattedLapTimeStr({
    lapTimeMs,
    lapTimeMsPlayer,
    isPlayer,
    index,
    spectatorIndex,
    showAbsoluteFormat,
    isSaveViewerMode
}) {
    const isReferenceCar = (!isSaveViewerMode) && spectatorIndex === index;
    const missingPlayerLap = lapTimeMsPlayer == null;

    const shouldShowAbsolute =
        showAbsoluteFormat ||
        isPlayer ||
        isReferenceCar ||
        isSaveViewerMode ||
        missingPlayerLap;

    if (shouldShowAbsolute) {
        return formatLapTime(lapTimeMs);
    }

    return formatLapDelta(lapTimeMs, lapTimeMsPlayer, isPlayer, index);
}

function replaceRevSuffix(str) {
    if (str.endsWith("_Reverse")) {
        return str.replace("_Reverse", " ⇄");
    }
    return str;
}

function formatSpeed(speedKmph, { isMetric = true, decimalPlaces = 1, addUnitSuffix = true } = {}) {
    if (typeof speedKmph !== 'number' || !isFinite(speedKmph)) {
        throw new Error(`Invalid speed: expected a finite number, got ${speedKmph} (type: ${typeof speedKmph})`);
    }

    let speed = speedKmph;
    let unit = 'km/h';

    if (!isMetric) {
        speed *= 0.621371; // Convert km/h to mph
        unit = 'mph';
    }

    const rounded = speed.toFixed(decimalPlaces);
    return addUnitSuffix ? `${rounded} ${unit}` : `${rounded}`;
}

function formatTemperature(tempCelsius, { isMetric = true, decimalPlaces = 1, addUnitSuffix = true } = {}) {
    if (typeof tempCelsius !== 'number' || !isFinite(tempCelsius)) {
        throw new Error(`Invalid temperature: expected a finite number, got ${tempCelsius} (type: ${typeof tempCelsius})`);
    }

    let temp = tempCelsius;
    let unit = '°C';

    if (!isMetric) {
        temp = (temp * 9 / 5) + 32; // Convert to Fahrenheit
        unit = '°F';
    }

    const rounded = temp.toFixed(decimalPlaces);
    return addUnitSuffix ? `${rounded} ${unit}` : `${rounded}`;
}

/**
 * Insert pit rejoin position into each driver's JSON (mutates input).
 * @param {Object[]} drivers - full grid of driver data JSON objects sorted by position
 * @param {number} pitLoss - estimated pit stop loss (s)
 */
function insertRejoinPositions(drivers, pitLoss) {
    if (pitLoss === null) {
        return;
    }
    const gaps = drivers.map(d => d["delta-info"]["delta-to-leader"]);
    const n = gaps.length;
    const pitLossMs = pitLoss * 1000;

    for (let i = 0; i < n; i++) {
        const driver = drivers[i];
        const rejoinGap = gaps[i] + pitLossMs;

        // Find first car whose gap is greater than rejoinGap
        let pos = gaps.findIndex(g => g > rejoinGap);
        if (pos === -1) {
            pos = n; // behind the whole field
        }

        driver["tyre-info"]["pit-rejoin-position"] = pos;
    }
}

function isPracticeSession(sessionType) {
    return sessionType.includes('Practice');
}

function isQualiSession(sessionType) {
    return (sessionType.includes('Qualifying') || sessionType.includes('Shootout'));
}

function isRaceSession(sessionType) {
    return !isPracticeSession(sessionType) && !isQualiSession(sessionType);
}

function getTLA(name) {
  if (!name || typeof name !== 'string') return '';

  let clean = name.trim();

  // Remove leading or trailing clan/guild tags in common formats
  clean = clean
    .replace(/^(\s*[\[\(\{<\$|]+.*?[\]\)\}>\$|]+\s*)+/, '') // leading tags like [TAG], $TAG$, |TAG|
    .replace(/(\s*[\[\(\{<\$|]+.*?[\]\)\}>\$|]+\s*)+$/, '') // trailing tags
    .replace(/^\s*[-_]+\s*/, '')                            // leading dashes/underscores
    .replace(/\s*[-_]+\s*$/, '')                            // trailing dashes/underscores
    .replace(/^\s*\|\s*/, '')                               // leading pipe separator
    .replace(/\s*\|\s*$/, '')                               // trailing pipe separator
    .trim();

  // If there's a separator (like "Clan | Player" or "Team - Player"), take the rightmost segment
  const parts = clean.split(/\s*\|\s*|\s*-\s*/);
  clean = parts[parts.length - 1].trim();

  // Keep only alphanumeric characters
  clean = clean.replace(/[^a-zA-Z0-9]/g, '');

  // Return first 3 uppercase letters
  return clean.substring(0, 3).toUpperCase();
}
