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
    }

    speech.rate = 1.2;    // Normal speed
    speech.pitch = 1;   // Normal pitch
    speech.volume = (volume / 100);  // Full volume

    // Speak the text out loud
    window.speechSynthesis.speak(speech);
}

function processTyreDeltaMessage(data) {
    let messageText = "";
    messageText += data['curr-tyre-type'] + " tyres are ";

    if (data['tyre-delta'] == 0) {
        messageText += "the same as " + data['other-tyre-type'] + " tyres"; // No "by ..."
    } else if (data['tyre-delta'] > 0) {
        messageText += "faster than ";
        messageText += data['other-tyre-type'] + " tyres by " + formatFloatWithTwoDecimals(Math.abs(data['tyre-delta'])) + " seconds";
    } else {
        messageText += "slower than ";
        messageText += data['other-tyre-type'] + " tyres by " + formatFloatWithTwoDecimals(Math.abs(data['tyre-delta'])) + " seconds";
    }

    console.log("received tyre delta update", data, "TTS text", messageText);
    textToSpeech(messageText);
}

function processCustomMarkerMessage(data) {
    console.log("processCustomMarkerMessage", data);
}

function processFinalClassificationNotification(data) {
    console.log("processFinalClassificationNotification", data);
    const playerPosition = data['player-position'];
    if (playerPosition && playerPosition >= 1 && playerPosition <= 3) {
        console.log("Podium finish! Player position:", playerPosition);
        const confettDurationMs = 10000;
        shootConfetti(confettDurationMs);
    }
}
