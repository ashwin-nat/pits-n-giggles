// Globals for preferences
let g_pref_is24HourFormat;
let g_pref_relativeDelta;
let g_pref_fuelTargetAverageFormat;
let g_pref_showFuelTarget;
let g_pref_fuelSurplusLapsPng;
let g_pref_lastLapAbsoluteFormat;
let g_pref_bestLapAbsoluteFormat;
let g_pref_tyreWearAverageFormat;
let g_pref_myTeamName;
let g_pref_numAdjacentCars;
let g_pref_numWeatherPredictionSamples;
let g_pref_ttsVoice;
let g_pref_ttsVolume;
let g_pref_tyreDeltaNotificationTtsFormat;
let g_pref_tyreDeltaNotificationOsdDurationSec;
let g_pref_speedUnitMetric;
let g_pref_tempUnitMetric;

function loadPreferences() {
    let missingPreference = false;

    // Load or assign default values, and track if any value is missing
    if (localStorage.getItem('is24HourFormat') !== null) {
        g_pref_is24HourFormat = localStorage.getItem('is24HourFormat') === 'true';
    } else {
        g_pref_is24HourFormat = true;
        missingPreference = true;
    }

    if (localStorage.getItem('g_pref_fuelSurplusLapsPng') !== null) {
        g_pref_fuelSurplusLapsPng = localStorage.getItem('g_pref_fuelSurplusLapsPng') === 'true';
    } else {
        g_pref_fuelSurplusLapsPng = true;
        missingPreference = true;
    }

    if (localStorage.getItem('showFuelTarget') !== null) {
        g_pref_showFuelTarget = localStorage.getItem('showFuelTarget') === 'true';
        console.log("Retrieved g_pref_showFuelTarget:", g_pref_showFuelTarget);
    } else {
        g_pref_showFuelTarget = false;
        missingPreference = true;
        console.log("Missing g_pref_showFuelTarget");
    }

    if (localStorage.getItem('fuelTargetAverageFormat') !== null) {
        g_pref_fuelTargetAverageFormat = localStorage.getItem('g_pref_fuelTargetAverageFormat') === 'true';
    } else {
        g_pref_fuelTargetAverageFormat = true;
        missingPreference = true;
    }

    if (localStorage.getItem('relativeDelta') !== null) {
        g_pref_relativeDelta = localStorage.getItem('relativeDelta') === 'true';
    } else {
        g_pref_relativeDelta = false;
        missingPreference = true;
    }

    if (localStorage.getItem('lastLapAbsoluteFormat') !== null) {
        g_pref_lastLapAbsoluteFormat = localStorage.getItem('lastLapAbsoluteFormat') === 'true';
    } else {
        g_pref_lastLapAbsoluteFormat = false;
        missingPreference = true;
    }

    if (localStorage.getItem('bestLapAbsoluteFormat') !== null) {
        g_pref_bestLapAbsoluteFormat = localStorage.getItem('bestLapAbsoluteFormat') === 'true';
    } else {
        g_pref_bestLapAbsoluteFormat = true;
        missingPreference = true;
    }

    if (localStorage.getItem('tyreWearAverageFormat') !== null) {
        g_pref_tyreWearAverageFormat = localStorage.getItem('tyreWearAverageFormat') === 'true';
    } else {
        g_pref_tyreWearAverageFormat = false;
        missingPreference = true;
    }

    g_pref_myTeamName = localStorage.getItem('myTeamName');
    if ((g_pref_myTeamName === null) || (g_pref_myTeamName === "")) {
        g_pref_myTeamName = "Custom Team";
        missingPreference = true;
    }

    g_pref_numAdjacentCars = localStorage.getItem('numAdjacentCars');
    if ((g_pref_numAdjacentCars === null) || (g_pref_numAdjacentCars === "")) {
        g_pref_numAdjacentCars = 2;
        missingPreference = true;
    } else {
        g_pref_numAdjacentCars = parseInt(g_pref_numAdjacentCars, 10); // localstorage saves everthing as string
    }

    g_pref_numWeatherPredictionSamples = localStorage.getItem('numWeatherPredictionSamples');
    if ((g_pref_numWeatherPredictionSamples === null) || (g_pref_numWeatherPredictionSamples === "")) {
        g_pref_numWeatherPredictionSamples = 3;
        missingPreference = true;
    } else {
        g_pref_numWeatherPredictionSamples = parseInt(g_pref_numWeatherPredictionSamples, 10); // localstorage saves everthing as string
    }

    g_pref_ttsVoice = localStorage.getItem('ttsVoice');
    if ((g_pref_ttsVoice === null)) {
        g_pref_ttsVoice = "";
        missingPreference = true;
    }

    g_pref_ttsVolume = localStorage.getItem('ttsVolume');
    if ((g_pref_ttsVolume === null)) {
        g_pref_ttsVolume = 100;
        missingPreference = true;
    } else {
        g_pref_ttsVolume = parseInt(g_pref_ttsVolume, 10);
    }

    if (localStorage.getItem('tyreDeltaNotificationTtsFormat') !== null) {
        g_pref_tyreDeltaNotificationTtsFormat = localStorage.getItem('tyreDeltaNotificationTtsFormat') === 'true';
    } else {
        g_pref_tyreDeltaNotificationTtsFormat = true;
        missingPreference = true;
    }

    g_pref_tyreDeltaNotificationOsdDurationSec = localStorage.getItem('tyreDeltaNotificationOsdDurationSec');
    if ((g_pref_tyreDeltaNotificationOsdDurationSec === null) || (g_pref_tyreDeltaNotificationOsdDurationSec === "")) {
        g_pref_tyreDeltaNotificationOsdDurationSec = 5;
        missingPreference = true;
    } else {
        g_pref_tyreDeltaNotificationOsdDurationSec = parseInt(g_pref_tyreDeltaNotificationOsdDurationSec, 10); // localstorage saves everthing as string
    }

    if (localStorage.getItem('speedUnitMetric') !== null) {
        g_pref_speedUnitMetric = localStorage.getItem('speedUnitMetric') === 'true';
    } else {
        g_pref_speedUnitMetric = true;
        missingPreference = true;
    }

    if (localStorage.getItem('tempUnitMetric') !== null) {
        g_pref_tempUnitMetric = localStorage.getItem('tempUnitMetric') === 'true';
    } else {
        g_pref_tempUnitMetric = true;
        missingPreference = true;
    }

    // If any preference was missing, save all current preferences
    if (missingPreference) {
        savePreferences();
    }

    console.log("Loaded Preferences:", {
        g_pref_myTeamName,
        g_pref_is24HourFormat,
        g_pref_lastLapAbsoluteFormat,
        g_pref_bestLapAbsoluteFormat,
        g_pref_tyreWearAverageFormat,
        g_pref_relativeDelta,
        g_pref_fuelSurplusLapsPng,
        g_pref_showFuelTarget,
        g_pref_fuelTargetAverageFormat,
        g_pref_numAdjacentCars,
        g_pref_numWeatherPredictionSamples,
        g_pref_ttsVoice,
        g_pref_ttsVolume,
        g_pref_tyreDeltaNotificationTtsFormat,
        g_pref_tyreDeltaNotificationOsdDurationSec,
        g_pref_speedUnitMetric,
        g_pref_tempUnitMetric
    });
    updateAllTooltips();
}

