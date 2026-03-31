import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property real scaleFactor: 1.0
    property int barWidth: 1400          // settable: controls overlay width
    readonly property int baseHeight: 64

    width: barWidth * scaleFactor
    height: baseHeight * scaleFactor

    // Data inputs
    property real circuitPosM: 0.0
    property real circuitLength: 1.0
    property var sectorsInfo: null    // { s1: float, s2: float } or null
    property var segmentInfo: null    // { type: str, name: str, turns: str } or null

    readonly property real progress: circuitLength > 0
        ? Math.min(1.0, Math.max(0.0, circuitPosM / circuitLength))
        : 0.0

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
        //   y=4  → primary label  (16px)  bottom=20
        //   y=26 → progress bar   (12px)  bottom=38
        //   y=43 → secondary label (13px)  bottom=56
        //   baseHeight=64
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
            Text {
                id: primaryLabel
                anchors.horizontalCenter: parent.horizontalCenter
                y: 4

                readonly property var info: infoGroup.displayedInfo

                text: {
                    if (!info) return ""
                    if (info.type === "straight") return info.name
                    return info.turns
                }

                color: "white"
                font.family: "Formula1"
                font.pixelSize: 16
                font.bold: !!info && info.type !== "straight"
                visible: text.length > 0
            }

            // Secondary label — sits below the bar
            // straight               → nothing
            // corner / complex_corner → corner name if available
            Text {
                id: secondaryLabel
                anchors.horizontalCenter: parent.horizontalCenter
                y: 43

                readonly property var info: infoGroup.displayedInfo

                text: {
                    if (!info || info.type === "straight") return ""
                    return info.name
                }

                color: Qt.rgba(1, 1, 1, 0.65)
                font.family: "Formula1"
                font.pixelSize: 13
                visible: text.length > 0
            }
        }

        // ==========================================================
        // PROGRESS BAR  (y=26, height=12, centred in baseHeight=64)
        // ==========================================================
        Item {
            id: progressBarArea
            x: 12
            y: 26
            width: parent.width - 24
            height: 12

            // Track background
            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(1, 1, 1, 0.18)
                radius: 4
            }

            // Progress fill
            Rectangle {
                id: progressFill
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                color: "#00cc00"
                radius: 4

                width: progressBarArea.width * root.progress
                Behavior on width {
                    NumberAnimation { duration: 80; easing.type: Easing.Linear }
                }
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
