pragma ComponentBehavior: Bound
import QtQuick 2.15

// Placeholder: UI is pending. `tyres` holds four entries (FL, FR, RL, RR) with
// position, compoundIcon, wear (%), coreTemp and surfaceTemp (C); values may be null.
Rectangle {
    id: root
    property string title: "TYRES STATUS"
    color: "transparent"

    property var tyres: []
    property bool telemetryDisabled: false

    Text {
        anchors.centerIn: parent
        text: root.telemetryDisabled ? "Telemetry disabled" : "Tyres Status"
        color: "#808080"
        font.pixelSize: 16
    }
}
