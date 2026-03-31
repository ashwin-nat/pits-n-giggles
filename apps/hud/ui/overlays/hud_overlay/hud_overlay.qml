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
    readonly property int baseHeight: 120

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
    property string speedUnitLabel: "km/h"
    property bool   drsEnabled:     false
    property bool   drsAvailable:   false
    property int    drsDistance:    0
    property real   ersRemPct:      0
    property real   ersHarvPct:     0
    property real   ersDeployedPct: 0
    property string ersMode:        "None"
    property int    tlWarnings:     0
    property var    surplusFuel:    null

    property int    trackTempC:     0
    property int    airTempC:       0

    // Marquee scroll speed in px/sec — increase for faster scrolling, decrease for slower
    readonly property real marqueeSpeed: 60

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
        let n = index / Math.max(1, total - 1)
        if (n < (1 / 3)) return "#39d37a"
        if (n < (2 / 3)) return "#ff1744"
        return "#9b30ff"
    }

    // Fill colour for the ERS inner circle based on current mode
    function ersInnerColor(mode) {
        let m = mode.toLowerCase()
        if (m.indexOf("overtake") !== -1) return "#ff1744"   // Red
        if (m.indexOf("hotlap")   !== -1) return "#00e676"   // Green
        if (m.indexOf("medium")   !== -1) return "#ffd700"   // Yellow
        return "#4a5a6a"                                      // Grey (none/off)
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

        // ── Rev lights — thin bar above the pill ─────────────────────────────
        Item {
            id: revLightsBar
            anchors.left:        parent.left
            anchors.right:       parent.right
            anchors.top:         parent.top
            anchors.leftMargin:  49
            anchors.rightMargin: 49
            height: 5

            RowLayout {
                anchors.fill: parent
                spacing: 1

                Repeater {
                    model: 20
                    Rectangle {
                        Layout.fillWidth:  true
                        Layout.fillHeight: true
                        radius: 1

                        readonly property int  litCount:  Math.round(root.clampPct(root.revLightsPct) / 100 * 20)
                        readonly property bool isLit:     index < litCount
                        readonly property bool isRedline: index >= 17

                        color: isLit ? root.revColor(index, 20) : "#192531"
                        Behavior on color { ColorAnimation { duration: 50 } }

                        onIsLitChanged: if (!isLit) opacity = 1.0

                        SequentialAnimation on opacity {
                            running: isLit && isRedline
                            loops:   Animation.Infinite
                            NumberAnimation { to: 0.45; duration: 180 }
                            NumberAnimation { to: 1.00; duration: 200 }
                        }
                    }
                }
            }
        }

        // ── Main HUD shell (full-width pill, radius = height/2) ──────────────
        Rectangle {
            id: hudShell
            anchors.left:  parent.left
            anchors.right: parent.right
            anchors.top:   revLightsBar.bottom
            anchors.topMargin: 3
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
                anchors.topMargin:     0
                anchors.bottomMargin:  0
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
                Item {
                    Layout.fillWidth:    true
                    Layout.fillHeight:   true
                    Layout.topMargin:    12
                    Layout.bottomMargin: 12

                    // ── Left 30% — Speed (top) | RPM (bottom) ────────────────
                    Item {
                        id: centerLeft
                        anchors.left:   parent.left
                        anchors.top:    parent.top
                        anchors.bottom: parent.bottom
                        width:          parent.width * 0.3

                        Column {
                            anchors.centerIn: parent
                            spacing: 0

                            Text {
                                text:                root.speedUnitLabel
                                font.family:         "Formula1"
                                font.pixelSize:      8
                                color:               "#7a94a8"
                                width:               centerLeft.width
                                horizontalAlignment: Text.AlignHCenter
                            }
                            Text {
                                text:                root.speedKmph
                                font.family:         "Formula1"
                                font.pixelSize:      20
                                font.bold:           true
                                color:               "#edf7ff"
                                width:               centerLeft.width
                                horizontalAlignment: Text.AlignHCenter
                            }
                            Rectangle {
                                width:  centerLeft.width
                                height: 1
                                color:  "#2b3946"
                            }
                            Text {
                                text:                root.rpm
                                font.family:         "Formula1"
                                font.pixelSize:      20
                                font.bold:           true
                                color:               "#edf7ff"
                                width:               centerLeft.width
                                horizontalAlignment: Text.AlignHCenter
                            }
                            Text {
                                text:                "RPM"
                                font.family:         "Formula1"
                                font.pixelSize:      8
                                color:               "#7a94a8"
                                width:               centerLeft.width
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }

                    // Vertical separator
                    Rectangle {
                        anchors.left:   centerLeft.right
                        anchors.top:    parent.top
                        anchors.bottom: parent.bottom
                        width: 1
                        color: "#2b3946"
                    }

                    // ── Right 70% — TL / AIR / TRACK (upper) + DRS (lower) ──
                    ColumnLayout {
                        anchors.left:   centerLeft.right
                        anchors.leftMargin: 6
                        anchors.right:  parent.right
                        anchors.top:    parent.top
                        anchors.bottom: parent.bottom
                        spacing: 0

                        // ── Upper row: TL / AIR / TRACK ───────────────────────
                        Item {
                            Layout.fillWidth:  true
                            Layout.fillHeight: true

                        RowLayout {
                            anchors.fill: parent
                            spacing: 0

                            // ── Track limits ──────────────────────────────────
                            Item {
                                Layout.fillWidth:  true
                                Layout.fillHeight: true

                                Row {
                                    anchors.centerIn: parent
                                    spacing: 3

                                    Image {
                                        source:  "../../../../../assets/overlays/tl-warns.svg"
                                        width:   12
                                        height:  12
                                        smooth:  true
                                        mipmap:  true
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    Text {
                                        text:            root.tlWarnings
                                        font.family:     "Formula1"
                                        font.pixelSize:  12
                                        font.bold:       true
                                        color:           "#edf7ff"
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }

                            // ── Air temperature ───────────────────────────────
                            Item {
                                Layout.fillWidth:  true
                                Layout.fillHeight: true

                                Row {
                                    anchors.centerIn: parent
                                    spacing: 3

                                    Image {
                                        source:  "../../../../../assets/overlays/air-temperature.svg"
                                        width:   12
                                        height:  12
                                        smooth:  true
                                        mipmap:  true
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    Text {
                                        text:            root.airTempC + "°"
                                        font.family:     "Formula1"
                                        font.pixelSize:  12
                                        font.bold:       true
                                        color:           "#edf7ff"
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }

                            // ── Track temperature ─────────────────────────────
                            Item {
                                Layout.fillWidth:  true
                                Layout.fillHeight: true

                                Row {
                                    anchors.centerIn: parent
                                    spacing: 3

                                    Image {
                                        source:  "../../../../../assets/overlays/track-temperature.svg"
                                        width:   12
                                        height:  12
                                        smooth:  true
                                        mipmap:  true
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    Text {
                                        text:            root.trackTempC + "°"
                                        font.family:     "Formula1"
                                        font.pixelSize:  12
                                        font.bold:       true
                                        color:           "#edf7ff"
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }
                        }
                        } // Item (upper row wrapper)

                        // ── Lower row: DRS bar (left 2/3) + Fuel (right 1/3) ─
                        Item {
                            Layout.fillWidth:  true
                            Layout.fillHeight: true

                            // DRS bar — spans first 2 of 3 columns
                            Item {
                                id: drsCell
                                anchors.left:   parent.left
                                anchors.top:    parent.top
                                anchors.bottom: parent.bottom
                                width:          (parent.width - 4) * 2 / 3

                                Rectangle {
                                    anchors.centerIn: parent
                                    height:       22
                                    width:        parent.width - 8
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
                                        id:              drsLabel
                                        anchors.centerIn: parent
                                        text:            "DRS"
                                        font.family:     "Formula1"
                                        font.pixelSize:  8
                                        color: root.drsEnabled
                                               ? "#00e676"
                                               : (root.drsAvailable || root.drsDistance > 0)
                                                   ? "#ffca52"
                                                   : "#3d4f5e"
                                        z: 1
                                    }
                                }
                            }

                            // Fuel — spans 3rd column
                            Item {
                                anchors.left:       drsCell.right
                                anchors.leftMargin: 4
                                anchors.right:      parent.right
                                anchors.top:        parent.top
                                anchors.bottom:     parent.bottom

                                Row {
                                    anchors.centerIn: parent
                                    spacing: 3

                                    Image {
                                        source:  "../../../../../assets/overlays/fuel-pump.svg"
                                        width:   12
                                        height:  12
                                        smooth:  true
                                        mipmap:  true
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    Text {
                                        text: root.surplusFuel !== null
                                              ? (root.surplusFuel >= 0 ? "+" : "") + root.surplusFuel.toFixed(2)
                                              : "---"
                                        font.family:    "Formula1"
                                        font.pixelSize: 12
                                        font.bold:      true
                                        color:          root.surplusFuel === null
                                                        ? "#3d4f5e"
                                                        : root.surplusFuel >= 0
                                                            ? "#00e676"
                                                            : "#ff1744"
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }
                        }
                    }
                } // Item (center)

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
                            let ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)

                            let cx      = width  / 2   // 44
                            let cy      = height / 2   // 44
                            let outerR  = 40           // outer split-ring radius
                            let innerR  = 34           // inner fill circle radius (was 26, expanded into freed battery-ring space)
                            let halfPi  = Math.PI / 2
                            let top     = -halfPi      // 12 o'clock

                            // ── outer background ring ──
                            ctx.beginPath()
                            ctx.arc(cx, cy, outerR, 0, 2 * Math.PI)
                            ctx.strokeStyle = "#1e2e3c"
                            ctx.lineWidth   = 2.5
                            ctx.stroke()

                            // ── harvest arc — left half, red ──
                            let harvestFrac = ersZone.animErsHarv / 100
                            if (harvestFrac > 0.002) {
                                ctx.beginPath()
                                ctx.arc(cx, cy, outerR, top, top - harvestFrac * Math.PI, true)
                                ctx.strokeStyle = "#FF1744"
                                ctx.lineWidth   = 3
                                ctx.lineCap     = "round"
                                ctx.stroke()
                            }

                            // ── deploy arc — right half, hotlap green ──
                            let deployFrac = (100 - ersZone.animErsDeploy) / 100
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
                            let fillFrac = ersZone.animErsRem / 100
                            if (fillFrac > 0.005) {
                                ctx.save()
                                let fillHeight = fillFrac * 2 * innerR
                                let fillTop    = cy + innerR - fillHeight
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
                color:        Qt.rgba(0, 0.9019607843, 0.462745098, 0.15)
                border.width: 1
                border.color: Qt.rgba(0, 0.9019607843, 0.462745098, 0.55)
                clip: true

                Rectangle {
                    anchors.left:   parent.left
                    anchors.top:    parent.top
                    anchors.bottom: parent.bottom
                    width:  Math.max(0, root.clampPct(root.throttleValue) / 100 * parent.width)
                    radius: parent.radius
                    color:  "#00e676"
                    Behavior on width { SmoothedAnimation { duration: 70 } }
                }
            }
        } // input bars

    } // scaledRoot
}
