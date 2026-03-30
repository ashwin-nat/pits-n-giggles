import QtQuick
import QtQuick.Window

Window {
    id: root
    width: 200
    height: 100
    visible: true
    color: "#00000000"   // transparent window

    property real scaleFactor: 1.0   // REQUIRED by BaseOverlayQML

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
