// pace_comp.qml
import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 400
    height: parent ? parent.height : 220

    /* REQUIRED BY MFD */
    property string title: "LAST LAP PACE COMP"

    /* FONT SIZE CONTROL */
    readonly property int baseFontSize: 13

    /* STRING-ONLY DATA (POPULATED BY PYTHON) */
    property var nextRow:   ({ name: "---", s1: "---", s2: "---", s3: "---", lap: "---" })
    property var playerRow: ({ name: "---", s1: "--:--.---", s2: "--:--.---", s3: "--:--.---", lap: "--:--.---" })
    property var prevRow:   ({ name: "---", s1: "---", s2: "---", s3: "---", lap: "---" })

    // Helper function to get color for delta values
    function getDeltaColor(valueStr) {
        if (valueStr === "---" || valueStr === "--:--.---") return "#ddd";

        // Check if it starts with + or -
        if (valueStr.startsWith("+")) return "#FF4444"; // Red for slower (positive)
        if (valueStr.startsWith("-")) return "#00FF00"; // Green for faster (negative)

        return "#ddd"; // Default
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 0

        // Table container
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Column {
                anchors.fill: parent
                spacing: 0

                // Header Row
                Rectangle {
                    width: parent.width
                    height: 35
                    color: "transparent"

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: "#555"
                    }

                    Row {
                        anchors.fill: parent
                        anchors.bottomMargin: 8
                        spacing: 0

                        Text {
                            width: 90
                            height: parent.height
                            text: "DRIVER"
                            color: "#888"
                            font.family: "Formula1"
                            font.pixelSize: baseFontSize - 2
                            font.bold: true
                            font.letterSpacing: 1.2
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignBottom
                        }
                        Text {
                            width: 70
                            height: parent.height
                            text: "S1"
                            color: "#888"
                            font.family: "Formula1"
                            font.pixelSize: baseFontSize - 2
                            font.bold: true
                            font.letterSpacing: 1.2
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignBottom
                        }
                        Text {
                            width: 70
                            height: parent.height
                            text: "S2"
                            color: "#888"
                            font.family: "Formula1"
                            font.pixelSize: baseFontSize - 2
                            font.bold: true
                            font.letterSpacing: 1.2
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignBottom
                        }
                        Text {
                            width: 70
                            height: parent.height
                            text: "S3"
                            color: "#888"
                            font.family: "Formula1"
                            font.pixelSize: baseFontSize - 2
                            font.bold: true
                            font.letterSpacing: 1.2
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignBottom
                        }
                        Text {
                            width: 84
                            height: parent.height
                            text: "LAP"
                            color: "#888"
                            font.family: "Formula1"
                            font.pixelSize: baseFontSize - 2
                            font.bold: true
                            font.letterSpacing: 1.2
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignBottom
                        }
                    }
                }

                Item { height: 10 }

                // PREV Row
                Item {
                    width: parent.width
                    height: 40

                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width
                        spacing: 0

                        Text {
                            width: 90
                            text: prevRow.name
                            color: "#bbb"
                            font.family: "Formula1"
                            font.pixelSize: baseFontSize - 2
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: prevRow.s1
                            color: getDeltaColor(prevRow.s1)
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: prevRow.s2
                            color: getDeltaColor(prevRow.s2)
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: prevRow.s3
                            color: getDeltaColor(prevRow.s3)
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 84
                            text: prevRow.lap
                            color: getDeltaColor(prevRow.lap)
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                }

                // PLAYER Row
                Item {
                    width: parent.width
                    height: 46

                    Rectangle {
                        anchors.fill: parent
                        anchors.leftMargin: -16
                        anchors.rightMargin: -16
                        color: "transparent"
                        border.color: "#FFFFFF"
                        border.width: 2
                    }

                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width
                        spacing: 0

                        Text {
                            width: 90
                            text: playerRow.name
                            color: "#FFFFFF"
                            font.family: "Formula1"
                            font.pixelSize: baseFontSize - 2
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: playerRow.s1
                            color: "#FFFFFF"
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: playerRow.s2
                            color: "#FFFFFF"
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: playerRow.s3
                            color: "#FFFFFF"
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 84
                            text: playerRow.lap
                            color: "#FFFFFF"
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                }

                // NEXT Row
                Item {
                    width: parent.width
                    height: 40

                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width
                        spacing: 0

                        Text {
                            width: 90
                            text: nextRow.name
                            color: "#bbb"
                            font.family: "Formula1"
                            font.pixelSize: baseFontSize - 2
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: nextRow.s1
                            color: getDeltaColor(nextRow.s1)
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: nextRow.s2
                            color: getDeltaColor(nextRow.s2)
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 70
                            text: nextRow.s3
                            color: getDeltaColor(nextRow.s3)
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        Text {
                            width: 84
                            text: nextRow.lap
                            color: getDeltaColor(nextRow.lap)
                            font.family: "B612 Mono"
                            font.pixelSize: baseFontSize
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }
    }
}
