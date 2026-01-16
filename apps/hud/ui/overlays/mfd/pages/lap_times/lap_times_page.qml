import QtQuick 2.15
import QtQuick.Controls 2.15

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

    property int rowsVersion: 0  // Version counter to force updates

    function emptyRow() {
        return [
            { text: "---", color: colDim },
            { text: "---", color: colDim },
            { text: "---", color: colDim },
            { text: "---", color: colDim },
            { text: "---", color: colDim }
        ]
    }

    // Debug: monitor property changes
    // onRowsChanged: {
    //     console.log("QML: Rows property changed! Length:", rows.length)
    //     if (rows.length > 0) {
    //         console.log("QML: First row:", JSON.stringify(rows[0]))
    //     }
    // }

    // onRowsVersionChanged: {
    //     console.log("QML: rowsVersion changed to:", rowsVersion)
    // }

    /* -----------------------------
     * LAYOUT
     * ----------------------------- */

    Rectangle {
        id: container
        anchors.fill: parent
        anchors.margins: margins
        color: "transparent"

        Column {
            anchors.fill: parent
            spacing: 0

            /* ---------- HEADER ---------- */
            Row {
                width: parent.width
                height: Math.max(35, (parent.height - (numRows * Math.max(40, (parent.height - 35) / (numRows + 1)))))

                Repeater {
                    model: headers
                    Rectangle {
                        width: container.width * columnWidthRatios[index]
                        height: parent.height
                        color: "#2a2a2a"
                        border.color: colGrid
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: colText
                            font.family: fontFamily
                            font.pixelSize: fontSize
                            font.bold: true
                        }
                    }
                }
            }

            /* ---------- ROWS ---------- */
            Repeater {
                id: rowRepeater
                model: numRows

                Rectangle {
                    id: rowRect
                    width: container.width
                    height: (container.height - 35) / numRows
                    color: (index % 2 === 0) ? "transparent" : colAltRow
                    border.color: colGrid

                    property int rowIndex: index
                    property var rowData: (root.rows && root.rows.length > rowIndex) ? root.rows[rowIndex] : root.emptyRow()

                    Row {
                        anchors.fill: parent

                        Repeater {
                            id: cellRepeater
                            model: numCols

                            Rectangle {
                                id: cellRect
                                width: container.width * columnWidthRatios[index]
                                height: parent.height
                                color: "transparent"
                                border.color: colGrid

                                property int colIndex: index
                                property var cellData: (rowRect.rowData && rowRect.rowData.length > colIndex) ?
                                                       rowRect.rowData[colIndex] :
                                                       { text: "???", color: root.colDim }

                                Text {
                                    anchors.centerIn: parent
                                    text: cellRect.cellData.text
                                    color: cellRect.cellData.color
                                    font.family: fontFamily
                                    font.pixelSize: fontSize
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

    /* -----------------------------
     * HELPER API (KEPT FOR COMPATIBILITY)
     * ----------------------------- */

    function clearTable() {
        rows = [
            emptyRow(), emptyRow(), emptyRow(), emptyRow(), emptyRow()
        ]
        rowsVersion++
    }
}
