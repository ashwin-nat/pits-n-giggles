import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#0a0a0a"
    property string title: "TYRE WEAR INFO"

    property string iconSourcePrefix: "../../../../../../../assets/tyre-icons/"
    readonly property var tyreIcons: ({
        "Super Soft": iconSourcePrefix + "super_soft_tyre.svg",
        "Soft":       iconSourcePrefix + "soft_tyre.svg",
        "Medium":     iconSourcePrefix + "medium_tyre.svg",
        "Hard":       iconSourcePrefix + "hard_tyre.svg",
        "Inters":     iconSourcePrefix + "intermediate_tyre.svg",
        "Wet":        iconSourcePrefix + "wet_tyre.svg"
    })

    property string currentCompound: "—"
    property string currentCompoundVisual: ""

    property int tyreAge: 0
    property real wearRate: 0.0
    property bool telemetryDisabled: false
    property var wearTableData: []

    // Tyre counts for available tyres
    property var tyreCounts: ({
        "Soft": 0,
        "Medium": 0,
        "Hard": 0,
        "Super Soft": 0,
        "Inters": 0,
        "Wet": 0
    })

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        // Top section with current tyre info and available tyres
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "#1b1b1b"
            radius: 6

            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 16

                // LEFT: Current tyre info
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 4

                        // Top row: Icon, Compound, Age
                        RowLayout {
                            Layout.alignment: Qt.AlignHCenter
                            spacing: 8

                            // Tyre icon
                            Image {
                                id: tyreIcon
                                Layout.preferredWidth: 28
                                Layout.preferredHeight: 28
                                source: root.tyreIcons[root.currentCompoundVisual] || ""
                                fillMode: Image.PreserveAspectFit
                            }

                            // Compound name
                            Text {
                                text: root.currentCompound
                                font.family: "Formula1"
                                font.pixelSize: 13
                                font.bold: true
                                color: "#FFFFFF"
                            }

                            // Divider
                            Text {
                                text: "•"
                                font.pixelSize: 12
                                color: "#444444"
                            }

                            // Age label
                            Text {
                                text: "Age:"
                                font.family: "Formula1"
                                font.pixelSize: 12
                                color: "#888888"
                            }

                            // Age value
                            Text {
                                text: root.tyreAge + "L"
                                font.family: "Formula1"
                                font.pixelSize: 12
                                font.bold: true
                                color: "#00D4FF"
                            }
                        }

                        // Bottom row: Wear rate
                        RowLayout {
                            Layout.alignment: Qt.AlignHCenter
                            spacing: 8

                            Text {
                                text: "Rate:"
                                font.family: "Formula1"
                                font.pixelSize: 12
                                color: "#888888"
                            }

                            Text {
                                text: root.wearRate > 0 ? root.wearRate.toFixed(2) + "%/L" : "—"
                                font.family: "Formula1"
                                font.pixelSize: 12
                                font.bold: true
                                color: "#00D4FF"
                            }
                        }
                    }
                }

                // Vertical divider
                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.fillHeight: true
                    color: "#333333"
                }

                // RIGHT: Available tyres
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 2

                        // Title
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Unused Tyres"
                            font.family: "Formula1"
                            font.pixelSize: 8
                            color: "#888888"
                        }

                        // Tyre grid (2 rows x 3 columns)
                        ColumnLayout {
                            spacing: 4

                            // Top row: Soft, Medium, Hard
                            RowLayout {
                                Layout.alignment: Qt.AlignRight
                                spacing: 6

                                Repeater {
                                    model: ["Soft", "Medium", "Hard"]

                                    RowLayout {
                                        spacing: 0

                                        Image {
                                            Layout.preferredWidth: 24
                                            Layout.preferredHeight: 24
                                            source: root.tyreIcons[modelData] || ""
                                            fillMode: Image.PreserveAspectFit
                                        }

                                        Text {
                                            text: "x" + root.tyreCounts[modelData]
                                            font.family: "Formula1"
                                            font.pixelSize: 9
                                            font.bold: true
                                            color: root.tyreCounts[modelData] > 0 ? "#00D4FF" : "#666666"
                                        }
                                    }
                                }
                            }

                            // Bottom row: Super Soft, Inters, Wet
                            RowLayout {
                                Layout.alignment: Qt.AlignRight
                                spacing: 6

                                Repeater {
                                    model: ["Super Soft", "Inters", "Wet"]

                                    RowLayout {
                                        spacing: 0

                                        Image {
                                            Layout.preferredWidth: 24
                                            Layout.preferredHeight: 24
                                            source: root.tyreIcons[modelData] || ""
                                            fillMode: Image.PreserveAspectFit
                                        }

                                        Text {
                                            text: "x" + root.tyreCounts[modelData]
                                            font.family: "Formula1"
                                            font.pixelSize: 9
                                            font.bold: true
                                            color: root.tyreCounts[modelData] > 0 ? "#00D4FF" : "#666666"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Separator
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#333333"
        }

        // Wear table or telemetry disabled message
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // Telemetry disabled message
            Text {
                anchors.centerIn: parent
                visible: root.telemetryDisabled
                text: "Telemetry disabled - Wear data unavailable"
                font.family: "Formula1"
                font.pixelSize: 13
                color: "#FF6B6B"
            }

            // Wear table
            Rectangle {
                anchors.fill: parent
                visible: !root.telemetryDisabled
                color: "#1a1a1a"
                border.color: "#333333"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    // Header
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 28
                        color: "#2a2a2a"

                        RowLayout {
                            anchors.fill: parent
                            spacing: 0

                            Repeater {
                                model: ["Lap", "FL", "FR", "RL", "RR"]

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    color: "transparent"
                                    border.color: "#333333"
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData
                                        font.family: "Formula1"
                                        font.pixelSize: 12
                                        font.bold: true
                                        color: "#00D4FF"
                                    }
                                }
                            }
                        }
                    }

                    // Table rows
                    Repeater {
                        model: root.wearTableData

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#1a1a1a"

                            RowLayout {
                                anchors.fill: parent
                                spacing: 0

                                // Lap label
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    color: "transparent"
                                    border.color: "#333333"
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.label
                                        font.family: "Formula1"
                                        font.pixelSize: 12
                                        font.bold: true
                                        color: "#FFFFFF"
                                    }
                                }

                                // FL
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    color: "transparent"
                                    border.color: "#333333"
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.fl.toFixed(2) + "%"
                                        font.family: "B612 Mono"
                                        font.pixelSize: 12
                                        color: getWearColor(modelData.fl)
                                    }
                                }

                                // FR
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    color: "transparent"
                                    border.color: "#333333"
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.fr.toFixed(2) + "%"
                                        font.family: "B612 Mono"
                                        font.pixelSize: 12
                                        color: getWearColor(modelData.fr)
                                    }
                                }

                                // RL
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    color: "transparent"
                                    border.color: "#333333"
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.rl.toFixed(2) + "%"
                                        font.family: "B612 Mono"
                                        font.pixelSize: 12
                                        color: getWearColor(modelData.rl)
                                    }
                                }

                                // RR
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    color: "transparent"
                                    border.color: "#333333"
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.rr.toFixed(2) + "%"
                                        font.family: "B612 Mono"
                                        font.pixelSize: 12
                                        color: getWearColor(modelData.rr)
                                    }
                                }
                            }
                        }
                    }

                    // Fill remaining space
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                }
            }
        }
    }

    function getWearColor(wear) {
        if (wear < 50) return "#00FF00"; // Green
        if (wear < 75) return "#FFFF00"; // Yellow
        return "#FF0000"; // Red
    }
}