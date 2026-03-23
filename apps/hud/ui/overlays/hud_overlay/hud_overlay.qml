// MIT License
//
// Copyright (c) [2026] [Ashwin Natarajan]
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0

    readonly property int baseWidth: 470
    readonly property int baseHeight: 112

    width:  Math.max(1, Math.round(baseWidth  * scaleFactor))
    height: Math.max(1, Math.round(baseHeight * scaleFactor))
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property real   throttleValue:  0
    property real   brakeValue:     0
    property int    revLightsPct:   0
    property int    rpm:            0
    property int    gear:           0
    property int    speedKmph:      0
    property bool   drsEnabled:     false
    property bool   drsAvailable:   false
    property int    drsDistance:    0
    property real   ersRemPct:      0
    property real   ersHarvPct:     0
    property real   ersDeployedPct: 0
    property string ersMode:        "None"
    property int    turnNumber:     0
    property string turnName:       ""
    property int    tlWarnings:     0

    // ── Helpers ─────────────────────────────────────────────────────────────

    function gearLabel(g) {
        if (g < 0)  return "R"
        if (g === 0) return "N"
        return g.toString()
    }

    function clampPct(v) {
        return Math.max(0, Math.min(100, v))
    }

    function revColor(index, total) {
        var n = index / Math.max(1, total - 1)
        if (n < 0.55) return "#39d37a"
        if (n < 0.85) return "#ffb347"
        return "#ff5f64"
    }

    function turnLabel() {
        if (turnNumber > 0 && turnName.length > 0)
            return "T" + turnNumber + "  " + turnName
        if (turnNumber > 0)
            return "TURN " + turnNumber
        if (turnName.length > 0)
            return turnName
        return "TRACK DATA"
    }

    // Color for the ERS battery ring based on current mode
    function ersInnerColor(mode) {
        var m = mode.toLowerCase()
        if (m.indexOf("overtake") !== -1) return "#c46bff"   // Purple
        if (m.indexOf("high")     !== -1) return "#5b9fff"   // Blue
        if (m.indexOf("medium")   !== -1) return "#3fd6d0"   // Cyan
        if (m.indexOf("low")      !== -1) return "#39d37a"   // Green
        return "#6b7a8a"                                      // Grey (none/off)
    }

    function tlColor() {
        if (tlWarnings >= 2) return "#ff4444"
        if (tlWarnings >= 1) return "#ffc000"
        return "#6a7f92"
    }

    // ── Root scaled container ────────────────────────────────────────────────

    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width:  baseWidth
        height: baseHeight

        readonly property int edgeBarWidth: 8
        readonly property int edgeGap:      4

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: baseWidth  / 2
            origin.y: baseHeight / 2
        }

        // ── Brake bar (left edge) ────────────────────────────────────────────
        Rectangle {
            anchors.left:   parent.left
            anchors.top:    parent.top
            anchors.bottom: parent.bottom
            width:  scaledRoot.edgeBarWidth
            radius: width / 2
            color:        Qt.rgba(1, 0.35, 0.4, 0.20)
            border.width: 1
            border.color: Qt.rgba(1, 0.45, 0.5, 0.55)

            Rectangle {
                id: brakeBarFill
                anchors.left:   parent.left
                anchors.right:  parent.right
                anchors.bottom: parent.bottom
                height: Math.max(0, root.clampPct(root.brakeValue) / 100 * parent.height)
                radius: parent.radius
                color: "#ff5f67"
                Behavior on height { SmoothedAnimation { duration: 70 } }

                Rectangle {
                    visible: brakeBarFill.height > 3
                    anchors { left: parent.left; right: parent.right; top: parent.top }
                    height: 1
                    color: Qt.rgba(1, 1, 1, 0.55)
                }
            }
        }

        // ── Throttle bar (right edge) ────────────────────────────────────────
        Rectangle {
            anchors.right:  parent.right
            anchors.top:    parent.top
            anchors.bottom: parent.bottom
            width:  scaledRoot.edgeBarWidth
            radius: width / 2
            color:        Qt.rgba(0.3, 0.9, 0.55, 0.20)
            border.width: 1
            border.color: Qt.rgba(0.4, 1.0, 0.65, 0.55)

            Rectangle {
                id: throttleBarFill
                anchors.left:   parent.left
                anchors.right:  parent.right
                anchors.bottom: parent.bottom
                height: Math.max(0, root.clampPct(root.throttleValue) / 100 * parent.height)
                radius: parent.radius
                color: "#45df87"
                Behavior on height { SmoothedAnimation { duration: 70 } }

                Rectangle {
                    visible: throttleBarFill.height > 3
                    anchors { left: parent.left; right: parent.right; top: parent.top }
                    height: 1
                    color: Qt.rgba(1, 1, 1, 0.55)
                }
            }
        }

        // ── Main HUD shell ───────────────────────────────────────────────────
        Rectangle {
            id: hudShell
            anchors {
                left:   parent.left
                right:  parent.right
                top:    parent.top
                bottom: parent.bottom
                leftMargin:  scaledRoot.edgeBarWidth + scaledRoot.edgeGap
                rightMargin: scaledRoot.edgeBarWidth + scaledRoot.edgeGap
            }
            clip:         true
            radius:       24
            border.width: 1
            border.color: "#2b3946"

            gradient: Gradient {
                GradientStop { position: 0.0; color: "#172130" }
                GradientStop { position: 0.5; color: "#121b28" }
                GradientStop { position: 1.0; color: "#0e1620" }
            }

            // Subtle diagonal sheen
            Rectangle {
                width:    parent.width * 0.76
                height:   parent.height * 1.7
                x:        parent.width * 0.15
                y:        -parent.height * 0.56
                rotation: -15
                radius:   width / 2
                color:    Qt.rgba(1, 1, 1, 0.025)
            }

            // ── Three-zone layout ────────────────────────────────────────────
            RowLayout {
                anchors.fill:    parent
                anchors.margins: 6
                spacing: 8

                // ════════════════════════════════════════════════════════════
                //  LEFT — GEAR
                // ════════════════════════════════════════════════════════════
                Item {
                    Layout.preferredWidth: 82
                    Layout.fillHeight:     true

                    Rectangle {
                        id: gearDial
                        property int observedGear: root.gear
                        onObservedGearChanged: gearPulse.restart()

                        width:  78
                        height: 78
                        radius: 39
                        anchors.centerIn: parent
                        color:        "#0b1520"
                        border.width: 2
                        border.color: {
                            if (root.gear < 0)   return "#ff6d74"
                            if (root.gear === 0) return "#ffc16d"
                            return "#4a9fd4"
                        }

                        // Inner glow ring
                        Rectangle {
                            anchors.centerIn: parent
                            width:  parent.width  - 6
                            height: parent.height - 6
                            radius: width / 2
                            color:        "transparent"
                            border.width: 1
                            border.color: {
                                if (root.gear < 0)   return Qt.rgba(1.00, 0.43, 0.45, 0.20)
                                if (root.gear === 0) return Qt.rgba(1.00, 0.76, 0.43, 0.20)
                                return Qt.rgba(0.29, 0.62, 0.83, 0.20)
                            }
                        }

                        SequentialAnimation {
                            id: gearPulse
                            NumberAnimation { target: gearDial; property: "scale"; to: 1.08; duration: 70;  easing.type: Easing.OutCubic  }
                            NumberAnimation { target: gearDial; property: "scale"; to: 1.00; duration: 120; easing.type: Easing.InOutQuad }
                        }

                        Text {
                            anchors.centerIn: parent
                            text:            root.gearLabel(root.gear)
                            font.family:     "Formula1"
                            font.pixelSize:  38
                            font.bold:       true
                            color:           "#edf7ff"
                        }
                    }
                }

                // ════════════════════════════════════════════════════════════
                //  CENTER — CORE DATA
                // ════════════════════════════════════════════════════════════
                ColumnLayout {
                    Layout.fillWidth:  true
                    Layout.fillHeight: true
                    spacing: 2

                    // Corner name (elide on overflow, flash on entry)
                    Text {
                        id: cornerNameText
                        Layout.fillWidth:      true
                        Layout.preferredHeight: 16
                        text:                  root.turnLabel().toUpperCase()
                        font.family:           "Formula1"
                        font.pixelSize:        11
                        font.letterSpacing:    1.0
                        color:                 "#a8bfd4"
                        opacity:               0.65
                        elide:                 Text.ElideRight
                        horizontalAlignment:   Text.AlignHCenter
                        verticalAlignment:     Text.AlignVCenter
                        Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.InOutQuad } }
                    }

                    Connections {
                        target: root
                        function onTurnNumberChanged() {
                            if (root.turnNumber > 0) cornerFlash.restart()
                        }
                    }

                    SequentialAnimation {
                        id: cornerFlash
                        NumberAnimation { target: cornerNameText; property: "opacity"; to: 1.0;  duration: 180; easing.type: Easing.OutQuad   }
                        PauseAnimation  { duration: 2500 }
                        NumberAnimation { target: cornerNameText; property: "opacity"; to: 0.65; duration: 600; easing.type: Easing.InOutQuad  }
                    }

                    // Speed (large, fills remaining height)
                    Item {
                        Layout.fillWidth:  true
                        Layout.fillHeight: true

                        Text {
                            anchors.centerIn:   parent
                            text:               root.speedKmph
                            font.family:        "Formula1"
                            font.pixelSize:     44
                            font.bold:          true
                            color:              "#edf7ff"
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }

                    // RPM bar — segmented, green → orange → red
                    Item {
                        Layout.fillWidth:       true
                        Layout.preferredHeight: 10

                        RowLayout {
                            anchors.fill: parent
                            spacing: 1

                            Repeater {
                                model: 20
                                Rectangle {
                                    id: revSeg
                                    Layout.fillWidth:  true
                                    Layout.fillHeight: true
                                    radius: 1

                                    readonly property int  litCount:  Math.round(root.clampPct(root.revLightsPct) / 100 * 20)
                                    readonly property bool isLit:     index < litCount
                                    readonly property bool isRedline: index >= 17

                                    color: isLit ? root.revColor(index, 20) : "#192531"
                                    Behavior on color { ColorAnimation { duration: 50 } }

                                    onIsLitChanged: if (!isLit) revSeg.opacity = 1.0

                                    SequentialAnimation on opacity {
                                        running: revSeg.isLit && revSeg.isRedline
                                        loops:   Animation.Infinite
                                        NumberAnimation { to: 0.45; duration: 180 }
                                        NumberAnimation { to: 1.00; duration: 200 }
                                    }
                                }
                            }
                        }
                    }

                    // Secondary info row — track limits (left) + DRS (right)
                    RowLayout {
                        Layout.fillWidth:       true
                        Layout.preferredHeight: 14
                        spacing: 6

                        // Track limits
                        Text {
                            id: tlText
                            text:            "TL  " + root.tlWarnings
                            font.family:     "Formula1"
                            font.pixelSize:  10
                            color:           root.tlColor()
                            verticalAlignment: Text.AlignVCenter

                            onColorChanged: if (root.tlWarnings < 2) tlText.opacity = 1.0

                            SequentialAnimation on opacity {
                                running: root.tlWarnings >= 2
                                loops:   Animation.Infinite
                                NumberAnimation { to: 0.45; duration: 280 }
                                NumberAnimation { to: 1.00; duration: 280 }
                            }
                        }

                        Item { Layout.fillWidth: true }

                        // DRS badge
                        Rectangle {
                            Layout.preferredHeight: 12
                            Layout.preferredWidth:  drsLabel.implicitWidth + 12
                            radius:       5
                            color:        root.drsEnabled   ? Qt.rgba(0.21, 0.85, 0.79, 0.18)
                                        : root.drsAvailable ? Qt.rgba(1.00, 0.79, 0.32, 0.12)
                                        :                     Qt.rgba(0.16, 0.22, 0.28, 0.50)
                            border.width: 1
                            border.color: root.drsEnabled   ? "#35d8cb"
                                        : root.drsAvailable ? "#ffca52"
                                        :                     "#2d3e4d"

                            Text {
                                id: drsLabel
                                anchors.centerIn: parent
                                text: root.drsEnabled
                                    ? "DRS"
                                    : root.drsAvailable
                                        ? (root.drsDistance > 0 ? root.drsDistance + "m" : "DRS")
                                        : "DRS"
                                font.family:    "Formula1"
                                font.pixelSize: 8
                                color: root.drsEnabled   ? "#35d8cb"
                                     : root.drsAvailable ? "#ffca52"
                                     :                     "#3d4f5e"
                            }
                        }
                    }
                } // ColumnLayout (center)

                // ════════════════════════════════════════════════════════════
                //  RIGHT — ERS
                // ════════════════════════════════════════════════════════════
                Item {
                    id: ersZone
                    Layout.preferredWidth: 94
                    Layout.fillHeight:     true

                    // Smoothly animated source values drive the canvas
                    property real animErsRem:    root.clampPct(root.ersRemPct)
                    property real animErsHarv:   root.clampPct(root.ersHarvPct)
                    property real animErsDeploy: root.clampPct(root.ersDeployedPct)
                    Behavior on animErsRem    { SmoothedAnimation { duration: 220 } }
                    Behavior on animErsHarv   { SmoothedAnimation { duration: 220 } }
                    Behavior on animErsDeploy { SmoothedAnimation { duration: 220 } }

                    onAnimErsRemChanged:    ersCanvas.requestPaint()
                    onAnimErsHarvChanged:   ersCanvas.requestPaint()
                    onAnimErsDeployChanged: ersCanvas.requestPaint()

                    Connections {
                        target: root
                        function onErsModeChanged() { ersCanvas.requestPaint() }
                    }

                    // Canvas draws: outer split ring + battery progress ring + center disk
                    Canvas {
                        id: ersCanvas
                        anchors.centerIn: parent
                        width:  88
                        height: 88

                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)

                            var cx = width  / 2   // 44
                            var cy = height / 2   // 44
                            var outerR      = 40  // outer split-ring radius
                            var battR       = 33  // battery progress-ring radius
                            var battStroke  = 7   // battery ring stroke width
                            var innerR      = 26  // center dark disk radius
                            var halfPi      = Math.PI / 2
                            var top         = -halfPi  // 12 o'clock

                            // ── background ring (grey) ──
                            ctx.beginPath()
                            ctx.arc(cx, cy, outerR, 0, 2 * Math.PI)
                            ctx.strokeStyle = "#1e2e3c"
                            ctx.lineWidth   = 2.5
                            ctx.stroke()

                            // ── deploy arc — left half, orange/red ──
                            // Drains: starts at top, sweeps CCW (left side), proportional to deployedPct
                            var deployFrac = ersZone.animErsDeploy / 100
                            if (deployFrac > 0.002) {
                                ctx.beginPath()
                                ctx.arc(cx, cy, outerR, top, top - deployFrac * Math.PI, true)
                                ctx.strokeStyle = "#ff7a38"
                                ctx.lineWidth   = 3
                                ctx.lineCap     = "round"
                                ctx.stroke()
                            }

                            // ── harvest arc — right half, green ──
                            // Fills: starts at top, sweeps CW (right side), proportional to harvPct
                            var harvestFrac = ersZone.animErsHarv / 100
                            if (harvestFrac > 0.002) {
                                ctx.beginPath()
                                ctx.arc(cx, cy, outerR, top, top + harvestFrac * Math.PI, false)
                                ctx.strokeStyle = "#39d37a"
                                ctx.lineWidth   = 3
                                ctx.lineCap     = "round"
                                ctx.stroke()
                            }

                            // ── battery ring background ──
                            ctx.beginPath()
                            ctx.arc(cx, cy, battR, 0, 2 * Math.PI)
                            ctx.strokeStyle = "#101e2c"
                            ctx.lineWidth   = battStroke + 1
                            ctx.stroke()

                            // ── battery progress (clockwise from top) ──
                            var battFrac = ersZone.animErsRem / 100
                            if (battFrac > 0.002) {
                                ctx.beginPath()
                                ctx.arc(cx, cy, battR, top, top + battFrac * 2 * Math.PI, false)
                                ctx.strokeStyle = root.ersInnerColor(root.ersMode)
                                ctx.lineWidth   = battStroke
                                ctx.lineCap     = "round"
                                ctx.stroke()
                            }

                            // ── center dark disk ──
                            ctx.beginPath()
                            ctx.arc(cx, cy, innerR, 0, 2 * Math.PI)
                            ctx.fillStyle = "#09131f"
                            ctx.fill()
                        }
                    }

                    // Battery percentage — centered inside canvas
                    Text {
                        anchors.horizontalCenter: ersCanvas.horizontalCenter
                        anchors.verticalCenter:   ersCanvas.verticalCenter
                        anchors.verticalCenterOffset: -5
                        text:            Math.round(root.clampPct(root.ersRemPct)) + "%"
                        font.family:     "B612Mono"
                        font.pixelSize:  14
                        font.bold:       true
                        color:           root.ersInnerColor(root.ersMode)
                        horizontalAlignment: Text.AlignHCenter
                        Behavior on color { ColorAnimation { duration: 250 } }
                    }

                    // ERS mode label — small, below percentage
                    Text {
                        anchors.horizontalCenter: ersCanvas.horizontalCenter
                        anchors.verticalCenter:   ersCanvas.verticalCenter
                        anchors.verticalCenterOffset: 9
                        text:            root.ersMode.toUpperCase()
                        font.family:     "Formula1"
                        font.pixelSize:  7
                        color:           Qt.rgba(0.67, 0.79, 0.87, 0.65)
                        horizontalAlignment: Text.AlignHCenter
                    }

                } // ersZone

            } // RowLayout
        } // hudShell
    } // scaledRoot
}
