pragma ComponentBehavior: Bound
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property string title: "TYRE SETS"

    property var bestSets: []
    property var compoundMappings: []

    property string iconSourcePrefix: "../../../../../../../assets/tyre-icons/"
    readonly property var tyreIcons: ({
        "Super Soft": iconSourcePrefix + "super_soft_tyre.svg",
        "Soft":       iconSourcePrefix + "soft_tyre.svg",
        "Medium":     iconSourcePrefix + "medium_tyre.svg",
        "Hard":       iconSourcePrefix + "hard_tyre.svg",
        "Inters":     iconSourcePrefix + "intermediate_tyre.svg",
        "Wet":        iconSourcePrefix + "wet_tyre.svg"
    })

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
            color: root.textDim
            font.pixelSize: 9
            font.family: "Formula1"
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
                    id: bestSetCell
                    required property int index

                    Layout.fillWidth: true
                    Layout.preferredHeight: 55
                    radius: 2
                    color: root.bgColor

                    property var entry: bestSetCell.index < root.bestSets.length ? root.bestSets[bestSetCell.index] : null

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 6
                        spacing: 8

                        Image {
                            Layout.preferredWidth: 32
                            Layout.preferredHeight: 32
                            fillMode: Image.PreserveAspectFit
                            source: bestSetCell.entry && root.tyreIcons[bestSetCell.entry.compound] ? root.tyreIcons[bestSetCell.entry.compound] : ""
                            smooth: true
                            antialiasing: true
                            mipmap: true
                        }

                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 0

                            Label {
                                font.pixelSize: 14
                                font.family: "B612 Mono"
                                text: {
                                    if (!bestSetCell.entry || bestSetCell.entry.deltaS === undefined || bestSetCell.entry.deltaS === null)
                                        return "---"
                                    var v = bestSetCell.entry.deltaS
                                    return (v > 0 ? "+" : "") + v.toFixed(3)
                                }
                                color: {
                                    if (!bestSetCell.entry || bestSetCell.entry.deltaS === undefined || bestSetCell.entry.deltaS === null)
                                        return root.textDim
                                    var d = bestSetCell.entry.deltaS
                                    if (d < -0.5) return root.primary
                                    if (d < 0) return root.textColor
                                    if (d < 0.5) return root.warning
                                    return root.danger
                                }
                            }

                            Label {
                                text: "s/lap"
                                font.pixelSize: 9
                                color: root.textDim
                            }
                        }

                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }

        Rectangle {
            Layout.preferredHeight: 1
            Layout.fillWidth: true
            color: root.borderColor
        }

        // =========================
        // ACTUAL COMPOUNDS
        // =========================

        Label {
            text: "ACTUAL COMPOUNDS"
            color: root.textDim
            font.pixelSize: 9
            font.family: "Formula1"
        }

        GridLayout {
            columns: 4
            rowSpacing: 6
            columnSpacing: 6
            Layout.fillWidth: true

            Repeater {
                model: root.compoundMappings

                Rectangle {
                    id: compoundCell
                    required property var modelData

                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    color: root.bgColor

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 4
                        spacing: 4

                        Image {
                            Layout.preferredWidth: 18
                            Layout.preferredHeight: 18
                            fillMode: Image.PreserveAspectFit
                            source: root.tyreIcons[compoundCell.modelData.visualCompound]
                            smooth: true
                            antialiasing: true
                            mipmap: true
                        }

                        Label {
                            font.pixelSize: 9
                            font.family: "B612 Mono"
                            text: compoundCell.modelData.actualCompound
                            color: root.primary
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