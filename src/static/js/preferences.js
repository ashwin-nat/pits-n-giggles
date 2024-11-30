// Globals for preferences
let g_pref_is24HourFormat;
let g_pref_relativeDelta;
let g_pref_lastLapAbsoluteFormat;
let g_pref_bestLapAbsoluteFormat;
let g_pref_tyreWearAverageFormat;
let g_pref_myTeamName;
let g_pref_numAdjacentCars;
let g_pref_numWeatherPredictionSamples;

function loadPreferences() {
    let missingPreference = false;

    // Load or assign default values, and track if any value is missing
    if (localStorage.getItem('is24HourFormat') !== null) {
        g_pref_is24HourFormat = localStorage.getItem('is24HourFormat') === 'true';
    } else {
        g_pref_is24HourFormat = true;
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
        g_pref_numAdjacentCars,
        g_pref_numWeatherPredictionSamples,
    });
}

function savePreferences() {
    localStorage.setItem('is24HourFormat', g_pref_is24HourFormat);
    localStorage.setItem('relativeDelta', g_pref_relativeDelta);
    localStorage.setItem('lastLapAbsoluteFormat', g_pref_lastLapAbsoluteFormat);
    localStorage.setItem('bestLapAbsoluteFormat', g_pref_bestLapAbsoluteFormat);
    localStorage.setItem('tyreWearAverageFormat', g_pref_tyreWearAverageFormat);
    localStorage.setItem('myTeamName', g_pref_myTeamName);
    localStorage.setItem('numAdjacentCars', g_pref_numAdjacentCars);
    localStorage.setItem('numWeatherPredictionSamples', g_pref_numWeatherPredictionSamples);

    console.log("Saved Preferences:", {
        g_pref_myTeamName,
        g_pref_is24HourFormat,
        g_pref_lastLapAbsoluteFormat,
        g_pref_bestLapAbsoluteFormat,
        g_pref_tyreWearAverageFormat,
        g_pref_relativeDelta,
        g_pref_numAdjacentCars,
        g_pref_numWeatherPredictionSamples,
    });
}