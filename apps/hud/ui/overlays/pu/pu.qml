// MIT License
//
// Copyright (c) [2025] [Ashwin Natarajan]
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
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property real scaleFactor: 1.0
    property bool minimalView: false

    // Live data — set by Python via set_qml_property
    property real   totalPowerKw:  0
    property real   icePowerKw:    0
    property real   mgukPowerKw:   0
    property real   iceFraction:   0
    property real   mgukFraction:  0
    property real   ersRemPct:     0
    property real   deployPct:     0
    property real   harvestPct:    0
    property string ersMode:       ""
    property string ersModeColor:  "#444444"
    property int    iceTempC:      0
    property bool   f1_26Enabled:  false
    property bool   otActive:      false

    // Full layout adds the ICE / MGU-K breakdown row (14px content + 4px gap)
    readonly property int baseWidth:  220
    readonly property int baseHeight: minimalView ? 80 : 96

    width:  baseWidth  * scaleFactor
    height: baseHeight * scaleFactor

    // ── Helpers ──────────────────────────────────────────────────────────────

    function tempColor(t) {
        if (t >= 120) return "#ff1744"
        if (t >= 110) return "#ffa726"
        return "#c8d6e5"
    }

    // ── Design tokens ─────────────────────────────────────────────────────────
    readonly property color clrBorder:  "#2b3946"
    readonly property color clrTrack:   "#1e2e3c"
    readonly property color clrLabel:   "#7a94a8"
    readonly property color clrValue:   "#c8d6e5"
    readonly property color clrPrimary: "#edf7ff"
    readonly property color clrIce:     "#e53935"
    readonly property color clrMguk:    "#42a5f5"

    // ── Scaled root ───────────────────────────────────────────────────────────
    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width:  root.baseWidth
        height: root.baseHeight

        transform: Scale {
            xScale: root.scaleFactor
            yScale: root.scaleFactor
            origin.x: root.baseWidth  / 2
            origin.y: root.baseHeight / 2
        }

        // ═════════════════════════════════════════════════════════════════════
        //  FULL OVERLAY  — adds ICE / MGU-K breakdown row
        // ═════════════════════════════════════════════════════════════════════
        Rectangle {
            anchors.fill: parent
            color:        "#de131d2a"
            radius:       6
            border.width: 1
            border.color: root.clrBorder
            visible: !root.minimalView

            ColumnLayout {
                anchors.fill:         parent
                anchors.topMargin:    10
                anchors.bottomMargin: 10
                anchors.leftMargin:   10
                anchors.rightMargin:  10
                spacing: 0

                // ── Total power ───────────────────────────────────────────
                Item {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 28

                    property real displayKw: root.totalPowerKw
                    Behavior on displayKw { SmoothedAnimation { duration: 150; velocity: -1 } }

                    Text {
                        anchors.centerIn: parent
                        text:           parent.displayKw.toFixed(2) + " kW"
                        font.family:    "Formula1"
                        font.pixelSize: 24
                        font.weight:    Font.Bold
                        color:          root.clrPrimary
                    }
                }

                Item { Layout.fillWidth: true; Layout.preferredHeight: 4 }

                // ── Power split bar ───────────────────────────────────────
                Rectangle {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 10
                    color: root.clrTrack
                    clip:  true

                    Rectangle {
                        id: iceBarFull
                        property real animFrac: root.iceFraction
                        Behavior on animFrac { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
                        anchors.left: parent.left
                        height:       parent.height
                        width:        parent.width * animFrac
                        color:        root.clrIce
                    }

                    Rectangle {
                        property real animFrac: root.mgukFraction
                        Behavior on animFrac { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
                        anchors.left: iceBarFull.right
                        height:       parent.height
                        width:        parent.width * animFrac
                        color:        root.clrMguk
                    }
                }

                Item { Layout.fillWidth: true; Layout.preferredHeight: 4 }

                // ── ICE / MGU-K breakdown (full-only) ─────────────────────
                RowLayout {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 14
                    spacing: 0

                    // ICE — left side
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text:               "ICE"
                            font.family:        "Formula1"
                            font.pixelSize:     8
                            font.letterSpacing: 0.8
                            color:              root.clrIce
                            Layout.alignment:   Qt.AlignVCenter
                        }

                        Item {
                            Layout.fillWidth: true
                            height:           14

                            property real displayKw: root.icePowerKw
                            Behavior on displayKw {
                                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                            }

                            Text {
                                anchors.left:           parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                text:           parent.displayKw.toFixed(2)
                                font.family:    "Formula1"
                                font.pixelSize: 10
                                font.weight:    Font.Bold
                                color:          root.clrIce
                            }
                        }
                    }

                    // MGU-K — right side
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        layoutDirection: Qt.RightToLeft

                        Text {
                            text:               "MGU-K"
                            font.family:        "Formula1"
                            font.pixelSize:     8
                            font.letterSpacing: 0.8
                            color:              root.clrMguk
                            Layout.alignment:   Qt.AlignVCenter
                        }

                        Item {
                            Layout.fillWidth: true
                            height:           14

                            property real displayKw: root.mgukPowerKw
                            Behavior on displayKw {
                                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                            }

                            Text {
                                anchors.right:          parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                text:           parent.displayKw.toFixed(2)
                                font.family:    "Formula1"
                                font.pixelSize: 10
                                font.weight:    Font.Bold
                                color:          root.clrMguk
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true; Layout.preferredHeight: 6 }

                // ── Temperature ───────────────────────────────────────────
                RowLayout {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 12
                    spacing: 5

                    Text {
                        text:               "TEMP"
                        font.family:        "Formula1"
                        font.pixelSize:     8
                        font.letterSpacing: 0.8
                        color:              root.clrLabel
                        Layout.alignment:   Qt.AlignVCenter
                    }

                    Text {
                        id:             tempLabelFull
                        text:           root.iceTempC + "°C"
                        font.family:    "Formula1"
                        font.pixelSize: 10
                        font.weight:    Font.Bold
                        color:          root.tempColor(root.iceTempC)
                        Layout.alignment: Qt.AlignVCenter
                        Behavior on color { ColorAnimation { duration: 400 } }

                        property real critPulse: 1.0
                        opacity: critPulse

                        SequentialAnimation on critPulse {
                            running: root.iceTempC >= 120
                            loops:   Animation.Infinite
                            NumberAnimation { to: 0.5; duration: 600; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 1.0; duration: 600; easing.type: Easing.InOutSine }
                            onStopped: tempLabelFull.critPulse = 1.0
                        }
                    }
                }
            }
        }

        // ═════════════════════════════════════════════════════════════════════
        //  MINIMAL OVERLAY
        // ═════════════════════════════════════════════════════════════════════
        Rectangle {
            anchors.fill: parent
            color:        "#de131d2a"
            radius:       6
            border.width: 1
            border.color: root.clrBorder
            visible: root.minimalView

            ColumnLayout {
                anchors.fill:         parent
                anchors.topMargin:    10
                anchors.bottomMargin: 10
                anchors.leftMargin:   10
                anchors.rightMargin:  10
                spacing: 0

                // ── Total power ───────────────────────────────────────────
                Item {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 28

                    property real displayKw: root.totalPowerKw
                    Behavior on displayKw { SmoothedAnimation { duration: 150; velocity: -1 } }

                    Text {
                        anchors.centerIn: parent
                        text:           parent.displayKw.toFixed(2) + " kW"
                        font.family:    "Formula1"
                        font.pixelSize: 24
                        font.weight:    Font.Bold
                        color:          root.clrPrimary
                    }
                }

                Item { Layout.fillWidth: true; Layout.preferredHeight: 4 }

                // ── Power split bar ───────────────────────────────────────
                Rectangle {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 10
                    color: root.clrTrack
                    clip:  true

                    Rectangle {
                        id: iceBarMin
                        property real animFrac: root.iceFraction
                        Behavior on animFrac { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
                        anchors.left: parent.left
                        height:       parent.height
                        width:        parent.width * animFrac
                        color:        root.clrIce
                    }

                    Rectangle {
                        property real animFrac: root.mgukFraction
                        Behavior on animFrac { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
                        anchors.left: iceBarMin.right
                        height:       parent.height
                        width:        parent.width * animFrac
                        color:        root.clrMguk
                    }
                }

                Item { Layout.fillWidth: true; Layout.preferredHeight: 6 }

                // ── Temperature ───────────────────────────────────────────
                RowLayout {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 12
                    spacing: 5

                    Text {
                        text:               "TEMP"
                        font.family:        "Formula1"
                        font.pixelSize:     8
                        font.letterSpacing: 0.8
                        color:              root.clrLabel
                        Layout.alignment:   Qt.AlignVCenter
                    }

                    Text {
                        id:             tempLabelMin
                        text:           root.iceTempC + "°C"
                        font.family:    "Formula1"
                        font.pixelSize: 10
                        font.weight:    Font.Bold
                        color:          root.tempColor(root.iceTempC)
                        Layout.alignment: Qt.AlignVCenter
                        Behavior on color { ColorAnimation { duration: 400 } }

                        property real critPulse: 1.0
                        opacity: critPulse

                        SequentialAnimation on critPulse {
                            running: root.iceTempC >= 120
                            loops:   Animation.Infinite
                            NumberAnimation { to: 0.5; duration: 600; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 1.0; duration: 600; easing.type: Easing.InOutSine }
                            onStopped: tempLabelMin.critPulse = 1.0
                        }
                    }
                }
            }
        }
    }
}
