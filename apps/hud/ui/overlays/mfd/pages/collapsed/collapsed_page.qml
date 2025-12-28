// pages/collapsed/collapsed_page.qml
import QtQuick

Item {
    id: page
    width: parent ? parent.width : 0
    implicitHeight: 36 * root.scaleFactor

    property string title: "MFD test 69420"

    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.35

        Text {
            anchors.centerIn: parent
            text: page.title
            font.pixelSize: 13 * root.scaleFactor
            font.family: "Formula1"
            color: "white"
        }
    }
}
