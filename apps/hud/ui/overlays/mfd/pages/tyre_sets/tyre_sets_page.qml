import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property string title: "TYRE SETS"

    property var tyreIcons: ({})
    property var bestSets: []
    property var compoundMappings: []

    readonly property color bgColor: "#1a1a1a"
    readonly property color textColor: "#e0e0e0"
    readonly property color textDim: "#808080"
    readonly property color primary: "#00ff88"
    readonly property color warning: "#ffaa00"
    readonly property color danger: "#ff4444"
    readonly property color borderColor: "#333333"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        // =========================
        // BEST AVAILABLE SETS
        // =========================

        Label {
            text: "BEST AVAILABLE SETS"
            color: textDim
            font.pixelSize: 9
        }

        GridLayout {
            id: bestSetsGrid
            columns: 3
            rowSpacing: 6
            columnSpacing: 6
            Layout.fillWidth: true

            Repeater {
                model: 6

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 55
                    radius: 2
                    color: bgColor

                    property var entry: index < bestSets.length ? bestSets[index] : null

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 6
                        spacing: 8

                        Image {
                            Layout.preferredWidth: 32
                            Layout.preferredHeight: 32
                            fillMode: Image.PreserveAspectFit
                            source: entry && tyreIcons[entry.compound] ? tyreIcons[entry.compound] : ""
                        }

                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 0

                            Label {
                                font.pixelSize: 14
                                font.family: "B612 Mono"
                                text: {
                                    if (!entry || entry.deltaS === undefined || entry.deltaS === null)
                                        return "---"
                                    var v = entry.deltaS
                                    return (v > 0 ? "+" : "") + v.toFixed(3)
                                }
                                color: {
                                    if (!entry || entry.deltaS === undefined || entry.deltaS === null)
                                        return textDim
                                    var d = entry.deltaS
                                    if (d < -0.5) return primary
                                    if (d < 0) return textColor
                                    if (d < 0.5) return warning
                                    return danger
                                }
                            }

                            Label {
                                text: "s/lap"
                                font.pixelSize: 9
                                color: textDim
                            }
                        }

                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }

        Rectangle {
            height: 1
            Layout.fillWidth: true
            color: borderColor
        }

        // =========================
        // ACTUAL COMPOUNDS
        // =========================

        Label {
            text: "ACTUAL COMPOUNDS"
            color: textDim
            font.pixelSize: 9
        }

        GridLayout {
            columns: 4
            rowSpacing: 6
            columnSpacing: 6
            Layout.fillWidth: true

            Repeater {
                model: compoundMappings

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    color: bgColor

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 4
                        spacing: 4

                        Image {
                            Layout.preferredWidth: 18
                            Layout.preferredHeight: 18
                            fillMode: Image.PreserveAspectFit
                            source: tyreIcons[modelData.visualCompound]
                        }

                        Label {
                            font.pixelSize: 9
                            font.family: "B612 Mono"
                            text: modelData.actualCompound
                            color: primary
                        }

                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
}