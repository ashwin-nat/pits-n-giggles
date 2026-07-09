pragma ComponentBehavior: Bound
import QtQuick 2.15

Item {
    id: root
    property string title: "LAP TIMES"

    /* -----------------------------
     * CONFIG
     * ----------------------------- */
    readonly property int numRows: 5
    readonly property int numCols: 5

    readonly property var headers: ["Lap", "S1", "S2", "S3", "Time"]

    // Column width ratios (must sum to 1.0)
    readonly property var columnWidthRatios: [0.12, 0.22, 0.22, 0.22, 0.22]  // Lap, S1, S2, S3, Time

    readonly property color colText: "#e0e0e0"
    readonly property color colDim: "#808080"
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

    property var rows: [
        emptyRow(), emptyRow(), emptyRow(), emptyRow(), emptyRow()
    ]

    function emptyRow() {
        return [
            { text: "---", color: colDim },
            { text: "---", color: colDim },
            { text: "---", color: colDim },
            { text: "---", color: colDim },
            { text: "---", color: colDim }
        ]
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
                        height: parent.height
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
                model: root.numRows

                Rectangle {
                    id: rowRect
                    required property int index

                    width: container.width
                    height: (container.height - 35) / root.numRows
                    color: (rowRect.index % 2 === 0) ? "transparent" : root.colAltRow
                    border.color: root.colGrid

                    property int rowIndex: rowRect.index
                    property var rowData: (root.rows && root.rows.length > rowIndex) ? root.rows[rowIndex] : root.emptyRow()

                    Row {
                        anchors.fill: parent

                        Repeater {
                            id: cellRepeater
                            model: root.numCols

                            Rectangle {
                                id: cellRect
                                required property int index

                                width: container.width * root.columnWidthRatios[cellRect.index]
                                height: parent.height
                                color: "transparent"
                                border.color: root.colGrid

                                property int colIndex: cellRect.index
                                property var cellData: (rowRect.rowData && rowRect.rowData.length > colIndex) ?
                                                       rowRect.rowData[colIndex] :
                                                       { text: "???", color: root.colDim }

                                Text {
                                    anchors.centerIn: parent
                                    text: cellRect.cellData.text
                                    color: cellRect.cellData.color
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
