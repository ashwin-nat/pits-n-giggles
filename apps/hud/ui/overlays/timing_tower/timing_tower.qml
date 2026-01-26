import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0
    property int numRows: 5  // Set by Python
    readonly property int rowHeight: 32
    readonly property int headerHeight: 40
    readonly property int margins: 25

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
        return width + 20; // Add padding
    }

    readonly property int baseHeight: headerHeight + (rowHeight * numRows) + margins

    width: baseWidth * scaleFactor
    height: baseHeight * scaleFactor
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    // Exposed properties for Python to set
    property string sessionInfo: "-- / --"
    property var tableData: []
    property int referenceRow: -1
    property string errorMessage: ""
    property bool showError: false

    // Global scaling root
    Item {
        id: scaledRoot
        anchors.centerIn: parent
        width: baseWidth
        height: baseHeight

        transform: Scale {
            xScale: scaleFactor
            yScale: scaleFactor
            origin.x: baseWidth / 2
            origin.y: baseHeight / 2
        }

        // Main container
        Rectangle {
            anchors.fill: parent
            anchors.margins: 5
            color: Qt.rgba(0.04, 0.04, 0.04, 0.86)
            radius: 8

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 5
                spacing: 5

                // Header section
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 35
                    color: Qt.rgba(0.06, 0.06, 0.06, 0.78)
                    radius: 5

                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width - 6
                        height: 25
                        color: Qt.rgba(0.16, 0.16, 0.16, 0.78)
                        radius: 3

                        Text {
                            anchors.centerIn: parent
                            text: sessionInfo
                            font.family: "Formula1"
                            font.pixelSize: 15
                            color: "#ffffff"
                        }
                    }
                }

                // Timing table section
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Qt.rgba(0.06, 0.06, 0.06, 0.86)
                    radius: 6

                    // Error message display
                    Text {
                        anchors.centerIn: parent
                        text: errorMessage
                        font.pixelSize: 12
                        font.bold: true
                        color: "#ffb86b"
                        visible: showError
                    }

                    // Column widths
                    QtObject {
                        id: cols
                        readonly property int pos: 40
                        readonly property int team: 30
                        readonly property int name: 160
                        readonly property int delta: 90
                        readonly property int tyre: 75
                        readonly property int ers: 75
                        readonly property int pens: 80
                    }

                    // Table content
                    ListView {
                        id: tableView
                        anchors.fill: parent
                        anchors.margins: 2
                        clip: true
                        interactive: false
                        visible: !showError

                        model: tableData

                        delegate: Rectangle {
                            width: tableView.width
                            height: 32
                            color: index % 2 === 0 ? Qt.rgba(0.1, 0.1, 0.1, 0.7) : Qt.rgba(0.08, 0.08, 0.08, 0.7)

                            // Reference row border
                            Rectangle {
                                anchors.fill: parent
                                color: "transparent"
                                border.color: "white"
                                border.width: modelData.isReference ? 2 : 0
                                radius: 2
                                visible: modelData.isReference
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
                                        anchors.centerIn: parent
                                        width: 20
                                        height: 20
                                        sourceSize.width: width * Screen.devicePixelRatio
                                        sourceSize.height: height * Screen.devicePixelRatio
                                        source: modelData.teamIcon || ""
                                        fillMode: Image.PreserveAspectFit
                                        smooth: true
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
                                Rectangle {
                                    width: showErsDrsInfo ? cols.ers : 0
                                    height: parent.height
                                    color: Qt.rgba(0.1, 0.1, 0.1, 0.7)
                                    visible: showErsDrsInfo

                                    Row {
                                        anchors.fill: parent
                                        spacing: 0

                                        // ERS bar (left)
                                        Rectangle {
                                            width: parent.width * 0.15
                                            height: parent.height
                                            color: {
                                                switch(modelData.ersMode) {
                                                    case "Medium": return "#ffff00"
                                                    case "Hotlap": return "#00ff00"
                                                    case "Overtake": return "#ff0000"
                                                    default: return "#888888"
                                                }
                                            }
                                            border.color: "black"
                                            border.width: 1
                                        }

                                        // ERS text (center)
                                        Text {
                                            width: parent.width * 0.70
                                            height: parent.height
                                            text: modelData.ers
                                            font.family: "Formula1"
                                            font.pixelSize: 12
                                            color: "white"
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }

                                        // DRS bar (right)
                                        Rectangle {
                                            width: parent.width * 0.15
                                            height: parent.height
                                            color: modelData.drs ? "#00ff00" : "#888888"
                                            border.color: "black"
                                            border.width: 1
                                        }
                                    }

                                    // Reference border overlay for ERS column
                                    Rectangle {
                                        anchors.fill: parent
                                        color: "transparent"
                                        border.color: "white"
                                        border.width: modelData.isReference ? 2 : 0
                                        visible: modelData.isReference
                                    }
                                }

                                // Penalties
                                Rectangle {
                                    width: showPens ? cols.pens : 0
                                    height: parent.height
                                    color: "transparent"
                                    visible: showPens

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.penalties
                                        font.family: "Formula1"
                                        font.pixelSize: 11
                                        color: "white"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        wrapMode: Text.NoWrap
                                        elide: Text.ElideRight
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
