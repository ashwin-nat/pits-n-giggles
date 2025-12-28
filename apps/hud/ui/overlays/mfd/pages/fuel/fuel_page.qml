import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 0
    implicitHeight: content.implicitHeight + 24

    /* ---------- COLORS ---------- */
    readonly property color bgColor: "#1a1a1a"
    readonly property color borderColor: "#333333"
    readonly property color textColor: "#e0e0e0"
    readonly property color dimTextColor: "#808080"
    readonly property color primaryColor: "#00ff88"
    readonly property color warningColor: "#ffaa00"
    readonly property color dangerColor: "#ff4444"

    readonly property color surplusColor: {
        if (!root.surplusValid)        return dimTextColor
        if (root.surplusValue < 0)     return dangerColor
        if (root.surplusValue < 0.2)   return warningColor
        return primaryColor
    }

    Column {
        id: content
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 16

        GridLayout {
            columns: 2
            rowSpacing: 12
            columnSpacing: 12

            FuelCard { title: "CURRENT RATE"; value: root.currValue; unit: "kg/lap"; primary: true }
            FuelCard { title: "LAST LAP";     value: root.lastValue; unit: "kg";     primary: true }
            FuelCard { title: "TARGET AVG";   value: root.tgtAvgValue; unit: "kg/lap" }
            FuelCard { title: "TARGET NEXT";  value: root.tgtNextValue; unit: "kg" }
        }

        Text {
            text: root.surplusText
            font.family: "B612 Mono"
            font.pixelSize: 14
            color: surplusColor
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    component FuelCard: Rectangle {
        required property string title
        required property string value
        required property string unit
        property bool primary: false

        implicitWidth: 160
        implicitHeight: 78
        radius: 8
        color: bgColor
        border.color: borderColor

        Column {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 6

            Text {
                text: title
                font.family: "Formula1"
                font.pixelSize: 9
                color: dimTextColor
            }

            Row {
                spacing: 4

                Text {
                    text: value
                    font.family: "Formula1"
                    font.pixelSize: 16
                    font.weight: Font.Bold
                    color: value === "---"
                           ? dimTextColor
                           : (primary ? primaryColor : textColor)
                }

                Text {
                    text: unit
                    font.family: "Formula1"
                    font.pixelSize: 11
                    color: dimTextColor
                    verticalAlignment: Text.AlignBottom
                }
            }
        }
    }
}
