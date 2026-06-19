import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0
    readonly property int baseWidth: 450
    readonly property int baseHeight: 120

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
    property real throttleSmoothed: 0
    property real brakeSmoothed:    0
    property real steeringSmoothed: 0
    property real revLightsSmoothed: 0
    property real smoothingFactor:  0.2


    // ----------------------------------------------------------
    // HISTORY - fixed-size circular buffer (Float32Array x 3)
    // historyHead is the next write slot and always points at the oldest entry
    // once full; reading starts at historyHead and wraps via % maxHistoryLength.
    // ----------------------------------------------------------
    property var throttleHistory: null
    property var brakeHistory:    null
    property var steeringHistory: null
    property int maxHistoryLength: 175
    property int historyHead:  0
    property int historyCount: 0

    function _resetHistory() {
        throttleHistory = new Float32Array(maxHistoryLength)
        brakeHistory    = new Float32Array(maxHistoryLength)
        steeringHistory = new Float32Array(maxHistoryLength)
        historyHead  = 0
        historyCount = 0
    }

    Component.onCompleted:     _resetHistory()
    onMaxHistoryLengthChanged: _resetHistory()

    function updateTelemetry(throttle, brake, steering, revPct) {
        throttleSmoothed = throttleSmoothed * smoothingFactor + throttle * (1 - smoothingFactor)
        brakeSmoothed    = brakeSmoothed    * smoothingFactor + brake * (1 - smoothingFactor)
        steeringSmoothed = steeringSmoothed * smoothingFactor + steering * (1 - smoothingFactor)
        revLightsSmoothed = revLightsSmoothed * smoothingFactor + revPct * (1 - smoothingFactor)

        throttleHistory[historyHead] = throttleSmoothed
        brakeHistory[historyHead]    = brakeSmoothed
        steeringHistory[historyHead] = steeringSmoothed
        historyHead = (historyHead + 1) % maxHistoryLength
        if (historyCount < maxHistoryLength) historyCount++

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

                    // top gradient strip (rev lights)
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        height: 3
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0.0; color: "transparent" }
                            GradientStop { position: 0.3; color: Qt.rgba(brakeColor.r, brakeColor.g, brakeColor.b, root.revLightsSmoothed / 100) }
                            GradientStop { position: 0.7; color: Qt.rgba(throttleColor.r, throttleColor.g, throttleColor.b, root.revLightsSmoothed / 100) }
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

                            if (!root.throttleHistory || root.historyCount < 2)
                                return

                            let len   = root.historyCount
                            let start = (root.historyHead - len + root.maxHistoryLength) % root.maxHistoryLength
                            let spacing = width / (maxHistoryLength - 1)

                            // Throttle tint fill
                            let gradT = ctx.createLinearGradient(0, height, 0, 0)
                            gradT.addColorStop(0, Qt.rgba(throttleColor.r, throttleColor.g, throttleColor.b, 0.15))
                            gradT.addColorStop(1, Qt.rgba(throttleColor.r, throttleColor.g, throttleColor.b, 0))
                            ctx.fillStyle = gradT
                            ctx.beginPath()
                            ctx.moveTo(0, height)
                            for (let t=0; t<len; t++) {
                                let yT = height - (root.throttleHistory[(start + t) % root.maxHistoryLength] / 100) * height
                                ctx.lineTo(t * spacing, yT)
                            }
                            ctx.lineTo((len-1)*spacing, height)
                            ctx.closePath()
                            ctx.fill()

                            // Brake tint fill
                            let gradB = ctx.createLinearGradient(0, height, 0, 0)
                            gradB.addColorStop(0, Qt.rgba(brakeColor.r, brakeColor.g, brakeColor.b, 0.15))
                            gradB.addColorStop(1, Qt.rgba(brakeColor.r, brakeColor.g, brakeColor.b, 0))
                            ctx.fillStyle = gradB
                            ctx.beginPath()
                            ctx.moveTo(0, height)
                            for (let b=0; b<len; b++) {
                                let yB = height - (root.brakeHistory[(start + b) % root.maxHistoryLength] / 100) * height
                                ctx.lineTo(b*spacing, yB)
                            }
                            ctx.lineTo((len-1)*spacing, height)
                            ctx.closePath()
                            ctx.fill()

                            // --- THROTTLE LINE ---
                            ctx.strokeStyle = throttleColor
                            ctx.lineWidth = 2
                            ctx.beginPath()
                            for (let t2=0; t2<len; t2++) {
                                let yT2 = height - (root.throttleHistory[(start + t2) % root.maxHistoryLength]/100)*height
                                if (t2===0) ctx.moveTo(0,yT2)
                                else ctx.lineTo(t2*spacing, yT2)
                            }
                            ctx.stroke()

                            // --- BRAKE LINE ---
                            ctx.strokeStyle = brakeColor
                            ctx.beginPath()
                            for (let b2=0; b2<len; b2++) {
                                let yB2 = height - (root.brakeHistory[(start + b2) % root.maxHistoryLength]/100)*height
                                if (b2===0) ctx.moveTo(0,yB2)
                                else ctx.lineTo(b2*spacing, yB2)
                            }
                            ctx.stroke()

                            // --- STEERING LINE ---
                            ctx.strokeStyle = steeringColor
                            ctx.beginPath()
                            for (let s=0; s<len; s++) {
                                let yS = height/2 - (root.steeringHistory[(start + s) % root.maxHistoryLength]/100)*(height/2)
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
                            height: (root.brakeSmoothed / 100) * parent.height
                            color: brakeColor
                            Behavior on height { SmoothedAnimation { duration: 60 } }
                        }

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 2
                            text: Math.round(root.brakeSmoothed)
                            font.pixelSize: 10
                            color: root.brakeSmoothed > 10 ? "#000000" : root.brakeColor
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
                            height: (root.throttleSmoothed / 100) * parent.height
                            color: throttleColor
                            Behavior on height { SmoothedAnimation { duration: 60 } }
                        }

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 2
                            text: Math.round(root.throttleSmoothed)
                            font.pixelSize: 10
                            color: root.throttleSmoothed > 10 ? "#000000" : root.throttleColor
                        }
                    }
                }
            }
        }
    }
}
