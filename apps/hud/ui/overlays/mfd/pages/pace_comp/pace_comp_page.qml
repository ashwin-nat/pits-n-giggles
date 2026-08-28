pragma ComponentBehavior: Bound
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
        "Alpine '26":            teamIconPrefix + "alpine.svg",
        "Aston Martin":          teamIconPrefix + "aston_martin.svg",
        "Aston Martin '24":      teamIconPrefix + "aston_martin.svg",
        "Aston Martin '26":      teamIconPrefix + "aston_martin.svg",
        "Ferrari":               teamIconPrefix + "ferrari.svg",
        "Ferrari '24":           teamIconPrefix + "ferrari.svg",
        "Ferrari '26":           teamIconPrefix + "ferrari.svg",
        "Haas":                  teamIconPrefix + "haas.svg",
        "Haas '24":              teamIconPrefix + "haas.svg",
        "Haas '26":              teamIconPrefix + "haas.svg",
        "McLaren":               teamIconPrefix + "mclaren.svg",
        "Mclaren":               teamIconPrefix + "mclaren.svg",
        "Mclaren '24":           teamIconPrefix + "mclaren.svg",
        "Mclaren '26":           teamIconPrefix + "mclaren.svg",
        "Mercedes":              teamIconPrefix + "mercedes.svg",
        "Mercedes '24":          teamIconPrefix + "mercedes.svg",
        "Mercedes '26":          teamIconPrefix + "mercedes.svg",
        "RB":                    teamIconPrefix + "rb.svg",
        "Rb '24":                teamIconPrefix + "rb.svg",
        "RB '26":                teamIconPrefix + "rb.svg",
        "VCARB":                 teamIconPrefix + "rb.svg",
        "Alpha Tauri":           teamIconPrefix + "rb.svg",
        "Red Bull":              teamIconPrefix + "red_bull.svg",
        "Red Bull Racing":       teamIconPrefix + "red_bull.svg",
        "Red Bull Racing '24":   teamIconPrefix + "red_bull.svg",
        "Red Bull Racing '26":   teamIconPrefix + "red_bull.svg",
        "Sauber":                teamIconPrefix + "sauber.svg",
        "Sauber '24":            teamIconPrefix + "sauber.svg",
        "Alfa Romeo":            teamIconPrefix + "sauber.svg",
        "Williams":              teamIconPrefix + "williams.svg",
        "Williams '24":          teamIconPrefix + "williams.svg",
        "Williams '26":          teamIconPrefix + "williams_26.svg",
        "Audi '26":              teamIconPrefix + "audi.svg",
        "Cadillac '26":          teamIconPrefix + "cadillac.svg"
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
    property var rows: []

    /* ─────────────────────────────────────────────────────
     * HELPERS
     * ───────────────────────────────────────────────────── */
    // Delta sign:  "+" → opponent faster → red (bad for ref)
    //              "-" → ref faster      → green
    //              ref row values are absolute times → accent
    function deltaColor(str, isRef) {
        if (isRef)  return "white"
        if (!str || str === "—" || str === "--:--") return colDim
        let first = str.charAt(0)
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
        anchors.margins: root.margins
        color: "transparent"

        readonly property int  headerH: 28
        readonly property real rowH: root.rows.length > 0 ? (height - headerH) / root.rows.length : 0

        // Waiting for data
        Text {
            anchors.centerIn: parent
            visible: root.rows.length === 0
            text: "WAITING FOR DATA"
            font.family: "Formula1"
            font.pixelSize: 11
            color: "#666666"
        }

        Column {
            anchors.fill: parent
            spacing: 0
            visible: root.rows.length > 0

            /* ── HEADER ── */
            Row {
                width: container.width
                height: container.headerH

                Repeater {
                    model: root.headers

                    Rectangle {
                        id: headerCell
                        required property string modelData
                        required property int index

                        width: container.width * root.colRatios[headerCell.index]
                        height: container.headerH
                        color: "#2a2a2a"
                        border.color: root.colGrid

                        Text {
                            anchors.centerIn: parent
                            text: headerCell.modelData
                            color: root.colAccent
                            font.family: root.fontFamily
                            font.pixelSize: root.fontSizeLabel
                            font.bold: true
                        }
                    }
                }
            }

            /* ── DATA ROWS ── */
            Repeater {
                model: root.rows.length

                delegate: Item {
                    id: rowItem
                    required property int index

                    width: container.width
                    height: container.rowH

                    property int  rowIndex: rowItem.index
                    property var  rd:       root.rows[rowItem.rowIndex] || {}
                    property bool isRef:    rd.isRef === true

                    // Row background
                    Rectangle {
                        anchors.fill: parent
                        color: rowItem.index % 2 === 0 ? "transparent" : root.colAltRow
                    }

                    // White border for ref row (on top of everything)
                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: rowItem.isRef ? "white" : root.colGrid
                        border.width: rowItem.isRef ? 2 : 0
                    }

                    Row {
                        anchors.fill: parent

                            /* POS */
                            Rectangle {
                                width: container.width * root.colRatios[0]
                                height: parent.height
                                color: "transparent"
                                border.color: root.colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.position || "—"
                                    color: rowItem.isRef ? "white" : root.colText
                                    font.family: root.fontFamily
                                    font.pixelSize: root.fontSizeLabel
                                    font.bold: true
                                }
                            }

                            /* DRIVER  (team logo + name) */
                            Rectangle {
                                width: container.width * root.colRatios[1]
                                height: parent.height
                                color: "transparent"
                                border.color: root.colGrid
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
                                    color: rowItem.isRef ? "white" : root.colText
                                    font.family: root.fontFamily
                                    font.pixelSize: root.fontSizeLabel
                                    font.bold: rowItem.isRef
                                    elide: Text.ElideRight
                                }
                            }

                            /* S1 */
                            Rectangle {
                                width: container.width * root.colRatios[2]
                                height: parent.height
                                color: "transparent"
                                border.color: root.colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.s1 || "—"
                                    color: root.deltaColor(rowItem.rd.s1, rowItem.isRef)
                                    font.family: root.monoFontFamily
                                    font.pixelSize: root.fontSizeMono
                                }
                            }

                            /* S2 */
                            Rectangle {
                                width: container.width * root.colRatios[3]
                                height: parent.height
                                color: "transparent"
                                border.color: root.colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.s2 || "—"
                                    color: root.deltaColor(rowItem.rd.s2, rowItem.isRef)
                                    font.family: root.monoFontFamily
                                    font.pixelSize: root.fontSizeMono
                                }
                            }

                            /* S3 */
                            Rectangle {
                                width: container.width * root.colRatios[4]
                                height: parent.height
                                color: "transparent"
                                border.color: root.colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.s3 || "—"
                                    color: root.deltaColor(rowItem.rd.s3, rowItem.isRef)
                                    font.family: root.monoFontFamily
                                    font.pixelSize: root.fontSizeMono
                                }
                            }

                            /* LAP */
                            Rectangle {
                                width: container.width * root.colRatios[5]
                                height: parent.height
                                color: "transparent"
                                border.color: root.colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text:  rowItem.rd.lap || "—"
                                    color: root.deltaColor(rowItem.rd.lap, rowItem.isRef)
                                    font.family: root.monoFontFamily
                                    font.pixelSize: root.fontSizeMono
                                    font.bold: true
                                }
                            }
                        }
                    }
                }
            }
        }
}

