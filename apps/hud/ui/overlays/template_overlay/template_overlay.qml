import QtQuick
import QtQuick.Window
import "../base"

OverlayWindow {
    id: root
    width: 200
    height: 100
    visible: true

    property real scaleFactor: 1.0   // REQUIRED by BaseOverlay

    Rectangle {
        anchors.fill: parent
        color: "#66000000"

        Text {
            anchors.centerIn: parent
            text: "Minimal Overlay"
            color: "white"
            font.pixelSize: 18 * root.scaleFactor
        }
    }
}
