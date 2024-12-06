function processTyreDeltaMessage(data) {
    console.log("received tyre delta update", data);
    let messageText = "";
    messageText += data['curr-tyre-type'] + " tyres are ";

    if (data['tyre-delta'] == 0) {
        messageText += "the same as ";
    } else if (data['tyre-delta'] > 0) {
        messageText += "faster than ";
    } else {
        messageText += "slower than ";
    }
    messageText += data['other-tyre-type'] + " tyres by " + formatFloatWithTwoDecimals(Math.abs(data['tyre-delta'])) + " seconds";
    console.log("TTS text", messageText);

    textToSpeech(messageText);
}

function processCustomMarkerMessage(data) {
    console.log("processCustomMarkerMessage", data);
}