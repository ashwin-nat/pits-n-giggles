import QtQuick 2.15

Item {
    id: root
    property string title: "PACE COMPARISON"

    /* ─────────────────────────────────────────────────────
     * CONFIG
     * ───────────────────────────────────────────────────── */
    readonly property var    headers:   ["POS", "DRIVER", "S1", "S2", "S3", "LAP"]
    readonly property var    colRatios: [0.06,   0.30,    0.16, 0.16, 0.16, 0.16]

    readonly property color  colText:    "#e0e0e0"
    readonly property color  colDim:     "#808080"
    readonly property color  colGrid:    "#333333"
    readonly property color  colAltRow:  "#252525"
    readonly property color  colAccent:  "#00D4FF"
    readonly property color  colGreen:   "#00ff88"   // ref faster than opponent
    readonly property color  colRed:     "#ff4444"   // opponent faster than ref
    readonly property string fontFamily:     "Formula1"
    readonly property string monoFontFamily: "B612 Mono"
    readonly property int    fontSizeLabel:  10   // POS and driver name
    readonly property int    fontSizeMono:   11   // all numeric values — tweak here
    readonly property int    margins:    8

    /* ─────────────────────────────────────────────────────
     * TEAM LOGOS
     * ───────────────────────────────────────────────────── */
    readonly property string teamIconPrefix: "../../../../../../../assets/team-logos/"
    readonly property var teamIcons: ({
        "Alpine":                teamIconPrefix + "alpine.svg",
        "Alpine '24":            teamIconPrefix + "alpine.svg",
        "Aston Martin":          teamIconPrefix + "aston_martin.svg",
        "Aston Martin '24":      teamIconPrefix + "aston_martin.svg",
        "Ferrari":               teamIconPrefix + "ferrari.svg",
        "Ferrari '24":           teamIconPrefix + "ferrari.svg",
        "Haas":                  teamIconPrefix + "haas.svg",
        "Haas '24":              teamIconPrefix + "haas.svg",
        "McLaren":               teamIconPrefix + "mclaren.svg",
        "Mclaren":               teamIconPrefix + "mclaren.svg",
        "Mclaren '24":           teamIconPrefix + "mclaren.svg",
        "Mercedes":              teamIconPrefix + "mercedes.svg",
        "Mercedes '24":          teamIconPrefix + "mercedes.svg",
        "RB":                    teamIconPrefix + "rb.svg",
        "Rb '24":                teamIconPrefix + "rb.svg",
        "VCARB":                 teamIconPrefix + "rb.svg",
        "Alpha Tauri":           teamIconPrefix + "rb.svg",
        "Red Bull":              teamIconPrefix + "red_bull.svg",
        "Red Bull Racing":       teamIconPrefix + "red_bull.svg",
        "Red Bull Racing '24":   teamIconPrefix + "red_bull.svg",
        "Sauber":                teamIconPrefix + "sauber.svg",
        "Sauber '24":            teamIconPrefix + "sauber.svg",
        "Alfa Romeo":            teamIconPrefix + "sauber.svg",
        "Williams":              teamIconPrefix + "williams.svg",
        "Williams '24":          teamIconPrefix + "williams.svg"
    })
    readonly property string defaultTeamIcon: teamIconPrefix + "default.svg"

    /* ─────────────────────────────────────────────────────
     * DATA  (Python sets these)
     *
     * rows: list of {
     *   position: string,
     *   team:     string  (team name for icon lookup),
     *   name:     string,
     *   s1, s2, s3, lap: string  (absolute for ref, signed delta for others),
     *   isRef:    bool
     * }
     * Not padded — Repeater model matches rows.length exactly.
     * ───────────────────────────────────────────────────── */
    property var rows:        []
    property int rowsVersion: 0

    /* ─────────────────────────────────────────────────────
     * HELPERS
     * ───────────────────────────────────────────────────── */
    // Delta sign:  "+" → opponent faster → red (bad for ref)
    //              "-" → ref faster      → green
    //              ref row values are absolute times → accent
    function deltaColor(str, isRef) {
        if (isRef)  return "white"
        if (!str || str === "—" || str === "--:--") return colDim
        var first = str.charAt(0)
        if (first === "+") return colRed
        if (first === "-") return colGreen
        return colDim
    }

    /* ─────────────────────────────────────────────────────
     * LAYOUT
     * ───────────────────────────────────────────────────── */
    Rectangle {
        id: container
        anchors.fill: parent
        anchors.margins: margins
        color: "transparent"

        readonly property int  headerH: 28
        readonly property real rowH: rows.length > 0 ? (height - headerH) / rows.length : 0

        Column {
            anchors.fill: parent
            spacing: 0

            /* ── HEADER ── */
            Row {
                width: container.width
                height: container.headerH

                Repeater {
                    model: headers

                    Rectangle {
                        width: container.width * colRatios[index]
                        height: container.headerH
                        color: "#2a2a2a"
                        border.color: colGrid

                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: colAccent
                            font.family: fontFamily
                            font.pixelSize: fontSizeLabel
                            font.bold: true
                        }
                    }
                }
            }

            /* ── DATA ROWS ── */
            Repeater {
                model: rows.length

                delegate: Item {
                    id: rowItem

                    width: container.width
                    height: container.rowH

                    property int  rowIndex: index
                    property var  rd:       root.rows[rowIndex] || {}
                    property bool isRef:    rd.isRef === true

                    // Row background
                    Rectangle {
                        anchors.fill: parent
                        color: index % 2 === 0 ? "transparent" : colAltRow
                    }

                    // White border for ref row (on top of everything)
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: rowItem.isRef ? "white" : colGrid
                        border.width: rowItem.isRef ? 2 : 0
                    }

                    Row {
                        anchors.fill: parent

                            /* POS */
                            Rectangle {
                                width: container.width * colRatios[0]
                                height: parent.height
                                color: "transparent"
                                border.color: colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.position || "—"
                                    color: rowItem.isRef ? "white" : colText
                                    font.family: fontFamily
                                    font.pixelSize: fontSizeLabel
                                    font.bold: true
                                }
                            }

                            /* DRIVER  (team logo + name) */
                            Rectangle {
                                width: container.width * colRatios[1]
                                height: parent.height
                                color: "transparent"
                                border.color: colGrid
                                clip: true

                                Image {
                                    id: teamLogo
                                    anchors {
                                        left: parent.left
                                        leftMargin: 3
                                        verticalCenter: parent.verticalCenter
                                    }
                                    width: 16
                                    height: 16
                                    source: root.teamIcons[rowItem.rd.team] || root.defaultTeamIcon
                                    fillMode: Image.PreserveAspectFit
                                    smooth: true
                                    mipmap: true
                                }

                                Text {
                                    anchors {
                                        left:           teamLogo.right
                                        leftMargin:     4
                                        right:          parent.right
                                        rightMargin:    4
                                        verticalCenter: parent.verticalCenter
                                    }
                                    text:  rowItem.rd.name || "—"
                                    color: rowItem.isRef ? "white" : colText
                                    font.family: fontFamily
                                    font.pixelSize: fontSizeLabel
                                    font.bold: rowItem.isRef
                                    elide: Text.ElideRight
                                }
                            }

                            /* S1 */
                            Rectangle {
                                width: container.width * colRatios[2]
                                height: parent.height
                                color: "transparent"
                                border.color: colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.s1 || "—"
                                    color: deltaColor(rowItem.rd.s1, rowItem.isRef)
                                    font.family: monoFontFamily
                                    font.pixelSize: fontSizeMono
                                }
                            }

                            /* S2 */
                            Rectangle {
                                width: container.width * colRatios[3]
                                height: parent.height
                                color: "transparent"
                                border.color: colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.s2 || "—"
                                    color: deltaColor(rowItem.rd.s2, rowItem.isRef)
                                    font.family: monoFontFamily
                                    font.pixelSize: fontSizeMono
                                }
                            }

                            /* S3 */
                            Rectangle {
                                width: container.width * colRatios[4]
                                height: parent.height
                                color: "transparent"
                                border.color: colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.s3 || "—"
                                    color: deltaColor(rowItem.rd.s3, rowItem.isRef)
                                    font.family: monoFontFamily
                                    font.pixelSize: fontSizeMono
                                }
                            }

                            /* LAP */
                            Rectangle {
                                width: container.width * colRatios[5]
                                height: parent.height
                                color: "transparent"
                                border.color: colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.lap || "—"
                                    color: deltaColor(rowItem.rd.lap, rowItem.isRef)
                                    font.family: monoFontFamily
                                    font.pixelSize: fontSizeMono
                                    font.bold: true
                                }
                            }
                        }
                    }
                }
            }
        }
}

