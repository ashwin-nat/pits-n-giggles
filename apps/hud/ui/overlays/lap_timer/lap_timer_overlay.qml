import QtQuick
import QtQuick.Layouts

Window {
    id: root

    property real scaleFactor: 1.0

    // Base dimensions (unscaled)
    readonly property int baseWidth: 280
    readonly property int baseHeight: 180

    // Font sizes - easy to adjust
    readonly property int fontSizeLabel: 11
    readonly property int fontSizeValue: 13
    readonly property int fontSizeEstimated: 11
    readonly property int fontSizeEstimatedValue: 13

    width: baseWidth * scaleFactor
    height: baseHeight * scaleFactor
    color: "transparent"

    // Exposed properties for Python to update
    property string currentTime: "--:--.---"
    property string currentColor: "#00FFFF"
    property string deltaTime: "---"
    property string deltaColor: "#FFFFFF"
    property string lastTime: "--:--.---"
    property string bestTime: "--:--.---"
    property string estimatedTime: "--:--.---"

    // Sector status arrays (-2=NA, -1=Invalid, 0=Yellow, 1=Green, 2=Purple)
    property var currentSectorStatus: [-2, -2, -2]
    property var lastSectorStatus: [-2, -2, -2]
    property var bestSectorStatus: [-2, -2, -2]

    // Scaled root item
    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: baseWidth
        height: baseHeight

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: baseWidth / 2
            origin.y: baseHeight / 2
        }

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 2
                spacing: 2

                // 2x2 Grid of cards
                GridLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    columns: 2
                    rowSpacing: 2
                    columnSpacing: 2

                    // Current lap card (top-left)
                    Card {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 135
                        Layout.minimumHeight: 38

                        labelText: "CURRENT"
                        valueText: root.currentTime
                        valueColor: root.currentColor
                    }

                    // Delta card (top-right)
                    Card {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 135
                        Layout.minimumHeight: 38

                        labelText: "DELTA"
                        valueText: root.deltaTime
                        valueColor: root.deltaColor
                    }

                    // Last lap card (bottom-left)
                    CardWithSectorBar {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 135
                        Layout.minimumHeight: 46

                        labelText: "LAST"
                        valueText: root.lastTime
                        valueColor: "#FFFFFF"
                        sectorStatus: root.lastSectorStatus
                    }

                    // Best lap card (bottom-right)
                    CardWithSectorBar {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 135
                        Layout.minimumHeight: 46

                        labelText: "BEST"
                        valueText: root.bestTime
                        valueColor: "#00FF00"
                        sectorStatus: root.bestSectorStatus
                    }
                }

                // Estimated time bar
                Rectangle {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 28
                    color: "#1a1a1a"
                    border.color: "#333333"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 4
                        anchors.rightMargin: 4
                        anchors.topMargin: 2
                        anchors.bottomMargin: 2
                        spacing: 3

                        Text {
                            text: "ESTIMATED:"
                            font.family: "Formula1"
                            font.pixelSize: root.fontSizeEstimated
                            color: "#888888"
                            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                        }

                        Text {
                            text: root.estimatedTime
                            font.family: "Formula1"
                            font.pixelSize: root.fontSizeEstimatedValue
                            font.bold: true
                            color: "#FFFFFF"
                            Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
                        }
                    }
                }

                // Current sector status bar at bottom
                SectorStatusBar {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 12
                    Layout.bottomMargin: 2
                    sectorStatus: root.currentSectorStatus
                }
            }
        }
    }

    // Card component
    component Card: Rectangle {
        property string labelText: ""
        property string valueText: ""
        property string valueColor: "#FFFFFF"

        color: "#1a1a1a"
        border.color: "#333333"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 2
            anchors.rightMargin: 2
            anchors.topMargin: 1
            anchors.bottomMargin: 1
            spacing: 0

            Text {
                text: labelText
                font.family: "Formula1"
                font.pixelSize: root.fontSizeLabel
                color: "#888888"
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: valueText
                font.family: "Formula1"
                font.pixelSize: root.fontSizeValue
                font.bold: true
                color: valueColor
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }

    // Card with sector bar component
    component CardWithSectorBar: Rectangle {
        property string labelText: ""
        property string valueText: ""
        property string valueColor: "#FFFFFF"
        property var sectorStatus: [0, 0, 0]

        color: "#1a1a1a"
        border.color: "#333333"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 2
            anchors.rightMargin: 2
            anchors.topMargin: 1
            anchors.bottomMargin: 1
            spacing: 0

            Text {
                text: labelText
                font.family: "Formula1"
                font.pixelSize: root.fontSizeLabel
                color: "#888888"
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: valueText
                font.family: "Formula1"
                font.pixelSize: root.fontSizeValue
                font.bold: true
                color: valueColor
                Layout.alignment: Qt.AlignHCenter
            }

            SectorStatusBar {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
                sectorStatus: parent.parent.sectorStatus
            }
        }
    }

    // Sector status bar component
    component SectorStatusBar: Canvas {
        id: canvas
        property var sectorStatus: [-2, -2, -2]

        onSectorStatusChanged: requestPaint()

        onPaint: {
            let ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            let sectorWidth = width / 3
            let colors = {
                "-2": "#6c757d",  // NA (gray)
                "-1": "#dc3545",  // Invalid (red)
                "0": "#ffc107",   // Yellow
                "1": "#28a745",   // Green
                "2": "#800080"    // Purple
            }

            // Draw filled rectangles for each sector
            for (let i = 0; i < 3; i++) {
                let status = sectorStatus[i]
                ctx.fillStyle = colors[status.toString()] || "#323232"
                ctx.fillRect(i * sectorWidth, 0, sectorWidth, height)
            }

            // Draw black separator lines
            ctx.strokeStyle = "#000000"
            ctx.lineWidth = 1
            for (let i = 1; i < 3; i++) {
                let x = i * sectorWidth
                ctx.beginPath()
                ctx.moveTo(x, 0)
                ctx.lineTo(x, height)
                ctx.stroke()
            }
        }
    }
}
