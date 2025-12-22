import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: root
    visible: true

    property real scaleFactor: 1.0
    property int numRows: 5  // Set by Python
    readonly property int baseWidth: 550
    readonly property int rowHeight: 32
    readonly property int headerHeight: 40
    readonly property int margins: 25
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

                    // Table header (invisible but defines column structure)
                    // COLUMN WIDTH CONFIGURATION - Adjust these values to change column widths
                    Item {
                        id: tableHeader
                        width: parent.width
                        height: 0
                        visible: false

                        readonly property int posWidth: 40      // Position column
                        readonly property int teamWidth: 30     // Team icon column
                        readonly property int nameWidth: 160    // Driver name column
                        readonly property int deltaWidth: 90    // Delta/gap column
                        readonly property int tyreWidth: 75     // Tyre info column
                        readonly property int ersWidth: 75      // ERS/DRS column
                        readonly property int pensWidth: 80     // Penalties column
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

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 4
                                anchors.rightMargin: 4
                                spacing: 0

                                // Position
                                Text {
                                    Layout.preferredWidth: tableHeader.posWidth
                                    Layout.fillHeight: true
                                    text: modelData.position < 10 ? modelData.position + " " : modelData.position
                                    font.family: "Consolas"
                                    font.pixelSize: 12
                                    color: "#ddd"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                // Team icon
                                Item {
                                    Layout.preferredWidth: tableHeader.teamWidth
                                    Layout.fillHeight: true

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
                                    }
                                }

                                // Driver name
                                Text {
                                    Layout.preferredWidth: tableHeader.nameWidth
                                    Layout.fillHeight: true
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
                                    Layout.preferredWidth: tableHeader.deltaWidth
                                    Layout.fillHeight: true
                                    text: modelData.delta
                                    font.family: "Consolas"
                                    font.pixelSize: 13
                                    color: "#ffffff"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                // Tyre
                                Item {
                                    Layout.preferredWidth: tableHeader.tyreWidth
                                    Layout.fillHeight: true

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
                                    Layout.preferredWidth: tableHeader.ersWidth
                                    Layout.fillHeight: true
                                    color: Qt.rgba(0.1, 0.1, 0.1, 0.7)

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
                                Text {
                                    Layout.preferredWidth: tableHeader.pensWidth
                                    Layout.fillHeight: true
                                    text: modelData.penalties
                                    font.family: "Formula1"
                                    font.pixelSize: 11
                                    color: "#ffcc00"
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
