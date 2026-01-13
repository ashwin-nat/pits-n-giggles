// pace_comp.qml
import QtQuick
import QtQuick.Layouts

Item {
    id: page
    width: parent ? parent.width : 400
    height: parent ? parent.height : 220

    /* REQUIRED BY MFD */
    property string title: "LAST LAP PACE COMP"

    /* STRING-ONLY DATA (POPULATED BY PYTHON) */
    property var nextRow:   ({ name: "---", s1: "---", s2: "---", s3: "---", lap: "---" })
    property var playerRow: ({ name: "---", s1: "--:--.---", s2: "--:--.---", s3: "--:--.---", lap: "--:--.---" })
    property var prevRow:   ({ name: "---", s1: "---", s2: "---", s3: "---", lap: "---" })

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        GridLayout {
            Layout.fillWidth: true
            columns: 5
            rowSpacing: 6
            columnSpacing: 12

            /* HEADER */
            Text { text: "DRIVER"; color: "#aaa"; font.family: "Formula1"; font.pixelSize: 12 }
            Text { text: "S1";     color: "#aaa"; font.family: "Formula1"; font.pixelSize: 12 }
            Text { text: "S2";     color: "#aaa"; font.family: "Formula1"; font.pixelSize: 12 }
            Text { text: "S3";     color: "#aaa"; font.family: "Formula1"; font.pixelSize: 12 }
            Text { text: "LAP";    color: "#aaa"; font.family: "Formula1"; font.pixelSize: 12 }

            /* PREV */
            Text { text: prevRow.name; color: "#ddd"; font.family: "Formula1"; font.pixelSize: 13 }
            Text { text: prevRow.s1;   color: "#ddd"; font.family: "Consolas"; font.pixelSize: 13 }
            Text { text: prevRow.s2;   color: "#ddd"; font.family: "Consolas"; font.pixelSize: 13 }
            Text { text: prevRow.s3;   color: "#ddd"; font.family: "Consolas"; font.pixelSize: 13 }
            Text { text: prevRow.lap;  color: "#ddd"; font.family: "Consolas"; font.pixelSize: 13 }

            /* PLAYER */
            Text { text: playerRow.name; color: "white"; font.family: "Formula1"; font.pixelSize: 14; font.bold: true }
            Text { text: playerRow.s1;   color: "white"; font.family: "Consolas"; font.pixelSize: 14; font.bold: true }
            Text { text: playerRow.s2;   color: "white"; font.family: "Consolas"; font.pixelSize: 14; font.bold: true }
            Text { text: playerRow.s3;   color: "white"; font.family: "Consolas"; font.pixelSize: 14; font.bold: true }
            Text { text: playerRow.lap;  color: "white"; font.family: "Consolas"; font.pixelSize: 14; font.bold: true }

            /* NEXT */
            Text { text: nextRow.name; color: "#ddd"; font.family: "Formula1"; font.pixelSize: 13 }
            Text { text: nextRow.s1;   color: "#ddd"; font.family: "Consolas"; font.pixelSize: 13 }
            Text { text: nextRow.s2;   color: "#ddd"; font.family: "Consolas"; font.pixelSize: 13 }
            Text { text: nextRow.s3;   color: "#ddd"; font.family: "Consolas"; font.pixelSize: 13 }
            Text { text: nextRow.lap;  color: "#ddd"; font.family: "Consolas"; font.pixelSize: 13 }
        }

        Item { Layout.fillHeight: true }
    }
}
