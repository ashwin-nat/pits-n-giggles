import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 400
    height: parent ? parent.height : 220
    property string title: "FUEL"

    /* ---------- DATA ---------- */
    property string currValue: "---"
    property string lastValue: "---"
    property string tgtAvgValue: "---"
    property string tgtNextValue: "---"

    property string surplusText: "Surplus: ---"
    property real surplusValue: 0.0
    property bool surplusValid: false

    property real fuelInTank: 0.0
    property real fuelCapacity: 0.0

    /* ---------- COLORS ---------- */
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

    /* ---------- TWEAK ME ---------- */
    readonly property int metricLabelSize: 10   // label / unit font size in the bottom strip
    readonly property int metricValueSize: 15   // value font size in the bottom strip

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        /* ── HERO: surplus laps ──────────────────────────────── */
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Row {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: surplusValid
                          ? (surplusValue >= 0 ? "+" : "") + surplusValue.toFixed(3)
                          : "---"
                    font.family: "B612 Mono"
                    font.pixelSize: 36
                    font.weight: Font.Bold
                    color: surplusColor
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: 4
                    text: "laps"
                    font.family: "Formula1"
                    font.pixelSize: 11
                    color: dimTextColor
                }
            }
        }

        /* ── DIVIDER ─────────────────────────────────────────── */
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: borderColor
        }

        /* ── METRICS STRIP ───────────────────────────────────── */
        RowLayout {
            Layout.fillWidth: true
            implicitHeight: 66
            spacing: 0

            MetricCell {
                Layout.fillWidth: true
                Layout.fillHeight: true
                label: "RATE"
                value: currValue
                unit: "kg/lap"
                accent: true
            }

            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: borderColor }

            MetricCell {
                Layout.fillWidth: true
                Layout.fillHeight: true
                label: "LAST LAP"
                value: lastValue
                unit: "kg"
            }

            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: borderColor }

            MetricCell {
                Layout.fillWidth: true
                Layout.fillHeight: true
                label: "TGT AVG"
                value: tgtAvgValue
                unit: "kg/lap"
            }

            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: borderColor }

            MetricCell {
                Layout.fillWidth: true
                Layout.fillHeight: true
                label: "TGT NEXT"
                value: tgtNextValue
                unit: "kg"
            }
        }
    }

    component MetricCell: Item {
        required property string label
        required property string value
        required property string unit
        property bool accent: false

        Column {
            anchors.centerIn: parent
            spacing: 3

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: label
                font.family: "Formula1"
                font.pixelSize: metricLabelSize
                color: dimTextColor
                font.letterSpacing: 1
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: value
                font.family: "B612 Mono"
                font.pixelSize: metricValueSize
                font.weight: Font.Bold
                color: value === "---" ? dimTextColor : (accent ? primaryColor : textColor)
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: unit
                font.family: "Formula1"
                font.pixelSize: metricLabelSize
                color: dimTextColor
            }
        }
    }
}
