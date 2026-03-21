import QtQuick
import QtQuick.Layouts

Item {
    id: root
    property string title: "TYRE WEAR INFO"

    /* ---------- ASSETS ---------- */
    property string iconSourcePrefix: "../../../../../../../assets/tyre-icons/"
    readonly property var tyreIcons: ({
        "Super Soft": iconSourcePrefix + "super_soft_tyre.svg",
        "Soft":       iconSourcePrefix + "soft_tyre.svg",
        "Medium":     iconSourcePrefix + "medium_tyre.svg",
        "Hard":       iconSourcePrefix + "hard_tyre.svg",
        "Inters":     iconSourcePrefix + "intermediate_tyre.svg",
        "Wet":        iconSourcePrefix + "wet_tyre.svg"
    })

    /* ---------- DATA ---------- */
    property string currentCompound: "—"
    property string currentCompoundVisual: ""
    property int    tyreAge: 0
    property real   wearRate: 0.0
    property bool   telemetryDisabled: false
    property var    wearTableData: []
    property var    tyreCounts: ({
        "Soft": 0, "Medium": 0, "Hard": 0,
        "Super Soft": 0, "Inters": 0, "Wet": 0
    })

    /* ---------- COLORS ---------- */
    readonly property color bgCard:      "#1b1b1b"
    readonly property color bgTable:     "#1a1a1a"
    readonly property color bgHeader:    "#2a2a2a"
    readonly property color bgAltRow:    "#222222"
    readonly property color borderColor: "#333333"
    readonly property color textColor:   "#e0e0e0"
    readonly property color dimColor:    "#808080"
    readonly property color accentColor: "#00D4FF"
    readonly property color okColor:     "#00ff88"
    readonly property color warnColor:   "#ffaa00"
    readonly property color dangerColor: "#ff4444"

    /* ---------- HELPERS ---------- */
    function isValid(v)   { return v !== undefined && v !== null && isFinite(v) }
    function wearText(v)  { return isValid(v) ? v.toFixed(2) + "%" : "—" }
    function wearColor(v) {
        if (!isValid(v)) return dimColor
        if (v < 50)      return okColor
        if (v < 75)      return warnColor
        return dangerColor
    }

    /* ---------- LAYOUT ---------- */
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        // ── Active tyre + inventory ──────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: bgCard
            radius: 8

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 12

                // Left: active tyre info
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 6

                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 8

                        Image {
                            Layout.preferredWidth: 28
                            Layout.preferredHeight: 28
                            source: root.tyreIcons[root.currentCompoundVisual] || ""
                            fillMode: Image.PreserveAspectFit
                            smooth: true; antialiasing: true; mipmap: true
                        }

                        Text {
                            text: root.currentCompound
                            font.family: "Formula1"
                            font.pixelSize: 14
                            font.bold: true
                            color: textColor
                        }

                        Rectangle { width: 1; height: 16; color: borderColor }

                        Text {
                            text: "Age"
                            font.family: "Formula1"
                            font.pixelSize: 11
                            color: dimColor
                        }

                        Text {
                            text: root.tyreAge + "L"
                            font.family: "Formula1"
                            font.pixelSize: 13
                            font.bold: true
                            color: accentColor
                        }
                    }

                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 6

                        Text {
                            text: "Wear Rate"
                            font.family: "Formula1"
                            font.pixelSize: 10
                            color: dimColor
                        }

                        Text {
                            text: root.wearRate > 0 ? root.wearRate.toFixed(2) + "%/L" : "—"
                            font.family: "Formula1"
                            font.pixelSize: 12
                            font.bold: true
                            color: accentColor
                        }
                    }
                }

                // Divider
                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.fillHeight: true
                    color: borderColor
                }

                // Right: tyre inventory
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 4

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "UNUSED SETS"
                        font.family: "Formula1"
                        font.pixelSize: 8
                        font.letterSpacing: 1
                        color: dimColor
                    }

                    // Row 1: Soft, Medium, Hard
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 8

                        Repeater {
                            model: ["Soft", "Medium", "Hard"]

                            RowLayout {
                                spacing: 2
                                property int count: root.tyreCounts[modelData]

                                Image {
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 20
                                    source: root.tyreIcons[modelData] || ""
                                    fillMode: Image.PreserveAspectFit
                                    smooth: true; antialiasing: true; mipmap: true
                                    opacity: count > 0 ? 1.0 : 0.3
                                }

                                Text {
                                    text: "×" + count
                                    font.family: "Formula1"
                                    font.pixelSize: 9
                                    font.bold: true
                                    color: count > 0 ? accentColor : dimColor
                                }
                            }
                        }
                    }

                    // Row 2: Super Soft, Inters, Wet
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 8

                        Repeater {
                            model: ["Super Soft", "Inters", "Wet"]

                            RowLayout {
                                spacing: 2
                                property int count: root.tyreCounts[modelData]

                                Image {
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 20
                                    source: root.tyreIcons[modelData] || ""
                                    fillMode: Image.PreserveAspectFit
                                    smooth: true; antialiasing: true; mipmap: true
                                    opacity: count > 0 ? 1.0 : 0.3
                                }

                                Text {
                                    text: "×" + count
                                    font.family: "Formula1"
                                    font.pixelSize: 9
                                    font.bold: true
                                    color: count > 0 ? accentColor : dimColor
                                }
                            }
                        }
                    }
                }
            }
        }

        // ── Wear table ───────────────────────────────────────────────────
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Text {
                anchors.centerIn: parent
                visible: root.telemetryDisabled
                text: "Telemetry disabled — wear data unavailable"
                font.family: "Formula1"
                font.pixelSize: 12
                color: dangerColor
            }

            Rectangle {
                id: tableRect
                anchors.fill: parent
                visible: !root.telemetryDisabled
                color: bgTable
                radius: 6
                clip: true

                readonly property int    headerH: 28
                readonly property int    numRows: root.wearTableData.length
                readonly property real   rowH:    numRows > 0 ? (height - headerH) / numRows : 36
                readonly property real   colW:    width / 5

                Column {
                    anchors.fill: parent
                    spacing: 0

                    // Header
                    Row {
                        width: tableRect.width
                        height: tableRect.headerH

                        Repeater {
                            model: ["LAP", "FL", "FR", "RL", "RR"]

                            Rectangle {
                                width: tableRect.colW
                                height: tableRect.headerH
                                color: bgHeader

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData
                                    font.family: "Formula1"
                                    font.pixelSize: 11
                                    font.bold: true
                                    color: accentColor
                                }
                            }
                        }
                    }

                    // Data rows
                    Repeater {
                        model: root.wearTableData

                        delegate: Rectangle {
                            id: rowRect
                            required property var modelData
                            required property int index

                            width: tableRect.width
                            height: tableRect.rowH
                            color: index % 2 === 0 ? "transparent" : bgAltRow

                            Row {
                                anchors.fill: parent

                                // Lap label
                                Item {
                                    width: tableRect.colW
                                    height: parent.height

                                    Text {
                                        anchors.centerIn: parent
                                        text: rowRect.modelData.label
                                        font.family: "Formula1"
                                        font.pixelSize: 12
                                        font.bold: true
                                        color: textColor
                                    }
                                }

                                // FL FR RL RR
                                WearCell { width: tableRect.colW; height: parent.height; value: rowRect.modelData.fl }
                                WearCell { width: tableRect.colW; height: parent.height; value: rowRect.modelData.fr }
                                WearCell { width: tableRect.colW; height: parent.height; value: rowRect.modelData.rl }
                                WearCell { width: tableRect.colW; height: parent.height; value: rowRect.modelData.rr }
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Components ───────────────────────────────────────────────────────
    component WearCell: Item {
        required property var value

        Text {
            anchors.centerIn: parent
            text: root.wearText(value)
            font.family: "B612 Mono"
            font.pixelSize: 12
            color: root.wearColor(value)
        }
    }
}
