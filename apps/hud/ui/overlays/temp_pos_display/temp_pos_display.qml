import QtQuick
import QtQuick.Window

Window {
    id: root
    width: 200
    height: 100
    visible: true
    color: "black"

    property real scaleFactor: 1.0   // REQUIRED by BaseOverlayQML
    property real circuitPosM: 0.0

    Rectangle {
        anchors.fill: parent
        color: "black"

        Text {
            anchors.centerIn: parent
            text: root.circuitPosM.toFixed(2)
            color: "white"
            font.pixelSize: 18 * root.scaleFactor
        }
    }
}