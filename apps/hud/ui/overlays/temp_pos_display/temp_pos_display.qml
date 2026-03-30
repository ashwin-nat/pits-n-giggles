import QtQuick
import QtQuick.Window

Window {
    id: root
    width: 200
    height: 100
    visible: true
    color: "black"

    property real scaleFactor: 1.0   // REQUIRED by BaseOverlayQML
    property string circuitPosM: ""

    Rectangle {
        anchors.fill: parent
        color: "black"

        Text {
            anchors.centerIn: parent
            text: root.circuitPosM
            color: "white"
            font.pixelSize: 18 * root.scaleFactor
        }
    }
}