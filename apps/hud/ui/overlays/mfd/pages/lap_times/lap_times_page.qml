pragma ComponentBehavior: Bound
import QtQuick 2.15
import "../../../base"

Item {
    id: root
    property string title: "LAP TIMES"

    /* -----------------------------
     * CONFIG
     * ----------------------------- */
    readonly property int numRows: 5

    readonly property var headers: ["Lap", "S1", "S2", "S3", "Time"]

    // Column width ratios (must sum to 1.0)
    readonly property var columnWidthRatios: [0.12, 0.22, 0.22, 0.22, 0.22]  // Lap, S1, S2, S3, Time

    readonly property color colText: "#e0e0e0"
    readonly property color colGrid: "#333333"
    readonly property color colAltRow: "#252525"

    readonly property color colRed: "red"
    readonly property color colGreen: "lime"
    readonly property color colPurple: "magenta"

    readonly property string fontFamily: "Formula1"
    readonly property int fontSize: 12

    readonly property int margins: 8  // Padding around the table

    /* -----------------------------
     * DATA MODEL
     * Python updates this ONLY
     * ----------------------------- */

    // One payload per tick from TableDiffer, applied by DiffedTableModel.
    // Python seeds the blank rows on page activation, so every value in the
    // model is a string and the roles keep the types the first append() gave
    // them.
    property var tableUpdate: null

    DiffedTableModel {
        id: tableModel
        tableUpdate: root.tableUpdate
    }

    /* -----------------------------
     * LAYOUT
     * ----------------------------- */

    Rectangle {
        id: container
        anchors.fill: parent
        anchors.margins: root.margins
        color: "transparent"

        Column {
            anchors.fill: parent
            spacing: 0

            /* ---------- HEADER ---------- */
            Row {
                width: parent.width
                height: Math.max(35, (parent.height - (root.numRows * Math.max(40, (parent.height - 35) / (root.numRows + 1)))))

                Repeater {
                    model: root.headers
                    Rectangle {
                        id: headerCell
                        required property int index
                        required property string modelData

                        width: container.width * root.columnWidthRatios[headerCell.index]
                        height: parent ? parent.height : 0
                        color: "#2a2a2a"
                        border.color: root.colGrid
                        Text {
                            anchors.centerIn: parent
                            text: headerCell.modelData
                            color: root.colText
                            font.family: root.fontFamily
                            font.pixelSize: root.fontSize
                            font.bold: true
                        }
                    }
                }
            }

            /* ---------- ROWS ---------- */
            Repeater {
                id: rowRepeater
                model: tableModel

                Rectangle {
                    id: rowRect
                    required property int index
                    required property string lapText
                    required property string lapColour
                    required property string s1Text
                    required property string s1Colour
                    required property string s2Text
                    required property string s2Colour
                    required property string s3Text
                    required property string s3Colour
                    required property string timeText
                    required property string timeColour

                    // Roles are flat (one per cell) because ListModel.set()
                    // cannot patch a nested list role; the columns are gathered
                    // back into a list here purely to drive the cell Repeater.
                    readonly property var cells: [
                        { text: rowRect.lapText,  colour: rowRect.lapColour  },
                        { text: rowRect.s1Text,   colour: rowRect.s1Colour   },
                        { text: rowRect.s2Text,   colour: rowRect.s2Colour   },
                        { text: rowRect.s3Text,   colour: rowRect.s3Colour   },
                        { text: rowRect.timeText, colour: rowRect.timeColour }
                    ]

                    width: container.width
                    height: (container.height - 35) / root.numRows
                    color: (rowRect.index % 2 === 0) ? "transparent" : root.colAltRow
                    border.color: root.colGrid

                    Row {
                        anchors.fill: parent

                        Repeater {
                            id: cellRepeater
                            model: rowRect.cells

                            Rectangle {
                                id: cellRect
                                required property int index
                                required property var modelData

                                width: container.width * root.columnWidthRatios[cellRect.index]
                                height: parent ? parent.height : 0
                                color: "transparent"
                                border.color: root.colGrid

                                Text {
                                    anchors.centerIn: parent
                                    text: cellRect.modelData.text
                                    color: cellRect.modelData.colour
                                    font.family: root.fontFamily
                                    font.pixelSize: root.fontSize
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideNone
                                }
                            }
                        }
                    }
                }
            }
        }
    }

}
