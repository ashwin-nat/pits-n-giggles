import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 400
    height: parent ? parent.height : 220

    /* ---------- DATA ---------- */
    property string currValue: "---"
    property string lastValue: "---"
    property string tgtAvgValue: "---"
    property string tgtNextValue: "---"

    property string surplusText: "Surplus: ---"
    property real surplusValue: 0.0
    property bool surplusValid: false

    /* ---------- COLORS ---------- */
    readonly property color bgColor: "#1a1a1a"
    readonly property color borderColor: "#333333"
    readonly property color textColor: "#e0e0e0"
    readonly property color dimTextColor: "#808080"
    readonly property color primaryColor: "#00ff88"
    readonly property color warningColor: "#ffaa00"
    readonly property color dangerColor: "#ff4444"

    readonly property color surplusColor: {
        if (!surplusValid)        return dimTextColor
        if (surplusValue < 0)     return dangerColor
        if (surplusValue < 0.2)   return warningColor
        return primaryColor
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        GridLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            columns: 2
            rowSpacing: 12
            columnSpacing: 12

            FuelCard { title: "CURRENT RATE"; value: currValue; unit: "kg/lap"; primary: true }
            FuelCard { title: "LAST LAP";     value: lastValue; unit: "kg";     primary: true }
            FuelCard { title: "TARGET AVG";   value: tgtAvgValue; unit: "kg/lap" }
            FuelCard { title: "TARGET NEXT";  value: tgtNextValue; unit: "kg" }
        }

        Item { Layout.fillHeight: true } // spacer

        Text {
            text: surplusText
            font.family: "B612 Mono"
            font.pixelSize: 14
            color: surplusColor
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }
    }

    component FuelCard: Rectangle {
        required property string title
        required property string value
        required property string unit
        property bool primary: false

        Layout.fillWidth: true
        Layout.preferredHeight: 72
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
