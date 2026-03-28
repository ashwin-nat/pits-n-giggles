import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0
    property int numRows: 5  // Set by Python
    readonly property int rowHeight: 28
    readonly property int headerHeight: 34
    readonly property int margins: 20

    // Column toggle properties - set by Python
    property bool showTeamLogos: true
    property bool showTyreInfo: true
    property bool showDeltas: true
    property bool showErsDrsInfo: true
    property bool showPens: true

    // Dynamic width calculation based on enabled columns
    readonly property int baseWidth: {
        var width = cols.pos + cols.name;
        if (showTeamLogos) width += cols.team;
        if (showDeltas) width += cols.delta;
        if (showTyreInfo) width += cols.tyre;
        if (showErsDrsInfo) {
            // DRS bar needs extra space if pens are disabled
            // In the main layout, it spills into the pens column
            // this workaround is good enough
            width += showPens ? cols.ers : cols.ers + 10;
        }
        if (showPens) width += cols.pens;
        return width + 10; // Add padding
    }

    readonly property int baseHeight: headerHeight + (rowHeight * numRows) + margins

    width: (mode === "tt" ? ttBaseWidth : baseWidth) * scaleFactor
    height: (mode === "tt" ? ttBaseHeight : baseHeight) * scaleFactor
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    // Exposed properties for Python to set
    property string sessionInfo: "-- / --"
    property var tableData: []
    property int referenceRow: -1
    property string errorMessage: ""
    property bool showError: false
    property string mode: "race"  // "race" or "tt"
    property var ttTableData: []

    // TT mode column widths and dimensions
    readonly property int ttColLabel: 52
    readonly property int ttColLapTime: 85
    readonly property int ttColSector: 62
    // +34: accounts for nested margins (outer rect 8, layout 8, col 4) + 4 left margin + 10 right padding
    readonly property int ttBaseWidth: ttColLabel + ttColLapTime + ttColSector * 3 + 34
    readonly property int ttColHeaderHeight: 22
    readonly property int ttBaseHeight: headerHeight + ttColHeaderHeight + (rowHeight * 4) + margins

    // Global scaling root
    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: mode === "tt" ? ttBaseWidth : baseWidth
        height: mode === "tt" ? ttBaseHeight : baseHeight

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: scaledRoot.width / 2
            origin.y: scaledRoot.height / 2
        }

        // Main container
        Rectangle {
            anchors.fill: parent
            anchors.margins: 4
            color: Qt.rgba(0.04, 0.04, 0.06, 0.90)
            radius: 8

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 3

                // Header section
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 28
                    color: Qt.rgba(0.12, 0.12, 0.14, 0.95)
                    radius: 5

                    Text {
                        anchors.centerIn: parent
                        text: sessionInfo
                        font.family: "Formula1"
                        font.pixelSize: 13
                        color: "#cccccc"
                    }
                }

                // Timing table section
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"
                    radius: 6

                    // Error message display (race mode only)
                    Text {
                        anchors.centerIn: parent
                        text: errorMessage
                        font.pixelSize: 12
                        font.bold: true
                        color: "#ffb86b"
                        visible: showError && mode === "race"
                    }

                    // Column widths
                    QtObject {
                        id: cols
                        readonly property int pos: 30
                        readonly property int team: 25
                        readonly property int name: 120
                        readonly property int delta: 72
                        readonly property int tyre: 58
                        readonly property int ers: 58
                        readonly property int pens: 56
                    }

                    // Table content (race mode)
                    ListView {
                        id: tableView
                        anchors.fill: parent
                        anchors.margins: 2
                        clip: true
                        interactive: false
                        visible: !showError && mode === "race"

                        model: tableData

                        delegate: Item {
                            width: tableView.width
                            height: 28

                            // Row background
                            Rectangle {
                                anchors.fill: parent
                                color: modelData.isReference
                                    ? Qt.rgba(1, 1, 1, 0.07)
                                    : Qt.rgba(0.08, 0.08, 0.10, 0.6)
                                radius: 3
                            }

                            // Bottom separator
                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: 1
                                color: Qt.rgba(1, 1, 1, 0.05)
                            }

                            // Reference row left accent
                            Rectangle {
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                width: 2
                                height: parent.height - 6
                                color: modelData.isReference ? "#ffffff" : "transparent"
                                radius: 1
                            }

                            Row {
                                anchors.left: parent.left
                                anchors.leftMargin: 4
                                anchors.verticalCenter: parent.verticalCenter
                                height: parent.height
                                spacing: 0

                                // Position
                                Text {
                                    width: cols.pos
                                    height: parent.height
                                    text: modelData.position < 10 ? modelData.position + " " : modelData.position
                                    font.family: "Consolas"
                                    font.pixelSize: 12
                                    color: "#ddd"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                // Team icon
                                Item {
                                    width: showTeamLogos ? cols.team : 0
                                    height: parent.height
                                    visible: showTeamLogos

                                    Image {
                                        anchors.right: parent.right
                                        anchors.rightMargin: 4
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 20
                                        height: 20
                                        sourceSize.width: width * Screen.devicePixelRatio * 2
                                        sourceSize.height: height * Screen.devicePixelRatio * 2
                                        source: modelData.teamIcon || ""
                                        fillMode: Image.PreserveAspectFit
                                        smooth: true
                                        mipmap: true
                                        cache: true
                                        antialiasing: true
                                    }
                                }

                                // Driver name
                                Text {
                                    width: cols.name
                                    height: parent.height
                                    text: modelData.name
                                    font.family: "Formula1"
                                    font.pixelSize: 13
                                    color: "#ffffff"
                                    horizontalAlignment: Text.AlignLeft
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }

                                // Delta
                                Text {
                                    width: showDeltas ? cols.delta : 0
                                    height: parent.height
                                    text: modelData.delta
                                    font.family: "Consolas"
                                    font.pixelSize: 13
                                    color: "#ffffff"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    visible: showDeltas
                                }

                                // Tyre
                                Item {
                                    width: showTyreInfo ? cols.tyre : 0
                                    height: parent.height
                                    visible: showTyreInfo

                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 4

                                        Image {
                                            width: 20
                                            height: 20
                                            sourceSize.width: width * Screen.devicePixelRatio
                                            sourceSize.height: height * Screen.devicePixelRatio
                                            source: modelData.tyreIcon || ""
                                            fillMode: Image.PreserveAspectFit
                                            smooth: true
                                            anchors.verticalCenter: parent.verticalCenter
                                            cache: true
                                            antialiasing: true
                                        }

                                        Text {
                                            text: modelData.tyreWear
                                            font.family: "Consolas"
                                            font.pixelSize: 13
                                            color: "#ffffff"
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                    }
                                }

                                // ERS/DRS
                                Item {
                                    width: showErsDrsInfo ? cols.ers : 0
                                    height: parent.height
                                    visible: showErsDrsInfo

                                    // ERS mode strip (left)
                                    Rectangle {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 1
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 6
                                        height: parent.height - 8
                                        radius: 2
                                        color: {
                                            switch(modelData.ersMode) {
                                                case "Medium": return "#e6d800"
                                                case "Hotlap": return "#00e676"
                                                case "Overtake": return "#ff1744"
                                                default: return "#444444"
                                            }
                                        }
                                    }

                                    // ERS text (center)
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.ers
                                        font.family: "Consolas"
                                        font.pixelSize: 13
                                        color: "#dddddd"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }

                                    // DRS strip (right)
                                    Rectangle {
                                        anchors.right: parent.right
                                        anchors.rightMargin: 1
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 6
                                        height: parent.height - 8
                                        radius: 2
                                        color: modelData.drs ? "#00e676" : "#333333"
                                    }
                                }

                                // Penalties
                                Rectangle {
                                    width: showPens ? cols.pens : 0
                                    height: parent.height
                                    color: "transparent"
                                    visible: showPens

                                    Text {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 4
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: modelData.penalties
                                        font.family: "Formula1"
                                        font.pixelSize: 11
                                        color: "white"
                                        horizontalAlignment: Text.AlignLeft
                                        verticalAlignment: Text.AlignVCenter
                                        wrapMode: Text.NoWrap
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                        }
                    }

                    // TT table (time trial mode)
                    Column {
                        anchors.fill: parent
                        anchors.margins: 2
                        spacing: 0
                        visible: mode === "tt"

                        // Column headers
                        Row {
                            width: parent.width
                            height: ttColHeaderHeight

                            Text {
                                width: ttColLabel
                                height: parent.height
                                text: ""
                            }
                            Text {
                                width: ttColLapTime
                                height: parent.height
                                text: "LAP"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#888888"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            Text {
                                width: ttColSector
                                height: parent.height
                                text: "S1"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#888888"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            Text {
                                width: ttColSector
                                height: parent.height
                                text: "S2"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#888888"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            Text {
                                width: ttColSector
                                height: parent.height
                                text: "S3"
                                font.family: "Formula1"
                                font.pixelSize: 10
                                color: "#888888"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        Repeater {
                            model: ttTableData

                            delegate: Item {
                                width: parent.width
                                height: 28

                                Rectangle {
                                    anchors.fill: parent
                                    color: Qt.rgba(0.08, 0.08, 0.10, 0.6)
                                    radius: 3
                                }

                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    width: parent.width
                                    height: 1
                                    color: Qt.rgba(1, 1, 1, 0.05)
                                }

                                Row {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 4
                                    anchors.verticalCenter: parent.verticalCenter
                                    height: parent.height

                                    Text {
                                        width: ttColLabel
                                        height: parent.height
                                        text: modelData.label
                                        font.family: "Formula1"
                                        font.pixelSize: 12
                                        color: "#aaaaaa"
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Text {
                                        width: ttColLapTime
                                        height: parent.height
                                        text: modelData["lap-time-str"]
                                        font.family: "Consolas"
                                        font.pixelSize: 13
                                        color: "#ffffff"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Text {
                                        width: ttColSector
                                        height: parent.height
                                        text: modelData["s1-time-str"]
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: "#cccccc"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Text {
                                        width: ttColSector
                                        height: parent.height
                                        text: modelData["s2-time-str"]
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: "#cccccc"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    Text {
                                        width: ttColSector
                                        height: parent.height
                                        text: modelData["s3-time-str"]
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        color: "#cccccc"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
