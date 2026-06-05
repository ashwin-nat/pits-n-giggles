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
    color: "#000000"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property real scaleFactor: 1.0

    // Live data — set by Python via set_qml_property
    property real   totalPowerKw:  0
    property real   icePowerKw:    0
    property real   mgukPowerKw:   0
    property real   iceFraction:   0
    property real   mgukFraction:  0
    property int    iceTempC:      0
    property string ersMode:       ""
    property color  ersColor:      "#c4c4d4"

    readonly property int baseWidth:  220
    readonly property int baseHeight: 106

    width:  baseWidth  * scaleFactor
    height: baseHeight * scaleFactor

    // ── Design tokens (aligned with lap_timer palette) ────────────────────────
    readonly property color clrBorder:  "#26263a"
    readonly property color clrTrack:   "#14141c"
    readonly property color clrLabel:   "#55556e"
    readonly property color clrValue:   "#c4c4d4"
    readonly property color clrPrimary: "#ffffff"
    readonly property color clrIce:     "#ff1744"
    readonly property color clrMguk:    "#41bff3"

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

        Rectangle {
            anchors.fill: parent
            color:        "#0c0c10"
            radius:       6
            border.width: 1
            border.color: root.clrBorder

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
                        text:           parent.displayKw.toFixed(1) + " kW"
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

                // ── ICE / MGU-K breakdown ─────────────────────────────────
                RowLayout {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 18
                    spacing: 0

                    // ICE — left side
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text:               "ICE"
                            font.family:        "Formula1"
                            font.pixelSize:     10
                            font.letterSpacing: 0.8
                            color:              root.clrValue
                            Layout.alignment:   Qt.AlignVCenter
                        }

                        Item {
                            Layout.fillWidth: true
                            height:           18

                            property real displayKw: root.icePowerKw
                            Behavior on displayKw {
                                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                            }

                            Text {
                                anchors.left:           parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                text:           parent.displayKw.toFixed(1)
                                font.family:    "Formula1"
                                font.pixelSize: 13
                                font.weight:    Font.Bold
                                color:          root.clrValue
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
                            font.pixelSize:     10
                            font.letterSpacing: 0.8
                            color:              root.clrValue
                            Layout.alignment:   Qt.AlignVCenter
                        }

                        Item {
                            Layout.fillWidth: true
                            height:           18

                            property real displayKw: root.mgukPowerKw
                            Behavior on displayKw {
                                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                            }

                            Text {
                                anchors.right:          parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                text:           parent.displayKw.toFixed(1)
                                font.family:    "Formula1"
                                font.pixelSize: 13
                                font.weight:    Font.Bold
                                color:          root.clrValue
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true; Layout.preferredHeight: 4 }

                // ── Temperature + ERS mode ───────────────────────────────
                RowLayout {
                    Layout.fillWidth:       true
                    Layout.preferredHeight: 16
                    spacing: 0

                    // TEMP — left
                    RowLayout {
                        spacing: 5

                        Text {
                            text:               "TEMP"
                            font.family:        "Formula1"
                            font.pixelSize:     10
                            font.letterSpacing: 0.8
                            color:              root.clrLabel
                            Layout.alignment:   Qt.AlignVCenter
                        }

                        Text {
                            text:             root.iceTempC + "°C"
                            font.family:      "Formula1"
                            font.pixelSize:   13
                            font.weight:      Font.Bold
                            color:            root.clrValue
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }

                    Item { Layout.fillWidth: true }

                    // ERS mode — right
                    Text {
                        text:               root.ersMode
                        font.family:        "Formula1"
                        font.pixelSize:     13
                        font.weight:        Font.Bold
                        font.letterSpacing: 1.2
                        color:              root.ersColor
                        Layout.alignment:   Qt.AlignVCenter
                        Behavior on color { ColorAnimation { duration: 300 } }
                    }
                }
            }
        }

    }
}
