import QtQuick
import QtQuick.Layouts

Window {
    id: root

    property real scaleFactor: 1.0
    property bool minOverlayStyle: false

    readonly property int baseWidth:  minOverlayStyle ? 145 : 280
    readonly property int baseHeight: minOverlayStyle ? 76  : 180

    width:  baseWidth  * scaleFactor
    height: baseHeight * scaleFactor
    color: "#000000"

    // Exposed properties for Python to update
    property string currentTime: "--:--.---"
    property string currentColor: "#00FFFF"
    property string deltaTime: "---"
    property string deltaColor: "#FFFFFF"
    property string lastTime: "--:--.---"
    property string bestTime: "--:--.---"
    property string estimatedTime: "--:--.---"

    // Sector status arrays (-2=NA, -1=Invalid, 0=Yellow, 1=Green, 2=Purple)
    property var currentSectorStatus: [-2, -2, -2]
    property var lastSectorStatus:    [-2, -2, -2]
    property var bestSectorStatus:    [-2, -2, -2]

    // ── Design tokens ────────────────────────────────────────────────────────
    readonly property color bgBase:    "#0c0c10"
    readonly property color bgHero:    "#14141c"
    readonly property color bgCard:    "#0f0f14"
    readonly property color bgFooter:  "#141418"
    readonly property color divider:   "#26263a"
    readonly property color labelClr:  "#55556e"
    readonly property color textClr:   "#c4c4d4"

    // ── Scaled root ──────────────────────────────────────────────────────────
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

        // ════════════════════════════════════════════════════════════════════
        //  FULL OVERLAY
        // ════════════════════════════════════════════════════════════════════
        Rectangle {
            anchors.fill: parent
            color: bgBase
            visible: !root.minOverlayStyle

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // ── HERO: current lap + delta ─────────────────────────────
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 87
                    color: bgHero

                    // Coloured left accent bar
                    Rectangle {
                        width: 3
                        height: parent.height
                        color: root.currentColor
                        opacity: 0.85
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.leftMargin:   10
                        anchors.rightMargin:  10
                        anchors.topMargin:    8
                        anchors.bottomMargin: 6
                        spacing: 4

                        // Top row: label + time on left, delta on right
                        RowLayout {
                            Layout.fillWidth:  true
                            Layout.fillHeight: true
                            spacing: 8

                            // Left column: label + big time
                            ColumnLayout {
                                Layout.fillWidth:  true
                                Layout.fillHeight: true
                                spacing: 3

                                Text {
                                    text: "CURRENT"
                                    font.family: "Formula1"
                                    font.pixelSize: 9
                                    font.letterSpacing: 1.5
                                    color: labelClr
                                }

                                Text {
                                    text: root.currentTime
                                    font.family: "B612 Mono"
                                    font.pixelSize: 22
                                    font.weight: Font.Bold
                                    color: root.currentColor
                                }

                                Item { Layout.fillHeight: true }
                            }

                            // Right column: label + delta value (fixed width, right-aligned)
                            ColumnLayout {
                                Layout.preferredWidth: 76
                                Layout.alignment: Qt.AlignTop
                                spacing: 3

                                Text {
                                    text: "DELTA"
                                    font.family: "Formula1"
                                    font.pixelSize: 9
                                    font.letterSpacing: 1.5
                                    color: labelClr
                                    Layout.fillWidth: true
                                    horizontalAlignment: Text.AlignRight
                                }

                                Text {
                                    text: root.deltaTime
                                    font.family: "B612 Mono"
                                    font.pixelSize: 18
                                    font.weight: Font.Bold
                                    color: root.deltaColor
                                    Layout.fillWidth: true
                                    horizontalAlignment: Text.AlignRight
                                }
                            }
                        }

                        // Full-width sector bar at the bottom of the hero
                        SectorStatusBar {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 9
                            sectorStatus: root.currentSectorStatus
                        }
                    }
                }

                // Divider
                Rectangle { Layout.fillWidth: true; height: 1; color: divider }

                // ── LAST / BEST row ───────────────────────────────────────
                RowLayout {
                    Layout.fillWidth:    true
                    Layout.preferredHeight: 57
                    spacing: 0

                    // LAST card
                    Rectangle {
                        Layout.fillWidth:  true
                        Layout.fillHeight: true
                        color: bgCard

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.leftMargin:   8
                            anchors.rightMargin:  6
                            anchors.topMargin:    6
                            anchors.bottomMargin: 6
                            spacing: 3

                            Text {
                                text: "LAST"
                                font.family: "Formula1"
                                font.pixelSize: 9
                                font.letterSpacing: 1.2
                                color: labelClr
                            }

                            Text {
                                text: root.lastTime
                                font.family: "B612 Mono"
                                font.pixelSize: 14
                                font.weight: Font.Bold
                                color: textClr
                            }

                            Item { Layout.fillHeight: true }

                            SectorStatusBar {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 5
                                sectorStatus: root.lastSectorStatus
                            }
                        }
                    }

                    // Vertical divider
                    Rectangle { width: 1; Layout.fillHeight: true; color: divider }

                    // BEST card
                    Rectangle {
                        Layout.fillWidth:  true
                        Layout.fillHeight: true
                        color: bgCard

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.leftMargin:   8
                            anchors.rightMargin:  6
                            anchors.topMargin:    6
                            anchors.bottomMargin: 6
                            spacing: 3

                            RowLayout {
                                spacing: 5

                                Text {
                                    text: "BEST"
                                    font.family: "Formula1"
                                    font.pixelSize: 9
                                    font.letterSpacing: 1.2
                                    color: labelClr
                                }

                                // Purple pip — signals personal best / purple sector colour
                                Rectangle {
                                    width: 5; height: 5; radius: 2.5
                                    color: "#9b30ff"
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }

                            Text {
                                text: root.bestTime
                                font.family: "B612 Mono"
                                font.pixelSize: 14
                                font.weight: Font.Bold
                                color: "#00e060"
                            }

                            Item { Layout.fillHeight: true }

                            SectorStatusBar {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 5
                                sectorStatus: root.bestSectorStatus
                            }
                        }
                    }
                }

                // Divider
                Rectangle { Layout.fillWidth: true; height: 1; color: divider }

                // ── ESTIMATED footer ──────────────────────────────────────
                Rectangle {
                    Layout.fillWidth:    true
                    Layout.preferredHeight: 34
                    color: bgFooter

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin:   10
                        anchors.rightMargin:  10
                        anchors.topMargin:    2
                        anchors.bottomMargin: 2
                        spacing: 0

                        Text {
                            text: "EST"
                            font.family: "Formula1"
                            font.pixelSize: 9
                            font.letterSpacing: 1.5
                            color: labelClr
                        }

                        Item { Layout.fillWidth: true }

                        Text {
                            text: root.estimatedTime
                            font.family: "B612 Mono"
                            font.pixelSize: 13
                            font.weight: Font.Bold
                            color: "#9090a8"
                        }
                    }
                }
            }
        }

        // ════════════════════════════════════════════════════════════════════
        //  MINIMAL OVERLAY
        // ════════════════════════════════════════════════════════════════════
        Rectangle {
            anchors.fill: parent
            color: bgHero
            visible: root.minOverlayStyle

            // Left accent bar
            Rectangle {
                width: 3
                height: parent.height
                color: root.currentColor
                opacity: 0.85
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin:   10
                anchors.rightMargin:  8
                anchors.topMargin:    6
                anchors.bottomMargin: 6
                spacing: 3

                Text {
                    text: root.currentTime
                    font.family: "B612 Mono"
                    font.pixelSize: 20
                    font.weight: Font.Bold
                    color: root.currentColor
                    Layout.alignment: Qt.AlignHCenter
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                }

                Text {
                    text: root.deltaTime
                    font.family: "B612 Mono"
                    font.pixelSize: 13
                    font.weight: Font.Bold
                    color: root.deltaColor
                    Layout.alignment: Qt.AlignHCenter
                }

                SectorStatusBar {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 9
                    sectorStatus: root.currentSectorStatus
                }
            }
        }
    }

    // ── SectorStatusBar ──────────────────────────────────────────────────────
    // Renders three rounded pill segments with a small gap between each.
    component SectorStatusBar: Canvas {
        id: canvas
        property var sectorStatus: [-2, -2, -2]

        onSectorStatusChanged: requestPaint()

        onPaint: {
            let ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            let segW = width / 3

            let colors = {
                "-2": "#222235",   // NA  – near-invisible
                "-1": "#dc3545",   // Invalid
                "0":  "#ffc107",   // Yellow
                "1":  "#28a745",   // Green
                "2":  "#9b30ff"    // Purple
            }

            for (let i = 0; i < 3; i++) {
                let x = i * segW
                let y = 0
                let w = segW
                let h = height

                ctx.fillStyle = colors[sectorStatus[i].toString()] || "#222235"

                ctx.beginPath()
                ctx.rect(x, y, w, h)
                ctx.closePath()
                ctx.fill()
            }

            // Black separator lines between sectors
            ctx.strokeStyle = "#000000"
            ctx.lineWidth = 2
            for (let i = 1; i < 3; i++) {
                let x = Math.round(i * segW)
                ctx.beginPath()
                ctx.moveTo(x, 0)
                ctx.lineTo(x, height)
                ctx.stroke()
            }
        }
    }
}
