import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0
    readonly property int baseWidth: 420
    readonly property int baseHeight: 130

    width: baseWidth * scaleFactor
    height: baseHeight * scaleFactor
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint


    // ----------------------------------------------------------
    // COLORS
    // ----------------------------------------------------------
    property color throttleColor: "#76FF03"
    property color brakeColor:    "#FF1744"
    property color steeringColor: "#2979FF"

    // Telemetry values (0–100)
    //
    property real throttleValue: 0
    property real brakeValue:    0
    property real steeringValue: 0

    property real throttleSmoothed: 0
    property real brakeSmoothed:    0
    property real steeringSmoothed: 0
    property real smoothingFactor:  0.2


    // ----------------------------------------------------------
    // HISTORY
    // ----------------------------------------------------------
    property var throttleHistory: []
    property var brakeHistory:    []
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

        // ======================================================
        // BACKGROUND CONTAINER
        // ======================================================
        Rectangle {
            id: container
            x: 6
            y: 6
            width: baseWidth - 12
            height: baseHeight - 12
            radius: 6
            color: "#000000"


            // ==================================================
            // MAIN LAYOUT USING RowLayout (NO CLIPPING)
            // ==================================================
            RowLayout {
                id: mainLayout
                anchors.fill: parent
                anchors.margins: 8
                spacing: 10   // tighter spacing between chart and bars

            //----------------------------------------------------------------
            // GRAPH AREA
            //----------------------------------------------------------------
                Item {
                    id: graphArea
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    // top gradient strip
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        height: 3
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

                        onPaint: {
                            let ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)

                            // Grid
                            ctx.strokeStyle = "#1a1a1a"
                            ctx.lineWidth = 1
                            for (let i = 1; i < 4; i++) {
                                let y = height * i / 4
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

                            let spacing = width / (maxHistoryLength - 1)

                            // Throttle tint fill
                            let gradT = ctx.createLinearGradient(0, height, 0, 0)
                            gradT.addColorStop(0, Qt.rgba(throttleColor.r, throttleColor.g, throttleColor.b, 0.15))
                            gradT.addColorStop(1, Qt.rgba(throttleColor.r, throttleColor.g, throttleColor.b, 0))
                            ctx.fillStyle = gradT
                            ctx.beginPath()
                            ctx.moveTo(0, height)
                            for (let t=0; t<throttleHistory.length; t++) {
                                let yT = height - (throttleHistory[t] / 100) * height
                                ctx.lineTo(t * spacing, yT)
                            }
                            ctx.lineTo((throttleHistory.length-1)*spacing, height)
                            ctx.closePath()
                            ctx.fill()

                            // Brake tint fill
                            let gradB = ctx.createLinearGradient(0, height, 0, 0)
                            gradB.addColorStop(0, Qt.rgba(brakeColor.r, brakeColor.g, brakeColor.b, 0.15))
                            gradB.addColorStop(1, Qt.rgba(brakeColor.r, brakeColor.g, brakeColor.b, 0))
                            ctx.fillStyle = gradB
                            ctx.beginPath()
                            ctx.moveTo(0, height)
                            for (let b=0; b<brakeHistory.length; b++) {
                                let yB = height - (brakeHistory[b] / 100) * height
                                ctx.lineTo(b*spacing, yB)
                            }
                            ctx.lineTo((brakeHistory.length-1)*spacing, height)
                            ctx.closePath()
                            ctx.fill()

                            // --- THROTTLE LINE ---
                            ctx.strokeStyle = throttleColor
                            ctx.lineWidth = 2
                            ctx.beginPath()
                            for (let t2=0; t2<throttleHistory.length; t2++) {
                                let yT2 = height - (throttleHistory[t2]/100)*height
                                if (t2===0) ctx.moveTo(0,yT2)
                                else ctx.lineTo(t2*spacing, yT2)
                            }
                            ctx.stroke()

                            // --- BRAKE LINE ---
                            ctx.strokeStyle = brakeColor
                            ctx.beginPath()
                            for (let b2=0; b2<brakeHistory.length; b2++) {
                                let yB2 = height - (brakeHistory[b2]/100)*height
                                if (b2===0) ctx.moveTo(0,yB2)
                                else ctx.lineTo(b2*spacing, yB2)
                            }
                            ctx.stroke()

                            // --- STEERING LINE ---
                            ctx.strokeStyle = steeringColor
                            ctx.beginPath()
                            for (let s=0; s<steeringHistory.length; s++) {
                                let yS = height/2 - (steeringHistory[s]/100)*(height/2)
                                if (s===0) ctx.moveTo(0,yS)
                                else ctx.lineTo(s*spacing, yS)
                            }
                            ctx.stroke()
                        }
                    }
                }

                // ------------------------------------------------
                // VERTICAL BARS (fixed width)
                // ------------------------------------------------
                RowLayout {
                    id: bars
                    Layout.preferredWidth: 60
                    Layout.fillHeight: true
                    spacing: 6

                    // --- BRAKE BAR ---
                    Rectangle {
                        width: 22
                        Layout.fillHeight: true
                        radius: 3
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
                            anchors.bottomMargin: 2
                            text: Math.round(brakeValue)
                            font.pixelSize: 10
                            color: brakeValue > 10 ? "#000000" : brakeColor
                        }
                    }

                    // --- THROTTLE BAR ---
                    Rectangle {
                        width: 22
                        Layout.fillHeight: true
                        radius: 3
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
                            anchors.bottomMargin: 2
                            text: Math.round(throttleValue)
                            font.pixelSize: 10
                            color: throttleValue > 10 ? "#000000" : throttleColor
                        }
                    }
                }
            }
        }
    }
}
