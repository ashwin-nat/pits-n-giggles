import QtQuick
import QtQuick.Window
import QtQuick.Layouts


// pages/collapsed/collapsed_page.qml
Item {
    id: page
    implicitHeight: 36 * root.scaleFactor

    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.35

        Text {
            anchors.centerIn: parent
            text: root.collapsedTitle
            font.pixelSize: 13 * root.scaleFactor
            font.family: "Formula1"
            color: "white"
        }
    }
}
