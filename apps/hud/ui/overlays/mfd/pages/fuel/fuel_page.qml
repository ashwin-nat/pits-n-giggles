pragma ComponentBehavior: Bound
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
                    text: page.surplusValid
                          ? (page.surplusValue >= 0 ? "+" : "") + page.surplusValue.toFixed(3)
                          : "---"
                    font.family: "B612 Mono"
                    font.pixelSize: 36
                    font.weight: Font.Bold
                    color: page.surplusColor
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: 4
                    text: "laps"
                    font.family: "Formula1"
                    font.pixelSize: 11
                    color: page.dimTextColor
                }
            }
        }

        /* ── DIVIDER ─────────────────────────────────────────── */
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: page.borderColor
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
                value: page.currValue
                unit: "kg/lap"
                accent: true
            }

            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: page.borderColor }

            MetricCell {
                Layout.fillWidth: true
                Layout.fillHeight: true
                label: "LAST LAP"
                value: page.lastValue
                unit: "kg"
            }

            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: page.borderColor }

            MetricCell {
                Layout.fillWidth: true
                Layout.fillHeight: true
                label: "TGT AVG"
                value: page.tgtAvgValue
                unit: "kg/lap"
            }

            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: page.borderColor }

            MetricCell {
                Layout.fillWidth: true
                Layout.fillHeight: true
                label: "TGT NEXT"
                value: page.tgtNextValue
                unit: "kg"
            }
        }
    }

    component MetricCell: Item {
        id: metricCell
        required property string label
        required property string value
        required property string unit
        property bool accent: false

        Column {
            anchors.centerIn: parent
            spacing: 3

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: metricCell.label
                font.family: "Formula1"
                font.pixelSize: page.metricLabelSize
                color: page.dimTextColor
                font.letterSpacing: 1
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: metricCell.value
                font.family: "B612 Mono"
                font.pixelSize: page.metricValueSize
                font.weight: Font.Bold
                color: metricCell.value === "---" ? page.dimTextColor : (metricCell.accent ? page.primaryColor : page.textColor)
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: metricCell.unit
                font.family: "Formula1"
                font.pixelSize: page.metricLabelSize
                color: page.dimTextColor
            }
        }
    }
}
