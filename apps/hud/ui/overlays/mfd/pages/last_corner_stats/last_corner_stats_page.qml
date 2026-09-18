import QtQuick

Item {
    id: root
    property string title: "LAST CORNER STATS"
    width: parent ? parent.width : 400
    height: parent ? parent.height : standaloneHeight

    // Read by standalone_wrapper.qml to size the host window — this page is
    // meant to be a short, wide strip, not the 220px MFD-page default.
    readonly property int standaloneHeight: 90

    /* ─────────────────────────────────────────────────────
     * DATA
     * ───────────────────────────────────────────────────── */
    property bool   hasData:        false
    property bool   hasName:        false
    property string cornerLabel:    ""
    property string cornerName:     ""
    property string minSpeedText:   "---"
    // Independent of hasData - a corner can be mid-accumulation while the
    // strip is still showing (or has nothing but) the previous corner's stats.
    property bool   isAccumulating: false

    /* ─────────────────────────────────────────────────────
     * STYLE
     * ───────────────────────────────────────────────────── */
    readonly property color  colText:   "#e0e0e0"
    readonly property color  colDim:    "#808080"
    readonly property color  colAccent: "#00D4FF"
    readonly property color  colRec:    "#FF3B30"
    readonly property string fontFamily: "Formula1"

    // Corner names vary a lot in length ("STOWE" vs "MASERATI-ASCARI-VARIANTE"),
    // the speed readout never exceeds a few characters — give the name column
    // most of the width instead of splitting the strip evenly.
    readonly property real cornerColRatio: 0.68

    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.35
    }

    Item {
        visible: root.hasData
        anchors.fill: parent
        anchors.margins: 12

        // Left — corner identity
        Column {
            id: cornerCol
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: parent.width * root.cornerColRatio - 8
            spacing: 4

            Text {
                // Kept in the layout (not visible:false) so the row below never
                // shifts position between named and unnamed corners — an empty
                // string still reserves the line, just renders nothing.
                width: cornerCol.width
                text: root.hasName ? root.cornerLabel : ""
                font.pixelSize: 12
                font.family: root.fontFamily
                color: root.colDim
                elide: Text.ElideRight
            }
            Text {
                width: cornerCol.width
                text: root.hasName ? root.cornerName : root.cornerLabel
                font.pixelSize: 20
                font.family: root.fontFamily
                color: root.colText
                elide: Text.ElideRight
            }
        }

        // Right — minimum speed
        Column {
            id: speedCol
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: parent.width * (1 - root.cornerColRatio) - 8
            spacing: 4

            Row {
                width: speedCol.width
                layoutDirection: Qt.RightToLeft
                spacing: 5

                Text {
                    text: "Min. Speed"
                    font.pixelSize: 12
                    font.family: root.fontFamily
                    color: root.colDim
                }

                // Accumulation indicator - sits inside the existing content
                // margin (not spanning to the window edge), so it's never
                // affected by the OS rounding the borderless window's
                // corners. Breathes slowly while a corner is being driven.
                Rectangle {
                    id: accumulatingDot
                    visible: root.isAccumulating
                    width: 7
                    height: 7
                    radius: width / 2
                    color: root.colRec
                    anchors.verticalCenter: parent.verticalCenter

                    SequentialAnimation on opacity {
                        running: root.isAccumulating
                        loops: Animation.Infinite
                        NumberAnimation { from: 1.0;  to: 0.25; duration: 1100; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 0.25; to: 1.0;  duration: 1100; easing.type: Easing.InOutSine }
                    }
                }
            }
            Text {
                width: speedCol.width
                text: root.minSpeedText
                horizontalAlignment: Text.AlignRight
                font.pixelSize: 20
                font.family: root.fontFamily
                color: root.colAccent
            }
        }
    }
}
