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

    // Fill colour for the ERS inner circle based on current mode
    function ersInnerColor(mode) {
        var m = mode.toLowerCase()
        if (m.indexOf("overtake") !== -1) return "#ff1744"   // Red
        if (m.indexOf("hotlap")   !== -1) return "#00e676"   // Green
        if (m.indexOf("medium")   !== -1) return "#ffd700"   // Yellow
        return "#4a5a6a"                                      // Grey (none/off)
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

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: baseWidth  / 2
            origin.y: baseHeight / 2
        }

        // ── Main HUD shell (full-width pill, radius = height/2) ──────────────
        Rectangle {
            id: hudShell
            anchors.left:  parent.left
            anchors.right: parent.right
            anchors.top:   parent.top
            height: 98
            clip:         true
            radius:       49   // = height / 2  →  perfect stadium / parabolica shape
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
            // Left/right margins = 0 so gear/ERS circles are concentric with
            // the pill's semicircular ends (same radius, same centre point).
            RowLayout {
                anchors.fill:          parent
                anchors.topMargin:     5
                anchors.bottomMargin:  5
                anchors.leftMargin:    0
                anchors.rightMargin:   0
                spacing: 6

                // ════════════════════════════════════════════════════════════
                //  LEFT — GEAR  (zone width = pill height → concentric end)
                // ════════════════════════════════════════════════════════════
                Item {
                    Layout.preferredWidth: 98
                    Layout.fillHeight:     true

                    Rectangle {
                        id: gearDial
                        property int observedGear: root.gear
                        onObservedGearChanged: gearPulse.restart()

                        width:  86
                        height: 86
                        radius: 43
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
                            font.pixelSize:  42
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

                        // DRS badge – wider pill with distance-fill bar
                        Rectangle {
                            Layout.preferredHeight: 12
                            Layout.preferredWidth:  56
                            radius:       5
                            clip:         true
                            color:        root.drsEnabled
                                              ? Qt.rgba(0.00, 0.90, 0.42, 0.18)
                                              : (root.drsAvailable || root.drsDistance > 0)
                                                  ? Qt.rgba(1.00, 0.79, 0.32, 0.10)
                                                  : Qt.rgba(0.16, 0.22, 0.28, 0.50)
                            border.width: 1
                            border.color: root.drsEnabled
                                              ? "#00e676"
                                              : (root.drsAvailable || root.drsDistance > 0)
                                                  ? "#ffca52"
                                                  : "#2d3e4d"

                            // Fill bar: grows left→right as drsDistance shrinks toward 0
                            Rectangle {
                                anchors.left:   parent.left
                                anchors.top:    parent.top
                                anchors.bottom: parent.bottom
                                visible: !root.drsEnabled &&
                                         (root.drsDistance > 0 ||
                                          (root.drsAvailable && root.drsDistance === 0))
                                width: (root.drsAvailable && root.drsDistance === 0)
                                       ? parent.width
                                       : parent.width * Math.max(0.0, 1.0 - root.drsDistance / 250.0)
                                color: Qt.rgba(1.00, 0.79, 0.32, 0.50)
                                Behavior on width { SmoothedAnimation { duration: 150 } }
                            }

                            Text {
                                id:             drsLabel
                                anchors.centerIn: parent
                                text:           "DRS"
                                font.family:    "Formula1"
                                font.pixelSize: 8
                                color: root.drsEnabled
                                       ? "#00e676"
                                       : (root.drsAvailable || root.drsDistance > 0)
                                           ? "#ffca52"
                                           : "#3d4f5e"
                                z: 1
                            }
                        }
                    }
                } // ColumnLayout (center)

                // ════════════════════════════════════════════════════════════
                //  RIGHT — ERS  (zone width = pill height → concentric end)
                // ════════════════════════════════════════════════════════════
                Item {
                    id: ersZone
                    Layout.preferredWidth: 98
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

                    // Canvas draws: outer split ring (deploy/harvest) + inner fill circle
                    Canvas {
                        id: ersCanvas
                        anchors.centerIn: parent
                        width:  88
                        height: 88

                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)

                            var cx      = width  / 2   // 44
                            var cy      = height / 2   // 44
                            var outerR  = 40           // outer split-ring radius
                            var innerR  = 34           // inner fill circle radius (was 26, expanded into freed battery-ring space)
                            var halfPi  = Math.PI / 2
                            var top     = -halfPi      // 12 o'clock

                            // ── outer background ring ──
                            ctx.beginPath()
                            ctx.arc(cx, cy, outerR, 0, 2 * Math.PI)
                            ctx.strokeStyle = "#1e2e3c"
                            ctx.lineWidth   = 2.5
                            ctx.stroke()

                            // ── harvest arc — left half, red ──
                            var harvestFrac = ersZone.animErsHarv / 100
                            if (harvestFrac > 0.002) {
                                ctx.beginPath()
                                ctx.arc(cx, cy, outerR, top, top - harvestFrac * Math.PI, true)
                                ctx.strokeStyle = "#FF1744"
                                ctx.lineWidth   = 3
                                ctx.lineCap     = "round"
                                ctx.stroke()
                            }

                            // ── deploy arc — right half, hotlap green ──
                            var deployFrac = (100 - ersZone.animErsDeploy) / 100
                            if (deployFrac > 0.002) {
                                ctx.beginPath()
                                ctx.arc(cx, cy, outerR, top, top + deployFrac * Math.PI, false)
                                ctx.strokeStyle = "#00e676"
                                ctx.lineWidth   = 3
                                ctx.lineCap     = "round"
                                ctx.stroke()
                            }

                            // ── inner background disk ──
                            ctx.beginPath()
                            ctx.arc(cx, cy, innerR, 0, 2 * Math.PI)
                            ctx.fillStyle = "#09131f"
                            ctx.fill()

                            // ── bottom-to-top fill clipped to inner circle ──
                            var fillFrac = ersZone.animErsRem / 100
                            if (fillFrac > 0.005) {
                                ctx.save()
                                var fillHeight = fillFrac * 2 * innerR
                                var fillTop    = cy + innerR - fillHeight
                                ctx.beginPath()
                                ctx.rect(cx - innerR - 1, fillTop, 2 * innerR + 2, fillHeight + 1)
                                ctx.clip()

                                ctx.beginPath()
                                ctx.arc(cx, cy, innerR, 0, 2 * Math.PI)
                                ctx.fillStyle = root.ersInnerColor(root.ersMode)
                                ctx.fill()
                                ctx.restore()
                            }

                            // ── inner circle border ──
                            ctx.beginPath()
                            ctx.arc(cx, cy, innerR, 0, 2 * Math.PI)
                            ctx.strokeStyle = "#2b3946"
                            ctx.lineWidth   = 1.5
                            ctx.stroke()

                        }
                    }

                    // Battery percentage — outlined only in Medium mode (yellow fill)
                    Item {
                        anchors.centerIn: ersCanvas
                        width:  ersPctLabel.width
                        height: ersPctLabel.height

                        Repeater {
                            model: [[-1,-1],[-1,1],[1,-1],[1,1]]
                            Text {
                                visible:        root.ersMode.toLowerCase().indexOf("medium") !== -1
                                x: ersPctLabel.x + modelData[0]
                                y: ersPctLabel.y + modelData[1]
                                text:           Math.round(root.clampPct(root.ersRemPct)) + "%"
                                font.family:    "B612Mono"
                                font.pixelSize: 16
                                font.bold:      true
                                color:          "#000000"
                            }
                        }

                        Text {
                            id: ersPctLabel
                            text:            Math.round(root.clampPct(root.ersRemPct)) + "%"
                            font.family:     "B612Mono"
                            font.pixelSize:  16
                            font.bold:       true
                            color:           "#edf7ff"
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }

                } // ersZone

            } // RowLayout
        } // hudShell

        // ── Brake / Throttle bars (below pill, spanning straight section only) ─
        // Inset by hudShell.radius (49px) on each side so the bars start and
        // end exactly where the pill's curvature begins.
        // Brake  (left):  fills right → left
        // Throttle (right): fills left → right
        Row {
            anchors.left:        parent.left
            anchors.right:       parent.right
            anchors.top:         hudShell.bottom
            anchors.topMargin:   4
            anchors.leftMargin:  hudShell.radius
            anchors.rightMargin: hudShell.radius
            height:  10
            spacing: 4

            // Brake — right-to-left fill
            Rectangle {
                id: brakeTrack
                width:  (parent.width - parent.spacing) / 2
                height: parent.height
                radius: height / 2
                color:        Qt.rgba(1, 0.09, 0.27, 0.15)
                border.width: 1
                border.color: Qt.rgba(1, 0.09, 0.27, 0.55)
                clip: true

                Rectangle {
                    anchors.right:  parent.right
                    anchors.top:    parent.top
                    anchors.bottom: parent.bottom
                    width:  Math.max(0, root.clampPct(root.brakeValue) / 100 * parent.width)
                    radius: parent.radius
                    color:  "#FF1744"
                    Behavior on width { SmoothedAnimation { duration: 70 } }
                }
            }

            // Throttle — left-to-right fill
            Rectangle {
                id: throttleTrack
                width:  (parent.width - parent.spacing) / 2
                height: parent.height
                radius: height / 2
                color:        Qt.rgba(0.46, 1, 0.01, 0.15)
                border.width: 1
                border.color: Qt.rgba(0.46, 1, 0.01, 0.55)
                clip: true

                Rectangle {
                    anchors.left:   parent.left
                    anchors.top:    parent.top
                    anchors.bottom: parent.bottom
                    width:  Math.max(0, root.clampPct(root.throttleValue) / 100 * parent.width)
                    radius: parent.radius
                    color:  "#76FF03"
                    Behavior on width { SmoothedAnimation { duration: 70 } }
                }
            }
        } // input bars

    } // scaledRoot
}
