import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    width: 400 * scaleFactor
    height: 150 * scaleFactor
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property real scaleFactor: 1.0

    // Current values
    property real throttleValue: 0
    property real brakeValue: 0
    property real steeringValue: 0

    // History arrays to store past values for the graph
    property var throttleHistory: []
    property var brakeHistory: []
    property var steeringHistory: []
    property int maxHistoryLength: 100

    // Function called from Python to update telemetry
    function updateTelemetry(throttle, brake, steering) {
        throttleValue = throttle
        brakeValue = brake
        steeringValue = steering

        // Add to history
        throttleHistory.push(throttle)
        brakeHistory.push(brake)
        steeringHistory.push(steering)

        // Trim if too long
        if (throttleHistory.length > maxHistoryLength) {
            throttleHistory.shift()
            brakeHistory.shift()
            steeringHistory.shift()
        }

        // Request repaint
        canvas.requestPaint()
    }

    Rectangle {
        anchors.fill: parent
        color: "#CC000000"
        radius: 8 * scaleFactor
        border.color: "#404040"
        border.width: 2 * scaleFactor

        Row {
            anchors.fill: parent
            anchors.margins: 10 * scaleFactor
            spacing: 10 * scaleFactor

            // Graph canvas
            Canvas {
                id: canvas
                width: parent.width - 40 * scaleFactor
                height: parent.height
                renderStrategy: Canvas.Threaded
                renderTarget: Canvas.FramebufferObject

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)

                    // Draw grid
                    ctx.strokeStyle = "#303030"
                    ctx.lineWidth = 1

                    // Horizontal grid lines
                    for (var i = 0; i <= 4; i++) {
                        var y = (height / 4) * i
                        ctx.beginPath()
                        ctx.moveTo(0, y)
                        ctx.lineTo(width, y)
                        ctx.stroke()
                    }

                    // Vertical grid lines
                    for (var j = 0; j <= 10; j++) {
                        var x = (width / 10) * j
                        ctx.beginPath()
                        ctx.moveTo(x, 0)
                        ctx.lineTo(x, height)
                        ctx.stroke()
                    }

                    // Draw center line for steering (0 point)
                    ctx.strokeStyle = "#505050"
                    ctx.lineWidth = 2
                    ctx.beginPath()
                    ctx.moveTo(0, height / 2)
                    ctx.lineTo(width, height / 2)
                    ctx.stroke()

                    if (throttleHistory.length < 2) return

                    var spacing = width / (maxHistoryLength - 1)

                    // Draw throttle (green) - 0-100 scale
                    ctx.strokeStyle = "#00FF00"
                    ctx.lineWidth = 2 * scaleFactor
                    ctx.beginPath()
                    for (var t = 0; t < throttleHistory.length; t++) {
                        var xPos = t * spacing
                        var yPos = height - (throttleHistory[t] / 100) * height
                        if (t === 0) {
                            ctx.moveTo(xPos, yPos)
                        } else {
                            ctx.lineTo(xPos, yPos)
                        }
                    }
                    ctx.stroke()

                    // Draw brake (red) - 0-100 scale
                    ctx.strokeStyle = "#FF0000"
                    ctx.lineWidth = 2 * scaleFactor
                    ctx.beginPath()
                    for (var b = 0; b < brakeHistory.length; b++) {
                        var xPosB = b * spacing
                        var yPosB = height - (brakeHistory[b] / 100) * height
                        if (b === 0) {
                            ctx.moveTo(xPosB, yPosB)
                        } else {
                            ctx.lineTo(xPosB, yPosB)
                        }
                    }
                    ctx.stroke()

                    // Draw steering (blue) - -100 to 100 scale, centered
                    ctx.strokeStyle = "#00AAFF"
                    ctx.lineWidth = 2 * scaleFactor
                    ctx.beginPath()
                    for (var s = 0; s < steeringHistory.length; s++) {
                        var xPosS = s * spacing
                        // Map -100 to 100 onto 0 to height, with 0 at center
                        var yPosS = height / 2 - (steeringHistory[s] / 100) * (height / 2)
                        if (s === 0) {
                            ctx.moveTo(xPosS, yPosS)
                        } else {
                            ctx.lineTo(xPosS, yPosS)
                        }
                    }
                    ctx.stroke()
                }
            }

            // Vertical bars container
            Column {
                width: 20 * scaleFactor
                height: parent.height
                spacing: 5 * scaleFactor

                // Throttle bar (green)
                Rectangle {
                    width: parent.width
                    height: (parent.height - parent.spacing) / 2
                    color: "#202020"
                    border.color: "#00FF00"
                    border.width: 1 * scaleFactor
                    radius: 3 * scaleFactor

                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: parent.width - 4 * scaleFactor
                        height: (throttleValue / 100) * (parent.height - 4 * scaleFactor)
                        color: "#00FF00"
                        radius: 2 * scaleFactor
                    }
                }

                // Brake bar (red)
                Rectangle {
                    width: parent.width
                    height: (parent.height - parent.spacing) / 2
                    color: "#202020"
                    border.color: "#FF0000"
                    border.width: 1 * scaleFactor
                    radius: 3 * scaleFactor

                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: parent.width - 4 * scaleFactor
                        height: (brakeValue / 100) * (parent.height - 4 * scaleFactor)
                        color: "#FF0000"
                        radius: 2 * scaleFactor
                    }
                }
            }
        }
    }
}
