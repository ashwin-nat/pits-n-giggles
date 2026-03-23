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

    width: Math.max(1, Math.round(baseWidth * scaleFactor))
    height: Math.max(1, Math.round(baseHeight * scaleFactor))
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property real throttleValue: 0
    property real brakeValue: 0
    property int revLightsPct: 0
    property int rpm: 0
    property int gear: 0
    property int speedKmph: 0
    property bool drsEnabled: false
    property bool drsAvailable: false
    property int drsDistance: 0
    property real ersRemPct: 0
    property real ersHarvPct: 0
    property real ersDeployedPct: 0
    property string ersMode: "None"
    property int turnNumber: 0
    property string turnName: ""
    property int tlWarnings: 0

    function gearLabel(g) {
        if (g < 0)
            return "R"
        if (g === 0)
            return "N"
        return g.toString()
    }

    function clampPct(v) {
        return Math.max(0, Math.min(100, v))
    }

    function modeColor(mode) {
        var m = mode.toLowerCase()
        if (m === "overtake")
            return "#d66bff"
        if (m === "high")
            return "#ff9d4d"
        if (m === "medium")
            return "#5ec2ff"
        if (m === "low")
            return "#7fd66d"
        return "#7f8a96"
    }

    function ersModeFillColor(mode) {
        var m = mode.toLowerCase()
        if (m.indexOf("overtake") !== -1)
            return "#ff5f5f"
        if (m.indexOf("hotlap") !== -1 || m.indexOf("hot lap") !== -1)
            return "#57db7f"
        if (m.indexOf("medium") !== -1)
            return "#ffd54f"
        if (m.indexOf("none") !== -1)
            return "#8e98a4"
        return "#8e98a4"
    }

    function ersModeTextColor(mode) {
        var m = mode.toLowerCase()
        if (m.indexOf("overtake") !== -1)
            return "#fff4f4"
        if (m.indexOf("hotlap") !== -1 || m.indexOf("hot lap") !== -1)
            return "#03210f"
        if (m.indexOf("medium") !== -1)
            return "#241a00"
        if (m.indexOf("none") !== -1)
            return "#f2f6fc"
        return "#f2f6fc"
    }

    function revColor(index, total) {
        var n = index / Math.max(1, total - 1)
        if (n < 0.55)
            return "#39d37a"
        if (n < 0.85)
            return "#ffb347"
        return "#ff5f64"
    }

    function turnLabel() {
        if (turnNumber > 0 && turnName.length > 0)
            return "T" + turnNumber + " " + turnName
        if (turnNumber > 0)
            return "T" + turnNumber
        if (turnName.length > 0)
            return turnName
        return "TRACK DATA"
    }

    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: baseWidth
        height: baseHeight

        readonly property int edgeBarWidth: 8
        readonly property int edgeGap: 4

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: baseWidth / 2
            origin.y: baseHeight / 2
        }

        Rectangle {
            id: brakeBarTrack
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: scaledRoot.edgeBarWidth
            radius: width / 2
            color: Qt.rgba(1, 0.35, 0.4, 0.2)
            border.width: 1
            border.color: Qt.rgba(1, 0.45, 0.5, 0.55)

            Rectangle {
                id: brakeBarFill
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: Math.max(0, root.clampPct(root.brakeValue) / 100 * parent.height)
                radius: parent.radius
                color: "#ff5f67"
                Behavior on height { SmoothedAnimation { duration: 70 } }

                Rectangle {
                    visible: brakeBarFill.height > 3
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 1
                    color: Qt.rgba(1, 1, 1, 0.55)
                }
            }
        }

        Rectangle {
            id: throttleBarTrack
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: scaledRoot.edgeBarWidth
            radius: width / 2
            color: Qt.rgba(0.3, 0.9, 0.55, 0.2)
            border.width: 1
            border.color: Qt.rgba(0.4, 1, 0.65, 0.55)

            Rectangle {
                id: throttleBarFill
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: Math.max(0, root.clampPct(root.throttleValue) / 100 * parent.height)
                radius: parent.radius
                color: "#45df87"
                Behavior on height { SmoothedAnimation { duration: 70 } }

                Rectangle {
                    visible: throttleBarFill.height > 3
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 1
                    color: Qt.rgba(1, 1, 1, 0.55)
                }
            }
        }

        Rectangle {
            id: hudShell
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.leftMargin: scaledRoot.edgeBarWidth + scaledRoot.edgeGap
            anchors.rightMargin: scaledRoot.edgeBarWidth + scaledRoot.edgeGap
            clip: true
            radius: 24
            border.width: 1
            border.color: "#2b3946"
            color: "#101721"

            readonly property int pad: 4
            readonly property int gap: 3
            readonly property int topH: 20
            readonly property int revH: 11
            readonly property int rowH: Math.max(48, height - (pad * 2 + topH + revH + gap * 2))

            gradient: Gradient {
                GradientStop { position: 0.0; color: "#172130" }
                GradientStop { position: 0.5; color: "#121b28" }
                GradientStop { position: 1.0; color: "#0e1620" }
            }

            Rectangle {
                width: parent.width * 0.76
                height: parent.height * 1.7
                x: parent.width * 0.15
                y: -parent.height * 0.56
                rotation: -15
                radius: width / 2
                color: Qt.rgba(1, 1, 1, 0.035)
            }

            Repeater {
                model: 9
                Rectangle {
                    width: 1
                    height: hudShell.height
                    x: 12 + index * 56
                    color: Qt.rgba(0.5, 0.6, 0.7, 0.07)
                }
            }

            Item {
                anchors.fill: parent
                anchors.margins: hudShell.pad

                Rectangle {
                    id: turnBar
                    x: 0
                    y: 0
                    width: parent.width
                    height: hudShell.topH
                    radius: height / 2
                    color: Qt.rgba(0.05, 0.08, 0.12, 0.92)
                    border.width: 1
                    border.color: "#2f3d4b"

                    Text {
                        anchors.centerIn: parent
                        text: root.turnLabel()
                        font.family: "Formula1"
                        font.pixelSize: 11
                        font.bold: true
                        color: "#a8bfd4"
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                        width: parent.width - 14
                    }
                }

                Rectangle {
                    id: revStrip
                    x: 0
                    y: turnBar.y + turnBar.height + hudShell.gap
                    width: parent.width
                    height: hudShell.revH
                    radius: height / 2
                    color: "#0a1018"
                    border.width: 1
                    border.color: "#2c3b49"

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 1
                        spacing: 1

                        Repeater {
                            model: 20
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 1
                                readonly property int litCount: Math.round(root.clampPct(root.revLightsPct) / 100 * 20)
                                color: index < litCount ? root.revColor(index, 20) : "#1b2733"
                                Behavior on color { ColorAnimation { duration: 50 } }
                            }
                        }
                    }
                }

                Item {
                    id: mainRow
                    x: 0
                    y: revStrip.y + revStrip.height + hudShell.gap
                    width: parent.width
                    height: hudShell.rowH

                    readonly property int podGap: 4
                    readonly property int rightW: 170
                    readonly property int centerW: width - rightW - podGap

                    Rectangle {
                        id: drivePod
                        x: 0
                        y: 0
                        width: mainRow.centerW
                        height: mainRow.height
                        radius: 22
                        color: "#152232"
                        border.width: 1
                        border.color: "#344554"

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 8

                            Item {
                                Layout.preferredWidth: 66
                                Layout.fillHeight: true

                                Rectangle {
                                    id: gearDial
                                    property int observedGear: root.gear
                                    onObservedGearChanged: gearPulse.restart()

                                    width: 56
                                    height: 56
                                    radius: 28
                                    anchors.centerIn: parent
                                    color: "#0d1620"
                                    border.width: 2
                                    border.color: {
                                        if (root.gear < 0)
                                            return "#ff6d74"
                                        if (root.gear === 0)
                                            return "#ffc16d"
                                        return "#57b5ff"
                                    }

                                    SequentialAnimation {
                                        id: gearPulse
                                        NumberAnimation { target: gearDial; property: "scale"; to: 1.08; duration: 70; easing.type: Easing.OutCubic }
                                        NumberAnimation { target: gearDial; property: "scale"; to: 1.0; duration: 120; easing.type: Easing.InOutQuad }
                                    }

                                    Text {
                                        anchors.centerIn: parent
                                        text: root.gearLabel(root.gear)
                                        font.family: "Formula1"
                                        font.pixelSize: 32
                                        font.bold: true
                                        color: "#edf7ff"
                                    }
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                RowLayout {
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    spacing: 4

                                    Text {
                                        text: root.speedKmph
                                        font.family: "Formula1"
                                        font.pixelSize: 38
                                        font.bold: true
                                        color: "#edf7ff"
                                    }

                                    Item { Layout.fillWidth: true }

                                    Text {
                                        text: "KM/H"
                                        font.family: "Formula1"
                                        font.pixelSize: 11
                                        color: "#8ea1b4"
                                        horizontalAlignment: Text.AlignRight
                                        Layout.alignment: Qt.AlignBottom
                                        bottomPadding: 7
                                    }
                                }

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.topMargin: 42
                                    height: 1
                                    color: "#314150"
                                }

                                RowLayout {
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.topMargin: 46
                                    spacing: 6

                                    Text {
                                        text: root.rpm + " RPM"
                                        font.family: "Formula1"
                                        font.pixelSize: 12
                                        color: "#9bb0c4"
                                        elide: Text.ElideRight
                                    }

                                    Item { Layout.fillWidth: true }

                                    Text {
                                        text: "TL: " + root.tlWarnings
                                        font.family: "Formula1"
                                        font.pixelSize: 12
                                        color: "#9bb0c4"
                                        horizontalAlignment: Text.AlignRight
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        id: energyPod
                        x: mainRow.centerW + mainRow.podGap
                        y: 0
                        width: mainRow.rightW
                        height: mainRow.height
                        radius: 18
                        color: "#12202d"
                        border.width: 1
                        border.color: "#30414f"

                        readonly property bool overtakeMode: root.ersMode.toLowerCase().indexOf("overtake") !== -1

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 2

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 16
                                radius: 9
                                color: root.drsEnabled ? Qt.rgba(0.19, 0.84, 0.76, 0.17) : root.drsAvailable ? Qt.rgba(1, 0.8, 0.26, 0.17) : Qt.rgba(0.2, 0.27, 0.34, 0.24)
                                border.width: 1
                                border.color: root.drsEnabled ? "#35d8cb" : root.drsAvailable ? "#ffca52" : "#3f4d5b"

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 6
                                    anchors.rightMargin: 6

                                    Text {
                                        text: "DRS"
                                        font.family: "Formula1"
                                        font.pixelSize: 9
                                        color: root.drsEnabled ? "#35d8cb" : root.drsAvailable ? "#ffca52" : "#8493a2"
                                    }

                                    Item { Layout.fillWidth: true }

                                    Text {
                                        text: root.drsEnabled ? "ACTIVE" : root.drsAvailable ? (root.drsDistance > 0 ? root.drsDistance + "m" : "READY") : "OFF"
                                        font.family: "B612Mono"
                                        font.pixelSize: 10
                                        font.bold: true
                                        color: root.drsEnabled ? "#35d8cb" : root.drsAvailable ? "#ffca52" : "#7c8d9d"
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 18
                                spacing: 4

                                Rectangle {
                                    id: ersBarTrack
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    radius: 9
                                    color: "#09111a"
                                    border.width: 1
                                    border.color: energyPod.overtakeMode ? "#ff6a6a" : "#2d3d4c"
                                    clip: true

                                    Rectangle {
                                        id: ersBarFill
                                        width: Math.max(0, root.clampPct(root.ersRemPct) / 100 * parent.width)
                                        height: parent.height
                                        radius: parent.radius
                                        color: root.ersModeFillColor(root.ersMode)
                                        Behavior on width { SmoothedAnimation { duration: 130 } }
                                        Behavior on color { ColorAnimation { duration: 220 } }
                                    }

                                    Rectangle {
                                        id: overtakeGlow
                                        visible: energyPod.overtakeMode
                                        anchors.fill: parent
                                        color: "transparent"
                                        border.width: 1
                                        border.color: "#ff6a6a"
                                        radius: parent.radius
                                        opacity: 0.22

                                        SequentialAnimation on opacity {
                                            running: overtakeGlow.visible
                                            loops: Animation.Infinite
                                            NumberAnimation { to: 0.48; duration: 320; easing.type: Easing.InOutQuad }
                                            NumberAnimation { to: 0.14; duration: 380; easing.type: Easing.InOutQuad }
                                        }
                                    }

                                    Rectangle {
                                        id: overtakeSweep
                                        visible: energyPod.overtakeMode
                                        width: parent.width * 0.28
                                        height: parent.height
                                        x: -width
                                        radius: width / 2
                                        gradient: Gradient {
                                            GradientStop { position: 0.0; color: Qt.rgba(1.0, 0.35, 0.35, 0.0) }
                                            GradientStop { position: 0.45; color: Qt.rgba(1.0, 0.35, 0.35, 0.5) }
                                            GradientStop { position: 1.0; color: Qt.rgba(1.0, 0.35, 0.35, 0.0) }
                                        }

                                        NumberAnimation on x {
                                            running: overtakeSweep.visible
                                            loops: Animation.Infinite
                                            from: -overtakeSweep.width
                                            to: ersBarTrack.width
                                            duration: 720
                                        }
                                    }

                                    Text {
                                        id: ersModeText
                                        anchors.centerIn: parent
                                        text: root.ersMode.toUpperCase()
                                        font.family: "B612Mono"
                                        font.pixelSize: 10
                                        font.bold: true
                                        color: root.ersModeTextColor(root.ersMode)
                                        style: Text.Outline
                                        styleColor: Qt.rgba(1, 1, 1, 0.35)

                                        SequentialAnimation on scale {
                                            running: energyPod.overtakeMode
                                            loops: Animation.Infinite
                                            NumberAnimation { to: 1.08; duration: 240; easing.type: Easing.OutQuad }
                                            NumberAnimation { to: 1.0; duration: 260; easing.type: Easing.InOutQuad }
                                        }
                                    }
                                }

                                Text {
                                    text: Math.round(root.clampPct(root.ersRemPct)) + "%"
                                    font.family: "B612Mono"
                                    font.pixelSize: 10
                                    font.bold: true
                                    color: root.ersModeFillColor(root.ersMode)
                                    Layout.preferredWidth: 34
                                    horizontalAlignment: Text.AlignRight
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 12
                                spacing: 4

                                MiniBar {
                                    Layout.fillWidth: true
                                    label: "H"
                                    value: root.ersHarvPct
                                    accent: "#ff7369"
                                }

                                MiniBar {
                                    Layout.fillWidth: true
                                    label: "D"
                                    value: root.ersDeployedPct
                                    accent: "#5ade8e"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    component MiniBar: Item {
        property string label: ""
        property real value: 0
        property color accent: "#ffffff"

        RowLayout {
            anchors.fill: parent
            spacing: 3

            Text {
                text: label
                font.family: "B612Mono"
                font.pixelSize: 8
                color: accent
                Layout.preferredWidth: 10
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: height / 2
                color: "#09111a"
                border.width: 1
                border.color: "#2d3d4c"
                clip: true

                Rectangle {
                    width: Math.max(0, root.clampPct(value) / 100 * parent.width)
                    height: parent.height
                    radius: parent.radius
                    color: accent
                    opacity: 0.88
                    Behavior on width { SmoothedAnimation { duration: 120 } }
                }
            }
        }
    }
}
