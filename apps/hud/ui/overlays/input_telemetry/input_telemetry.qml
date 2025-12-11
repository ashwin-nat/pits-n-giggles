import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true
    width: 420 * scaleFactor
    height: 130 * scaleFactor
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property real scaleFactor: 1.0

    //
    // --- TOP-LEVEL CONSTANT COLORS ---
    //
    property color throttleColor: "#76FF03"
    property color brakeColor: "#FF1744"
    property color steeringColor: "#2979FF"

    //
    // Telemetry values (0–100)
    //
    property real throttleValue: 0
    property real brakeValue: 0
    property real steeringValue: 0

    // Smoothed display values
    property real throttleSmoothed: 0
    property real brakeSmoothed: 0
    property real steeringSmoothed: 0

    property real smoothingFactor: 0.2

    property var throttleHistory: []
    property var brakeHistory: []
    property var steeringHistory: []
    property int maxHistoryLength: 100

    function updateTelemetry(t, b, s) {
        throttleSmoothed = throttleSmoothed * smoothingFactor + t * (1 - smoothingFactor)
        brakeSmoothed    = brakeSmoothed    * smoothingFactor + b * (1 - smoothingFactor)
        steeringSmoothed = steeringSmoothed * smoothingFactor + s * (1 - smoothingFactor)

        throttleValue = throttleSmoothed
        brakeValue    = brakeSmoothed
        steeringValue = steeringSmoothed

        throttleHistory.push(throttleSmoothed)
        brakeHistory.push(brakeSmoothed)
        steeringHistory.push(steeringSmoothed)

        if (throttleHistory.length > maxHistoryLength) {
            throttleHistory.shift()
            brakeHistory.shift()
            steeringHistory.shift()
        }

        canvas.requestPaint()
    }

    //
    // MAIN: Single Black Container holding Graph + Brake + Throttle
    //
    Rectangle {
        id: container
        anchors.fill: parent
        anchors.margins: 6 * scaleFactor
        radius: 6 * scaleFactor
        color: "#000000"

        Row {
            anchors.fill: parent
            anchors.margins: 8 * scaleFactor
            spacing: 10 * scaleFactor    // tighter spacing between chart and bars

            //----------------------------------------------------------------
            // GRAPH AREA
            //----------------------------------------------------------------
            Item {
                id: graphArea
                width: parent.width - (70 * scaleFactor)
                height: parent.height

                // top gradient strip
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 3 * scaleFactor
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0.0; color: "transparent" }
                        GradientStop { position: 0.3; color: brakeColor }
                        GradientStop { position: 0.7; color: throttleColor }
                        GradientStop { position: 1.0; color: "transparent" }
                    }
                }

                Canvas {
                    id: canvas
                    anchors.fill: parent
                    renderStrategy: Canvas.Threaded
                    renderTarget: Canvas.FramebufferObject

                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)

                        // Grid
                        ctx.strokeStyle = "#1a1a1a"
                        ctx.lineWidth = 1
                        for (var i = 1; i < 4; i++) {
                            var y = height * i / 4
                            ctx.beginPath()
                            ctx.moveTo(0, y)
                            ctx.lineTo(width, y)
                            ctx.stroke()
                        }

                        ctx.strokeStyle = "#2a2a2a"
                        ctx.beginPath()
                        ctx.moveTo(0, height / 2)
                        ctx.lineTo(width, height / 2)
                        ctx.stroke()

                        if (throttleHistory.length < 2)
                            return

                        var spacing = width / (maxHistoryLength - 1)

                        // Throttle tint fill
                        var gradT = ctx.createLinearGradient(0, height, 0, 0)
                        gradT.addColorStop(0, Qt.rgba(throttleColor.r, throttleColor.g, throttleColor.b, 0.15))
                        gradT.addColorStop(1, Qt.rgba(throttleColor.r, throttleColor.g, throttleColor.b, 0))
                        ctx.fillStyle = gradT
                        ctx.beginPath()
                        ctx.moveTo(0, height)
                        for (var t=0; t<throttleHistory.length; t++) {
                            var yT = height - (throttleHistory[t] / 100) * height
                            ctx.lineTo(t*spacing, yT)
                        }
                        ctx.lineTo((throttleHistory.length-1)*spacing, height)
                        ctx.closePath()
                        ctx.fill()

                        // Brake tint fill
                        var gradB = ctx.createLinearGradient(0, height, 0, 0)
                        gradB.addColorStop(0, Qt.rgba(brakeColor.r, brakeColor.g, brakeColor.b, 0.15))
                        gradB.addColorStop(1, Qt.rgba(brakeColor.r, brakeColor.g, brakeColor.b, 0))
                        ctx.fillStyle = gradB
                        ctx.beginPath()
                        ctx.moveTo(0, height)
                        for (var b=0; b<brakeHistory.length; b++) {
                            var yB = height - (brakeHistory[b] / 100) * height
                            ctx.lineTo(b*spacing, yB)
                        }
                        ctx.lineTo((brakeHistory.length-1)*spacing, height)
                        ctx.closePath()
                        ctx.fill()

                        // Lines
                        // throttle
                        ctx.strokeStyle = throttleColor
                        ctx.lineWidth = 2
                        ctx.beginPath()
                        for (var t2=0; t2<throttleHistory.length; t2++) {
                            var yT2 = height - (throttleHistory[t2]/100)*height
                            if (t2===0) ctx.moveTo(0,yT2)
                            else ctx.lineTo(t2*spacing, yT2)
                        }
                        ctx.stroke()

                        // brake
                        ctx.strokeStyle = brakeColor
                        ctx.beginPath()
                        for (var b2=0; b2<brakeHistory.length; b2++) {
                            var yB2 = height - (brakeHistory[b2]/100)*height
                            if (b2===0) ctx.moveTo(0,yB2)
                            else ctx.lineTo(b2*spacing, yB2)
                        }
                        ctx.stroke()

                        // steering
                        ctx.strokeStyle = steeringColor
                        ctx.beginPath()
                        for (var s=0; s<steeringHistory.length; s++) {
                            var yS = height/2 - (steeringHistory[s]/100)*(height/2)
                            if (s===0) ctx.moveTo(0,yS)
                            else ctx.lineTo(s*spacing, yS)
                        }
                        ctx.stroke()
                    }
                }
            }

            //----------------------------------------------------------------
            // SIDE-BY-SIDE VERTICAL BARS
            //----------------------------------------------------------------
            Row {
                id: bars
                width: 60 * scaleFactor
                height: parent.height
                spacing: 6 * scaleFactor  // smaller spacing
                anchors.rightMargin: 4 * scaleFactor   // <--- add this for symmetry

                // Brake Bar (left)
                Rectangle {
                    width: 22 * scaleFactor
                    height: parent.height
                    radius: 3 * scaleFactor
                    color: "#202020"
                    border.color: brakeColor
                    clip: true

                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: (brakeValue / 100) * parent.height
                        color: brakeColor
                        Behavior on height { SmoothedAnimation { duration: 60 } }
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 2 * scaleFactor
                        text: Math.round(brakeValue)
                        font.pixelSize: 10 * scaleFactor
                        color: brakeValue > 10 ? "#000000" : brakeColor
                    }
                }

                // Throttle Bar (right)
                Rectangle {
                    width: 22 * scaleFactor
                    height: parent.height
                    radius: 3 * scaleFactor
                    color: "#202020"
                    border.color: throttleColor
                    clip: true

                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: (throttleValue / 100) * parent.height
                        color: throttleColor
                        Behavior on height { SmoothedAnimation { duration: 60 } }
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 2 * scaleFactor
                        text: Math.round(throttleValue)
                        font.pixelSize: 10 * scaleFactor
                        color: throttleValue > 10 ? "#000000" : throttleColor
                    }
                }
            }
        }
    }
}
