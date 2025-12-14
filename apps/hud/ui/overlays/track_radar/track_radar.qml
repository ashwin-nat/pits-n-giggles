import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0
    readonly property int baseWidth: 450
    readonly property int baseHeight: 450

    width: baseWidth * scaleFactor
    height: baseHeight * scaleFactor
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    // Radar properties
    property var driverData: []
    property real radarRange: 25.0  // meters - zoomed in for side awareness

    function updateTelemetry(drivers) {
        driverData = drivers || [];
    }

    // ==========================================================
    // GLOBAL SCALING ROOT
    // ==========================================================
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

        // Background (transparent)
        Rectangle {
            anchors.fill: parent
            color: "#1a1a1a"
            opacity: 0.6
            radius: 0
        }

        // Radar display area
        Item {
            id: radarArea
            anchors.centerIn: parent
            width: parent.width * 0.85
            height: parent.height * 0.85

            readonly property real centerX: width / 2
            readonly property real centerY: height / 2

            // Grid lines
            Repeater {
                model: 4
                delegate: Rectangle {
                    property real circleRadius: (index + 1) * (radarArea.width / 8)
                    x: radarArea.centerX - circleRadius
                    y: radarArea.centerY - circleRadius
                    width: circleRadius * 2
                    height: circleRadius * 2
                    color: "transparent"
                    border.color: "#333333"
                    border.width: 1
                    radius: circleRadius
                }
            }

            // Crosshair
            Rectangle {
                x: radarArea.centerX - width / 2
                y: 0
                width: 1
                height: radarArea.height
                color: "#333333"
            }
            Rectangle {
                x: 0
                y: radarArea.centerY - height / 2
                width: radarArea.width
                height: 1
                color: "#333333"
            }

            // Range labels - removed

            // Reference car (center)
            Item {
                x: radarArea.centerX
                y: radarArea.centerY

                Rectangle {
                    anchors.centerIn: parent
                    width: 16
                    height: 24
                    color: "#00ff88"
                    border.color: "#ffffff"
                    border.width: 2
                    radius: 2
                }
            }

            // Other cars
            Repeater {
                model: driverData
                delegate: Item {
                    id: carMarker

                    property var driver: modelData
                    property bool isRef: driver.is_ref || false

                    visible: !isRef && driver.relX !== undefined && driver.relZ !== undefined

                    // Convert world position to radar coordinates (flip X axis)
                    property real radarX: radarArea.centerX - (driver.relX / root.radarRange) * (radarArea.width / 2)
                    property real radarY: radarArea.centerY - (driver.relZ / root.radarRange) * (radarArea.height / 2)

                    // Check if within radar range
                    property real distance: Math.sqrt(driver.relX * driver.relX + driver.relZ * driver.relZ)
                    property bool inRange: distance <= root.radarRange

                    x: radarX
                    y: radarY

                    opacity: inRange ? 1.0 : 0.0

                    Rectangle {
                        anchors.centerIn: parent
                        width: 16
                        height: 24
                        color: getTeamColor(driver.team)
                        border.color: "#ffffff"
                        border.width: 1
                        radius: 2
                        rotation: driver.heading || 0
                    }

                    // Driver name on hover
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.top
                        anchors.bottomMargin: 5
                        width: nameText.width + 8
                        height: nameText.height + 4
                        color: "#000000"
                        opacity: 0.8
                        radius: 3
                        visible: mouseArea.containsMouse

                        Text {
                            id: nameText
                            anchors.centerIn: parent
                            text: driver.name || ""
                            color: "#ffffff"
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        anchors.margins: -10
                        hoverEnabled: true
                    }
                }
            }
        }

        // Info panel - removed
    }

    // Team color mapping
    function getTeamColor(team) {
        const colors = {
            "Red Bull Racing": "#3671C6",
            "Mercedes": "#27F4D2",
            "Ferrari": "#E8002D",
            "McLaren": "#FF8000",
            "Aston Martin": "#229971",
            "Alpine": "#FF87BC",
            "Williams": "#64C4FF",
            "AlphaTauri": "#5E8FAA",
            "Alfa Romeo": "#C92D4B",
            "Haas F1 Team": "#B6BABD",
            "Sauber": "#52E252",
            "RB": "#6692FF",
            "Kick Sauber": "#52E252"
        };
        return colors[team] || "#888888";
    }
}