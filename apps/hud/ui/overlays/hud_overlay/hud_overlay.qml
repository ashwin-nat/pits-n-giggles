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

// ─── SHAPE: compound — hexagon body flanked by two thin vertical bars ─────────
//
//   BRK │ /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\ │ THR
//   bar │ │  [rev lights]                       │ │ bar
//       │ │  [gear + speed]   │  [DRS / ERS]    │ │
//   bar │ \_____________________________________/ │ bar
//
// The two 12-px side bars are absolutely positioned; the hexagon sits between
// them.  No clipping required — all content is naturally inside the shape.

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0   // REQUIRED by BaseOverlayQML

    readonly property int baseWidth:  560
    readonly property int baseHeight: 112

    width:  Math.max(1, Math.round(baseWidth  * scaleFactor))
    height: Math.max(1, Math.round(baseHeight * scaleFactor))
    color:  "transparent"
    flags:  Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    // ─── Telemetry properties ─────────────────────────────────────────────────
    property real   throttleValue:  0
    property real   brakeValue:     0
    property int    revLightsPct:   0
    property int    rpm:            0
    property int    gear:           0
    property int    speedKmph:      0
    property bool   drsEnabled:     false
    property bool   drsAvailable:   false
    property int    drsDistance:    0
    property real   ersRemPct:      0       // 0–100
    property real   ersHarvPct:     0       // 0–100  (MGU-K / 2 MJ)
    property real   ersDeployedPct: 0       // 0–100  (deployed / 4 MJ)
    property string ersMode:        "None"
    property int    turnNumber:     0
    property string turnName:       ""

    // ─── Colours ─────────────────────────────────────────────────────────────
    readonly property color colBg:        "#0a0a0f"
    readonly property color colBorder:    "#1d1d2a"
    readonly property color colF1Red:     "#e8002d"
    readonly property color colThrottle:  "#39b54a"
    readonly property color colBrake:     "#e8002d"
    readonly property color colDrsActive: "#00d2be"
    readonly property color colDrsAvail:  "#ffd700"
    readonly property color colErs:       "#1e90ff"
    readonly property color colDim:       "#38384a"

    function gearLabel(g) {
        if (g < 0)   return "R"
        if (g === 0) return "N"
        return g.toString()
    }

    // ─── Scaled root ──────────────────────────────────────────────────────────
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

        // ── Brake bar — left, absolute ────────────────────────────────────────
        SideBar {
            x: 0;  y: 4
            width:  12
            height: parent.height - 8
            value:     root.brakeValue
            fillColor: root.colBrake
        }

        // ── Throttle bar — right, absolute ────────────────────────────────────
        SideBar {
            x: parent.width - 12;  y: 4
            width:  12
            height: parent.height - 8
            value:     root.throttleValue
            fillColor: root.colThrottle
        }

        // ── Hexagon body ──────────────────────────────────────────────────────
        // gap of 4 px on each side separates it from the side bars
        Item {
            id: mainBody
            x:      16
            y:      0
            width:  parent.width - 32   // 528 px
            height: parent.height

            // Hexagon background — 45° corner cuts
            Canvas {
                id: bgCanvas
                anchors.fill: parent
                z: 0
                readonly property int cut: 20

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    var c = cut, w = width, h = height

                    // Fill
                    ctx.fillStyle = "#0a0a0f"
                    ctx.beginPath()
                    ctx.moveTo(c, 0);    ctx.lineTo(w - c, 0)
                    ctx.lineTo(w, c);    ctx.lineTo(w, h - c)
                    ctx.lineTo(w - c, h); ctx.lineTo(c, h)
                    ctx.lineTo(0, h - c); ctx.lineTo(0, c)
                    ctx.closePath()
                    ctx.fill()

                    // Border
                    ctx.strokeStyle = "#26263a"
                    ctx.lineWidth = 1
                    ctx.stroke()
                }
            }

            // Content — inset to stay clear of the angled corners
            ColumnLayout {
                anchors.fill:        parent
                anchors.leftMargin:  bgCanvas.cut + 2
                anchors.rightMargin: bgCanvas.cut + 2
                spacing: 0
                z: 1

                // ── Rev-lights strip ──────────────────────────────────────────
                Canvas {
                    id: revCanvas
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 9

                    property int pct: root.revLightsPct
                    onPctChanged: requestPaint()

                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        var total = 15
                        var lit   = Math.round(pct / 100 * total)
                        var sw    = width / total
                        var gap   = 2
                        var bw    = sw - gap
                        var colors = [
                            "#39b54a","#39b54a","#39b54a","#39b54a","#39b54a",
                            "#ff8c00","#ff8c00","#ff8c00","#ff8c00","#ff8c00",
                            "#e8002d","#e8002d","#e8002d",
                            "#cc00ff","#cc00ff"
                        ]
                        for (var i = 0; i < total; i++) {
                            var x = i * sw + gap / 2
                            ctx.fillStyle = (i < lit) ? colors[i] : "#171720"
                            ctx.fillRect(x, 0, bw, height)
                        }
                    }
                }

                // hairline
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: root.colBorder
                }

                // ── Main row: gear+speed | divider | DRS+ERS ─────────────────
                RowLayout {
                    Layout.fillWidth:  true
                    Layout.fillHeight: true
                    spacing: 0

                    // CENTER: Gear + Speed
                    CenterPanel {
                        Layout.fillWidth:  true
                        Layout.fillHeight: true
                        gear:  root.gear
                        speed: root.speedKmph
                        rpm:   root.rpm
                    }

                    // Angled divider
                    AngledDivider { Layout.fillHeight: true }

                    // RIGHT: DRS + ERS
                    DrsErsPanel {
                        Layout.preferredWidth: 238
                        Layout.fillHeight:     true
                        drsEnabled:     root.drsEnabled
                        drsAvailable:   root.drsAvailable
                        drsDistance:    root.drsDistance
                        ersRemPct:      root.ersRemPct
                        ersHarvPct:     root.ersHarvPct
                        ersDeployedPct: root.ersDeployedPct
                        ersMode:        root.ersMode
                        turnNumber:     root.turnNumber
                        turnName:       root.turnName
                    }
                }
            }
        }
    }


    // ─────────────────────────────────────────────────────────────────────────
    // INLINE COMPONENTS
    // ─────────────────────────────────────────────────────────────────────────

    // ── SideBar ───────────────────────────────────────────────────────────────
    // Vertical fill bar (fill rises from bottom).  Colour tint bg + bright
    // glow cap at the current fill level.
    component SideBar: Item {
        property real  value:     0
        property color fillColor: "#ffffff"

        // Background tint
        Rectangle {
            anchors.fill: parent
            radius: 3
            color:        Qt.rgba(fillColor.r, fillColor.g, fillColor.b, 0.06)
            border.color: Qt.rgba(fillColor.r, fillColor.g, fillColor.b, 0.18)
            border.width: 1
        }

        // Animated fill
        Rectangle {
            id: sideFill
            anchors.bottom: parent.bottom
            anchors.left:   parent.left
            anchors.right:  parent.right
            height: Math.max(0, (value / 100) * parent.height)
            color:  fillColor
            radius: 3
            Behavior on height { SmoothedAnimation { duration: 40 } }

            // Glow cap — bright white line at the fill level
            Rectangle {
                visible: sideFill.height > 4
                anchors.top:   parent.top
                anchors.left:  parent.left
                anchors.right: parent.right
                height: 2
                radius: 1
                color: Qt.rgba(1, 1, 1, 0.55)
            }
        }
    }

    // ── AngledDivider ─────────────────────────────────────────────────────────
    component AngledDivider: Item {
        width: 12

        Rectangle {
            width:  1
            height: parent.height + 8
            anchors.centerIn: parent
            color: root.colBorder
            transform: Rotation {
                origin.x: 0.5
                origin.y: height / 2
                angle: -6
            }
        }
    }

    // ── CenterPanel ───────────────────────────────────────────────────────────
    // Gear (hero element) + speed + RPM, all packed tight.
    // Gear pulses briefly on each shift.
    component CenterPanel: Item {
        property int gear:  0
        property int speed: 0
        property int rpm:   0

        onGearChanged: {
            if (gearDisplay.scale === 1.0)
                gearPulse.restart()
        }

        // Brief scale-up flash on gear shift
        SequentialAnimation {
            id: gearPulse
            NumberAnimation { target: gearDisplay; property: "scale"; to: 1.14; duration: 55;  easing.type: Easing.OutQuad }
            NumberAnimation { target: gearDisplay; property: "scale"; to: 1.0;  duration: 110; easing.type: Easing.InOutQuad }
        }

        RowLayout {
            anchors.centerIn: parent
            spacing: 10

            // Giant gear
            Text {
                id: gearDisplay
                text: root.gearLabel(gear)
                font.family:    "Formula1"
                font.pixelSize: 60
                font.bold:      true
                transformOrigin: Item.Center
                color: {
                    if (gear < 0)   return "#ff5555"
                    if (gear === 0) return "#ffaa00"
                    return "#ffffff"
                }
                Behavior on color { ColorAnimation { duration: 80 } }
            }

            // Speed + RPM stacked
            ColumnLayout {
                spacing: 2

                RowLayout {
                    spacing: 3

                    Text {
                        text: speed
                        font.family:    "B612Mono"
                        font.pixelSize: 26
                        font.bold:      true
                        color: "#e8e8e8"
                    }

                    Text {
                        text: "km/h"
                        font.family:    "Formula1"
                        font.pixelSize: 9
                        color: "#50506a"
                        Layout.alignment: Qt.AlignBottom
                        bottomPadding: 3
                    }
                }

                Text {
                    text: (rpm / 1000).toFixed(1) + "k RPM"
                    font.family:    "B612Mono"
                    font.pixelSize: 10
                    color: "#404858"
                }
            }
        }
    }

    // ── DrsErsPanel ───────────────────────────────────────────────────────────
    // DRS badge
    // ERS remaining — large bar, colour-shifts blue→orange→red as it depletes
    //                 tiny mode dot on the left
    // HARV bar (red) / DEP bar (green) — side by side, no labels
    // Turn info
    component DrsErsPanel: Item {
        property bool   drsEnabled:     false
        property bool   drsAvailable:   false
        property int    drsDistance:    0
        property real   ersRemPct:      0
        property real   ersHarvPct:     0
        property real   ersDeployedPct: 0
        property string ersMode:        "None"
        property int    turnNumber:     0
        property string turnName:       ""

        ColumnLayout {
            anchors.fill:    parent
            anchors.margins: 7
            spacing: 5

            // ── DRS badge ─────────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth:       true
                Layout.preferredHeight: 20
                radius: 3
                color: {
                    if (drsEnabled)   return Qt.rgba(0, 0.82, 0.75, 0.18)
                    if (drsAvailable) return Qt.rgba(1, 0.84, 0,    0.12)
                    return "#0c0c14"
                }
                border.color: {
                    if (drsEnabled)   return root.colDrsActive
                    if (drsAvailable) return root.colDrsAvail
                    return "#232332"
                }
                border.width: 1

                RowLayout {
                    anchors.fill:        parent
                    anchors.leftMargin:  6
                    anchors.rightMargin: 6

                    Text {
                        text: "DRS"
                        font.family:    "Formula1"
                        font.pixelSize: 9
                        font.bold:      true
                        color: drsEnabled ? root.colDrsActive : drsAvailable ? root.colDrsAvail : root.colDim
                    }

                    Text {
                        text: {
                            if (drsEnabled)   return "ACTIVE"
                            if (drsAvailable) return (drsDistance > 0 ? drsDistance + "m" : "READY")
                            return "OFF"
                        }
                        font.family:    "B612Mono"
                        font.pixelSize: 9
                        color: drsEnabled ? root.colDrsActive : drsAvailable ? root.colDrsAvail : "#232332"
                        Layout.fillWidth:    true
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }

            // ── ERS remaining bar ─────────────────────────────────────────
            // mode dot + bar + % value
            RowLayout {
                Layout.fillWidth: true
                spacing: 5

                // ERS mode — coloured dot only, no text
                Rectangle {
                    width: 6; height: 6; radius: 3
                    color: {
                        var m = ersMode.toLowerCase()
                        if (m === "overtake") return "#cc00ff"
                        if (m === "high")     return "#ff8c00"
                        if (m === "medium")   return root.colErs
                        if (m === "low")      return root.colThrottle
                        return root.colDim
                    }
                    Layout.alignment: Qt.AlignVCenter
                }

                // REM bar
                Rectangle {
                    Layout.fillWidth: true
                    height: 11
                    radius: 3
                    color:        "#060612"
                    border.color: "#131325"
                    clip: true

                    Rectangle {
                        id: ersRemFill
                        width:  Math.max(0, (ersRemPct / 100) * parent.width)
                        height: parent.height
                        radius: 3
                        color: {
                            if (ersRemPct > 40) return root.colErs
                            if (ersRemPct > 15) return "#ff8c00"
                            return root.colBrake
                        }
                        Behavior on width { SmoothedAnimation { duration: 130 } }
                        Behavior on color { ColorAnimation  { duration: 300 } }

                        // Bright shimmer at right edge of fill
                        Rectangle {
                            visible: ersRemFill.width > 6
                            anchors.right:  parent.right
                            anchors.top:    parent.top
                            anchors.bottom: parent.bottom
                            width: 3
                            radius: 1
                            color: Qt.rgba(1, 1, 1, 0.30)
                        }
                    }
                }

                // Remaining %
                Text {
                    text: Math.round(ersRemPct) + "%"
                    font.family:    "B612Mono"
                    font.pixelSize: 9
                    color: ersRemPct > 40 ? root.colErs : ersRemPct > 15 ? "#ff8c00" : root.colBrake
                    Layout.preferredWidth: 28
                    horizontalAlignment:   Text.AlignRight
                }
            }

            // ── HARV (red) / DEP (green) mini-bars ───────────────────────
            // Side by side, colour-coded, no text — visual only
            RowLayout {
                Layout.fillWidth: true
                spacing: 5

                // HARV — red
                Rectangle {
                    Layout.fillWidth: true
                    height: 7
                    radius: 2
                    color:        "#100205"
                    border.color: "#2a0508"
                    clip: true

                    Rectangle {
                        width:  Math.max(0, (ersHarvPct / 100) * parent.width)
                        height: parent.height
                        radius: 2
                        color:  root.colBrake
                        Behavior on width { SmoothedAnimation { duration: 100 } }
                    }
                }

                // vertical separator
                Rectangle { width: 1; height: 7; color: root.colBorder }

                // DEP — green
                Rectangle {
                    Layout.fillWidth: true
                    height: 7
                    radius: 2
                    color:        "#011005"
                    border.color: "#052a0a"
                    clip: true

                    Rectangle {
                        width:  Math.max(0, (ersDeployedPct / 100) * parent.width)
                        height: parent.height
                        radius: 2
                        color:  root.colThrottle
                        Behavior on width { SmoothedAnimation { duration: 100 } }
                    }
                }
            }

            // ── Turn info ─────────────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 5

                Rectangle {
                    width: 3; height: 3; radius: 1.5
                    color: root.colF1Red
                    Layout.alignment: Qt.AlignVCenter
                }

                Text {
                    text: {
                        if (turnNumber <= 0) return "–"
                        return "T" + turnNumber + (turnName.length > 0 ? " · " + turnName : "")
                    }
                    font.family:    "Formula1"
                    font.pixelSize: 9
                    color: "#707090"
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
            }

            Item { Layout.fillHeight: true }   // push content upward
        }
    }
}
