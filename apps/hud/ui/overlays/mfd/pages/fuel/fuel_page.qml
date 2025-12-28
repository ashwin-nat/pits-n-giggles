import QtQuick
import QtQuick.Window
import QtQuick.Layouts


// pages/fuel/fuel_page.qml
Item {
    id: page
    implicitHeight: content.implicitHeight + 120 * root.scaleFactor

    Column {
        id: content
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 8 * root.scaleFactor

        Text {
            text: "FUEL"
            font.pixelSize: 14 * root.scaleFactor
            font.family: "Formula1"
            color: "#888"
        }

        Text {
            text: root.fuelSurplus
            font.pixelSize: 20 * root.scaleFactor
            font.family: "B612 Mono"
            color: "#00ff88"
        }
    }
}