function savePreferences() {
    localStorage.setItem('is24HourFormat', g_pref_is24HourFormat);
    localStorage.setItem('relativeDelta', g_pref_relativeDelta);
    localStorage.setItem('fuelSurplusLapsPng', g_pref_fuelSurplusLapsPng);
    localStorage.setItem('showFuelTarget', g_pref_showFuelTarget);
    localStorage.setItem('fuelTargetAverageFormat', g_pref_fuelTargetAverageFormat);
    localStorage.setItem('lastLapAbsoluteFormat', g_pref_lastLapAbsoluteFormat);
    localStorage.setItem('bestLapAbsoluteFormat', g_pref_bestLapAbsoluteFormat);
    localStorage.setItem('tyreWearAverageFormat', g_pref_tyreWearAverageFormat);
    localStorage.setItem('myTeamName', g_pref_myTeamName);
    localStorage.setItem('numAdjacentCars', g_pref_numAdjacentCars);
    localStorage.setItem('numWeatherPredictionSamples', g_pref_numWeatherPredictionSamples);
    localStorage.setItem('ttsVoice', g_pref_ttsVoice);
    localStorage.setItem('ttsVolume', g_pref_ttsVolume);
    localStorage.setItem('tyreDeltaNotificationTtsFormat', g_pref_tyreDeltaNotificationTtsFormat);
    localStorage.setItem('tyreDeltaNotificationOsdDurationSec', g_pref_tyreDeltaNotificationOsdDurationSec);
    localStorage.setItem('speedUnitMetric', g_pref_speedUnitMetric);
    localStorage.setItem('tempUnitMetric', g_pref_tempUnitMetric);

    console.log("Saved Preferences:", {
        g_pref_myTeamName,
        g_pref_is24HourFormat,
        g_pref_fuelSurplusLapsPng,
        g_pref_showFuelTarget,
        g_pref_fuelTargetAverageFormat,
        g_pref_lastLapAbsoluteFormat,
        g_pref_bestLapAbsoluteFormat,
        g_pref_tyreWearAverageFormat,
        g_pref_relativeDelta,
        g_pref_numAdjacentCars,
        g_pref_numWeatherPredictionSamples,
        g_pref_ttsVoice,
        g_pref_ttsVolume,
        g_pref_tyreDeltaNotificationTtsFormat,
        g_pref_tyreDeltaNotificationOsdDurationSec,
        g_pref_speedUnitMetric,
        g_pref_tempUnitMetric
    });

    updateAllTooltips();
}

