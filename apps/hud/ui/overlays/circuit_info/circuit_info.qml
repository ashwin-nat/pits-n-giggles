import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property real scaleFactor: 1.0
    property int barWidth: 1400          // settable: controls overlay width
    readonly property int baseHeight: 72

    width: barWidth * scaleFactor
    height: baseHeight * scaleFactor

    // Data inputs
    property real circuitPosM: 0.0
    property real circuitLength: 1.0
    property var sectorsInfo: null    // { s1: float, s2: float } or null
    property var segmentInfo: null    // { type: str, name: str, turns: str } or null
    property color completedSector1Color: "#888888"   // settable from Python
    property color completedSector2Color: "#888888"   // settable from Python

    // Helper: set one sector's completed colour by number (1 or 2)
    function setCompletedSectorColor(sector, color) {
        if (sector === 1) completedSector1Color = color
        else if (sector === 2) completedSector2Color = color
    }

    // Helper: set both completed sector colours at once
    function setCompletedSectorColors(s1Color, s2Color) {
        completedSector1Color = s1Color
        completedSector2Color = s2Color
    }

    readonly property real progress: circuitLength > 0
        ? Math.min(1.0, Math.max(0.0, circuitPosM / circuitLength))
        : 0.0

    // Which sector (1/2/3) the car is currently in
    readonly property int currentSector: {
        if (!sectorsInfo || circuitLength <= 0) return 1
        if (circuitPosM < sectorsInfo.s1) return 1
        if (circuitPosM < sectorsInfo.s2) return 2
        return 3
    }

    // Fraction along the bar where the active sector starts
    readonly property real activeSectorStartFrac: {
        if (!sectorsInfo || circuitLength <= 0) return 0
        if (currentSector === 2) return sectorsInfo.s1 / circuitLength
        if (currentSector === 3) return sectorsInfo.s2 / circuitLength
        return 0
    }

    // ==========================================================
    // SCALING ROOT
    // ==========================================================
    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: barWidth
        height: baseHeight

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: barWidth / 2
            origin.y: baseHeight / 2
        }

        Rectangle {
            anchors.fill: parent
            color: "transparent"
        }

        // ==========================================================
        // SEGMENT INFO  (fades on change)
        //   y=2  → primary bg      (20+8=28px)  bottom=30
        //   y=30 → progress bar    (12px)        bottom=42
        //   y=44 → secondary bg    (18+8=26px)   bottom=70
        //   baseHeight=72
        // ==========================================================
        Item {
            id: infoGroup
            anchors.fill: parent
            opacity: 1.0

            // Holds the info currently rendered — updated only after fade-out
            property var displayedInfo: null

            Connections {
                target: root
                function onSegmentInfoChanged() {
                    segFade.restart()
                }
            }

            // Fade out → swap text → fade in
            SequentialAnimation {
                id: segFade
                NumberAnimation {
                    target: infoGroup
                    property: "opacity"
                    to: 0
                    duration: 80
                    easing.type: Easing.InQuad
                }
                ScriptAction {
                    script: infoGroup.displayedInfo = root.segmentInfo
                }
                NumberAnimation {
                    target: infoGroup
                    property: "opacity"
                    to: 1
                    duration: 80
                    easing.type: Easing.OutQuad
                }
            }

            // Primary label — sits above the bar
            // straight       → segment name
            // corner         → turn string e.g. "Turn 5"
            // complex_corner → range string e.g. "Turns 3–5"
            Rectangle {
                id: primaryBg
                anchors.horizontalCenter: parent.horizontalCenter
                y: 2
                width: primaryLabel.implicitWidth + 20
                height: primaryLabel.implicitHeight + 8
                color: Qt.rgba(0, 0, 0, 0.6)
                radius: 4
                visible: primaryLabel.text.length > 0

                Text {
                    id: primaryLabel
                    anchors.centerIn: parent

                    readonly property var info: infoGroup.displayedInfo

                    text: {
                        if (!info) return ""
                        if (info.type === "straight") return info.name
                        return info.turns
                    }

                    color: "white"
                    font.family: "Formula1"
                    font.pixelSize: 20
                    font.bold: !!info && info.type !== "straight"
                    visible: text.length > 0
                }
            }

            // Secondary label — sits below the bar
            // straight               → nothing
            // corner / complex_corner → corner name if available
            Rectangle {
                id: secondaryBg
                anchors.horizontalCenter: parent.horizontalCenter
                y: 44
                width: secondaryLabel.implicitWidth + 20
                height: secondaryLabel.implicitHeight + 8
                color: Qt.rgba(0, 0, 0, 0.6)
                radius: 4
                visible: secondaryLabel.text.length > 0

                Text {
                    id: secondaryLabel
                    anchors.centerIn: parent

                    readonly property var info: infoGroup.displayedInfo

                    text: {
                        if (!info || info.type === "straight") return ""
                        return info.name
                    }

                    color: Qt.rgba(1, 1, 1, 0.85)
                    font.family: "Formula1"
                    font.pixelSize: 18
                    visible: text.length > 0
                }
            }
        }

        // ==========================================================
        // PROGRESS BAR  (y=30, height=12)
        // ==========================================================
        Item {
            id: progressBarArea
            x: 12
            y: 30
            width: parent.width - 24
            height: 12

            // Animate the right-edge position rather than the fill width, so that
            // a sector-boundary jump in activeSectorStartFrac doesn't cause the
            // width behaviour to animate from the previous sector's large value.
            property real animatedRightEdge: width * root.progress
            Behavior on animatedRightEdge {
                NumberAnimation { duration: 80; easing.type: Easing.Linear }
            }

            // Track background
            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(1, 1, 1, 0.18)
                radius: 4
            }

            // Sector 1 fill — shown as completed when car is in sector 2 or 3
            Rectangle {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                color: root.completedSector1Color
                radius: 4
                visible: root.sectorsInfo !== null && root.currentSector > 1
                width: root.sectorsInfo && root.circuitLength > 0
                    ? progressBarArea.width * (root.sectorsInfo.s1 / root.circuitLength)
                    : 0
            }

            // Sector 2 fill — shown as completed when car is in sector 3
            Rectangle {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                color: root.completedSector2Color
                radius: 4
                visible: root.sectorsInfo !== null && root.currentSector > 2
                x: root.sectorsInfo && root.circuitLength > 0
                    ? progressBarArea.width * (root.sectorsInfo.s1 / root.circuitLength)
                    : 0
                width: root.sectorsInfo && root.circuitLength > 0
                    ? progressBarArea.width * ((root.sectorsInfo.s2 - root.sectorsInfo.s1) / root.circuitLength)
                    : 0
            }

            // Active sector fill — white, from current sector start to current position
            Rectangle {
                id: activeSectorFill
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                color: "white"
                radius: 4
                x: progressBarArea.width * root.activeSectorStartFrac
                width: Math.max(0, progressBarArea.animatedRightEdge - x)
            }

            // Sector boundary dividers (only when sectorsInfo is available)
            Repeater {
                model: root.sectorsInfo ? 2 : 0
                delegate: Rectangle {
                    readonly property real frac: {
                        if (!root.sectorsInfo || root.circuitLength <= 0) return 0
                        return index === 0
                            ? root.sectorsInfo.s1 / root.circuitLength
                            : root.sectorsInfo.s2 / root.circuitLength
                    }

                    x: progressBarArea.width * frac - 1
                    anchors.top: parent.top
                    anchors.topMargin: -3
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: -3
                    width: 2
                    color: Qt.rgba(1, 1, 1, 0.65)
                    radius: 1
                }
            }

            // Current position marker (diamond)
            Canvas {
                id: positionMarker
                width: 14
                height: 14
                anchors.verticalCenter: parent.verticalCenter

                x: progressBarArea.width * root.progress - width / 2
                Behavior on x {
                    NumberAnimation { duration: 80; easing.type: Easing.Linear }
                }

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    ctx.fillStyle = "white"
                    ctx.beginPath()
                    ctx.moveTo(width / 2, 0)
                    ctx.lineTo(width, height / 2)
                    ctx.lineTo(width / 2, height)
                    ctx.lineTo(0, height / 2)
                    ctx.closePath()
                    ctx.fill()
                }

                Component.onCompleted: requestPaint()
            }
        }
    }
}
