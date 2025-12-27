// pages/collapsed/collapsed_page.qml
import QtQuick

Item {
    id: page
    implicitHeight: 36 * root.scaleFactor

    // PAGE-OWNED PROPERTY
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