function updateAllTooltips() {

    updateTooltip("best-lap-th", `Click to toggle between absolute and relative format. Current format is ${
                                                    (g_pref_bestLapAbsoluteFormat) ? ("Absolute") : ("Relative")}`);
    updateTooltip("last-lap-th", `Click to toggle between absolute and relative format. Current format is ${
                                                    (g_pref_lastLapAbsoluteFormat) ? ("Absolute") : ("Relative")}`);
    updateTooltip("delta-th", `Click to toggle between absolute and relative format. Current format is ${
                                                    (!g_pref_relativeDelta) ? ("Absolute") : ("Relative")}`);
    updateTooltip("tyre-info-th", `Click to toggle between average and max wear format. Current format is ${
                                                    (g_pref_tyreWearAverageFormat) ? ("Average") : ("yre with max wear")}`);
    updateTooltip("wear-prediction-th", `Click to toggle between average and max wear format. Current format is ${
                                                    (g_pref_tyreWearAverageFormat) ? ("Average") : ("Tyre with max wear")}`);
    if (g_pref_showFuelTarget) {
        updateTooltip("fuel-info-th", `Click to toggle between target fuel format. Current format is ${
            (g_pref_fuelTargetAverageFormat) ? ("Average target fuel rate") :
            ("Fuel usage target for next lap")}`);
    } else {
        updateTooltip("fuel-info-th", `Target fuel rate is disabled. Enable it via the settings`);
    }
    updateTooltip("tt-vmax-th", `Top Speed. Click to toggle between km/h and mph. Current format is ${
                                                    (g_pref_speedUnitMetric) ? ("km/h") : ("mph")}`);
}

function updateTooltip(id, newText) {
    let element = document.getElementById(id);
    element.setAttribute("data-bs-title", newText); // Update tooltip text

    // Reinitialize Bootstrap tooltip to reflect the change
    let tooltip = bootstrap.Tooltip.getInstance(element);
    if (tooltip) {
        tooltip.dispose(); // Remove existing instance
    }
    new bootstrap.Tooltip(element); // Reinitialize with new title
}
